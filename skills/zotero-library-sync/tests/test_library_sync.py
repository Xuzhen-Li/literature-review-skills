"""Tests for the collection checklist and optional note export."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_collections import check_collections, main as collections_main  # noqa: E402
from export_notes import main as notes_main  # noqa: E402


def test_checklist_covers_included_records_and_waits_for_yes():
    rows = [
        {"theme": "aroma", "record_id": "R1", "user_confirmed": "yes"},
        {"theme": "aroma", "record_id": "R2", "user_confirmed": "no"},
    ]
    assert check_collections(rows, ["R1", "R2"], ready=False) == []
    assert any("not confirmed" in error for error in check_collections(rows, ["R1", "R2"], ready=True))
    assert any("missing" in error for error in check_collections(rows[:1], ["R1", "R2"]))
    assert any("not in included" in error for error in check_collections(rows, ["R1"]))
    too_many = [
        {"theme": f"theme-{index}", "record_id": "R1", "user_confirmed": "yes"}
        for index in range(9)
    ]
    assert any("at most" in error for error in check_collections(too_many, ["R1"]))


def test_collection_cli(tmp_path):
    included = tmp_path / "included.tsv"
    included.write_text("record_id\tdoi\nR1\t10.1/example\n", encoding="utf-8")
    checklist = tmp_path / "collection_checklist.tsv"
    checklist.write_text("theme\trecord_id\tuser_confirmed\naroma\tR1\tyes\n", encoding="utf-8")
    assert collections_main(["--checklist", str(checklist), "--included", str(included), "--ready"]) == 0


def test_note_export_requires_a_user_ask_and_logs_attachments(tmp_path):
    reading = tmp_path / "reading"
    reading.mkdir()
    note = reading / "Lovelace2020.md"
    note.write_text("# Lovelace2020\n\nrecord_id: R1\n\n## Aim\n\nA finding.\n", encoding="utf-8")
    out = tmp_path / "export"
    log = tmp_path / "note_attachment_log.tsv"
    assert notes_main(["--reading", str(reading), "--out", str(out), "--log", str(log)]) == 2
    assert not log.exists()
    assert notes_main([
        "--confirm", "--reading", str(reading), "--out", str(out), "--log", str(log), "--date", "2026-10-09",
    ]) == 0
    copied = out / "Lovelace2020.md"
    assert copied.read_text(encoding="utf-8") == note.read_text(encoding="utf-8")
    copied.write_text("OLD\n", encoding="utf-8")
    assert notes_main([
        "--confirm", "--reading", str(reading), "--out", str(out), "--log", str(log), "--date", "2026-10-09",
    ]) == 0
    assert copied.read_text(encoding="utf-8") == "OLD\n"
    assert "already_present" in log.read_text(encoding="utf-8")
    assert notes_main(["--confirm", "--log", str(log), "--mark-attached", "Lovelace2020", "--date", "2026-10-09"]) == 0
    assert "attached" in log.read_text(encoding="utf-8")
    assert notes_main([
        "--confirm", "--reading", str(reading), "--out", str(out), "--log", str(log), "--date", "2026-10-09",
    ]) == 0
    assert "attached" in log.read_text(encoding="utf-8")
    assert copied.read_text(encoding="utf-8") == "OLD\n"
    assert notes_main(["--confirm", "--log", str(log), "--mark-attached", "Missing2020"]) == 1
    stray = reading / "scratch.md"
    stray.write_text("no id here\n", encoding="utf-8")
    assert notes_main([
        "--confirm", "--reading", str(reading), "--out", str(out), "--log", str(log),
    ]) == 1
