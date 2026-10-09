#!/usr/bin/env python3
"""Overclaim scan, change-log check, and kept-phrase decisions."""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

CHANGE_TYPES = {
    "hedge",
    "language",
    "consistency",
    "citation",
    "format",
    "structure",
    "cut_to_limit",
}
CHANGE_COLUMNS = (
    "id",
    "file",
    "location",
    "change_type",
    "before",
    "after",
    "reason",
)
LOCATION_RE = re.compile(
    r"(?:lines\s+\d+\s*-\s*\d+)|(?:p\.\s*\d+,\s*lines\s+\d+\s*-\s*\d+)",
    re.I,
)
DEFAULT_PHRASES = (
    Path(__file__).resolve().parents[1] / "references" / "overclaim_words.md"
)


def load_phrases(text: str) -> List[Tuple[str, str]]:
    """Load '- phrase' bullets under '## Block' and '## Review'."""
    severity = ""
    phrases: List[Tuple[str, str]] = []
    for line in text.splitlines():
        if line.startswith("## Block"):
            severity = "block"
        elif line.startswith("## Review"):
            severity = "review"
        elif line.startswith("## "):
            severity = ""
        elif line.startswith("- ") and severity:
            phrase = line[2:].strip()
            if phrase:
                phrases.append((phrase, severity))
    if not phrases or not any(level == "block" for _, level in phrases):
        raise ValueError("phrase file needs a ## Block list")
    return phrases


def find_overclaims(text: str, phrases: Sequence[Tuple[str, str]]) -> List[dict]:
    """Return non-overlapping hits, longest phrase first on each line."""
    ordered = sorted(phrases, key=lambda item: len(item[0]), reverse=True)
    hits: List[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        occupied = [False] * len(line)
        lowered = line.lower()
        for phrase, severity in ordered:
            needle = phrase.lower()
            start = 0
            while True:
                index = lowered.find(needle, start)
                if index < 0:
                    break
                end = index + len(needle)
                before_ok = index == 0 or not lowered[index - 1].isalnum()
                after_ok = end == len(lowered) or not lowered[end].isalnum()
                if before_ok and after_ok and not any(occupied[index:end]):
                    for cursor in range(index, end):
                        occupied[cursor] = True
                    hits.append(
                        {
                            "line": lineno,
                            "phrase": phrase,
                            "severity": severity,
                            "text": line.strip(),
                        }
                    )
                start = index + 1
    return hits


def _rows(text: str):
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
    rows = []
    for row in reader:
        rows.append({key: (value or "").strip() for key, value in row.items() if key})
    return reader.fieldnames or [], rows


def validate_change_log(text: str, block_phrases: Sequence[str]) -> List[str]:
    """Reject new claims and block-level wording introduced by an edit."""
    errors: List[str] = []
    fieldnames, rows = _rows(text)
    missing = [column for column in CHANGE_COLUMNS if column not in fieldnames]
    if missing:
        return [f"change log missing columns: {', '.join(missing)}"]
    seen = set()
    pairs = [(phrase, "block") for phrase in block_phrases]
    for index, row in enumerate(rows, start=2):
        ident = row["id"]
        prefix = f"change {ident or index}"
        if not re.fullmatch(r"C\d+", ident):
            errors.append(f"{prefix} id must look like C001")
        if ident in seen:
            errors.append(f"{prefix} duplicate id")
        seen.add(ident)
        if row["file"] != "10-polish/manuscript.md":
            errors.append(f"{prefix} file must be 10-polish/manuscript.md")
        if LOCATION_RE.search(row["location"]) is None:
            errors.append(f"{prefix} location needs lines N-M or p. N, lines N-M")
        change_type = row["change_type"]
        if change_type not in CHANGE_TYPES:
            errors.append(f"{prefix} change_type is not allowed")
        before = row["before"]
        after = row["after"]
        if not before:
            errors.append(f"{prefix} before is empty")
        if after == "[deleted]":
            if change_type not in {"cut_to_limit", "structure"}:
                errors.append(f"{prefix} [deleted] is only for a cut or a restructure")
        elif not after or after == before:
            errors.append(f"{prefix} after must differ from before")
        if len(row["reason"]) < 15:
            errors.append(f"{prefix} reason is too short")
        if after and after != "[deleted]":
            hits = find_overclaims(after, pairs)
            if hits:
                phrases = ", ".join(hit["phrase"] for hit in hits)
                errors.append(f"{prefix} after still contains: {phrases}")
    return errors


def check_decisions(hits: Sequence[dict], decisions_text: str) -> List[str]:
    """Every review-level hit needs a removed or kept decision."""
    errors: List[str] = []
    reader = csv.DictReader(io.StringIO(decisions_text), delimiter="\t")
    if reader.fieldnames:
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
    expected = {"line", "phrase", "decision", "reason"}
    if set(reader.fieldnames or []) != expected:
        return ["decisions file needs columns line, phrase, decision, reason"]
    decisions: Dict[Tuple[str, str], dict] = {}
    for row in reader:
        key = ((row.get("line") or "").strip(), (row.get("phrase") or "").strip())
        decisions[key] = {name: (row.get(name) or "").strip() for name in expected}
    for hit in hits:
        if hit["severity"] != "review":
            continue
        key = (str(hit["line"]), hit["phrase"])
        row = decisions.get(key)
        if row is None:
            errors.append(f"line {hit['line']} '{hit['phrase']}' has no decision")
            continue
        if row["decision"] not in {"removed", "kept"}:
            errors.append(f"line {hit['line']} decision must be removed or kept")
        elif row["decision"] == "removed":
            errors.append(
                f"line {hit['line']} '{hit['phrase']}' is marked removed but is still present"
            )
        elif len(row["reason"]) < 15 or not row["reason"].startswith("kept:"):
            errors.append(
                f"line {hit['line']} kept decision needs a reason starting with 'kept:'"
            )
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--phrases", type=Path, default=DEFAULT_PHRASES)
    parser.add_argument("--change-log", type=Path)
    parser.add_argument("--decisions", type=Path)
    args = parser.parse_args(argv)
    try:
        phrases = load_phrases(args.phrases.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    manuscript = args.manuscript.read_text(encoding="utf-8")
    hits = find_overclaims(manuscript, phrases)
    errors: List[str] = []
    for hit in hits:
        if hit["severity"] == "block":
            errors.append(f"line {hit['line']} block phrase '{hit['phrase']}'")
        else:
            print(f"REVIEW line {hit['line']} '{hit['phrase']}'")
    if args.decisions:
        errors.extend(check_decisions(hits, args.decisions.read_text(encoding="utf-8")))
    if args.change_log:
        block_only = [phrase for phrase, level in phrases if level == "block"]
        errors.extend(
            validate_change_log(args.change_log.read_text(encoding="utf-8"), block_only)
        )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK polish")
    return 0


if __name__ == "__main__":
    sys.exit(main())
