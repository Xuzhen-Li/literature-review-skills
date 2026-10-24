"""Tests for api_search.py. Every API is faked; urlopen is blocked."""
import csv
import importlib.util
import json
import urllib.parse
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


a = load("api_search")
dedup = load("dedup")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def boom(*x, **k):
        raise AssertionError("real network access in test")
    monkeypatch.setattr(a.urllib.request, "urlopen", boom)
    monkeypatch.setattr(a, "SLEEP", lambda s: None)
    for v in ("LRS_CONTACT_EMAIL", "OPENALEX_API_KEY", "NCBI_API_KEY", "S2_API_KEY"):
        monkeypatch.delenv(v, raising=False)


def qs(url):
    return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))


OPENALEX = {"meta": {"count": 2}, "results": [
    {"id": "https://openalex.org/W1", "title": "Gut microbiota and sleep", "publication_year": 2021,
     "doi": "https://doi.org/10.1000/AAA", "ids": {"pmid": "https://pubmed.ncbi.nlm.nih.gov/111"},
     "authorships": [{"author": {"display_name": "Li X"}}], "primary_location": {"source": {"display_name": "J Sleep"}},
     "abstract_inverted_index": {"sleep": [1], "Poor": [0]}, "best_oa_location": {"pdf_url": "https://x/1.pdf"}},
    {"id": "https://openalex.org/W2", "title": "Second", "publication_year": 2020, "doi": None, "ids": {},
     "authorships": [], "primary_location": None, "abstract_inverted_index": None, "best_oa_location": None}]}

EPMC_PAGES = {
    "*": {"hitCount": 2, "nextCursorMark": "c2", "resultList": {"result": [
        {"id": "111", "source": "MED", "pmid": "111", "doi": "10.1000/aaa", "title": "Gut microbiota and sleep.",
         "pubYear": "2021", "authorString": "Li X, Wang Y", "journalInfo": {"journal": {"title": "J Sleep"}},
         "abstractText": "<b>Poor</b> sleep"}]}},
    "c2": {"hitCount": 2, "nextCursorMark": "c3", "resultList": {"result": [
        {"id": "PPR9", "source": "PPR", "doi": "10.1101/2024.01.01.1", "title": "A preprint", "pubYear": "2024",
         "fullTextUrlList": {"fullTextUrl": [{"documentStyle": "pdf", "availabilityCode": "OA", "url": "https://b/p.pdf"}]}}]}},
}

ESEARCH = {"esearchresult": {"count": "1", "idlist": ["111"]}}
EFETCH = b"""<?xml version="1.0"?><PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>111</PMID>
<Article><Journal><Title>J Sleep</Title><JournalIssue><PubDate><Year>2021</Year></PubDate></JournalIssue></Journal>
<ArticleTitle>Gut <i>microbiota</i> and sleep.</ArticleTitle><Abstract><AbstractText>Poor sleep.</AbstractText></Abstract>
<AuthorList><Author><LastName>Li</LastName><Initials>X</Initials></Author></AuthorList></Article></MedlineCitation>
<PubmedData><ArticleIdList><ArticleId IdType="doi">10.1000/AAA</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>"""

S2 = {"total": 1, "data": [{"paperId": "abc", "title": "Gut microbiota and sleep", "year": 2021,
                            "authors": [{"name": "X Li"}], "venue": "J Sleep",
                            "externalIds": {"DOI": "10.1000/aaa", "PubMed": "111"}, "abstract": None,
                            "openAccessPdf": {"url": ""}}]}

ARXIV = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:arxiv="http://arxiv.org/schemas/atom">
<opensearch:totalResults>1</opensearch:totalResults>
<entry><id>http://arxiv.org/abs/2401.00001v2</id><title>Sleep  models</title><published>2024-01-01T00:00:00Z</published>
<summary>We model sleep.</summary><author><name>A B</name></author>
<link title="pdf" href="http://arxiv.org/pdf/2401.00001v2"/></entry></feed>"""

CROSSREF = {"message": {"total-results": 1, "next-cursor": "n", "items": [
    {"DOI": "10.1000/AAA", "title": ["Gut microbiota and sleep"], "issued": {"date-parts": [[2021, 3]]},
     "author": [{"family": "Li", "given": "X"}], "container-title": ["J Sleep"]}]}}


def fake_get(calls=None):
    def get(url, headers=None):
        if calls is not None:
            calls.append((url, headers))
        host = urllib.parse.urlsplit(url).netloc
        q = qs(url)
        if host == "api.openalex.org":
            body = OPENALEX if q.get("page") == "1" else {"meta": {"count": 2}, "results": []}
        elif host == "www.ebi.ac.uk":
            body = EPMC_PAGES.get(q["cursorMark"], {"hitCount": 2, "resultList": {"result": []}})
        elif "esearch" in url:
            body = ESEARCH
        elif "efetch" in url:
            return EFETCH
        elif host == "api.semanticscholar.org":
            body = S2
        elif host == "export.arxiv.org":
            return ARXIV
        elif host == "api.crossref.org":
            body = CROSSREF
        else:
            raise AssertionError(url)
        return json.dumps(body).encode()
    return get


def test_each_source_parses():
    q = {s: "gut microbiota sleep" for s in a.ALL_SOURCES}
    res = a.run(q, 100, fake_get(), pause=0)
    assert all(not r["error"] for r in res.values())
    oa = res["openalex"]["records"]
    assert oa[0]["doi"] == "10.1000/aaa" and oa[0]["pmid"] == "111" and oa[0]["abstract"] == "Poor sleep"
    assert oa[0]["pdf_url"] == "https://x/1.pdf" and oa[1]["doi"] == ""
    ep = res["europepmc"]["records"]
    assert [r["source_id"] for r in ep] == ["MED:111", "PPR:PPR9"]
    assert ep[0]["abstract"] == "Poor sleep" and ep[0]["authors"] == "Li X; Wang Y"
    assert ep[1]["pdf_url"] == "https://b/p.pdf" and ep[1]["journal"] == "preprint"
    pm = res["pubmed"]["records"][0]
    assert pm["title"] == "Gut microbiota and sleep." and pm["doi"] == "10.1000/aaa" and pm["year"] == "2021"
    assert res["semanticscholar"]["records"][0]["pmid"] == "111"
    ax = res["arxiv"]["records"][0]
    assert ax["doi"] == "10.48550/arxiv.2401.00001" and ax["title"] == "Sleep models"
    assert res["crossref"]["records"][0]["year"] == "2021"


def test_max_caps_records():
    res = a.run({"europepmc": "x"}, 1, fake_get(), pause=0)
    assert len(res["europepmc"]["records"]) == 1 and res["europepmc"]["total"] == 2


def test_count_only_requests_one_row():
    calls = []
    res = a.run({"openalex": "x", "pubmed": "x"}, 100, fake_get(calls), count_only=True, pause=0)
    assert res["openalex"] == {"total": 2, "records": [], "error": ""}
    assert qs(calls[0][0])["per_page"] == "1" and qs(calls[1][0])["retmax"] == "0"
    assert not any("efetch" in u for u, _ in calls)


def test_source_error_isolated():
    def get(url, headers=None):
        if "openalex" in url:
            raise a.SourceError("HTTP 500")
        return fake_get()(url, headers)
    res = a.run({"openalex": "x", "semanticscholar": "x"}, 10, get, pause=0)
    assert res["openalex"]["error"] == "HTTP 500" and res["semanticscholar"]["total"] == 1


def test_keys_sent_only_when_set(monkeypatch):
    calls = []
    a.run({"semanticscholar": "x", "openalex": "x"}, 10, fake_get(calls), pause=0)
    assert calls[0][1] is None and "api_key" not in qs(calls[1][0])
    monkeypatch.setenv("S2_API_KEY", "k")
    monkeypatch.setenv("OPENALEX_API_KEY", "ok")
    calls.clear()
    a.run({"semanticscholar": "x", "openalex": "x"}, 10, fake_get(calls), pause=0)
    assert calls[0][1] == {"x-api-key": "k"} and qs(calls[1][0])["api_key"] == "ok"


def test_doctype_refused():
    with pytest.raises(ValueError):
        a.xml_fromstring(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e "boom">]><x>&e;</x>')


def test_main_writes_csv_and_hit_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "http_get", lambda u, h=None: fake_get()(u, h))
    out = tmp_path / "raw"
    hc = tmp_path / "hit_counts.tsv"
    rc = a.main(["--query", "gut sleep", "--pubmed-query", "gut[tiab] AND sleep[tiab]",
                 "--sources", "pubmed,europepmc", "--out-dir", str(out), "--hit-counts", str(hc),
                 "--date", "20261024"])
    assert rc == 0
    rows = list(csv.reader(hc.open(), delimiter="\t"))
    assert rows[0] == ["database", "interface", "date", "count", "notes"]
    assert rows[1][:4] == ["pubmed", "NCBI E-utilities", "2026-10-24", "1"]
    assert "gut[tiab] AND sleep[tiab]" in rows[1][4] and "retrieved 1 of 1" in rows[1][4]
    assert (out / "europepmc_20261024.csv").exists()
    # same day again: refuses, nothing appended
    assert a.main(["--query", "q", "--sources", "pubmed", "--out-dir", str(out), "--hit-counts", str(hc),
                   "--date", "20261024"]) == 2
    assert len(list(csv.reader(hc.open(), delimiter="\t"))) == 3


def test_output_feeds_dedup(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "http_get", lambda u, h=None: fake_get()(u, h))
    out = tmp_path / "raw"
    assert a.main(["--query", "q", "--sources", "openalex,pubmed,semanticscholar", "--out-dir", str(out),
                   "--date", "20261024"]) == 0
    recs = []
    for p in sorted(out.glob("*.csv")):
        recs += dedup.parse_file(p, p.stem.split("_")[0], use_pandas=False)
    clusters = dedup.deduplicate(recs)[0]
    assert len(recs) == 4 and len(clusters) == 2  # 3 copies of 10.1000/aaa merge
    assert "10.1000/aaa" in repr(clusters)


def test_truncation_and_failure_exit_1(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "http_get", lambda u, h=None: fake_get()(u, h))
    hc = tmp_path / "h.tsv"
    assert a.main(["--query", "q", "--sources", "europepmc", "--max", "1", "--out-dir", str(tmp_path),
                   "--hit-counts", str(hc), "--date", "20261024"]) == 1
    assert "TRUNCATED" in hc.read_text()

    def down(u, h=None):
        raise a.SourceError("network error: offline")
    monkeypatch.setattr(a, "http_get", down)
    assert a.main(["--query", "q", "--sources", "arxiv", "--count-only", "--hit-counts", str(hc)]) == 1
    assert "[VERIFY]" in hc.read_text().splitlines()[-1]


@pytest.mark.parametrize("argv", [["--query", "q", "--sources", "scopus", "--count-only"],
                                  ["--sources", "pubmed", "--count-only"],
                                  ["--query", "q"]])
def test_bad_args(argv):
    assert a.main(argv) == 2
