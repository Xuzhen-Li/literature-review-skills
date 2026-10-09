#!/usr/bin/env python3
"""Check that every revision claim has a location and exists in the file."""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

HEADING_RE = re.compile(r"^## ((?:R\d+\.\d+)|(?:E\.\d+))\s*$", re.M)
LOCATION_RE = re.compile(r"^(\S+\.(?:md|txt)) lines (\d+)-(\d+)$")
PAGE_RE = re.compile(r"\b(?:p\.|page)\s+\d+,\s+lines\s+\d+\s*-\s*\d+", re.I)
REVISION_VERBS = re.compile(
    r"\b(?:we have revised|we have added|we have changed|we have deleted|"
    r"we have clarified|we revised|we added|we changed|we deleted|we clarified|"
    r"has been revised|has been added|has been changed|have been revised|"
    r"have been added)\b",
    re.I,
)
COLUMNS = ("comment_id", "action", "location", "change_quote", "response")
ACTIONS = {"revised", "declined", "clarified"}
INTERNAL_PATHS = ("10-polish/", "09-draft/", "14-revision/", "07-outline/")


def norm(text: str) -> str:
    text = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return re.sub(r"\s+", " ", text).strip()


def _strip_quote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _ids_in_order(text: str) -> List[str]:
    return HEADING_RE.findall(text)


def _sequential(ids: Sequence[str]) -> List[str]:
    errors: List[str] = []
    if not ids:
        return ["no reviewer comments"]
    groups: Dict[str, List[int]] = {}
    order: List[str] = []
    for ident in ids:
        if ident.startswith("E."):
            key = "E"
            number = int(ident.split(".")[1])
        else:
            key, number_text = ident.split(".")
            number = int(number_text)
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(number)
    if "E" in groups and order[0] != "E":
        errors.append("editor comments must come before reviewer comments")
    reviewer_keys = [key for key in order if key.startswith("R")]
    reviewer_numbers = [int(key[1:]) for key in reviewer_keys]
    if reviewer_numbers != list(range(1, len(reviewer_numbers) + 1)):
        errors.append(f"reviewer numbers must run R1, R2, ... got {reviewer_keys}")
    for key, numbers in groups.items():
        if numbers != list(range(1, len(numbers) + 1)):
            errors.append(f"{key} comments must be 1..N without gaps, got {numbers}")
    return errors


def _plan_actions(plan_text: str) -> Dict[str, str]:
    actions: Dict[str, str] = {}
    parts = re.split(r"^## ((?:R\d+\.\d+)|(?:E\.\d+))\s*$", plan_text, flags=re.M)
    for index in range(1, len(parts), 2):
        ident = parts[index]
        body = parts[index + 1]
        match = re.search(r"^-\s+Action:\s*(\S+)\s*$", body, re.M)
        if match:
            actions[ident] = match.group(1).strip()
    return actions


def _letter_sections(letter: str) -> Dict[str, str]:
    parts = re.split(r"^## ((?:R\d+\.\d+)|(?:E\.\d+))\s*$", letter, flags=re.M)
    return {parts[index]: parts[index + 1] for index in range(1, len(parts), 2)}


def _quote_in_range(manuscript: str, start: int, end: int, quote: str) -> bool:
    lines = manuscript.splitlines()
    if start < 1 or end < start or end > len(lines):
        return False
    chunk = "\n".join(lines[start - 1 : end])
    return norm(quote) in norm(chunk)


def check_response(
    table_text: str,
    letter_text: str,
    files: Dict[str, str],
    plan_text: str,
) -> List[str]:
    """Return errors. An empty list means the response is safe to export."""
    errors: List[str] = []
    reader = csv.DictReader(io.StringIO(table_text))
    if reader.fieldnames:
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
    missing = [column for column in COLUMNS if column not in (reader.fieldnames or [])]
    if missing:
        return [f"response table missing columns: {', '.join(missing)}"]
    rows = []
    for raw in reader:
        rows.append({key: (raw.get(key) or "").strip() for key in COLUMNS})
    if not rows:
        return ["response table has no rows"]
    ids = [row["comment_id"] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate comment ids")
    errors.extend(_sequential(ids))
    if _ids_in_order(letter_text) != ids:
        errors.append("letter headings do not match the response table order")
    for path_bit in INTERNAL_PATHS:
        if path_bit in letter_text:
            errors.append(f"letter contains an internal path ({path_bit})")
            break
    plan = _plan_actions(plan_text)
    if list(plan.keys()) != ids:
        errors.append("action plan headings do not match the response table")
    sections = _letter_sections(letter_text)

    for row in rows:
        ident = row["comment_id"]
        prefix = ident or "(blank)"
        action = row["action"]
        response = row["response"]
        if action not in ACTIONS:
            errors.append(f"{prefix} action must be revised, declined, or clarified")
            continue
        if ident in plan and plan[ident] != action:
            errors.append(f"{prefix} action does not match the plan")
        if ident not in sections or norm(response) not in norm(sections.get(ident, "")):
            errors.append(f"{prefix} response text is not in the letter section")
        claims_revision = REVISION_VERBS.search(response) is not None
        if action == "declined":
            if row["location"] != "none" or row["change_quote"] != "none":
                errors.append(f"{prefix} a declined comment uses location none and quote none")
            if claims_revision:
                errors.append(f"{prefix} a declined comment must not say the text was revised")
            if len(response) < 40:
                errors.append(f"{prefix} declined response needs a reason")
            continue
        if action == "clarified" and not claims_revision:
            if row["location"] != "none" or row["change_quote"] != "none":
                errors.append(f"{prefix} a clarification without an edit uses none")
            continue
        if not claims_revision:
            errors.append(f"{prefix} a revision must use a phrase such as 'we have revised'")
        if PAGE_RE.search(response) is None:
            errors.append(f"{prefix} response must cite p. N, lines N-N")
        for path_bit in INTERNAL_PATHS:
            if path_bit in response:
                errors.append(f"{prefix} response must not contain an internal path")
                break
        location = LOCATION_RE.fullmatch(row["location"])
        if location is None:
            errors.append(f"{prefix} location must be '<file>.md lines N-M'")
            continue
        quote = _strip_quote(row["change_quote"])
        if quote in {"", "none"} or len(quote) < 12:
            errors.append(f"{prefix} change quote must be the new text")
            continue
        relative = location.group(1)
        if ".." in Path(relative).parts:
            errors.append(f"{prefix} location escapes the project")
            continue
        manuscript = files.get(relative)
        if manuscript is None:
            errors.append(f"{prefix} manuscript file is missing: {relative}")
            continue
        start, end = int(location.group(2)), int(location.group(3))
        if not _quote_in_range(manuscript, start, end, quote):
            errors.append(f"{prefix} change quote is not in the cited lines")
    return errors


def _read_files(root: Path, table_text: str) -> Dict[str, str]:
    files: Dict[str, str] = {}
    reader = csv.DictReader(io.StringIO(table_text))
    root_resolved = root.resolve()
    for raw in reader:
        location = (raw.get("location") or "").strip()
        match = LOCATION_RE.fullmatch(location)
        if match is None:
            continue
        relative = match.group(1)
        path = (root_resolved / relative).resolve()
        if root_resolved not in path.parents and path != root_resolved:
            continue
        if path.is_file():
            files[relative] = path.read_text(encoding="utf-8")
    return files


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", required=True, type=Path)
    parser.add_argument("--letter", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args(argv)
    table_text = args.table.read_text(encoding="utf-8")
    errors = check_response(
        table_text,
        args.letter.read_text(encoding="utf-8"),
        _read_files(args.root, table_text),
        args.plan.read_text(encoding="utf-8"),
    )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK response")
    return 0


if __name__ == "__main__":
    sys.exit(main())
