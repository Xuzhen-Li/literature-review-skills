import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import find_oa_pdfs as f  # noqa: E402


def fake_get(url):
    if "10.1/open" in url:
        return {"title": "Open", "open_access": {"is_oa": True, "oa_status": "gold"},
                "best_oa_location": {"pdf_url": "https://x/open.pdf", "landing_page_url": "https://x"}}
    if "10.1/closed" in url:
        return {"title": "Closed", "open_access": {"is_oa": False, "oa_status": "closed"}}
    if "10.1/gone" in url:
        raise f.NotFound(url)
    raise OSError("connection reset")


@pytest.fixture(autouse=True)
def no_email(monkeypatch):
    monkeypatch.delenv("LRS_CONTACT_EMAIL", raising=False)


FULL_CHAIN = f.DEFAULT_LOOKUPS


@pytest.fixture(autouse=True)
def legacy_lookups(monkeypatch):
    # Tests written for the OpenAlex -> Unpaywall chain keep that chain;
    # tests that take the all_lookups fixture get the full default list back.
    monkeypatch.setattr(f, "DEFAULT_LOOKUPS", ("openalex", "unpaywall"))


@pytest.fixture
def all_lookups(legacy_lookups, monkeypatch):
    monkeypatch.setattr(f, "DEFAULT_LOOKUPS", FULL_CHAIN)


def test_rows_and_routes(tmp_path):
    saved = []
    rows = [{"record_id": "R0001", "doi": "https://doi.org/10.1/OPEN"},
            {"record_id": "R0002", "doi": "10.1/closed"},
            {"record_id": "R0003", "doi": ""},
            {"record_id": "R0004", "doi": "10.1/gone"}]
    out, stats = f.run(rows, get=fake_get, fetch=lambda u, d: saved.append(d) or "saved",
                       out_dir=tmp_path, pause=0)
    assert stats == {"lookup_errors": 0, "not_checked": 0, "download_failed": 0}
    assert out[0]["pdf_url"] == "https://x/open.pdf" and Path(out[0]["local_path"]).name.startswith("R0001-")
    assert out[1]["is_oa"] == "no" and out[1]["oa_status"] == "closed" and not out[1]["local_path"]
    assert out[2]["oa_status"] == "not_checked"
    assert out[3]["oa_status"] == "not_found"
    assert len(saved) == 1


def test_network_error_counts_as_not_checked():
    out, stats = f.run([{"doi": "10.1/flaky"}], get=fake_get, pause=0)
    assert out[0]["oa_status"] == "not_checked"
    assert stats["lookup_errors"] == 1 and stats["not_checked"] == 1


def test_unpaywall_only_with_email():
    assert f.unpaywall("10.1/x", lambda u: {}) is None


@pytest.mark.parametrize("first", ["https://doi.org/10.1/a", "doi:10.1/a", "10.1/a", "DOI 10.1/a"])
def test_plain_doi_list_keeps_first_line(tmp_path, first):
    p = tmp_path / "dois.txt"
    p.write_text(f"{first}\n10.1/b\n")
    rows = f.read_rows(p)
    assert len(rows) == 2 and rows[0]["doi"] == first


def test_header_detected_only_for_doi_column(tmp_path):
    p = tmp_path / "inc.tsv"
    p.write_text("record_id\tDOI\ttitle\nR1\t10.1/a\tA\n")
    assert f.read_rows(p) == [{"record_id": "R1", "doi": "10.1/a", "title": "A"}]


def test_colliding_dois_get_distinct_files():
    a = f.safe_name({"doi": "10.1/a:b"})
    b = f.safe_name({"doi": "10.1/a/b"})
    assert a != b and a.startswith("10.1_a_b-") and b.startswith("10.1_a_b-")
    assert f.safe_name({"doi": "10.1/a:b", "record_id": "R1"}) != f.safe_name({"doi": "10.1/a/b", "record_id": "R1"})


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("real network access in test")
    monkeypatch.setattr(f.urllib.request, "urlopen", boom)


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://x/a.pdf", "data:application/pdf,%PDF"])
def test_non_http_urls_refused(tmp_path, url):
    with pytest.raises(f.DownloadError):
        f.download(url, tmp_path / "a.pdf")
    assert not (tmp_path / "a.pdf").exists()


def test_download_failure_sets_exit_stats(tmp_path):
    def bad(url, dest):
        raise f.DownloadError("nope")
    out, stats = f.run([{"doi": "10.1/open"}], get=fake_get, fetch=bad, out_dir=tmp_path, pause=0)
    assert stats["download_failed"] == 1 and not out[0]["local_path"]


def test_no_overwrite(tmp_path):
    d = tmp_path / "a.pdf"
    d.write_bytes(b"%PDF old")
    assert f.download("https://unused.example/a.pdf", d) == "exists, not overwritten"


def test_out_refuses_overwrite_without_force(tmp_path):
    inp = tmp_path / "d.txt"
    inp.write_text("\n")
    out = tmp_path / "oa.csv"
    out.write_text("keep")
    assert f.main([str(inp), "-o", str(out)]) == 2
    assert out.read_text() == "keep"
    assert f.main([str(inp), "-o", str(out), "--force"]) == 0


# ---- stubbed urlopen: no real network in any test below ----
import io
import urllib.error


class FakeResp(io.BytesIO):
    def __init__(self, body, final_url):
        super().__init__(body)
        self._url = final_url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


@pytest.fixture
def stub_urlopen(monkeypatch):
    calls = []

    def install(handler):
        def fake(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else req
            calls.append(url)
            return handler(url)
        monkeypatch.setattr(f.urllib.request, "urlopen", fake)
        return calls
    return install


def test_redirect_to_non_http_refused(tmp_path, stub_urlopen):
    stub_urlopen(lambda u: FakeResp(b"%PDF-1.4 x", "file:///etc/passwd"))
    with pytest.raises(f.DownloadError, match="redirected"):
        f.download("https://x/a.pdf", tmp_path / "a.pdf")
    assert not (tmp_path / "a.pdf").exists()


def test_size_cap(tmp_path, stub_urlopen):
    stub_urlopen(lambda u: FakeResp(b"%PDF" + b"0" * 20, "https://x/a.pdf"))
    with pytest.raises(f.DownloadError, match="larger than"):
        f.download("https://x/a.pdf", tmp_path / "a.pdf", limit=10)
    assert not (tmp_path / "a.pdf").exists()
    assert f.download("https://x/a.pdf", tmp_path / "b.pdf", limit=100) == "saved"


def test_404_by_status_code(stub_urlopen):
    def h(u):
        raise urllib.error.HTTPError(u, 404, "Gone Away", {}, None)  # no "404" in msg
    stub_urlopen(h)
    with pytest.raises(f.NotFound):
        f.http_json("https://api.openalex.org/works/doi:10.1/x")


def test_500_is_not_not_found(stub_urlopen):
    def h(u):
        raise urllib.error.HTTPError(u, 500, "404 mentioned", {}, None)
    stub_urlopen(h)
    with pytest.raises(urllib.error.HTTPError):
        f.http_json("https://api.openalex.org/works/doi:10.1/x")


@pytest.mark.parametrize("url", ["ftp://x/a.pdf", "file:///etc/passwd"])
def test_bad_scheme_never_opens(tmp_path, stub_urlopen, url):
    calls = stub_urlopen(lambda u: FakeResp(b"%PDF", u))
    with pytest.raises(f.DownloadError):
        f.download(url, tmp_path / "a.pdf")
    assert calls == []


def test_not_found_status_is_structured():
    def g(url):
        raise f.NotFound(url)
    out, stats = f.run([{"doi": "10.1/error-in-doi"}], get=g, pause=0)
    assert out[0]["oa_status"] == "not_found" and stats["not_checked"] == 0


class SizedResp(FakeResp):
    def __init__(self, body, final_url):
        super().__init__(body, final_url)
        self.asked = []

    def read(self, n=-1):
        self.asked.append(n)
        return super().read(n)


def test_read_is_bounded(tmp_path, stub_urlopen):
    resp = SizedResp(b"%PDF" + b"0" * 50, "https://x/a.pdf")
    stub_urlopen(lambda u: resp)
    with pytest.raises(f.DownloadError):
        f.download("https://x/a.pdf", tmp_path / "a.pdf", limit=10)
    assert resp.asked == [11]  # never an unbounded read()


def _mixed(oa_exc, up_exc):
    def get(url):
        raise (oa_exc if "openalex" in url else up_exc)(url)
    return get


@pytest.mark.parametrize("oa_exc,up_exc", [(RuntimeError, f.NotFound), (f.NotFound, RuntimeError)])
def test_error_plus_404_is_not_checked(monkeypatch, oa_exc, up_exc):
    monkeypatch.setenv("LRS_CONTACT_EMAIL", "me@example.org")
    out, stats = f.run([{"doi": "10.1/mixed"}], get=_mixed(oa_exc, up_exc), pause=0)
    assert out[0]["oa_status"] == "not_checked"
    assert stats["lookup_errors"] == 1 and stats["not_checked"] == 1


def test_both_404_is_not_found(monkeypatch):
    monkeypatch.setenv("LRS_CONTACT_EMAIL", "me@example.org")
    out, stats = f.run([{"doi": "10.1/x"}], get=_mixed(f.NotFound, f.NotFound), pause=0)
    assert out[0]["oa_status"] == "not_found" and stats["not_checked"] == 0


def test_non_pdf_body_refused(tmp_path, stub_urlopen):
    stub_urlopen(lambda u: FakeResp(b"<html>login</html>", "https://x/a.pdf"))
    with pytest.raises(f.DownloadError, match="did not return a PDF"):
        f.download("https://x/a.pdf", tmp_path / "a.pdf")
    assert not (tmp_path / "a.pdf").exists()


def test_main_exit_1_on_not_checked(tmp_path, monkeypatch):
    def boom(doi, get):
        raise RuntimeError("offline")
    monkeypatch.setattr(f, "openalex", boom)
    monkeypatch.setattr(f.time, "sleep", lambda s: None)
    inp = tmp_path / "d.txt"
    inp.write_text("10.1/a\n")
    out = tmp_path / "oa.csv"
    assert f.main([str(inp), "-o", str(out)]) == 1
    assert "not_checked" in out.read_text()


# ---- extra free sources (Europe PMC, Semantic Scholar, arXiv) ----

def _multi_get(table):
    def get(url):
        for key, val in table.items():
            if key in url:
                if isinstance(val, Exception):
                    raise val
                return val
        raise f.NotFound(url)
    return get


EPMC_OA = {"resultList": {"result": [{"pmcid": "PMC123", "isOpenAccess": "Y", "title": "T"}]}}
OA_CLOSED = {"title": "C", "open_access": {"is_oa": False, "oa_status": "closed"}}


def test_default_chain_order():
    assert FULL_CHAIN == ("openalex", "unpaywall", "europepmc", "semanticscholar", "arxiv")


def test_europepmc_fills_pdf_when_openalex_closed(all_lookups):
    get = _multi_get({"openalex": OA_CLOSED, "europepmc": EPMC_OA})
    out, stats = f.run([{"doi": "10.1/c"}], get=get, pause=0)
    assert out[0]["source"] == "europepmc"
    assert out[0]["pdf_url"] == "https://europepmc.org/articles/PMC123?pdf=render"
    assert stats == {"lookup_errors": 0, "not_checked": 0, "download_failed": 0}


def test_europepmc_no_hit_is_not_found():
    with pytest.raises(f.NotFound):
        f.europepmc("10.1/x", lambda u: {"resultList": {"result": []}})


def test_europepmc_not_oa_has_no_pdf():
    r = f.europepmc("10.1/x", lambda u: {"resultList": {"result": [{"pmcid": "PMC9", "isOpenAccess": "N"}]}})
    assert r["pdf_url"] == "" and r["is_oa"] is False


def test_semanticscholar_pdf():
    seen = []
    r = f.semanticscholar("10.1/x", lambda u: seen.append(u) or {"openAccessPdf": {"url": "https://s2/x.pdf"}})
    assert r["pdf_url"] == "https://s2/x.pdf" and "paper/DOI:10.1/x" in seen[0]


def test_arxiv_doi_maps_without_request():
    def get(u):
        raise AssertionError("no request expected")
    r = f.arxiv("10.48550/arxiv.2106.15928", get)
    assert r["pdf_url"] == "https://arxiv.org/pdf/2106.15928"
    assert f.arxiv("10.1/x", get) is None


def test_failed_download_falls_through_to_next_source(tmp_path, all_lookups):
    get = _multi_get({"openalex": {"title": "O", "open_access": {"is_oa": True, "oa_status": "gold"},
                                   "best_oa_location": {"pdf_url": "https://publisher/blocked.pdf"}},
                      "europepmc": EPMC_OA})
    tried = []

    def fetch(url, dest):
        tried.append(url)
        if "publisher" in url:
            raise f.DownloadError("403")
        return "saved"
    out, stats = f.run([{"record_id": "R1", "doi": "10.1/y"}], get=get, fetch=fetch, out_dir=tmp_path, pause=0)
    assert tried == ["https://publisher/blocked.pdf", "https://europepmc.org/articles/PMC123?pdf=render"]
    assert out[0]["local_path"] and out[0]["source"] == "europepmc"
    assert stats["download_failed"] == 0


def test_all_downloads_fail_counts_once(tmp_path, all_lookups):
    get = _multi_get({"openalex": {"open_access": {"is_oa": True}, "best_oa_location": {"pdf_url": "https://a/1.pdf"}},
                      "europepmc": EPMC_OA, "semanticscholar": {"openAccessPdf": {"url": "https://a/1.pdf"}}})

    def fetch(url, dest):
        raise f.DownloadError("blocked")
    out, stats = f.run([{"doi": "10.1/z"}], get=get, fetch=fetch, out_dir=tmp_path, pause=0)
    assert stats["download_failed"] == 1 and not out[0]["local_path"]
    assert out[0]["note"].count("blocked") == 2  # duplicate URL tried once


def test_rerun_counts_existing_pdf_as_saved(tmp_path):
    """Second run: the PDF is already on disk, so local_path must be filled and
    please_fetch must not ask the user for it."""
    import please_fetch as pf
    rows = [{"record_id": "R0001", "doi": "10.1/open", "title": "Open"}]
    first, _ = f.run(rows, get=fake_get, fetch=lambda u, d: (d.write_bytes(b"%PDF-1.4"), "saved")[1],
                     out_dir=tmp_path, pause=0)
    calls = []
    second, stats = f.run(rows, get=fake_get, fetch=lambda u, d: calls.append(u) or f.download(u, d),
                          out_dir=tmp_path, pause=0)
    assert calls == ["https://x/open.pdf"]  # the real download() short-circuits on the existing file
    assert second[0]["local_path"] == first[0]["local_path"] != ""
    assert "exists, not overwritten" in second[0]["note"]
    assert stats["download_failed"] == 0
    need = [{"record_id": "R0001", "doi": "10.1/open", "need": "essential", "why": "core", "rank": "1"}]
    fetch, abstract, untriaged, _ = pf.build(second, need, None, 15)
    assert fetch == [] and abstract == [] and untriaged == []


@pytest.mark.parametrize("url", ["https://sci-hub.se/10.1/x", "https://www.researchgate.net/x.pdf",
                                 "http://libgen.rs/a.pdf"])
def test_blocked_host_refused_before_connect(tmp_path, url):
    with pytest.raises(f.DownloadError, match="blocked host"):
        f.download(url, tmp_path / "a.pdf")


def test_redirect_to_blocked_host_refused(tmp_path, stub_urlopen):
    stub_urlopen(lambda u: FakeResp(b"%PDF-1.4 x", "https://sci-hub.se/a.pdf"))
    with pytest.raises(f.DownloadError, match="blocked host"):
        f.download("https://x/a.pdf", tmp_path / "a.pdf")
    assert not (tmp_path / "a.pdf").exists()


def test_api_link_to_blocked_host_is_dropped(tmp_path):
    def get(url):
        return {"title": "T", "open_access": {"is_oa": True, "oa_status": "green"},
                "best_oa_location": {"pdf_url": "https://sci-hub.se/x.pdf"}}
    fetched = []
    out, _ = f.run([{"record_id": "R1", "doi": "10.1/x"}], get=get,
                   fetch=lambda u, d: fetched.append(u) or "saved", out_dir=tmp_path, pause=0)
    assert fetched == [] and out[0]["pdf_url"] == "" and "blocked host" in out[0]["note"]


def test_blocklist_shared_with_route_permission():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "figure-permissions" / "scripts"))
    try:
        import route_permission
    finally:
        sys.path.pop(0)
    assert f.BLOCKED_HOST_PARTS is route_permission.BLOCKED_HOST_PARTS


def test_s2_key_sent_only_to_semanticscholar(monkeypatch):
    monkeypatch.setenv("S2_API_KEY", "k")
    assert f.request_headers("https://api.semanticscholar.org/graph/v1/paper/DOI:10.1/x")["x-api-key"] == "k"
    assert "x-api-key" not in f.request_headers("https://api.openalex.org/works/doi:10.1/x")
    monkeypatch.delenv("S2_API_KEY")
    assert "x-api-key" not in f.request_headers("https://api.semanticscholar.org/graph/v1/paper/x")


def test_http_json_sends_s2_key(monkeypatch, stub_urlopen):
    seen = []

    def fake(req, timeout=None):
        seen.append(req.get_header("X-api-key"))
        return FakeResp(b"{}", req.full_url)
    monkeypatch.setattr(f.urllib.request, "urlopen", fake)
    monkeypatch.setenv("S2_API_KEY", "k")
    f.http_json("https://api.semanticscholar.org/graph/v1/paper/DOI:10.1/x")
    assert seen == ["k"]
