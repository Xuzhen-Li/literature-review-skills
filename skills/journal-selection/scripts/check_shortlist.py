#!/usr/bin/env python3
"""Validate 11-journal/journal_shortlist.md."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Sequence
from urllib.parse import parse_qs, urlparse

HEADERS = (
    "journal",
    "publisher",
    "article_type",
    "accepts_reviews",
    "invited_only",
    "oa_model",
    "apc",
    "word_limit",
    "indexing",
    "turnaround",
    "fit",
    "verified",
)
VERIFIED_RE = re.compile(r"^verified on (\d{4}-\d{2}-\d{2}) at (https://\S+)$")
BLOCKED_HOST_PARTS = (
    "wikipedia.org",
    "researchgate.net",
    "academia.edu",
    "reddit.com",
    "medium.com",
    "twitter.com",
    "facebook.com",
    "linkedin.com",
    "youtube.com",
    "bilibili.com",
    "doi.org",
    "sci-hub",
    "libgen",
    "letpub.com",
)


def _blocked(url: str) -> Optional[str]:
    host = (urlparse(url).hostname or "").lower()
    if not host or "." not in host:
        return "missing host"
    if host == "example.com" or host.endswith(".example") or host.endswith(".example.com"):
        return host
    for part in BLOCKED_HOST_PARTS:
        if part in host:
            return host
    if any(key.lower().startswith("utm_") for key in parse_qs(urlparse(url).query)):
        return "tracking parameter"
    return None


def _cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def check_shortlist(text: str, today: Optional[date] = None) -> List[str]:
    """Return errors for a journal shortlist. today defaults to the local date."""
    today = today or date.today()
    errors: List[str] = []
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return ["shortlist table is missing"]
    headers = _cells(table_lines[0])
    if headers != list(HEADERS):
        errors.append("table header does not match the required columns")
        return errors
    separator = _cells(table_lines[1])
    if len(separator) != len(HEADERS) or not all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in separator
    ):
        errors.append("table separator row is missing")
        return errors

    rows = []
    for line in table_lines[2:]:
        cells = _cells(line)
        if len(cells) != len(HEADERS):
            errors.append(f"row has {len(cells)} cells, expected {len(HEADERS)}")
            continue
        row = dict(zip(HEADERS, cells))
        if any(value == "" for value in row.values()):
            errors.append(f"empty cell in row {row.get('journal') or '(blank)'}")
        rows.append(row)

    if not 3 <= len(rows) <= 5:
        errors.append(f"shortlist must have 3 to 5 journals, found {len(rows)}")
    names = [row["journal"] for row in rows]
    if len(set(names)) != len(names):
        errors.append("duplicate journal names")

    for row in rows:
        label = row["journal"] or "(blank)"
        if row["publisher"] == "[VERIFY]":
            errors.append(f"{label} publisher is unverified")
        for column in ("accepts_reviews", "invited_only"):
            if row[column] not in {"yes", "no"}:
                errors.append(f"{label} {column} must be yes or no")
        match = VERIFIED_RE.fullmatch(row["verified"])
        if match is None:
            errors.append(
                f"{label} verified cell must be 'verified on YYYY-MM-DD at https://...'"
            )
            continue
        checked = datetime.strptime(match.group(1), "%Y-%m-%d").date()
        if checked > today:
            errors.append(f"{label} verification date is in the future")
        blocked = _blocked(match.group(2))
        if blocked:
            errors.append(f"{label} verification URL is not an official page ({blocked})")

    recommended = re.search(r"^Recommended:\s*(.+)\s*$", text, re.M)
    backup = re.search(r"^Backup:\s*(.+)\s*$", text, re.M)
    if recommended is None or backup is None:
        errors.append("missing 'Recommended:' or 'Backup:'")
        return errors
    by_name = {row["journal"]: row for row in rows}
    for label, match in (("Recommended", recommended), ("Backup", backup)):
        name = match.group(1).strip()
        row = by_name.get(name)
        if row is None:
            errors.append(f"{label} journal is not a table row")
            continue
        if row["accepts_reviews"] != "yes":
            errors.append(f"{label} journal does not accept reviews")
        if row["invited_only"] == "yes":
            invitation = f"Invitation for {name}: yes"
            if invitation not in text:
                errors.append(f"{label} journal is invited-only and has no invitation line")
    if recommended.group(1).strip() == backup.group(1).strip():
        errors.append("Recommended and Backup must be different journals")

    if re.search(r"^Double-anonymized:\s*(yes|no)\s*$", text, re.M) is None:
        errors.append("missing 'Double-anonymized: yes' or 'Double-anonymized: no'")
    style = re.search(r"^Reference style:\s*(.+)\s*$", text, re.M)
    if style is None or style.group(1).strip() in {"", "[VERIFY]"}:
        errors.append("missing a reference style copied from the journal, or 'not stated'")
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shortlist", type=Path)
    args = parser.parse_args(argv)
    errors = check_shortlist(args.shortlist.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK shortlist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
