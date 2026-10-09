#!/usr/bin/env python3
"""Check the Zotero collection checklist against the included record ids."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set


def _ids(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8-sig")
    sample = text.splitlines()[0] if text.splitlines() else ""
    delimiter = "\t" if "\t" in sample else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames or "record_id" not in [name.strip() for name in reader.fieldnames]:
        raise ValueError(f"{path} needs a record_id column")
    reader.fieldnames = [name.strip() for name in reader.fieldnames]
    return [(row.get("record_id") or "").strip() for row in reader if (row.get("record_id") or "").strip()]


def check_collections(
    checklist_rows: Sequence[dict],
    included_ids: Sequence[str],
    ready: bool = False,
    max_themes: int = 8,
) -> List[str]:
    errors: List[str] = []
    included = set(included_ids)
    seen: Set[str] = set()
    themes: Set[str] = set()
    if not checklist_rows:
        return ["collection checklist has no rows"]
    for row in checklist_rows:
        theme = (row.get("theme") or "").strip()
        record_id = (row.get("record_id") or "").strip()
        confirmed = (row.get("user_confirmed") or "").strip()
        if not theme or not record_id:
            errors.append("each checklist row needs a theme and a record_id")
            continue
        themes.add(theme)
        seen.add(record_id)
        if record_id not in included:
            errors.append(f"{record_id} is not in included.tsv")
        if confirmed not in {"yes", "no"}:
            errors.append(f"{record_id} user_confirmed must be yes or no")
        elif ready and confirmed != "yes":
            errors.append(f"{record_id} is not confirmed")
    if len(themes) > max_themes:
        errors.append(f"theme list has {len(themes)} names; keep at most {max_themes}")
    missing = sorted(included - seen)
    if missing:
        errors.append(f"checklist missing included records: {', '.join(missing)}")
    return errors


def _read_checklist(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        sample = handle.readline()
        handle.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header")
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checklist", required=True, type=Path)
    parser.add_argument("--included", required=True, type=Path)
    parser.add_argument("--ready", action="store_true")
    args = parser.parse_args(argv)
    try:
        errors = check_collections(
            _read_checklist(args.checklist),
            _ids(args.included),
            ready=args.ready,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK collections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
