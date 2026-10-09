"""Tests for original figure files."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from draw_originals import build_svg, draw, main  # noqa: E402

PLAN = """## Fig. 1

- Message: The argument runs from the question to the gap.
- Type: original
- Evidence IDs: E001, E002
- Panels or columns: Question; Evidence; Gap
- Do not copy: none
- File: not drawn yet

## Table 1

- Message: Studies differ by design.
- Type: original
- Evidence IDs: E002
- Panels or columns: Study; Design; Finding
- Do not copy: Table 2 of a paper already read
- File: not drawn yet

## Fig. 2

- Message: A published plate the user may license later.
- Type: adapted
- Evidence IDs: E001
- Panels or columns: Source panel
- Do not copy: Fig. 3 of that paper
- File: not drawn yet
"""

LEDGER = """id,type,sources,license,permission_status,caption_credit
Fig. 1,original,none,original,not_required,Created for this review.
Table 1,original,none,original,not_required,Created for this review.
Fig. 2,adapted,E001 Fig. 3,unknown,needed,PENDING
"""


def test_svg_is_xml_and_fig1_is_an_argument_map():
    svg = build_svg(
        {
            "id": "Fig. 1",
            "message": "Question to gap.",
            "type": "original",
            "evidence_ids": ["E001", "E002"],
            "panels": ["Question", "Gap"],
            "do_not_copy": "none",
        }
    )
    root = ET.fromstring(svg)
    blob = ET.tostring(root, encoding="unicode")
    assert "argument map" in blob
    assert "E001" in blob and "E002" in blob
    assert "crop of a published figure" in blob


def test_draw_writes_originals_and_skips_adapted(tmp_path):
    errors = draw(PLAN, LEDGER, tmp_path)
    assert errors == []
    svg = (tmp_path / "fig-1.svg").read_text(encoding="utf-8")
    pdf = (tmp_path / "fig-1.pdf").read_bytes()
    assert "argument map" in svg
    assert pdf.startswith(b"%PDF")
    assert b"E001" in pdf and b"argument map" in pdf
    table = (tmp_path / "table-1.svg").read_text(encoding="utf-8")
    assert "E002" in table and "Column headings only" in table
    assert not (tmp_path / "fig-2.svg").exists()
    assert not (tmp_path / "fig-2.pdf").exists()
    assert main(["--plan", str(tmp_path / "missing.md"), "--ledger", str(tmp_path / "x.csv"), "--out", str(tmp_path)]) == 1


def test_svg_text_stays_editable_and_a_crop_request_writes_nothing(tmp_path):
    """Special characters stay in text nodes, long evidence IDs stay in the PDF, and crop writes nothing."""
    evidence_ids = [f"E{index:03d}" for index in range(1, 21)]
    plan = PLAN.replace(
        "- Message: The argument runs from the question to the gap.",
        "- Message: A & B < C, drawn as text.",
    ).replace("- Evidence IDs: E001, E002", "- Evidence IDs: " + ", ".join(evidence_ids))
    ledger = LEDGER.replace(
        "Fig. 1,original,none,original,not_required,Created for this review.",
        "Fig. 1,original," + " ".join(evidence_ids) + ",original,not_required,Created for this review.",
    )
    assert draw(plan, ledger, tmp_path) == []
    svg_path = tmp_path / "fig-1.svg"
    pdf = (tmp_path / "fig-1.pdf").read_bytes()
    root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
    texts = [
        node.text or ""
        for node in root.iter()
        if node.tag.endswith("text")
    ]
    assert any("A & B < C, drawn as text." in text for text in texts)
    assert all(not node.tag.endswith("image") for node in root.iter())
    assert all(not node.tag.endswith("path") for node in root.iter())
    assert pdf.startswith(b"%PDF")
    for evidence_id in evidence_ids:
        assert evidence_id.encode("ascii") in pdf

    warned = tmp_path / "warned"
    warned.mkdir()
    safe = plan.replace(
        "A & B < C, drawn as text.",
        "Original map. Do not crop a published figure.",
    )
    assert draw(safe, ledger, warned) == []
    assert (warned / "fig-1.svg").is_file()

    crop_dir = tmp_path / "crop"
    crop_dir.mkdir()
    sentinel = crop_dir / "keep.txt"
    sentinel.write_text("leave me\n", encoding="utf-8")
    cropping = plan.replace(
        "A & B < C, drawn as text.",
        "Cropping the published plate into this panel.",
    )
    errors = draw(cropping, ledger, crop_dir)
    assert any("refusing to crop" in error for error in errors)
    assert sentinel.read_text(encoding="utf-8") == "leave me\n"
    assert list(crop_dir.glob("*.svg")) == []
    assert list(crop_dir.glob("*.pdf")) == []


def test_crop_request_writes_nothing(tmp_path):
    cropped = PLAN.replace(
        "The argument runs from the question to the gap.",
        "Crop the published figure into a new plate.",
    )
    errors = draw(cropped, LEDGER, tmp_path)
    assert any("refusing to crop" in error for error in errors)
    assert list(tmp_path.glob("*.svg")) == []
