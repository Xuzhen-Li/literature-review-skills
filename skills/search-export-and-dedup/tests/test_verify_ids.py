"""Tests for verify_ids.py. All HTTP is mocked; no network is used."""

import csv
import importlib.util
import io
import json
import urllib.error
import urllib.parse
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_ids.py"

CROSSREF_OK = {
    "status": "ok",
    "message": {
        "DOI": "10.1038/nature12373",
        "title": ["Nanometre-scale thermometry in a living cell"],
        "issued": {"date-parts": [[2013, 7, 31]]},
        "published-print": {"date-parts": [[2013, 8]]},
        "author": [
            {"given": "G.", "family": "Kucsko", "sequence": "first"},
            {"given": "P. C.", "family": "Maurer", "sequence": "additional"},
        ],
    },
}

ESUMMARY_OK = {
    "result": {
        "uids": ["23903748", "99999999"],
        "23903748": {
            "uid": "23903748",
            "title": "Nanometre-scale thermometry in a living cell.",
            "pubdate": "2013 Aug 1",
            "sortfirstauthor": "Kucsko G",
            "articleids": [
                {"idtype": "pubmed", "value": "23903748"},
                {"idtype": "doi", "value": "10.1038/nature12373"},
            ],
        },
        "99999999": {"uid": "99999999", "error": "cannot get document summary"},
    }
}


@pytest.fixture(scope="module")
def vi():
    spec = importlib.util.spec_from_file_location("lrs_verify_ids", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeResp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeOpener:
    def __init__(self, routes):
        self.routes = routes
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        url = req.full_url
        for prefix, handler in self.routes:
            if url.startswith(prefix):
                out = handler(url) if callable(handler) else handler
                if isinstance(out, Exception):
                    raise out
                if isinstance(out, int):
                    raise urllib.error.HTTPError(url, out, "err", {}, None)
                return FakeResp(json.dumps(out).encode())
        raise AssertionError(f"unexpected URL {url}")


def make_client(vi, routes, contact="lab@example.org"):
    sleeps = []
    opener = FakeOpener(routes)
    client = vi.PoliteClient(opener=opener, sleep=sleeps.append, clock=lambda: 0.0, contact=contact)
    return client, opener, sleeps


def row(**kw):
    base = {"record_id": "R1", "title": "", "year": "", "authors": "", "doi": "", "pmid": ""}
    base.update(kw)
    return base


GOOD = dict(title="Nanometre-scale thermometry in a living cell", year="2013",
            authors="Kucsko, G.; Maurer, P. C.")


def test_normalizers(vi):
    assert vi.normalize_doi("https://doi.org/10.1038/NATURE12373.") == "10.1038/nature12373"
    assert vi.normalize_pmid("PMID: 23903748") == "23903748"
    assert vi.normalize_pmid("23903748.0") == "23903748"
    assert vi.surname_key("Kucsko G") == "kucsko"
    assert vi.surname_key("Kucsko, G.; Maurer, P.") == "kucsko"
    assert vi.surname_key("Georg Kucsko") == "kucsko"
    assert vi.surname_key("Müller, A.") == "muller"


def test_title_match_tolerates_punctuation_and_markup(vi):
    assert vi.titles_match("Nanometre-scale thermometry in a living cell.",
                           "Nanometre-scale <i>thermometry</i> in a living cell")
    assert not vi.titles_match("A different paper entirely", "Nanometre-scale thermometry")


def test_doi_ok(vi):
    client, opener, _ = make_client(vi, [(vi.CROSSREF_WORKS, CROSSREF_OK)])
    res = vi.verify_rows([row(doi="10.1038/nature12373", **GOOD)], client)
    assert [r["status"] for r in res] == ["ok"]
    assert res[0]["flag"] == ""
    req = opener.requests[0]
    assert "mailto%40" not in req.full_url and "mailto=lab%40example.org" in req.full_url
    assert "mailto:lab@example.org" in req.get_header("User-agent")
    assert "10.1038%2Fnature12373" in req.full_url


def test_doi_title_mismatch_flagged_not_corrected(vi):
    client, _, _ = make_client(vi, [(vi.CROSSREF_WORKS, CROSSREF_OK)])
    r = row(doi="10.1038/nature12373", title="Quantum dots in mice", year="2013", authors="Kucsko G")
    original = dict(r)
    res = vi.verify_rows([r], client)
    assert res[0]["status"] == "mismatch"
    assert res[0]["title_match"] == "no" and res[0]["year_match"] == "yes"
    assert res[0]["flag"] == "[VERIFY]"
    assert r == original


def test_year_accepts_print_or_online(vi):
    client, _, _ = make_client(vi, [(vi.CROSSREF_WORKS, CROSSREF_OK)])
    res = vi.verify_rows([row(doi="10.1038/nature12373", title=GOOD["title"], year="2014")], client)
    assert res[0]["year_match"] == "no"


def test_doi_not_found(vi):
    client, _, _ = make_client(vi, [(vi.CROSSREF_WORKS, 404)])
    res = vi.verify_rows([row(doi="10.9999/nope")], client)
    assert res[0]["status"] == "not_found" and res[0]["flag"] == "[VERIFY]"


def test_invalid_formats(vi):
    res = vi.verify_rows([row(doi="nature12373", pmid="PMC123")], None, offline=True)
    assert {r["id_type"]: r["status"] for r in res} == {"doi": "invalid", "pmid": "invalid"}


def test_pmid_batch_ok_not_found_and_doi_conflict(vi):
    calls = []

    def handler(url):
        calls.append(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query))
        return ESUMMARY_OK

    client, _, _ = make_client(vi, [(vi.ESUMMARY, handler)])
    rows = [
        row(record_id="R1", pmid="23903748", **GOOD),
        row(record_id="R2", pmid="99999999"),
        row(record_id="R3", pmid="23903748", doi="", **GOOD),
    ]
    rows.append(row(record_id="R4", pmid="23903748", **GOOD))
    res = vi.verify_rows(rows, client)
    assert len(calls) == 1
    q = calls[0]
    assert q["db"] == ["pubmed"] and q["retmode"] == ["json"] and q["tool"] == [vi.TOOL]
    assert q["email"] == ["lab@example.org"]
    by = {r["row_id"]: r for r in res if r["id_type"] == "pmid"}
    assert by["R1"]["status"] == "ok"
    assert by["R2"]["status"] == "not_found"


def test_pmid_doi_conflict(vi):
    client, _, _ = make_client(vi, [(vi.ESUMMARY, ESUMMARY_OK), (vi.CROSSREF_WORKS, 404)])
    res = vi.verify_rows([row(pmid="23903748", doi="10.1000/other", **GOOD)], client)
    pm = [r for r in res if r["id_type"] == "pmid"][0]
    assert pm["status"] == "mismatch" and "10.1038/nature12373" in pm["detail"]


def test_ncbi_api_key_from_env_only_in_url(vi, monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("NCBI_API_KEY", "SECRETKEY123")
    seen = []
    client, _, _ = make_client(vi, [(vi.ESUMMARY, lambda u: seen.append(u) or ESUMMARY_OK)])
    table = tmp_path / "library.csv"
    with table.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row()))
        w.writeheader()
        w.writerow(row(pmid="23903748", **GOOD))
    assert vi.main([str(table)], client=client) == 0
    assert "api_key=SECRETKEY123" in seen[0]
    out = capsys.readouterr()
    assert "SECRETKEY123" not in out.out + out.err
    assert "SECRETKEY123" not in (tmp_path / "identifier_check.csv").read_text()
    assert client.intervals["eutils.ncbi.nlm.nih.gov"] == 0.1


def test_esummary_batches_of_200(vi):
    n = []
    client, _, _ = make_client(vi, [(vi.ESUMMARY, lambda u: n.append(u) or {"result": {}})])
    rows = [row(record_id=f"R{i}", pmid=str(1000 + i)) for i in range(450)]
    res = vi.verify_rows(rows, client)
    assert len(n) == 3
    assert all(r["status"] == "not_found" for r in res)


def test_rate_limit_spacing(vi):
    t = [0.0]
    sleeps = []
    opener = FakeOpener([(vi.CROSSREF_WORKS, CROSSREF_OK)])
    client = vi.PoliteClient(opener=opener, sleep=lambda s: sleeps.append(s), clock=lambda: t[0], contact="")
    vi.verify_rows([row(record_id=f"R{i}", doi="10.1038/nature12373") for i in range(3)], client)
    assert len(sleeps) == 2 and all(abs(s - 0.2) < 1e-9 for s in sleeps)
    assert "mailto" not in opener.requests[0].full_url


def test_retry_once_on_429(vi):
    state = {"n": 0}

    def handler(url):
        state["n"] += 1
        if state["n"] == 1:
            return urllib.error.HTTPError(url, 429, "slow", {"Retry-After": "3"}, None)
        return CROSSREF_OK

    client, _, sleeps = make_client(vi, [(vi.CROSSREF_WORKS, handler)])
    res = vi.verify_rows([row(doi="10.1038/nature12373", **GOOD)], client)
    assert res[0]["status"] == "ok" and 3.0 in sleeps


def test_network_down_degrades_to_unchecked(vi):
    down = urllib.error.URLError("no route")
    client, opener, _ = make_client(vi, [(vi.CROSSREF_WORKS, down), (vi.ESUMMARY, down)])
    rows = [row(record_id=f"R{i}", doi="10.1038/nature12373", pmid="23903748") for i in range(3)]
    res = vi.verify_rows(rows, client)
    assert {r["status"] for r in res} == {"unchecked"}
    assert len(opener.requests) == 1  # stops calling after first failure


def test_offline_cli_no_network(vi, tmp_path, capsys):
    table = tmp_path / "evidence_table.csv"
    table.write_text("evidence_id,doi,pmid,year,first_author\nE001,10.1038/nature12373,23903748,2013,Kucsko\n")
    out = tmp_path / "check.csv"
    assert vi.main([str(table), "--offline", "-o", str(out), "--strict"]) == 0
    rows = list(csv.DictReader(out.open()))
    assert [r["status"] for r in rows] == ["unchecked", "unchecked"]
    assert rows[0]["row_id"] == "E001"
    assert json.loads(capsys.readouterr().out)["unchecked"] == 2


def test_strict_exit_code(vi, tmp_path):
    table = tmp_path / "library.csv"
    table.write_text("record_id,doi,pmid\nR1,notadoi,\n")
    assert vi.main([str(table), "--offline", "--strict"]) == 1
    assert vi.main([str(table), "--offline"]) == 0


def test_missing_id_columns(vi, tmp_path):
    table = tmp_path / "x.csv"
    table.write_text("title\nfoo\n")
    with pytest.raises(SystemExit):
        vi.main([str(table), "--offline"])
