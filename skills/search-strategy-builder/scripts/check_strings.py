#!/usr/bin/env python3
"""Check that each database block locks exactly one search string."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

BREADTHS = ("wide", "middle", "tight")


def _sections(text: str) -> List[Tuple[str, str]]:
    parts = re.split(r"(?m)^## ", text)
    sections = []
    for part in parts[1:]:
        lines = part.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:])
        sections.append((title, body))
    return sections


def _is_database(title: str) -> bool:
    folded = title.casefold()
    if folded.startswith("prisma"):
        return False
    if folded in {"concepts", "limits", "notes"}:
        return False
    return True


def _fences(body: str) -> int:
    return len(re.findall(r"(?m)^```", body)) // 2


def check_strings(text: str) -> List[str]:
    """Accept one locked string, or wide/middle/tight with exactly one locked."""
    errors: List[str] = []
    sections = [item for item in _sections(text) if _is_database(item[0])]
    if not sections:
        return ["no database section found; use a heading such as '## PubMed'"]
    for title, body in sections:
        present = [name for name in BREADTHS if re.search(rf"(?m)^### {name}\s*$", body)]
        locked = len(re.findall(r"(?m)^- Locked: yes\s*$", body))
        declined = bool(re.search(r"(?m)^- Breadth declined:", body))
        if present and declined:
            errors.append(f"{title} cannot decline extra breadths and also list them")
        if present and present != list(BREADTHS):
            errors.append(f"{title} breadths must be wide, middle, and tight together")
        if present and _fences(body) < 3:
            errors.append(f"{title} needs one fenced string under each breadth")
        if not present and _fences(body) < 1:
            errors.append(f"{title} needs one fenced string")
        if locked != 1:
            errors.append(f"{title} must mark exactly one string with '- Locked: yes'")
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("search_strings", type=Path)
    args = parser.parse_args(argv)
    errors = check_strings(args.search_strings.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK search strings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
