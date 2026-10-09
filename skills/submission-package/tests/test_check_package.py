"""Tests for the submission package checker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_package import check_package, orcid_ok  # noqa: E402
from export_cover_letter import docx_bytes, docx_plain_text, main as export_main  # noqa: E402

NO_AI = (
    "No AI-assisted technology was used to draft, edit, or create figures "
    "for this manuscript. No AI system is an author."
)


def _parts():
    cover = """Dear Editor,

Title: Signals that sort a review
Article type: Review

Please consider this review. The manuscript is not under consideration elsewhere.

Corresponding author: Author One
Email: author.one@northlab.edu
"""
    title = """- Title: Signals that sort a review
- Article type: Review
- Authors: Author One; Author Two
- Corresponding author: Author One
- Affiliations: North Lab; South Lab
- Running title: Signals
- Word count: 6000
- Email: author.one@northlab.edu
"""
    declarations = f"""## Funding

No specific funding was received for this review.

## Competing interests

The authors declare no competing interests.

## Data availability

The evidence table and search strings are the data for this review.

## Artificial intelligence

{NO_AI}

## Author contributions

- Author One: Conceptualization; Writing - original draft (lead)
- Author Two: Writing - review & editing

## Authorship criteria

Each listed author meets all four ICMJE authorship criteria. AI tools are not authors.
"""
    reviewers = """Rule source: project default

## Reviewer 1
- Name: Reviewer Alpha
- Institution: East Observatory
- Email: reviewer.alpha@east-observatory.edu
- Reason: Works on the comparison in outline section S2 and is not a coauthor in the evidence table.
- Conflict check: clear

## Reviewer 2
- Name: Reviewer Beta
- Institution: West Station
- Email: reviewer.beta@west-station.edu
- Reason: Works on the comparison in outline section S3 and is not a coauthor in the evidence table.
- Conflict check: clear

## Reviewer 3
- Name: Reviewer Gamma
- Institution: Central Archive
- Email: reviewer.gamma@central-archive.edu
- Reason: Works on the comparison in outline section S4 and is not a coauthor in the evidence table.
- Conflict check: clear
"""
    checklist = """- [x] Manuscript
- [x] Cover letter
- [x] Title page
- [x] Declarations
- [x] Figure files
- [x] Permissions
- [x] Line numbers

Highlights: not required
Visual abstract: not required

## Upload order

1. Cover letter
2. Manuscript
3. Figure files
"""
    field_guide = """# Portal field guide

Source: verified on 2026-10-09 at https://journal-a.test/for-authors

## Field: Title

- Quoted line: "Enter the full title of the manuscript."

## Field: Article type

- Quoted line: "Select Review."
"""
    return {
        "cover_letter": cover,
        "title_page": title,
        "declarations": declarations,
        "suggested_reviewers": reviewers,
        "checklist": checklist,
        "field_guide": field_guide,
    }


def test_ready_package_passes_and_orcid_checksum():
    letter = docx_bytes(_parts()["cover_letter"])
    assert "Signals that sort a review" in docx_plain_text(letter)
    assert check_package(_parts(), cover_docx=letter) == []
    assert orcid_ok("0000-0000-0000-0001")
    assert not orcid_ok("0000-0000-0000-0002")


def test_highlights_and_visual_abstract_use_only_polished_claims():
    parts = _parts()
    parts["checklist"] = parts["checklist"].replace("Highlights: not required", "Highlights: required")
    parts["checklist"] = parts["checklist"].replace(
        "Visual abstract: not required", "Visual abstract: required"
    )
    parts["highlights"] = (
        "- A claim that was never drafted (Smith, 2020; E999).\n"
        "- Another new claim (Smith, 2020; E999).\n"
        "- A third new claim (Smith, 2020; E999).\n"
    )
    manuscript = (
        "The core result is stable in two settings (Smith, 2020; E014). "
        "The limit is the sample (Lee, 2021; E015). "
        "A second setting is still open (Lee, 2021; E015)."
    )
    assert any(
        "highlight" in error
        for error in check_package(parts, ready=False, manuscript_text=manuscript)
    )
    parts["highlights"] = (
        "- The core result is stable in two settings (Smith, 2020; E014).\n"
        "- The limit is the sample (Lee, 2021; E015).\n"
        "- A second setting is still open (Lee, 2021; E015).\n"
    )
    parts["visual_abstract"] = (
        "- Message: The core result is stable in two settings\n"
        "- Evidence IDs: E014\n"
        "- Rights: original\n"
    )
    errors = check_package(parts, ready=False, manuscript_text=manuscript)
    assert not any("highlight" in error or "visual abstract" in error for error in errors)


def test_author_page_limit_and_visual_abstract_image(tmp_path):
    parts = _parts()
    manuscript = (
        "The core result is stable in two settings (Smith, 2020; E014). "
        "The limit is the sample (Lee, 2021; E015). "
        "A second setting is still open (Lee, 2021; E015)."
    )
    parts["checklist"] = parts["checklist"].replace("Highlights: not required", "Highlights: required")
    parts["checklist"] = parts["checklist"].replace(
        "Visual abstract: not required", "Visual abstract: required"
    )
    parts["checklist"] += "Highlights max characters: 35\n"
    parts["highlights"] = (
        "- The core result is stable in two settings (Smith, 2020; E014).\n"
        "- The limit is the sample (Lee, 2021; E015).\n"
        "- A second setting is still open (Lee, 2021; E015).\n"
    )
    parts["visual_abstract"] = (
        "- Message: The core result is stable in two settings\n"
        "- Evidence IDs: E014\n"
        "- Rights: original\n"
    )
    too_long = check_package(parts, ready=False, manuscript_text=manuscript)
    assert any("35 characters" in error for error in too_long)
    parts["highlights"] = (
        "- The limit is the sample (Lee, 2021; E015).\n"
        "- The core result is stable (Smith, 2020; E014).\n"
        "- A second setting is still open (Lee, 2021; E015).\n"
    )
    letter = docx_bytes(parts["cover_letter"])
    missing = check_package(
        parts, cover_docx=letter, manuscript_text=manuscript, package_dir=tmp_path
    )
    assert any("visual_abstract.svg" in error for error in missing)
    (tmp_path / "visual_abstract.svg").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="80">'
        '<text x="8" y="40">The core result is stable in two settings</text></svg>\n',
        encoding="utf-8",
    )
    (tmp_path / "visual_abstract.pdf").write_bytes(b"%PDF-1.4\n")
    ready = check_package(
        parts, cover_docx=letter, manuscript_text=manuscript, package_dir=tmp_path
    )
    assert ready == []


def test_cover_letter_export_writes_a_docx(tmp_path):
    source = tmp_path / "cover_letter.md"
    source.write_text(_parts()["cover_letter"], encoding="utf-8")
    output = tmp_path / "cover_letter.docx"
    assert export_main(["--markdown", str(source), "--output", str(output)]) == 0
    assert output.read_bytes().startswith(b"PK")


def test_blocks_bad_role_conflict_placeholder_and_blind_gap():
    parts = _parts()
    parts["declarations"] = parts["declarations"].replace(
        "Conceptualization", "Had the idea"
    )
    assert any("CRediT" in error for error in check_package(parts))
    parts = _parts()
    parts["suggested_reviewers"] = parts["suggested_reviewers"].replace(
        "East Observatory", "North Lab"
    )
    assert any("affiliation" in error for error in check_package(parts))
    parts = _parts()
    parts["cover_letter"] = parts["cover_letter"].replace(
        "Signals that sort a review", "[TITLE]"
    )
    assert check_package(parts, ready=False) == []
    assert any("placeholder" in error for error in check_package(parts, ready=True))
    blind = "Double-anonymized: yes\n"
    assert any("author names" in error for error in check_package(_parts(), shortlist_text=blind))
