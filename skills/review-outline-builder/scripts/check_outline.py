#!/usr/bin/env python3
"""Validate a review outline: claims, evidence IDs, and word budget."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set

TARGET_RE = re.compile(r"^-\s+Target words:\s*(\d+)\s*$", re.M)
STATUS_RE = re.compile(r"^-\s+Status:\s*(draft|locked)\s*$", re.M)
TYPE_RE = re.compile(
    r"^-\s+Review type:\s*(narrative|systematic|scoping|umbrella)\s*$", re.M
)
DATE_RE = re.compile(r"^-\s+Date:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)
SECTION_RE = re.compile(r"^## S(\d+)\.\s+(.+?)\s*$", re.M)
BULLET_RE = re.compile(
    r"^-\s+(Claim|Evidence IDs|Word budget|Figures/tables):\s*(.*)$"
)
EVIDENCE_RE = re.compile(r"\bE\d{3,}\b")
GLOBAL_RE = re.compile(
    r"^## Global claim\s*\n+(.+?)(?=\n## |\Z)", re.M | re.S
)
ID_COLUMNS = ("evidence_id", "id")
STRUCTURAL_PREFIXES = (
    "acknowledgements",
    "acknowledgments",
    "funding",
    "author contributions",
)
METHODS_TYPES = {"systematic", "scoping", "umbrella"}
PRISMA_2020 = "https://www.prisma-statement.org/prisma-2020"
VERIFIED_LINE = r"verified on \d{4}-\d{2}-\d{2} at https://\S+"


def load_evidence_ids(path: Path) -> Set[str]:
    """Read evidence IDs from a CSV that uses evidence_id or id."""
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


def _section_blocks(text: str) -> List[dict]:
    matches = list(SECTION_RE.finditer(text))
    blocks = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        fields = {}
        for line in text[start:end].splitlines():
            bullet = BULLET_RE.match(line.strip())
            if bullet:
                fields[bullet.group(1)] = bullet.group(2).strip()
        blocks.append(
            {
                "number": int(match.group(1)),
                "title": match.group(2).strip(),
                "fields": fields,
            }
        )
    return blocks


def _first_section(sections: Sequence[dict], needle: str) -> Optional[dict]:
    return next((section for section in sections if needle in section["title"].casefold()), None)


def _pooled_titles(sections: Sequence[dict]) -> List[str]:
    hits = []
    for section in sections:
        title = section["title"].casefold()
        if "pooled" in title or "meta-analysis" in title or "meta analysis" in title:
            hits.append(section["title"])
    return hits


def check_systematic_checklist(text: str, sections: Sequence[dict], outline_text: str) -> List[str]:
    """Registration reminder and bias-tool checklist. Pooling stays off unless asked."""
    errors: List[str] = []
    if "## Protocol registration" not in text:
        errors.append("checklist needs ## Protocol registration")
    elif "registration" not in text.casefold() or PRISMA_2020 not in text:
        errors.append("protocol section must remind the user to report registration and cite PRISMA 2020")
    registry = re.search(r"(?m)^Registry ID:\s*(.+?)\s*$", text)
    registry_source = re.search(rf"(?m)^Registry source:\s*({VERIFIED_LINE})\s*$", text)
    if registry is None:
        errors.append("checklist needs 'Registry ID:'")
    elif registry.group(1) not in {"none yet", "[VERIFY]"} and registry_source is None:
        errors.append("a registry ID needs a Registry source line from the page you opened")
    if "## Bias tool" not in text:
        errors.append("checklist needs ## Bias tool")
    tool = re.search(r"(?m)^Tool:\s*(.+?)\s*$", text)
    official = re.search(r"(?m)^Official page:\s*(.+?)\s*$", text)
    if tool is None or official is None:
        errors.append("bias section needs 'Tool:' and 'Official page:'")
    elif tool.group(1) == "not chosen":
        if official.group(1) != "not opened":
            errors.append("an unchosen bias tool keeps 'Official page: not opened'")
    elif not re.fullmatch(VERIFIED_LINE, official.group(1)):
        errors.append("name a bias tool only with an Official page verified on the day you opened it")
    pooling = re.search(r"(?m)^Pooling:\s*(out of scope|in scope)\s*$", text)
    asked = re.search(r"(?m)^User asked:\s*(yes|no)\s*$", text)
    if pooling is None or asked is None:
        errors.append("checklist needs 'Pooling: out of scope' or 'in scope', and 'User asked: yes' or 'no'")
        return errors
    titles = _pooled_titles(sections)
    in_scope_line = bool(re.search(r"(?m)^- Pooled estimates: in scope\s*$", outline_text))
    if pooling.group(1) == "out of scope":
        if titles or in_scope_line:
            errors.append("pooled estimates stay out unless the checklist and the outline both say they are in scope")
        if re.search(r"pooled (estimate|effect|odds|mean)\s*[:=]\s*\d", text, re.I):
            errors.append("do not write a pooled number while pooling is out of scope")
    else:
        if asked.group(1) != "yes":
            errors.append("pooled estimates stay out unless the user asked")
        if not titles or not in_scope_line:
            errors.append("pooling is in scope but the outline does not say so in a section title and a scope line")
    return errors


def check_outline(
    text: str,
    evidence_ids: Optional[Set[str]] = None,
    require_locked: bool = False,
    checklist_text: Optional[str] = None,
    require_checklist: bool = False,
) -> List[str]:
    """Return a list of outline errors. An empty list means the outline passed."""
    errors: List[str] = []
    status = STATUS_RE.search(text)
    if status is None:
        errors.append("missing '- Status: draft' or '- Status: locked'")
    elif require_locked and status.group(1) != "locked":
        errors.append("status is not locked")

    review_type_match = TYPE_RE.search(text)
    if review_type_match is None:
        errors.append(
            "missing '- Review type:' (narrative, systematic, scoping, or umbrella)"
        )
        review_type = ""
    else:
        review_type = review_type_match.group(1)

    if DATE_RE.search(text) is None:
        errors.append("missing '- Date: YYYY-MM-DD'")

    target_match = TARGET_RE.search(text)
    if target_match is None:
        errors.append("missing '- Target words: <integer>'")
        target = None
    else:
        target = int(target_match.group(1))
        if target <= 0:
            errors.append("target words must be positive")

    global_match = GLOBAL_RE.search(text)
    if global_match is None:
        errors.append("missing '## Global claim' paragraph")
    else:
        claim = " ".join(global_match.group(1).split())
        if len(claim) < 20 or not claim.endswith("."):
            errors.append("global claim must be a sentence of at least 20 characters")

    sections = _section_blocks(text)
    if not sections:
        errors.append("no '## S<n>. <title>' sections")
        return errors

    numbers = [section["number"] for section in sections]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"section numbers must be 1..N in order, got {numbers}")

    titles = [section["title"] for section in sections]
    folded = [title.casefold() for title in titles]
    if len(set(folded)) != len(folded):
        errors.append("duplicate section titles")
    if not any("introduction" in title for title in folded):
        errors.append("missing a section whose title contains 'Introduction'")
    if not any("conclusion" in title for title in folded):
        errors.append("missing a section whose title contains 'Conclusion'")
    limitations = _first_section(sections, "limitation")
    next_questions = _first_section(sections, "next question")
    conclusion = _first_section(sections, "conclusion")
    if limitations is None:
        errors.append("missing a section whose title contains 'Limitation'")
    if next_questions is None:
        errors.append("missing a section whose title contains 'Next question'")
    if limitations and next_questions and limitations["number"] == next_questions["number"]:
        errors.append("limitations and next questions must be different sections")
    if conclusion and limitations and conclusion["number"] == limitations["number"]:
        errors.append("limitations must not be folded into the conclusion")
    if conclusion and next_questions and conclusion["number"] == next_questions["number"]:
        errors.append("next questions must not be folded into the conclusion")
    pooled = _pooled_titles(sections)
    pooling_line = bool(re.search(r"(?m)^- Pooled estimates: in scope\s*$", text))
    if pooled and not pooling_line:
        errors.append(
            "pooled estimates stay out of the outline unless it says '- Pooled estimates: in scope'"
        )
    if pooling_line and not pooled:
        errors.append("pooling is marked in scope but no section title says so")
    if review_type in METHODS_TYPES and not any("method" in title for title in folded):
        errors.append("this review type needs a section title containing 'Method'")
    if review_type == "systematic":
        if checklist_text is None:
            if require_checklist:
                errors.append("systematic reviews need 07-outline/systematic_methods_checklist.md")
        else:
            errors.extend(check_systematic_checklist(checklist_text, sections, text))
    elif checklist_text is not None:
        errors.append("the methods checklist is only for a systematic review")

    total = 0
    budgets_complete = True
    for section in sections:
        label = f"S{section['number']}"
        fields = section["fields"]
        for key in ("Claim", "Evidence IDs", "Word budget", "Figures/tables"):
            if key not in fields or fields[key] == "":
                errors.append(f"{label} missing '- {key}:'")
        claim = fields.get("Claim", "")
        if claim and (len(claim) < 12 or not claim.endswith(".")):
            errors.append(f"{label} claim must be a sentence ending with a period")
        budget_raw = fields.get("Word budget", "")
        if budget_raw:
            if not budget_raw.isdigit():
                errors.append(f"{label} word budget is not an integer")
                budgets_complete = False
            else:
                total += int(budget_raw)
        else:
            budgets_complete = False
        evidence_field = fields.get("Evidence IDs", "")
        structural = section["title"].casefold().startswith(STRUCTURAL_PREFIXES)
        if not evidence_field:
            continue
        if evidence_field == "none":
            if not structural:
                errors.append(
                    f"{label} uses 'Evidence IDs: none' but is not a structural section"
                )
            continue
        found = EVIDENCE_RE.findall(evidence_field)
        if not found:
            errors.append(f"{label} evidence IDs must look like E001")
        elif evidence_ids is not None:
            unknown = [item for item in found if item not in evidence_ids]
            if unknown:
                errors.append(
                    f"{label} unknown evidence IDs: {', '.join(unknown)}"
                )

    if target is not None and target > 0 and budgets_complete and total != target:
        errors.append(f"word budgets sum to {total}, target is {target}")
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outline", type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument(
        "--locked",
        action="store_true",
        help="require '- Status: locked'",
    )
    parser.add_argument("--checklist", type=Path)
    args = parser.parse_args(argv)
    try:
        evidence_ids = load_evidence_ids(args.evidence)
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    text = args.outline.read_text(encoding="utf-8")
    review_type_match = TYPE_RE.search(text)
    review_type = review_type_match.group(1) if review_type_match else ""
    checklist_text = None
    if args.checklist:
        checklist_text = args.checklist.read_text(encoding="utf-8")
    errors = check_outline(
        text,
        evidence_ids,
        require_locked=args.locked,
        checklist_text=checklist_text,
        require_checklist=review_type == "systematic",
    )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK outline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
