#!/usr/bin/env python3
"""Rank a narrative library and check a user-confirmed core set.

The rank is a suggestion from token overlap. It does not drop records and it
does not apply a numeric cap. Confirmation is a separate file the user accepts.
Systematic, scoping, and umbrella reviews keep the full eligibility screen.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "in",
    "on",
    "for",
    "to",
    "with",
    "by",
    "from",
    "at",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "this",
    "that",
    "these",
    "those",
    "into",
    "over",
    "than",
    "not",
    "no",
}
FULL_SCREEN_TYPES = {"systematic", "scoping", "umbrella"}
BANNER = "not a complete systematic review"
NOT_READ_PHRASE = "not read"
DECISIONS = {"core", "not_read"}


def content_tokens(text: str) -> Set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if token not in STOPWORDS and len(token) > 2
    }


def rank_records(rows: Sequence[dict], question: str) -> List[dict]:
    """Return every input row, ranked by overlap with the question.

    overlap_score counts shared content tokens in the title and abstract.
    Equal scores break by record_id. No row is removed.
    """
    question_tokens = content_tokens(question)
    scored = []
    for row in rows:
        record_id = (row.get("record_id") or "").strip()
        blob = f"{row.get('title') or ''} {row.get('abstract') or ''}"
        scored.append(
            {
                "record_id": record_id,
                "overlap_score": len(question_tokens & content_tokens(blob)),
            }
        )
    scored.sort(key=lambda item: (-item["overlap_score"], item["record_id"]))
    ranked = []
    for index, item in enumerate(scored, start=1):
        ranked.append(
            {
                "record_id": item["record_id"],
                "overlap_score": str(item["overlap_score"]),
                "rank": str(index),
            }
        )
    return ranked


def _read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header")
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        rows = []
        for row in reader:
            rows.append({key: (value or "").strip() for key, value in row.items() if key})
        return rows


def _ids(rows: Iterable[dict], column: str = "record_id") -> List[str]:
    return [(row.get(column) or "").strip() for row in rows]


def check_screening_table(
    rows: Sequence[dict],
    core_ids: Set[str],
    not_read_ids: Set[str],
) -> List[str]:
    """Narrative screening.csv uses include/not_read, not eligibility exclusions."""
    errors: List[str] = []
    seen: List[str] = []
    for row in rows:
        record_id = (row.get("record_id") or "").strip()
        decision = (row.get("decision") or "").strip()
        reason = (row.get("reason_code") or "").strip()
        stage = (row.get("stage") or "").strip()
        seen.append(record_id)
        if decision == "exclude" or decision == "maybe":
            errors.append(f"{record_id} uses {decision}; narrative rows are include or not_read")
        if stage != "title_abstract":
            errors.append(f"{record_id} stage must be title_abstract in narrative mode")
        consensus = (row.get("consensus") or "").strip()
        if record_id in core_ids and (decision != "include" or reason != "CORE" or consensus != "include"):
            errors.append(f"{record_id} is in the core but is not include/CORE/include")
        if record_id in not_read_ids and (
            decision != "not_read" or reason != "NOT_READ" or consensus != "not_read"
        ):
            errors.append(f"{record_id} was not read but is not not_read/NOT_READ/not_read")
    if set(seen) != core_ids | not_read_ids or len(seen) != len(set(seen)):
        errors.append("screening.csv must list each library record once")
    return errors


def check_core(
    library_ids: Sequence[str],
    decisions: Sequence[dict],
    included_ids: Sequence[str],
    not_read_ids: Sequence[str],
    flow_text: str,
    review_type: str,
    screening_rows: Optional[Sequence[dict]] = None,
) -> List[str]:
    """Check a narrative core. Other review types must not use this shortcut."""
    if review_type in FULL_SCREEN_TYPES:
        return [
            f"{review_type} reviews keep the full eligibility screen; "
            "do not replace it with a ranked core"
        ]
    if review_type != "narrative":
        return [f"unknown review type for a narrative core: {review_type}"]
    errors: List[str] = []
    if any("max_core" in row for row in decisions):
        errors.append("fixed caps are not allowed")
    library = [item for item in library_ids if item]
    if len(library) != len(set(library)):
        errors.append("library record_id values must be unique")
    decided: Dict[str, str] = {}
    for row in decisions:
        record_id = (row.get("record_id") or "").strip()
        decision = (row.get("decision") or "").strip()
        if record_id in decided:
            errors.append(f"duplicate decision for {record_id}")
        if decision not in DECISIONS:
            errors.append(f"{record_id or '(blank)'} decision must be core or not_read")
        decided[record_id] = decision
    missing = [item for item in library if item not in decided]
    extra = [item for item in decided if item not in set(library)]
    if missing:
        errors.append(f"decisions missing records: {', '.join(missing)}")
    if extra:
        errors.append(f"decisions name records that are not in the library: {', '.join(extra)}")
    core_ids = {item for item, decision in decided.items() if decision == "core"}
    logged = {item for item, decision in decided.items() if decision == "not_read"}
    if not core_ids:
        errors.append("the confirmed core is empty")
    if set(included_ids) != core_ids:
        errors.append("included.tsv must list the confirmed core and nothing else")
    if set(not_read_ids) != logged:
        errors.append("not_read.tsv must list every record the user left out of the core")
    if BANNER not in flow_text:
        errors.append(f"flow file must say '{BANNER}'")
    if NOT_READ_PHRASE not in flow_text:
        errors.append(f"flow file must say records were '{NOT_READ_PHRASE}'")
    if screening_rows is not None:
        errors.extend(check_screening_table(screening_rows, core_ids, logged))
    return errors


def _write_rank(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("record_id", "overlap_score", "rank"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if "--max-core" in raw:
        print("ERROR fixed caps are not allowed", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    rank_parser = subparsers.add_parser("rank", help="write a suggestion rank for every record")
    rank_parser.add_argument("--library", required=True, type=Path)
    rank_parser.add_argument("--question", required=True)
    rank_parser.add_argument("--out", required=True, type=Path)

    check_parser = subparsers.add_parser("check", help="check a user-confirmed narrative core")
    check_parser.add_argument("--library", required=True, type=Path)
    check_parser.add_argument("--decisions", required=True, type=Path)
    check_parser.add_argument("--included", required=True, type=Path)
    check_parser.add_argument("--not-read", required=True, type=Path)
    check_parser.add_argument("--flow", required=True, type=Path)
    check_parser.add_argument("--screening", required=True, type=Path)
    check_parser.add_argument("--review-type", required=True)

    args = parser.parse_args(raw)
    try:
        library_rows = _read_csv(args.library)
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    if args.command == "rank":
        _write_rank(args.out, rank_records(library_rows, args.question))
        print("OK narrative rank")
        return 0
    try:
        decisions = _read_csv(args.decisions)
        included = _read_csv(args.included)
        not_read = _read_csv(args.not_read)
        screening = _read_csv(args.screening)
        flow_text = args.flow.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    errors = check_core(
        _ids(library_rows),
        decisions,
        _ids(included),
        _ids(not_read),
        flow_text,
        args.review_type,
        screening,
    )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK narrative core")
    return 0


if __name__ == "__main__":
    sys.exit(main())
