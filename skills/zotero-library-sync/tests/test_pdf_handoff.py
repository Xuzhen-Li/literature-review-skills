"""DOI list and user-uploaded PDFs. No network."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pdf_handoff import accept_uploads, main, upload_list  # noqa: E402


def test_upload_list_copies_doi_and_skips_files_already_held():
    rows = [
        {
            "record_id": "R1",
            "doi": "10.1000/example",
            "title": "A paper",
            "pdf_status": "awaiting_user_upload",
            "pdf_url": "https://doi.org/10.1000/example",
        },
        {
            "record_id": "R2",
            "doi": "",
            "title": "No identifier",
            "pdf_status": "no_download_permission",
        },
        {
            "record_id": "R3",
            "doi": "10.1000/open",
            "title": "Open",
            "pdf_status": "available",
        },
    ]
    listed = upload_list(rows)
    assert [row["record_id"] for row in listed] == ["R1", "R2"]
    assert listed[0]["doi"] == "10.1000/example"
    assert listed[0]["save_as"] == "04-library/uploads/R1.pdf"
    assert listed[1]["doi"] == ""


def test_accept_reads_only_the_upload_folder(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    (uploads / "R1.pdf").write_bytes(b"%PDF-1.4\n")
    (uploads / "R2.txt").write_text("not a pdf", encoding="utf-8")
    rows = [
        {
            "record_id": "R1",
            "doi": "10.1000/example",
            "pdf_status": "awaiting_user_upload",
            "pdf_url": "https://publisher.example/secret.pdf",
        },
        {
            "record_id": "R2",
            "doi": "10.1000/other",
            "pdf_status": "awaiting_user_upload",
            "pdf_url": "",
        },
    ]
    updated = accept_uploads(rows, uploads)
    assert updated[0]["pdf_status"] == "user_uploaded"
    assert updated[0]["pdf_url"] == ""
    assert updated[0]["retrieval_route"] == "user_upload"
    assert updated[1]["pdf_status"] == "awaiting_user_upload"


def test_cli_writes_the_list_without_fetching(tmp_path):
    status = tmp_path / "pdf_status.csv"
    status.write_text(
        "record_id,doi,title,pdf_status\n"
        "R1,10.1000/example,A paper,no_download_permission\n",
        encoding="utf-8",
    )
    out = tmp_path / "doi_for_upload.tsv"
    assert main(["write", "--status", str(status), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "10.1000/example" in text
    assert "https://" not in text
