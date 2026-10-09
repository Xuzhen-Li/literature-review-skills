#!/usr/bin/env python3
"""Check that a polished manuscript follows the post-lock style brief."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence

FIG_RE = re.compile(r"Fig\. \d+\b")


def _line(text: str, label: str) -> Optional[str]:
    match = re.search(rf"(?m)^-\s+{re.escape(label)}:\s*(.+?)\s*$", text)
    if match is None:
        return None
    return match.group(1).strip()


def _marker(label: str) -> str:
    cleaned = label.strip()
    if not cleaned:
        return ""
    return f"**{cleaned[:1].upper()}{cleaned[1:]}.**"


def _abstract(manuscript: str) -> str:
    match = re.search(r"(?m)^#{1,2} Abstract\s*$", manuscript)
    if match is None:
        return ""
    rest = manuscript[match.end():]
    nxt = re.search(r"(?m)^## ", rest)
    return rest[: nxt.start()] if nxt else rest


def check_style_fit(brief: str, manuscript: str, journal_name: str = "") -> List[str]:
    """Require a post-lock brief and apply its headings, abstract shape, and figure budget."""
    errors: List[str] = []
    refreshed = _line(brief, "Refreshed after journal lock")
    if refreshed != "yes":
        errors.append("style brief has not been refreshed after journal lock")
    locked = _line(brief, "Locked journal")
    if journal_name and locked != journal_name:
        errors.append("style brief locked journal does not match the journal lock")
    pattern = _line(brief, "Heading pattern")
    if not pattern:
        errors.append("style brief needs '- Heading pattern:'")
        headings: List[str] = []
    else:
        headings = [part.strip() for part in pattern.split("|")]
        if not headings or any(not part for part in headings):
            errors.append("heading pattern needs at least one heading")
        folded = [part.casefold() for part in headings]
        if not any("limitation" in part for part in folded):
            errors.append("heading pattern must include a Limitations heading")
        if not any("next question" in part for part in folded):
            errors.append("heading pattern must include a Next questions heading")
    body = [
        heading.strip()
        for heading in re.findall(r"(?m)^## (.+?)\s*$", manuscript)
        if heading.strip().casefold() != "abstract"
    ]
    if headings and body != headings:
        errors.append("manuscript headings do not follow the style brief heading pattern")
    shape = _line(brief, "Abstract shape")
    abstract = _abstract(manuscript)
    if not shape:
        errors.append("style brief needs '- Abstract shape:'")
    elif not abstract:
        errors.append("manuscript needs an Abstract section")
    else:
        cursor = 0
        for label in [part.strip() for part in shape.split(";") if part.strip()]:
            token = _marker(label)
            found = abstract.find(token, cursor)
            if found < 0:
                errors.append(f"abstract is missing {token} in brief order")
                break
            cursor = found + len(token)
    budget_raw = _line(brief, "Figure budget")
    if budget_raw is None or not budget_raw.isdigit() or int(budget_raw) < 1:
        errors.append("style brief needs a positive '- Figure budget:' integer")
    else:
        figures = set(FIG_RE.findall(manuscript))
        if len(figures) > int(budget_raw):
            errors.append(
                f"manuscript cites {len(figures)} figures; the style brief budget is {budget_raw}"
            )
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--manuscript", required=True, type=Path)
    parser.add_argument("--journal", default="")
    args = parser.parse_args(argv)
    errors = check_style_fit(
        args.brief.read_text(encoding="utf-8"),
        args.manuscript.read_text(encoding="utf-8"),
        args.journal,
    )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK style fit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
