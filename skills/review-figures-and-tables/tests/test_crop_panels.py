"""Ledger rules for cropping panels the user already holds."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from crop_panels import main, publication_ready, validate_rows, write_crops  # noqa: E402

HEADER = (
    "figure_id,panel_id,source_pdf,page,original_figure,crop_box,"
    "copyright_status,used_in\n"
)


def _pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4\n%fake\n")


def _row(pdf: Path, **overrides) -> dict:
    row = {
        "figure_id": "Fig. 2",
        "panel_id": "a",
        "source_pdf": str(pdf),
        "page": "1",
        "original_figure": "Figure 1",
        "crop_box": "10,20,110,80",
        "copyright_status": "cc-by",
        "used_in": "Fig. 2a",
    }
    row.update(overrides)
    return row


def test_empty_or_missing_ledger_writes_nothing(tmp_path):
    out = tmp_path / "crops"
    assert write_crops("", out) == ["panel crop ledger is empty"]
    assert not out.exists()
    missing = tmp_path / "missing.csv"
    assert main(["--ledger", str(missing), "--out", str(out)]) == 1
    assert not out.exists()


def test_duplicate_panel_and_remote_path_are_refused(tmp_path):
    pdf = tmp_path / "paper.pdf"
    _pdf(pdf)
    rows = [
        _row(pdf),
        _row(pdf, panel_id="b", used_in="Fig. 2b"),
    ]
    assert any("duplicates" in error for error in validate_rows(rows, lambda _path: None))
    remote = [_row(pdf, source_pdf="https://example.test/paper.pdf")]
    assert any("local file" in error for error in validate_rows(remote, lambda _path: None))


def test_needs_permission_is_not_a_publication_file(tmp_path):
    pdf = tmp_path / "paper.pdf"
    _pdf(pdf)
    ledger = HEADER + (
        f'Fig. 2,a,{pdf},1,Figure 1,"10,20,110,80",needs-permission,Fig. 2a\n'
    )
    out = tmp_path / "crops"

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("needs-permission must not be cropped for publication")

    assert write_crops(ledger, out, crop=fail_if_called) == []
    assert list(out.glob("*.pdf")) == []
    assert "needs-permission" in (out / "crop_blocked.tsv").read_text(encoding="utf-8")
    assert publication_ready([_row(pdf, copyright_status="needs-permission")]) is False
    assert publication_ready([_row(pdf)]) is True


def test_cleared_row_writes_only_after_validation(tmp_path):
    pdf = tmp_path / "paper.pdf"
    _pdf(pdf)
    ledger = HEADER + f'Fig. 2,a,{pdf},1,Figure 1,"10,20,110,80",cc-by,Fig. 2a\n'
    out = tmp_path / "crops"
    written = []

    def fake_crop(source, page, box, dest):
        written.append((Path(source).name, page, box))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"%PDF-cropped\n")

    assert write_crops(ledger, out, crop=fake_crop) == []
    assert written == [("paper.pdf", 1, (10.0, 20.0, 110.0, 80.0))]
    assert (out / "Fig.-2__a.pdf").is_file()
