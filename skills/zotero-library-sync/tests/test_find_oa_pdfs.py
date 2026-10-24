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
