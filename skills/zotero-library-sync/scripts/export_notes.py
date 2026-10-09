#!/usr/bin/env python3
"""Copy project notes for the user to attach in their library.

The script runs only after --confirm. It does not log into a reference manager
and it does not overwrite a note that is already in the export folder.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence

RECORD_RE = re.compile(r"(?m)^record_id:\s*(\S+)\s*$")
LOG_FIELDS = ("citation_key", "record_id", "note_path", "status", "date")


def _read_log(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            return []
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def _write_log(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in LOG_FIELDS})


def export_notes(
    reading_dir: Path,
    out_dir: Path,
    log_path: Path,
    today: str,
) -> List[str]:
    notes = sorted(path for path in reading_dir.glob("*.md") if path.is_file())
    if not notes:
        return ["no notes to export"]
    errors: List[str] = []
    pending = []
    for note in notes:
        text = note.read_text(encoding="utf-8")
        match = RECORD_RE.search(text)
        if match is None:
            errors.append(f"{note.name} has no record_id line")
            continue
        pending.append((note, text, match.group(1)))
    if errors:
        return errors
    prior = {row.get("citation_key"): row.get("status") for row in _read_log(log_path)}
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for note, text, record_id in pending:
        destination = out_dir / note.name
        if destination.exists():
            status = "attached" if prior.get(note.stem) == "attached" else "already_present"
        else:
            destination.write_text(text, encoding="utf-8")
            status = "prepared"
        rows.append(
            {
                "citation_key": note.stem,
                "record_id": record_id,
                "note_path": str(destination),
                "status": status,
                "date": today,
            }
        )
    _write_log(log_path, rows)
    return []


def mark_attached(log_path: Path, citation_key: str, today: str) -> List[str]:
    rows = _read_log(log_path)
    if not rows:
        return ["note log is missing"]
    found = False
    for row in rows:
        if row.get("citation_key") == citation_key:
            row["status"] = "attached"
            row["date"] = today
            found = True
    if not found:
        return [f"{citation_key} is not in the note log"]
    _write_log(log_path, rows)
    return []


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--reading", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--mark-attached")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    if not args.confirm:
        print("ERROR refusing to export notes until the user asks", file=sys.stderr)
        return 2
    if args.mark_attached:
        if args.log is None:
            print("ERROR --log is required", file=sys.stderr)
            return 2
        errors = mark_attached(args.log, args.mark_attached, args.date)
    else:
        if args.reading is None or args.out is None or args.log is None:
            print("ERROR --reading, --out, and --log are required", file=sys.stderr)
            return 2
        errors = export_notes(args.reading, args.out, args.log, args.date)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK note export")
    return 0


if __name__ == "__main__":
    sys.exit(main())
