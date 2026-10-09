"""Tests for the outline checker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_outline import check_outline, main  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "outline_template.md"
IDS = {"E001", "E002", "E003", "E004"}


def _outline(review_type="narrative", status="draft", budgets=(800, 1500, 1700, 800, 550, 650)):
    b1, b2, b3, b4, b5, b6 = budgets
    return f"""- Status: {status}
- Review type: {review_type}
- Target words: {sum(budgets)}
- Date: 2026-10-09

## Global claim

This review argues that the cited studies do not yet support one mechanism.

## S1. Introduction

- Claim: The question is narrower than the early reports suggested.
- Evidence IDs: E001, E002
- Word budget: {b1}
- Figures/tables: none

## S2. Shared findings

- Claim: Two independent lines of evidence agree on the direction of the effect.
- Evidence IDs: E002, E003
- Word budget: {b2}
- Figures/tables: Fig. 1

## S3. Points of disagreement

- Claim: The studies disagree on whether the effect is stable outside one setting.
- Evidence IDs: E003, E004
- Word budget: {b3}
- Figures/tables: Table 1

## S4. Limitations

- Claim: The evidence does not support a single mechanism outside the measured settings.
- Evidence IDs: E004
- Word budget: {b4}
- Figures/tables: none

## S5. Next questions

- Claim: The next question is whether the same direction appears in a second setting.
- Evidence IDs: E001
- Word budget: {b5}
- Figures/tables: none

## S6. Conclusions

- Claim: The practical implication is limited to the settings those studies actually measured.
- Evidence IDs: E004
- Word budget: {b6}
- Figures/tables: none
"""


def test_template_and_valid_outline_pass():
    assert check_outline(TEMPLATE.read_text(encoding="utf-8"), IDS) == []
    assert check_outline(_outline(), IDS) == []


def test_budget_must_sum_and_lock_is_explicit():
    broken = _outline().replace("- Word budget: 650", "- Word budget: 100")
    assert any("word budgets" in error for error in check_outline(broken, IDS))
    assert any("not locked" in error for error in check_outline(_outline(), IDS, True))
    assert check_outline(_outline(status="locked"), IDS, True) == []


def test_unknown_ids_methods_and_short_claim():
    text = _outline().replace("E004", "E999")
    assert any("E999" in error for error in check_outline(text, IDS))
    systematic = _outline(review_type="systematic")
    assert any("Method" in error for error in check_outline(systematic, IDS))
    short = _outline().replace(
        "- Claim: The question is narrower than the early reports suggested.",
        "- Claim: Too short",
    )
    assert any("S1 claim" in error for error in check_outline(short, IDS))


def _systematic_outline():
    narrative = _outline(review_type="systematic")
    narrative = narrative.replace("- Target words: 6000", "- Target words: 6400")
    narrative = narrative.replace(
        "## S2. Shared findings",
        """## S2. Methods

- Claim: The search and eligibility rules are the ones locked in the project files.
- Evidence IDs: E001
- Word budget: 400
- Figures/tables: none

## S3. Shared findings""",
    )
    narrative = narrative.replace("## S3. Points of disagreement", "## S4. Points of disagreement")
    narrative = narrative.replace("## S4. Limitations", "## S5. Limitations")
    narrative = narrative.replace("## S5. Next questions", "## S6. Next questions")
    narrative = narrative.replace("## S6. Conclusions", "## S7. Conclusions")
    return narrative


def test_required_closing_sections_and_systematic_checklist():
    dropped = _outline().replace("## S4. Limitations", "## S4. Caveats")
    assert any("Limitation" in error for error in check_outline(dropped, IDS))
    pooled = _outline().replace("## S3. Points of disagreement", "## S3. Pooled estimates")
    assert any("Pooled estimates" in error for error in check_outline(pooled, IDS))
    checklist = (TEMPLATE.parent / "systematic_methods_checklist.md").read_text(encoding="utf-8")
    systematic = _systematic_outline()
    assert any("Method" in error for error in check_outline(_outline(review_type="systematic"), IDS))
    assert check_outline(systematic, IDS, checklist_text=checklist, require_checklist=True) == []
    invented = checklist.replace("Registry ID: none yet", "Registry ID: CRD42025000001")
    assert any("Registry source" in error for error in check_outline(
        systematic, IDS, checklist_text=invented, require_checklist=True
    ))
    asked = checklist.replace("Pooling: out of scope", "Pooling: in scope").replace(
        "User asked: no", "User asked: yes"
    )
    without_section = check_outline(systematic, IDS, checklist_text=asked, require_checklist=True)
    assert any("pooling is in scope" in error for error in without_section)


def test_cli_exit_codes(tmp_path):
    outline = tmp_path / "outline.md"
    outline.write_text(_outline(), encoding="utf-8")
    evidence = tmp_path / "evidence.csv"
    evidence.write_text("evidence_id,note\nE001,a\nE002,b\nE003,c\nE004,d\n", encoding="utf-8")
    assert main([str(outline), "--evidence", str(evidence)]) == 0
    evidence.write_text("evidence_id,note\nE001,a\n", encoding="utf-8")
    assert main([str(outline), "--evidence", str(evidence)]) == 1
