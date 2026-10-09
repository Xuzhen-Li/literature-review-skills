#!/usr/bin/env python3
"""Check citation keys, unresolved markers, and outline coverage."""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple

PAREN_RE = re.compile(r"\(([^()]*)\)")
EVIDENCE_RE = re.compile(r"\bE\d{3,}\b")
COMMENT_RE = re.compile(r"<!--\s*(E\d{3,})\s*-->")
NAME_RE = re.compile(
    r"^(?:\[VERIFY\]|[A-Z][A-Za-z'\-]+(?: et al\.| and [A-Z][A-Za-z'\-]+)?, \d{4})$"
)
HEADER_IDS_RE = re.compile(r"^-\s+Evidence IDs:\s*(.+)$", re.M)
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?")
DROPPED_RE = re.compile(r"\bdropped (E\d{3,})\b")
SECTION_RE = re.compile(r"^## S(\d+)\.\s+(.+?)\s*$", re.M)
ID_COLUMNS = ("evidence_id", "id")


def load_evidence_ids(path: Path) -> Set[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header")
        fields = [name.strip() for name in reader.fieldnames]
        reader.fieldnames = fields
        column = next((name for name in ID_COLUMNS if name in fields), None)
        if column is None:
            raise ValueError(f"{path} needs a column named evidence_id or id")
        return {
            (row.get(column) or "").strip()
            for row in reader
            if (row.get(column) or "").strip()
        }


def parse_group(inner: str) -> Optional[List[str]]:
    """Parse '(Name, Year; E001; Name et al., Year; E002)'."""
    parts = [part.strip() for part in inner.split(";")]
    if len(parts) < 2 or len(parts) % 2 != 0:
        return None
    found: List[str] = []
    for index in range(0, len(parts), 2):
        name, evidence_id = parts[index], parts[index + 1]
        if not re.fullmatch(r"E\d{3,}", evidence_id):
            return None
        if not NAME_RE.fullmatch(name):
            return None
        found.append(evidence_id)
    return found


def collect_ids(text: str) -> Tuple[Set[str], List[str]]:
    """Collect evidence IDs from citation groups and HTML comments."""
    errors: List[str] = []
    found: Set[str] = set()
    occupied = set()
    for match in COMMENT_RE.finditer(text):
        found.add(match.group(1))
        occupied.update(range(match.start(), match.end()))
    for match in PAREN_RE.finditer(text):
        inner = match.group(1)
        if not EVIDENCE_RE.search(inner):
            continue
        parsed = parse_group(inner)
        if parsed is None:
            errors.append(f"malformed citation: ({inner})")
        else:
            found.update(parsed)
        occupied.update(range(match.start(), match.end()))
    for match in EVIDENCE_RE.finditer(text):
        if match.start() not in occupied:
            errors.append(f"evidence ID outside a citation or comment: {match.group()}")
    if "[NEEDS SOURCE]" in text:
        errors.append("unresolved [NEEDS SOURCE]")
    if "[VERIFY]" in text:
        errors.append("unresolved [VERIFY]")
    return found, errors


def _word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def check_section(
    text: str,
    evidence_ids: Optional[Set[str]] = None,
    budget: Optional[int] = None,
) -> List[str]:
    """Check one section file that has a metadata header and '## Prose'."""
    if "## Prose" not in text:
        return ["missing ## Prose"]
    header, prose = text.split("## Prose", 1)
    header_match = HEADER_IDS_RE.search(header)
    if header_match is None:
        return ["missing '- Evidence IDs:' in the section header"]
    header_ids = EVIDENCE_RE.findall(header_match.group(1))
    if not header_ids:
        return ["section header must list at least one evidence ID"]
    found, errors = collect_ids(prose)
    if set(header_ids) != found:
        missing = sorted(set(header_ids) - found)
        extra = sorted(found - set(header_ids))
        if missing:
            errors.append(f"header IDs not cited in prose: {', '.join(missing)}")
        if extra:
            errors.append(f"prose cites IDs absent from the header: {', '.join(extra)}")
    if evidence_ids is not None:
        unknown = sorted(found - evidence_ids)
        if unknown:
            errors.append(f"unknown evidence IDs: {', '.join(unknown)}")
    if budget is not None:
        count = _word_count(prose)
        low = math.floor(budget * 0.9)
        high = math.ceil(budget * 1.1)
        if not low <= count <= high:
            errors.append(f"word count {count} is outside {low}-{high} for budget {budget}")
    return errors


def outline_evidence_ids(outline_text: str) -> Set[str]:
    found: Set[str] = set()
    for line in outline_text.splitlines():
        match = re.match(r"^-\s+Evidence IDs:\s*(.+)$", line.strip())
        if match and match.group(1) != "none":
            found.update(EVIDENCE_RE.findall(match.group(1)))
    return found


def check_finished_draft(outline_text: str, drafts: dict) -> List[str]:
    """Refuse a finished draft while limitations or next questions are absent."""
    matches = list(SECTION_RE.finditer(outline_text))
    sections = [(int(match.group(1)), match.group(2).strip()) for match in matches]
    errors: List[str] = []

    def first(needle: str) -> Optional[int]:
        found = [number for number, title in sections if needle in title.casefold()]
        return found[0] if found else None

    limitations = first("limitation")
    next_questions = first("next question")
    conclusion = first("conclusion")
    if limitations is None:
        errors.append("outline has no Limitations section")
    if next_questions is None:
        errors.append("outline has no Next questions section")
    if limitations is not None and next_questions is not None and limitations == next_questions:
        errors.append("limitations and next questions must be different sections")
    if conclusion is not None and next_questions is not None and conclusion == next_questions:
        errors.append("next questions must not be folded into the conclusion")
    for number, label in ((limitations, "Limitations"), (next_questions, "Next questions")):
        if number is None:
            continue
        text = drafts.get(number)
        if not text:
            errors.append(f"{label} section S{number} has no draft file")
        elif not re.search(r"(?m)^-\s+Status:\s*checked\s*$", text):
            errors.append(f"{label} section S{number} is not Status: checked")
    return errors


def check_manuscript(
    manuscript: str,
    outline_text: str,
    change_log: str,
    evidence_ids: Set[str],
) -> List[str]:
    """Check an assembled manuscript against the outline and the change log."""
    found, errors = collect_ids(manuscript)
    unknown = sorted(found - evidence_ids)
    if unknown:
        errors.append(f"unknown evidence IDs: {', '.join(unknown)}")
    outline_ids = outline_evidence_ids(outline_text)
    dropped = set(DROPPED_RE.findall(change_log))
    missing = sorted(outline_ids - found - dropped)
    if missing:
        errors.append(
            "outline IDs missing from the manuscript need a change-log reason "
            f"'dropped E###': {', '.join(missing)}"
        )
    still_cited = sorted(dropped & found)
    if still_cited:
        errors.append(f"dropped IDs are still cited: {', '.join(still_cited)}")
    outside_outline = sorted(found - outline_ids)
    if outside_outline:
        errors.append(
            f"cited IDs are not in the outline: {', '.join(outside_outline)}"
        )
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("section", nargs="?", type=Path)
    parser.add_argument("--budget", type=int)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--manuscript", type=Path)
    parser.add_argument("--outline", type=Path)
    parser.add_argument("--change-log", type=Path)
    parser.add_argument("--finish", action="store_true")
    parser.add_argument("--drafts", type=Path)
    args = parser.parse_args(argv)
    evidence_ids = None
    if args.evidence:
        try:
            evidence_ids = load_evidence_ids(args.evidence)
        except (OSError, ValueError) as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
    if args.finish:
        if not args.outline or not args.drafts:
            print("ERROR finish mode needs --outline and --drafts", file=sys.stderr)
            return 1
        drafts = {}
        for path in sorted(args.drafts.glob("S*.md")):
            match = re.match(r"S(\d+)", path.name)
            if match is None:
                continue
            number = int(match.group(1))
            if number in drafts:
                print(f"ERROR two draft files for section {number}", file=sys.stderr)
                return 1
            drafts[number] = path.read_text(encoding="utf-8")
        errors = check_finished_draft(args.outline.read_text(encoding="utf-8"), drafts)
        if errors:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
            return 1
        print("OK draft set")
        return 0
    if args.manuscript:
        if not args.outline or not args.change_log or evidence_ids is None:
            print(
                "ERROR manuscript mode needs --outline, --change-log, and --evidence",
                file=sys.stderr,
            )
            return 1
        errors = check_manuscript(
            args.manuscript.read_text(encoding="utf-8"),
            args.outline.read_text(encoding="utf-8"),
            args.change_log.read_text(encoding="utf-8"),
            evidence_ids,
        )
    else:
        if args.section is None or args.budget is None or evidence_ids is None:
            print(
                "ERROR section mode needs a path, --budget, and --evidence",
                file=sys.stderr,
            )
            return 1
        errors = check_section(
            args.section.read_text(encoding="utf-8"),
            evidence_ids,
            args.budget,
        )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK citations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
