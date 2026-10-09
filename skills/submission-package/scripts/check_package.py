#!/usr/bin/env python3
"""Check the submission package under 13-submission/."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

ROLES = {
    "Conceptualization",
    "Data curation",
    "Formal analysis",
    "Funding acquisition",
    "Investigation",
    "Methodology",
    "Project administration",
    "Resources",
    "Software",
    "Supervision",
    "Validation",
    "Visualization",
    "Writing \u2013 original draft",
    "Writing \u2013 review & editing",
}
NO_FUNDING = "No specific funding was received for this review."
NO_AI = (
    "No AI-assisted technology was used to draft, edit, or create figures "
    "for this manuscript. No AI system is an author."
)
NO_COI = "The authors declare no competing interests."
PLACEHOLDER_RE = re.compile(
    r"\[(?:VERIFY|JOURNAL|TITLE|NEEDS SOURCE|DATE|EDITOR|AUTHOR|"
    r"INSTITUTION|EMAIL|TOPIC|TOOL|ORCID)\]|\bTODO\b|\bTBD\b"
)
CHECKLIST_BITS = (
    "Manuscript",
    "Cover letter",
    "Title page",
    "Declarations",
    "Figure files",
    "Permissions",
    "Line numbers",
)
FILES = {
    "cover_letter": "cover_letter.md",
    "title_page": "title_page.md",
    "declarations": "declarations.md",
    "suggested_reviewers": "suggested_reviewers.md",
    "checklist": "file_checklist.md",
}


def normalize_role(role: str) -> str:
    cleaned = re.sub(r"\s+", " ", role.strip())
    cleaned = cleaned.replace(" - ", " \u2013 ")
    if cleaned == "Writing \u2013 review and editing":
        return "Writing \u2013 review & editing"
    return cleaned


def orcid_ok(value: str) -> bool:
    """ISO 7064 mod 11-2 check digit used by ORCID."""
    if not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", value):
        return False
    digits = value.replace("-", "")
    total = 0
    for character in digits[:-1]:
        total = (total + int(character)) * 2
    remainder = total % 11
    check = (12 - remainder) % 11
    expected = "X" if check == 10 else str(check)
    return digits[-1] == expected


def section(text: str, heading: str) -> Optional[str]:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    if match is None:
        return None
    rest = text[match.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    body = rest[: nxt.start()] if nxt else rest
    return body.strip()


def _words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?", text))


def _bad_email(email: str) -> bool:
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return True
    host = email.split("@", 1)[1].lower()
    return host in {"example.com", "example.org", "test.com", "localhost"} or host.endswith(
        ".example"
    )


def _authors(title_page: str) -> List[str]:
    match = re.search(r"^-\s+Authors:\s*(.+)$", title_page, re.M)
    if match is None:
        return []
    return [part.strip() for part in match.group(1).split(";") if part.strip()]


def _line(text: str, label: str) -> Optional[str]:
    match = re.search(rf"^-\s+{re.escape(label)}:\s*(.+)$", text, re.M)
    if match is None:
        return None
    return match.group(1).strip()


def check_package(
    parts: Dict[str, str],
    ready: bool = True,
    shortlist_text: str = "",
) -> List[str]:
    """Check submission texts. ready=True is the final-submit check."""
    errors: List[str] = []
    for key in FILES:
        if key not in parts:
            errors.append(f"missing {key}")
    if errors:
        return errors
    cover = parts["cover_letter"]
    title = parts["title_page"]
    declarations = parts["declarations"]
    reviewers = parts["suggested_reviewers"]
    checklist = parts["checklist"]
    blob = "\n".join(parts.values())

    if not cover.startswith("Dear "):
        errors.append("cover letter must start with 'Dear '")
    if "not under consideration elsewhere" not in cover:
        errors.append(
            "cover letter must say the manuscript is not under consideration elsewhere"
        )
    if _words(cover) > 500 and ready:
        errors.append("cover letter is over 500 words")

    authors = _authors(title)
    if not authors:
        errors.append("title page needs '- Authors:'")
    corresponding = _line(title, "Corresponding author")
    if corresponding is None:
        errors.append("title page needs '- Corresponding author:'")
    elif corresponding not in authors:
        errors.append("corresponding author is not in the author list")
    if _line(title, "Affiliations") is None:
        errors.append("title page needs '- Affiliations:'")
    article = _line(title, "Article type")
    if article is None or "Review" not in article:
        errors.append("title page article type must contain 'Review'")
    for label in ("Title", "Running title", "Word count", "Email"):
        if _line(title, label) is None:
            errors.append(f"title page needs '- {label}:'")
    word_count = _line(title, "Word count")
    if word_count is not None and not word_count.isdigit():
        errors.append("title page word count must be an integer")
    email = _line(title, "Email")
    if email and _bad_email(email):
        errors.append("title page email is missing or uses an example host")
    for orcid in re.findall(r"ORCID:\s*(\S+)", title):
        if not orcid_ok(orcid):
            errors.append(f"ORCID failed the checksum: {orcid}")

    cover_title = re.search(r"^Title:\s*(.+)$", cover, re.M)
    page_title = _line(title, "Title")
    if ready:
        if cover_title is None or page_title is None or cover_title.group(1).strip() != page_title:
            errors.append("cover letter Title does not match the title page")
        cover_email = re.search(r"^Email:\s*(\S+)\s*$", cover, re.M)
        if cover_email is None or (email and cover_email.group(1) != email):
            errors.append("cover letter email does not match the title page")

    for heading in (
        "Funding",
        "Competing interests",
        "Data availability",
        "Artificial intelligence",
        "Author contributions",
        "Authorship criteria",
    ):
        if section(declarations, heading) is None:
            errors.append(f"declarations missing ## {heading}")
    funding = section(declarations, "Funding") or ""
    if ready and NO_FUNDING not in funding and not (
        re.search(r"\d", funding)
        and re.search(r"grant|award|funder|funded", funding, re.I)
    ):
        errors.append("funding must be the no-funding sentence or a numbered grant")
    interests = section(declarations, "Competing interests") or ""
    if NO_COI not in interests and (
        "competing interest" not in interests.lower() or len(interests) < 40
    ):
        errors.append(
            "competing interests need the no-conflict sentence or a real disclosure"
        )
    data = section(declarations, "Data availability") or ""
    if ready and "evidence table" not in data.lower():
        errors.append("data availability must mention the evidence table")
    ai_text = section(declarations, "Artificial intelligence") or ""
    if NO_AI not in ai_text and not (
        "not an author" in ai_text.lower() and "full responsibility" in ai_text.lower()
    ):
        errors.append(
            "AI section must use the no-AI sentence or disclose the tool and responsibility"
        )
    criteria = section(declarations, "Authorship criteria") or ""
    if "four ICMJE" not in criteria or "not authors" not in criteria.lower():
        errors.append(
            "authorship criteria must name the four ICMJE criteria and exclude AI authors"
        )

    contrib = section(declarations, "Author contributions") or ""
    names = []
    for line in contrib.splitlines():
        match = re.match(r"^-\s+(.+?):\s+(.+)$", line.strip())
        if not match:
            continue
        names.append(match.group(1).strip())
        for raw_role in match.group(2).split(";"):
            role_body = raw_role.strip()
            degree = re.match(r"^(.+?)\s*\((lead|equal|supporting)\)$", role_body)
            role_name = degree.group(1) if degree else role_body
            if normalize_role(role_name) not in ROLES:
                errors.append(f"not a CRediT role: {role_name}")
    if authors and names != authors:
        errors.append(
            "author-contribution names must match the title-page authors, in order"
        )

    errors.extend(_reviewers(reviewers, title, ready))
    for bit in CHECKLIST_BITS:
        if bit not in checklist:
            errors.append(f"checklist missing {bit}")
    if "## Upload order" not in checklist:
        errors.append("checklist missing ## Upload order")
    if re.search(r"^Highlights:\s*(required|not required)\s*$", checklist, re.M) is None:
        errors.append("checklist needs 'Highlights: required' or 'Highlights: not required'")
    if shortlist_text and re.search(r"^Double-anonymized:\s*yes\s*$", shortlist_text, re.M):
        if "Manuscript contains no author names" not in checklist:
            errors.append(
                "checklist must say the manuscript contains no author names"
            )
    if ready:
        if PLACEHOLDER_RE.search(blob):
            errors.append("package still contains a placeholder")
        if re.search(r"- \[ \]", checklist):
            errors.append("checklist has an unchecked box")
    return errors


def _reviewers(text: str, title_page: str, ready: bool) -> List[str]:
    errors: List[str] = []
    rule = re.search(r"^Rule source:\s*(.+)\s*$", text, re.M)
    if rule is None:
        errors.append("reviewers file needs 'Rule source:'")
    elif rule.group(1).strip() != "project default" and not re.fullmatch(
        r"verified on \d{4}-\d{2}-\d{2} at https://\S+", rule.group(1).strip()
    ):
        errors.append("Rule source must be 'project default' or a verified-on line")
    required = re.search(r"^Required count:\s*(\d+)\s*$", text, re.M)
    blocks = re.split(r"^## Reviewer (\d+)\s*$", text, flags=re.M)
    found = []
    if len(blocks) > 1:
        for index in range(1, len(blocks), 2):
            found.append((int(blocks[index]), blocks[index + 1]))
    numbers = [number for number, _body in found]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"reviewer headings must be 1..N, got {numbers}")
    expected = int(required.group(1)) if required else None
    if expected is None and not 3 <= len(found) <= 5:
        errors.append(f"suggest 3 to 5 reviewers, found {len(found)}")
    if expected is not None and len(found) != expected:
        errors.append(f"Required count is {expected}, found {len(found)}")
    affiliations = (_line(title_page, "Affiliations") or "").casefold()
    emails = []
    for number, body in found:
        fields = {}
        for line in body.splitlines():
            match = re.match(r"^-\s+([^:]+):\s*(.*)$", line.strip())
            if match:
                fields[match.group(1).strip()] = match.group(2).strip()
        prefix = f"Reviewer {number}"
        for label in ("Name", "Institution", "Email", "Reason", "Conflict check"):
            if not fields.get(label):
                errors.append(f"{prefix} missing {label}")
        if fields.get("Conflict check") != "clear":
            errors.append(f"{prefix} conflict check must be clear")
        institution = fields.get("Institution", "")
        if institution.isupper() and len(institution) <= 8:
            errors.append(f"{prefix} use the full institution name, not an acronym")
        if len(institution) >= 8 and institution.casefold() in affiliations:
            errors.append(f"{prefix} institution matches an author affiliation")
        email = fields.get("Email", "")
        if email:
            emails.append(email)
            if _bad_email(email):
                errors.append(f"{prefix} email is not usable")
        reason = fields.get("Reason", "")
        if reason and len(reason) < 30:
            errors.append(f"{prefix} reason is too short")
    if len(emails) != len(set(emails)):
        errors.append("duplicate reviewer emails")
    if not ready:
        return errors
    return errors


def load_parts(directory: Path) -> Dict[str, str]:
    parts = {}
    for key, name in FILES.items():
        path = directory / name
        if path.is_file():
            parts[key] = path.read_text(encoding="utf-8")
    return parts


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--shortlist", type=Path)
    args = parser.parse_args(argv)
    shortlist = ""
    if args.shortlist:
        shortlist = args.shortlist.read_text(encoding="utf-8")
    errors = check_package(
        load_parts(args.directory),
        ready=not args.draft,
        shortlist_text=shortlist,
    )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK submission package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
