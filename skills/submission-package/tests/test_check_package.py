"""Tests for the submission package checker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_package import check_package, orcid_ok  # noqa: E402

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

## Upload order

1. Cover letter
2. Manuscript
3. Figure files
"""
    return {
        "cover_letter": cover,
        "title_page": title,
        "declarations": declarations,
        "suggested_reviewers": reviewers,
        "checklist": checklist,
    }


def test_ready_package_passes_and_orcid_checksum():
    assert check_package(_parts()) == []
    assert orcid_ok("0000-0000-0000-0001")
    assert not orcid_ok("0000-0000-0000-0002")


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
