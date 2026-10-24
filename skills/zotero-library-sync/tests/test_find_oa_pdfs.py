import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import find_oa_pdfs as f  # noqa: E402


def fake_get(url):
    if "10.1/open" in url:
        return {"title": "Open", "open_access": {"is_oa": True, "oa_status": "gold"},
                "best_oa_location": {"pdf_url": "https://x/open.pdf", "landing_page_url": "https://x"}}
    if "10.1/closed" in url:
        return {"title": "Closed", "open_access": {"is_oa": False, "oa_status": "closed"}}
    raise OSError("HTTP Error 404")


def test_rows_and_routes(tmp_path, monkeypatch):
    monkeypatch.delenv("LRS_CONTACT_EMAIL", raising=False)
    saved = []
    rows = [{"record_id": "R0001", "doi": "https://doi.org/10.1/OPEN"},
            {"record_id": "R0002", "doi": "10.1/closed"},
            {"record_id": "R0003", "doi": ""}]
    out, errors = f.run(rows, get=fake_get, fetch=lambda u, d: saved.append(d) or "saved",
                        out_dir=tmp_path, pause=0)
    assert errors == 0
    assert out[0]["pdf_url"] == "https://x/open.pdf" and out[0]["local_path"].endswith("R0001.pdf")
    assert out[1]["is_oa"] == "no" and out[1]["oa_status"] == "closed" and not out[1]["local_path"]
    assert out[2]["oa_status"] == "not_checked"
    assert len(saved) == 1


def test_unpaywall_only_with_email(monkeypatch):
    monkeypatch.delenv("LRS_CONTACT_EMAIL", raising=False)
    assert f.unpaywall("10.1/x", lambda u: {}) is None


def test_plain_doi_list(tmp_path):
    p = tmp_path / "dois.txt"
    p.write_text("10.1/a\n10.1/b\n")
    assert [r["doi"] for r in f.read_rows(p)] == ["10.1/a", "10.1/b"]


def test_no_overwrite(tmp_path):
    d = tmp_path / "a.pdf"
    d.write_bytes(b"%PDF old")
    assert f.download("https://unused", d) == "exists, not overwritten"
