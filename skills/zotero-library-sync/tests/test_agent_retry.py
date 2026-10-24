import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import agent_retry as ar  # noqa: E402
import find_oa_pdfs as foa  # noqa: E402
import please_fetch as pf  # noqa: E402


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("real network access in test")
    monkeypatch.setattr(foa.urllib.request, "urlopen", boom)
    monkeypatch.delenv("LRS_CONTACT_EMAIL", raising=False)


STATUS = [
    {"record_id": "R1", "doi": "10.1/have", "title": "Have", "local_path": "pdfs/R1.pdf", "pdf_url": "", "landing_url": ""},
    {"record_id": "R2", "doi": "10.3390/ijms1", "title": "MDPI", "local_path": "",
     "pdf_url": "https://www.mdpi.com/x/pdf", "landing_url": "https://doi.org/10.3390/ijms1"},
    {"record_id": "R3", "doi": "10.1038/s41588-1", "title": "Nature", "local_path": "",
     "pdf_url": "https://sci-hub.se/x.pdf", "landing_url": ""},
    {"record_id": "R4", "doi": "", "title": "No DOI", "local_path": ""},
    {"record_id": "R6", "doi": "", "title": "No DOI, has OA link", "local_path": "",
     "pdf_url": "https://repo.example.edu/r6.pdf", "landing_url": ""},
    {"record_id": "R5", "doi": "10.1111/tpj.1", "title": "Wiley", "local_path": "", "pdf_url": "", "landing_url": ""},
]


def test_worklist_rows_and_candidates():
    rows = ar.worklist(STATUS, "04-library/agent_pdfs")
    assert [r["record_id"] for r in rows] == ["R2", "R3", "R6", "R5"]
    c2 = rows[0]["candidate_urls"].split(" | ")
    assert c2[0] == "https://www.mdpi.com/x/pdf" and "https://doi.org/10.3390/ijms1" in c2
    assert any("europepmc.org" in u for u in c2)
    c3 = rows[1]["candidate_urls"]
    assert "sci-hub" not in c3 and "https://www.nature.com/articles/s41588-1.pdf" in c3
    assert "onlinelibrary.wiley.com/doi/pdfdirect/10.1111/tpj.1" in rows[3]["candidate_urls"]
    assert rows[2]["candidate_urls"] == "https://repo.example.edu/r6.pdf" and rows[2]["landing_url"] == ""
    assert rows[0]["save_as"] == "04-library/agent_pdfs/R2.pdf"
    assert len(c2) == len(set(c2))


def test_worklist_adds_openalex_locations_without_blocked_hosts():
    def get(url):
        assert "api.openalex.org" in url
        return {"locations": [
            {"is_oa": True, "pdf_url": "https://repo.example.edu/1.pdf", "landing_page_url": "https://repo.example.edu/1"},
            {"is_oa": True, "pdf_url": "https://www.biorxiv.org/content/10.1101/1.full.pdf"},
            {"is_oa": False, "pdf_url": "https://paywalled.example/x.pdf"},
            {"is_oa": True, "pdf_url": "https://www.researchgate.net/x.pdf"}]}
    rows = ar.worklist(STATUS[1:2], "in", get=get)
    c = rows[0]["candidate_urls"]
    assert "repo.example.edu/1.pdf" in c and "biorxiv" in c
    assert "paywalled" not in c and "researchgate" not in c


def _work(tmp_path, **marks):
    rows = ar.worklist(STATUS, str(tmp_path / "in"))
    for r in rows:
        r.update(marks.get(r["record_id"], {}))
    return rows


def test_accept_ingests_real_pdf_rejects_html_and_records_reasons(tmp_path):
    inc, pdfs = tmp_path / "in", tmp_path / "pdfs"
    inc.mkdir()
    (inc / "R2.pdf").write_bytes(b"%PDF-1.7 body")
    (inc / "R3.pdf").write_bytes(b"<!DOCTYPE html><html>Just a moment...</html>")
    work = _work(tmp_path, R3={"agent_reason": "browser showed a login page"},
                 R5={"agent_retry": "failed", "agent_reason": "403 in browser too; Cloudflare check"},
                 R6={"agent_retry": "failed", "agent_reason": "404", "agent_retry_method": "curl"})
    merged, unfinished = ar.accept(STATUS, work, inc, pdfs)
    by = {r["record_id"]: r for r in merged}
    assert by["R2"]["agent_retry"] == "got" and Path(by["R2"]["local_path"]).read_bytes().startswith(b"%PDF")
    assert by["R3"]["agent_retry"] == "failed" and "not a PDF" in by["R3"]["agent_reason"]
    assert by["R3"]["agent_reason"].startswith("browser showed a login page; ")
    assert by["R6"]["agent_retry_method"] == "curl"
    assert by["R5"]["agent_retry"] == "failed" and "Cloudflare" in by["R5"]["agent_reason"]
    assert by["R1"]["local_path"] == "pdfs/R1.pdf" and by["R1"]["agent_retry"] == ""
    assert unfinished == []


def test_accept_never_overwrites_existing_pdf(tmp_path):
    inc, pdfs = tmp_path / "in", tmp_path / "pdfs"
    inc.mkdir()
    pdfs.mkdir()
    (pdfs / "R2.pdf").write_bytes(b"%PDF-1.4 older different file")
    (inc / "R2.pdf").write_bytes(b"%PDF-1.7 new")
    work = _work(tmp_path, R3={"agent_retry": "failed", "agent_reason": "x"},
                 R5={"agent_retry": "failed", "agent_reason": "y"},
                 R6={"agent_retry": "failed", "agent_reason": "z"})
    merged, _ = ar.accept(STATUS, work, inc, pdfs)
    assert (pdfs / "R2.pdf").read_bytes() == b"%PDF-1.4 older different file"
    r2 = next(r for r in merged if r["record_id"] == "R2")
    assert r2["local_path"].endswith("R2-agent.pdf")


def test_accept_flags_untried_and_bad_marks(tmp_path):
    inc = tmp_path / "in"
    inc.mkdir()
    merged, unfinished = ar.accept(STATUS, _work(tmp_path), inc, tmp_path / "pdfs")
    assert unfinished == ["R2", "R3", "R6", "R5"]
    with pytest.raises(ValueError, match="needs a reason"):
        ar.accept(STATUS, _work(tmp_path, R2={"agent_retry": "failed"}), inc, tmp_path / "pdfs")
    with pytest.raises(ValueError, match="got or failed"):
        ar.accept(STATUS, _work(tmp_path, R2={"agent_retry": "maybe"}), inc, tmp_path / "pdfs")
    merged, _ = ar.accept(STATUS, _work(tmp_path, R2={"agent_retry": "got"}), inc, tmp_path / "pdfs")
    assert "no file" in next(r for r in merged if r["record_id"] == "R2")["agent_reason"]


def test_only_essential_still_missing_after_retry_reach_please_fetch(tmp_path):
    inc = tmp_path / "in"
    inc.mkdir()
    (inc / "R2.pdf").write_bytes(b"%PDF-1.7")
    work = _work(tmp_path, R3={"agent_retry": "failed", "agent_reason": "publisher 403 in browser"},
                 R5={"agent_retry": "failed", "agent_reason": "no OA copy"},
                 R6={"agent_retry": "failed", "agent_reason": "404"})
    for w in work:
        if w["record_id"] == "R3":
            w["agent_retry_method"] = "curl"
    merged, _ = ar.accept(STATUS, work, inc, tmp_path / "pdfs")
    need = [{"record_id": "R2", "need": "essential", "why": "core", "rank": "1"},
            {"record_id": "R3", "need": "essential", "why": "core", "rank": "2"},
            {"record_id": "R4", "need": "abstract_ok", "why": "", "rank": ""},
            {"record_id": "R6", "need": "abstract_ok", "why": "", "rank": ""},
            {"record_id": "R5", "need": "useful", "why": "extra", "rank": ""}]
    fetch, abstract, untriaged, _ = pf.build(merged, need, None, 15)
    assert [r["record_id"] for r in fetch] == ["R3"] and not untriaged
    md = pf.render_md(fetch, len(abstract))
    assert "Agent retry failed (curl): publisher 403 in browser" in md
    assert "my own browser" not in md


def test_main_roundtrip_and_no_overwrite(tmp_path):
    st = tmp_path / "oa_check.csv"
    with st.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=foa.FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(STATUS)
    wl = tmp_path / "agent_retry.tsv"
    assert ar.main(["worklist", str(st), "-o", str(wl), "--incoming", str(tmp_path / "in")]) == 0
    assert ar.main(["worklist", str(st), "-o", str(wl)]) == 2
    (tmp_path / "in").mkdir()
    out = tmp_path / "after.csv"
    args = ["accept", "--status", str(st), "--worklist", str(wl), "--incoming", str(tmp_path / "in"),
            "--pdf-dir", str(tmp_path / "pdfs"), "-o", str(out)]
    assert ar.main(args) == 1  # nothing tried yet
    assert "agent_retry" in out.read_text().splitlines()[0]
    assert ar.main(args) == 2  # refuses to overwrite
    assert ar.main(args + ["--force"]) == 1  # documented rerun after exit 1


def test_polite_user_agent(monkeypatch):
    assert "mailto" not in foa.user_agent() and "Mozilla" not in foa.user_agent()
    monkeypatch.setenv("LRS_CONTACT_EMAIL", "me@example.org")
    assert foa.user_agent().endswith("; mailto:me@example.org)")


def test_empty_http_reason_not_shown():
    import io
    import urllib.error
    e = urllib.error.HTTPError("u", 503, "", {}, io.BytesIO(b""))
    assert foa.err_text(e) == "HTTP 503"
    assert foa.err_text(urllib.error.HTTPError("u", 403, "Forbidden", {}, io.BytesIO(b""))) == "HTTP 403 Forbidden"


def test_second_layer_no_overwrite_of_agent_copy(tmp_path):
    inc, pdfs = tmp_path / "in", tmp_path / "pdfs"
    inc.mkdir()
    pdfs.mkdir()
    (pdfs / "R2.pdf").write_bytes(b"%PDF-1.4 A")
    (pdfs / "R2-agent.pdf").write_bytes(b"%PDF-1.4 B")
    (inc / "R2.pdf").write_bytes(b"%PDF-1.7 C")
    with pytest.raises(ValueError, match="not overwriting"):
        ar.accept(STATUS, _work(tmp_path), inc, pdfs)
    assert (pdfs / "R2.pdf").read_bytes() == b"%PDF-1.4 A"
    assert (pdfs / "R2-agent.pdf").read_bytes() == b"%PDF-1.4 B"


def test_worklist_keeps_only_http_https_candidates():
    def get(url):
        return {"locations": [{"is_oa": True, "pdf_url": "ftp://ftp.example.org/x.pdf",
                               "landing_page_url": "javascript:alert(1)"},
                              {"is_oa": True, "pdf_url": "http://repo.example.edu/2.pdf"}]}
    row = dict(STATUS[1], pdf_url="file:///etc/passwd")
    c = ar.worklist([row], "in", get=get)[0]["candidate_urls"].split(" | ")
    assert "http://repo.example.edu/2.pdf" in c
    assert all(u.split(":", 1)[0] in ("http", "https") for u in c)


def test_worklist_survives_openalex_error():
    def get(url):
        raise OSError("HTTP 503")
    rows = ar.worklist(STATUS[1:2], "in", get=get)
    assert len(rows) == 1 and "https://www.mdpi.com/x/pdf" in rows[0]["candidate_urls"]


def test_no_unverified_mdpi_pattern():
    assert ar.publisher_patterns("10.3390/ijms1") == []
