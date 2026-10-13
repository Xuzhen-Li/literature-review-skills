#!/usr/bin/env python3
"""Hand DOIs to the user when this computer cannot download the paper.

The script writes an upload list and accepts PDFs the user has placed on
disk. It does not fetch a URL.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional, Sequence

AWAITING = "awaiting_user_upload"
NO_PERMISSION = "no_download_permission"
UPLOADED = "user_uploaded"
UPLOAD_STATUSES = {AWAITING, NO_PERMISSION}
LIST_FIELDS = ("record_id", "doi", "title", "save_as")


def _read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header")
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        return [
            {key: (value or "").strip() for key, value in row.items() if key}
            for row in reader
        ]


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    delimiter = "\t" if path.suffix == ".tsv" else ","
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            delimiter=delimiter,
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def upload_list(rows: Sequence[dict]) -> List[dict]:
    """Rows the user must upload. DOI is copied, never invented."""
    listed = []
    for row in rows:
        if (row.get("pdf_status") or "") not in UPLOAD_STATUSES:
            continue
        record_id = (row.get("record_id") or "").strip()
        if not record_id:
            continue
        listed.append(
            {
                "record_id": record_id,
                "doi": (row.get("doi") or "").strip(),
                "title": (row.get("title") or "").strip(),
                "save_as": f"04-library/uploads/{record_id}.pdf",
            }
        )
    return listed


def _is_pdf(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    with path.open("rb") as handle:
        return handle.read(5) == b"%PDF-"


def accept_uploads(rows: Sequence[dict], upload_dir: Path) -> List[dict]:
    """Mark a row uploaded when the user has put that PDF in the folder."""
    updated = []
    for row in rows:
        copied = dict(row)
        record_id = (copied.get("record_id") or "").strip()
        if copied.get("pdf_status") in UPLOAD_STATUSES and _is_pdf(upload_dir / f"{record_id}.pdf"):
            copied["pdf_status"] = UPLOADED
            copied["retrieval_route"] = "user_upload"
            copied["local_path"] = f"04-library/uploads/{record_id}.pdf"
            copied["pdf_url"] = ""
            note = "user uploaded the PDF for this DOI"
            copied["notes"] = note
        updated.append(copied)
    return updated


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    write_parser = subparsers.add_parser("write", help="write the DOI upload list")
    write_parser.add_argument("--status", required=True, type=Path)
    write_parser.add_argument("--out", required=True, type=Path)
    accept_parser = subparsers.add_parser("accept", help="record PDFs the user uploaded")
    accept_parser.add_argument("--status", required=True, type=Path)
    accept_parser.add_argument("--uploads", required=True, type=Path)
    accept_parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        rows = _read_csv(args.status)
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    if args.command == "write":
        listed = upload_list(rows)
        if not listed:
            print("ERROR no records are waiting for a user upload", file=sys.stderr)
            return 1
        _write_csv(args.out, LIST_FIELDS, listed)
        print(f"OK doi upload list {len(listed)}")
        return 0
    updated = accept_uploads(rows, args.uploads)
    fieldnames = list(rows[0].keys()) if rows else ["record_id"]
    for extra in ("pdf_status", "retrieval_route", "local_path", "pdf_url", "notes"):
        if extra not in fieldnames:
            fieldnames.append(extra)
    _write_csv(args.out, fieldnames, updated)
    gained = sum(1 for row in updated if row.get("pdf_status") == UPLOADED)
    print(f"OK user uploads {gained}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
