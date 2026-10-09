#!/usr/bin/env python3
"""Check the submission package under 13-submission/."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from export_cover_letter import docx_plain_text

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
    "field_guide": "portal_field_guide.md",
}
EVIDENCE_RE = re.compile(r"\bE\d{3,}\b")
BLOCKED_GUIDE_HOSTS = (
    "letpub.com",
    "scimagojr.com",
    "wikipedia.org",
    "researchgate.net",
    "sci-hub",
    "libgen",
)


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


def check_field_guide(text: str) -> List[str]:
    """The field guide may quote only lines the agent read on the author page."""
    errors: List[str] = []
    source = re.search(r"(?m)^Source:\s*(verified on \d{4}-\d{2}-\d{2} at https://\S+)\s*$", text)
    if source is None:
        errors.append("field guide needs 'Source: verified on YYYY-MM-DD at https://...'")
    else:
        url = source.group(1).split(" at ", 1)[1]
        host = url.split("/")[2].lower() if url.startswith("https://") else ""
        if any(part in host for part in BLOCKED_GUIDE_HOSTS):
            errors.append("field guide source is not an author page")
    if re.search(r"(?i)\b(password|cookie|sign in|log in)\b", text):
        errors.append("field guide must not ask for a login, password, or cookie")
    fields = re.findall(r"(?m)^## Field:\s*(.+?)\s*$", text)
    if not fields:
        errors.append("field guide needs at least one '## Field:' section")
    quotes = re.findall(r'(?m)^- Quoted line:\s*"(.+)"\s*$', text)
    if len(quotes) < len(fields) or not quotes:
        errors.append("each field needs a Quoted line copied in double quotes")
    if any(not quote.strip() or "[" in quote for quote in quotes):
        errors.append("a quoted line must be the sentence you read, not a placeholder")
    return errors


def _flag(text: str, label: str) -> Optional[str]:
    match = re.search(rf"(?m)^{re.escape(label)}:\s*(required|not required)\s*$", text)
    if match is None:
        return None
    return match.group(1)


def _claim_text(bullet: str) -> str:
    text = re.sub(r"\([^)]*E\d{3,}[^)]*\)", "", bullet)
    text = EVIDENCE_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip(" -.;")


def _visual_image_errors(directory: Path, message: str = "") -> List[str]:
    """A required visual abstract is an original SVG plus PDF, not an embedded picture."""
    svg_path = directory / "visual_abstract.svg"
    pdf_path = directory / "visual_abstract.pdf"
    if not svg_path.is_file() or not pdf_path.is_file():
        return ["a required visual abstract needs visual_abstract.svg and visual_abstract.pdf"]
    errors: List[str] = []
    try:
        root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
    except (ET.ParseError, OSError, UnicodeError):
        return ["visual abstract SVG is not valid XML"]
    texts = [node.text or "" for node in root.iter() if node.tag.endswith("text")]
    tags = {node.tag.split("}")[-1] for node in root.iter()}
    blob = " ".join(texts)
    if not blob.strip():
        errors.append("visual abstract SVG must keep its wording in editable text")
    elif message and message.casefold() not in blob.casefold():
        errors.append("visual abstract SVG text must include the message from visual_abstract.md")
    if "image" in tags:
        errors.append("visual abstract SVG must not embed an image")
    try:
        if not pdf_path.read_bytes().startswith(b"%PDF"):
            errors.append("visual abstract PDF is missing")
    except OSError:
        errors.append("visual abstract PDF is missing")
    return errors


def _optional_piece(
    kind: str,
    body: Optional[str],
    manuscript: str,
    required: bool,
    count_bounds: Tuple[int, int] = (3, 5),
    max_chars: Optional[int] = None,
) -> List[str]:
    errors: List[str] = []
    if not required:
        if body is None or body.strip() == "Not required.":
            return errors
        errors.append(f"{kind} must be omitted or say 'Not required.' when the author page does not ask for it")
        return errors
    if body is None or body.strip() in {"", "Not required."}:
        errors.append(f"{kind} is required by the author page")
        return errors
    if not manuscript:
        errors.append(f"{kind} needs the polished manuscript text")
        return errors
    if kind == "highlights":
        bullets = [line.strip()[2:].strip() for line in body.splitlines() if line.strip().startswith("- ")]
        low, high = count_bounds
        if not low <= len(bullets) <= high:
            errors.append(f"highlights need {low} to {high} bullets, found {len(bullets)}")
        manuscript_ids = set(EVIDENCE_RE.findall(manuscript))
        folded = manuscript.casefold()
        for bullet in bullets:
            ids = set(EVIDENCE_RE.findall(bullet))
            claim = _claim_text(bullet)
            if not ids or not ids <= manuscript_ids or claim.casefold() not in folded:
                errors.append("each highlight must be a sentence already in the polished manuscript")
                break
            if max_chars is not None and len(claim) > max_chars:
                errors.append(
                    f"a highlight is longer than the author-page limit of {max_chars} characters"
                )
                break
    else:
        message = re.search(r"(?m)^-\s+Message:\s*(.+?)\s*$", body)
        ids = set(EVIDENCE_RE.findall(body))
        if message is None or message.group(1).casefold() not in manuscript.casefold():
            errors.append("visual abstract message must be copied from the polished manuscript")
        elif not ids or not ids <= set(EVIDENCE_RE.findall(manuscript)):
            errors.append("visual abstract evidence IDs must already be in the polished manuscript")
        if not re.search(r"(?m)^-\s+Rights:\s*original\s*$", body):
            errors.append("visual abstract rights must be original")
        if re.search(r"(?i)\bcrop\b|reproduced from", body):
            errors.append("visual abstract must not crop or reuse a published figure")
    return errors


def check_package(
    parts: Dict[str, str],
    ready: bool = True,
    shortlist_text: str = "",
    cover_docx: Optional[bytes] = None,
    manuscript_text: str = "",
    package_dir: Optional[Path] = None,
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
    if re.search(r"^Visual abstract:\s*(required|not required)\s*$", checklist, re.M) is None:
        errors.append("checklist needs 'Visual abstract: required' or 'Visual abstract: not required'")
    errors.extend(check_field_guide(parts["field_guide"]))
    highlights_flag = _flag(checklist, "Highlights")
    visual_flag = _flag(checklist, "Visual abstract")
    count_match = re.search(r"(?m)^Highlights count:\s*(\d+)(?:\s*-\s*(\d+))?\s*$", checklist)
    if count_match:
        left = int(count_match.group(1))
        right = int(count_match.group(2) or left)
        count_bounds = (min(left, right), max(left, right))
    else:
        count_bounds = (3, 5)
    max_match = re.search(r"(?m)^Highlights max characters:\s*(\d+)\s*$", checklist)
    max_chars = int(max_match.group(1)) if max_match else None
    if highlights_flag is not None:
        errors.extend(
            _optional_piece(
                "highlights",
                parts.get("highlights"),
                manuscript_text,
                highlights_flag == "required",
                count_bounds,
                max_chars,
            )
        )
    if visual_flag is not None:
        errors.extend(
            _optional_piece(
                "visual abstract",
                parts.get("visual_abstract"),
                manuscript_text,
                visual_flag == "required",
            )
        )
    if visual_flag == "required" and ready and package_dir is not None:
        message = ""
        visual_body = parts.get("visual_abstract") or ""
        found = re.search(r"(?m)^-\s+Message:\s*(.+?)\s*$", visual_body)
        if found:
            message = found.group(1).strip()
        errors.extend(_visual_image_errors(package_dir, message))
    if ready:
        if cover_docx is None:
            errors.append("cover letter docx is missing")
        else:
            extracted = docx_plain_text(cover_docx)
            if extracted is None:
                errors.append("cover letter docx is not a word-processor file")
            else:
                if page_title and page_title not in extracted:
                    errors.append("cover letter docx does not contain the title")
                if "not under consideration elsewhere" not in extracted:
                    errors.append("cover letter docx is missing the overlap sentence")
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
    parser.add_argument("--manuscript", type=Path)
    args = parser.parse_args(argv)
    shortlist = ""
    if args.shortlist:
        shortlist = args.shortlist.read_text(encoding="utf-8")
    cover_docx = None
    docx_path = args.directory / "cover_letter.docx"
    if docx_path.is_file():
        cover_docx = docx_path.read_bytes()
    manuscript_text = ""
    if args.manuscript:
        manuscript_text = args.manuscript.read_text(encoding="utf-8")
    errors = check_package(
        load_parts(args.directory),
        ready=not args.draft,
        shortlist_text=shortlist,
        cover_docx=cover_docx,
        manuscript_text=manuscript_text,
        package_dir=args.directory,
    )
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK submission package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
