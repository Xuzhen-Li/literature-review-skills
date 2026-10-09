#!/usr/bin/env python3
"""Concatenate locked outline sections into 10-polish/manuscript.md."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

SECTION_RE = re.compile(r"^## S(\d+)\.\s+(.+?)\s*$", re.M)


def assemble(outline_text: str, drafts: Dict[int, str]) -> str:
    """Join section prose in outline order under the outline titles."""
    matches = list(SECTION_RE.finditer(outline_text))
    if not matches:
        raise ValueError("outline has no sections")
    numbers = [int(match.group(1)) for match in matches]
    missing = [number for number in numbers if number not in drafts]
    if missing:
        raise ValueError(f"missing drafts: {missing}")
    extra = sorted(number for number in drafts if number not in numbers)
    if extra:
        raise ValueError(f"drafts not in the outline: {extra}")
    chunks: List[str] = []
    for match in matches:
        number = int(match.group(1))
        text = drafts[number]
        if "## Prose" not in text:
            raise ValueError(f"S{number} missing ## Prose")
        prose = text.split("## Prose", 1)[1].strip()
        if not prose:
            raise ValueError(f"S{number} prose is empty")
        chunks.append(f"## {match.group(2).strip()}\n\n{prose}")
    return "\n\n".join(chunks) + "\n"


def _load_drafts(draft_dir: Path) -> Dict[int, str]:
    drafts: Dict[int, str] = {}
    for path in sorted(draft_dir.glob("S*.md")):
        match = re.match(r"S(\d+)", path.name)
        if match is None:
            continue
        number = int(match.group(1))
        if number in drafts:
            raise ValueError(f"two draft files for section {number}")
        drafts[number] = path.read_text(encoding="utf-8")
    return drafts


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outline", required=True, type=Path)
    parser.add_argument("--drafts", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        text = assemble(
            args.outline.read_text(encoding="utf-8"),
            _load_drafts(args.drafts),
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
