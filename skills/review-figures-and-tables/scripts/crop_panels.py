#!/usr/bin/env python3
"""Crop panels from PDFs the user already has, using a source ledger.

An empty or missing ledger writes nothing. The same source panel cannot be
used twice. `needs-permission` rows are not written as publication files.
This script does not download a PDF.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

COLUMNS = (
    "figure_id",
    "panel_id",
    "source_pdf",
    "page",
    "original_figure",
    "crop_box",
    "copyright_status",
    "used_in",
)
STATUSES = {
    "cc-by",
    "cc-by-nc",
    "publisher-permission-granted",
    "needs-permission",
}
BLOCKED = "needs-permission"


def _read_rows(text: str) -> List[dict]:
    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None:
        return []
    reader.fieldnames = [name.strip() for name in reader.fieldnames]
    rows = []
    for row in reader:
        rows.append({key: (value or "").strip() for key, value in row.items() if key})
    return rows


def parse_box(value: str) -> Optional[Tuple[float, float, float, float]]:
    parts = [part.strip() for part in (value or "").split(",")]
    if len(parts) != 4:
        return None
    try:
        box = tuple(float(part) for part in parts)
    except ValueError:
        return None
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def validate_rows(rows: Sequence[dict], pdf_ok: Callable[[str], Optional[str]]) -> List[str]:
    if not rows:
        return ["panel crop ledger is empty"]
    errors: List[str] = []
    seen = set()
    for index, row in enumerate(rows, start=1):
        missing = [column for column in COLUMNS if not row.get(column)]
        if missing:
            errors.append(f"row {index} missing {', '.join(missing)}")
            continue
        if row["copyright_status"] not in STATUSES:
            errors.append(f"row {index} copyright_status is not allowed")
        if "://" in row["source_pdf"]:
            errors.append(f"row {index} source_pdf must be a local file")
        else:
            problem = pdf_ok(row["source_pdf"])
            if problem:
                errors.append(f"row {index} {problem}")
        if not row["page"].isdigit() or int(row["page"]) < 1:
            errors.append(f"row {index} page must be a positive integer")
        if parse_box(row["crop_box"]) is None:
            errors.append(f"row {index} crop_box must be x0,y0,x1,y1")
        key = (row["source_pdf"], row["page"], row["original_figure"], row["crop_box"])
        if key in seen:
            errors.append(f"row {index} duplicates a source panel")
        seen.add(key)
    return errors


def publication_ready(rows: Sequence[dict]) -> bool:
    return bool(rows) and all(row.get("copyright_status") != BLOCKED for row in rows)


def local_pdf_problem(path: str) -> Optional[str]:
    file_path = Path(path)
    if not file_path.is_file():
        return "source_pdf is not on disk"
    with file_path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            return "source_pdf is not a PDF"
    return None


def crop_pdf(source: Path, page: int, box: Tuple[float, float, float, float], dest: Path) -> None:
    """Crop one page of a local PDF. Raises if pypdf is not installed."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise RuntimeError("pypdf is required to crop a local PDF") from exc
    reader = PdfReader(str(source))
    if page < 1 or page > len(reader.pages):
        raise ValueError(f"page {page} is outside {source.name}")
    pdf_page = reader.pages[page - 1]
    x0, y0, x1, y1 = box
    pdf_page.cropbox.lower_left = (x0, y0)
    pdf_page.cropbox.upper_right = (x1, y1)
    writer = PdfWriter()
    writer.add_page(pdf_page)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as handle:
        writer.write(handle)


def _write_blocked(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("figure_id", "panel_id", "copyright_status"),
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "figure_id": row["figure_id"],
                    "panel_id": row["panel_id"],
                    "copyright_status": row["copyright_status"],
                }
            )


def write_crops(
    ledger_text: str,
    out_dir: Path,
    crop: Callable[..., None] = crop_pdf,
) -> List[str]:
    """Validate, then write publication crops. Any error writes nothing."""
    if not ledger_text.strip():
        return ["panel crop ledger is empty"]
    rows = _read_rows(ledger_text)
    header_ok = True
    if rows:
        header_ok = set(COLUMNS).issubset(rows[0].keys()) or all(
            column in ledger_text.splitlines()[0] for column in COLUMNS
        )
    if not header_ok:
        return ["panel crop ledger header is missing a required column"]
    errors = validate_rows(rows, local_pdf_problem)
    if errors:
        return errors
    blocked = [row for row in rows if row["copyright_status"] == BLOCKED]
    ready = [row for row in rows if row["copyright_status"] != BLOCKED]
    written: List[Path] = []
    try:
        for row in ready:
            box = parse_box(row["crop_box"])
            assert box is not None
            dest = out_dir / f"{row['figure_id'].replace(' ', '-')}__{row['panel_id']}.pdf"
            crop(Path(row["source_pdf"]), int(row["page"]), box, dest)
            written.append(dest)
    except (OSError, RuntimeError, ValueError) as exc:
        for path in written:
            path.unlink(missing_ok=True)
        return [str(exc)]
    if blocked:
        _write_blocked(out_dir / "crop_blocked.tsv", blocked)
    return []


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.ledger.is_file():
        print("ERROR panel crop ledger is missing", file=sys.stderr)
        return 1
    errors = write_crops(args.ledger.read_text(encoding="utf-8"), args.out)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK panel crops")
    return 0


if __name__ == "__main__":
    sys.exit(main())
