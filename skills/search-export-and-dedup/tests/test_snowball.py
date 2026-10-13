"""Tests for snowball.py. OpenAlex is mocked; no network is used."""

import csv
import importlib.util
import io
import json
import urllib.error
import urllib.parse
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE.parents[0] / "scripts" / "snowball.py"
DEDUP_PATH = HERE.parents[0] / "scripts" / "dedup.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def sb():
    return load(MODULE_PATH, "lrs_snowball")


def work(wid, doi, title, year=2020, pmid=None):
    w = {"id": f"https://openalex.org/{wid}", "doi": f"https://doi.org/{doi}" if doi else None,
         "title": title, "publication_year": year,
         "authorships": [{"author": {"display_name": "Ada Lovelace"}}, {"author": {"display_name": "C Babbage"}}],
         "primary_location": {"source": {"display_name": "Nature"}},
         "ids": {"openalex": f"https://openalex.org/{wid}"}}
    if pmid:
        w["ids"]["pmid"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"
    return w


SEED = {"id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/seed",
        "referenced_works": [f"https://openalex.org/W{100 + i}" for i in range(60)], "cited_by_count": 3}


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeOpenAlex:
    def __init__(self, fail=None):
        self.urls = []
        self.fail = fail

    def __call__(self, req, timeout=None):
        url = req.full_url
        self.urls.append(url)
        if self.fail:
            raise self.fail
        parts = urllib.parse.urlsplit(url)
        q = urllib.parse.parse_qs(parts.query)
        if parts.path == "/works/doi:10.1/seed":
            return Resp(json.dumps(SEED).encode())
        if parts.path.startswith("/works/doi:"):
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        filt = q["filter"][0]
        if filt.startswith("openalex:"):
            ids = filt.split(":", 1)[1].split("|")
            res = [work(i, f"10.5555/{i.lower()}", f"Ref {i}") for i in ids]
            return Resp(json.dumps({"meta": {"next_cursor": None}, "results": res}).encode())
        if filt == "cites:W1":
            if q["cursor"][0] == "*":
                body = {"meta": {"next_cursor": "c2"},
                        "results": [work("W900", "10.5556/a", "Citer A", pmid="123"), work("W901", None, "Citer B")]}
            else:
                body = {"meta": {"next_cursor": None}, "results": [work("W902", "10.5555/w100", "Ref W100 dup")]}
            return Resp(json.dumps(body).encode())
        raise AssertionError(url)


def client(sb, opener):
    return sb.Client(opener=opener, sleep=lambda s: None, clock=lambda: 0.0)


def test_backward_and_forward(sb, tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("LRS_CONTACT_EMAIL", "lab@example.org")
    monkeypatch.setenv("OPENALEX_API_KEY", "OAKEY999")
    seeds = tmp_path / "included.tsv"
    seeds.write_text("record_id\tdoi\nR1\thttps://doi.org/10.1/SEED\nR2\t10.1/missing\nR3\t\n")
    out = tmp_path / "snowball.csv"
    fake = FakeOpenAlex()
    assert sb.main([str(seeds), "-o", str(out)], client=client(sb, fake)) == 0
    printed = capsys.readouterr()
    assert "OAKEY999" not in printed.out + printed.err
    report = json.loads((tmp_path / "snowball.json").read_text())
    assert "OAKEY999" not in out.read_text() + json.dumps(report)
    assert report["seeds"] == 2 and report["seeds_not_found"] == ["10.1/missing"]
    assert report["backward"] == 60 and report["forward"] == 3
    assert report["unique_candidates"] == 62  # W902 duplicates W100 by DOI
    # 60 refs in OR batches of 50 -> 2 list calls
    batches = [u for u in fake.urls if "filter=openalex" in u]
    assert len(batches) == 2
    assert all("api_key=OAKEY999" in u and "mailto=lab%40example.org" in u for u in fake.urls)
    rows = list(csv.DictReader(out.open()))
    assert list(rows[0]) == sb.OUT_COLUMNS
    a = next(r for r in rows if r["openalex_id"] == "W900")
    assert a == {"title": "Citer A", "year": "2020", "authors": "Ada Lovelace; C Babbage", "journal": "Nature",
                 "doi": "10.5556/a", "pmid": "123", "openalex_id": "W900", "direction": "forward",
                 "seed_doi": "10.1/seed"}


def test_forward_cap(sb, tmp_path):
    fake = FakeOpenAlex()
    rows, report = sb.snowball(["10.1/seed"], client(sb, fake), backward=False, max_forward=1)
    assert len(rows) == 1 and report["forward_capped"] == ["10.1/seed"]
    assert not any("cursor=c2" in u for u in fake.urls)


def test_offline_exits_2_without_output(sb, tmp_path, capsys):
    seeds = tmp_path / "s.txt"
    seeds.write_text("10.1/seed\n")
    out = tmp_path / "o.csv"
    fake = FakeOpenAlex(fail=urllib.error.URLError("offline"))
    assert sb.main([str(seeds), "-o", str(out)], client=client(sb, fake)) == 2
    assert not out.exists() and len(fake.urls) == 1
    assert "network unavailable" in capsys.readouterr().err


def test_retry_after_429(sb):
    calls = {"n": 0}
    sleeps = []

    def opener(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 429, "x", {"Retry-After": "5"}, None)
        return Resp(json.dumps({"ok": 1}).encode())

    c = sb.Client(opener=opener, sleep=sleeps.append, clock=lambda: 0.0, gap=0.0)
    assert c.get("/doi:10.1/x", {}) == {"ok": 1} and 5.0 in sleeps


def test_spacing_between_requests(sb):
    sleeps = []
    c = sb.Client(opener=FakeOpenAlex(), sleep=sleeps.append, clock=lambda: 0.0, gap=0.15)
    c.get("/doi:10.1/seed", {})
    c.get("/doi:10.1/seed", {})
    assert sleeps == [0.15]


def test_output_feeds_dedup(sb, tmp_path):
    dedup = load(DEDUP_PATH, "lrs_dedup_for_snowball")
    rows, _ = sb.snowball(["10.1/seed"], client(sb, FakeOpenAlex()))
    out = tmp_path / "snowball.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=sb.OUT_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    recs = dedup.parse_file(out, "snowball", use_pandas=False)
    assert len(recs) == 63
    assert {r["doi"] for r in recs if r["title"] == "Citer A"} == {"10.5556/a"}
    kept, *_ = dedup.deduplicate(recs)
    assert len(kept) == 62


def test_seed_csv_with_quoted_newline(sb, tmp_path):
    seeds = tmp_path / "included.csv"
    seeds.write_text('record_id,title,doi\nR1,"two\nlines",10.1/a\nR2,x,10.1/b\n')
    assert sb.read_seeds(seeds) == ["10.1/a", "10.1/b"]


def test_doi_is_url_encoded(sb):
    urls = []

    def opener(req, timeout=None):
        urls.append(req.full_url)
        return Resp(b"{}")

    sb.snowball(["10.1/a b#c?d"], client(sb, opener))
    assert "/doi:10.1/a%20b%23c%3Fd?" in urls[0]


def test_http_error_keeps_partial_results(sb, tmp_path, capsys):
    seeds = tmp_path / "s.txt"
    seeds.write_text("10.1/seed\n")
    out = tmp_path / "o.csv"
    fake = FakeOpenAlex()
    real = fake.__call__

    def opener(req, timeout=None):
        if "cites:" in req.full_url:
            raise urllib.error.HTTPError(req.full_url, 500, "x", {}, None)
        return real(req, timeout=timeout)

    assert sb.main([str(seeds), "-o", str(out)], client=client(sb, opener)) == 1
    rows = list(csv.DictReader(out.open()))
    report = json.loads((tmp_path / "o.json").read_text())
    assert len(rows) == 60 and report["backward"] == 60 and report["incomplete"]
    err = capsys.readouterr().err
    assert "OpenAlex HTTP 500 for cites:W1" in err
