"""Tests for asreview_io.py (offline)."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "asreview_io.py"

LIBRARY = (
    "record_id,title,year,authors,journal,doi,pmid,abstract,sources,n_copies,identity_key\n"
    "R1,Paper one,2020,\"A, B; C, D\",J,10.1/a,,Abstract one,pubmed,1,doi:10.1/a\n"
    "R2,Paper two,2021,,J,,,,wos,1,ty:paper two|2021\n"
    "R3,,2022,,J,,,Only abstract,wos,1,x\n"
)

SCREENING = (
    "record_id,stage,screener,decision,reason_code,reason_note,date,consensus\n"
    "R1,title_abstract,A,include,,,2026-01-01,include\n"
    "R2,title_abstract,A,exclude,WRONG_POP,,2026-01-01,exclude\n"
    "R3,title_abstract,A,maybe,,,2026-01-01,maybe\n"
    "R2,full_text,A,exclude,X,,2026-01-02,exclude\n"
)

# Shape of an ASReview LAB CSV export: imported columns kept, asreview_* added.
ASREVIEW_EXPORT = (
    "lrs_record_id,title,abstract,authors,keywords,doi,year,journal,included,"
    "asreview_group_id,asreview_label,asreview_time,asreview_note,asreview_user_name\n"
    "R1,Paper one,Abstract one,\"A, B; C, D\",,10.1/a,2020,J,,0,1,2026-10-01 10:00:00,on topic,Ann\n"
    "R3,,Only abstract,,,,2022,J,,2,,,,\n"
    "R2,Paper two,,,,,2021,J,,1,0,2026-10-01 10:05:00,,\n"
)


@pytest.fixture(scope="module")
def aio():
    spec = importlib.util.spec_from_file_location("lrs_asreview_io", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_export_columns_and_prior_labels(aio, tmp_path, capsys):
    lib = tmp_path / "library.csv"
    lib.write_text(LIBRARY)
    scr = tmp_path / "screening.csv"
    scr.write_text(SCREENING)
    out = tmp_path / "asreview_in.csv"
    assert aio.main(["export", str(lib), "-o", str(out), "--screening", str(scr)]) == 0
    rows = list(csv.DictReader(out.open()))
    header = list(rows[0])
    assert header == aio.EXPORT_COLUMNS
    assert "record_id" not in header  # reserved by ASReview
    assert not any(h.startswith("asreview_") for h in header)  # ASReview strips these on export
    assert [(r["lrs_record_id"], r["included"]) for r in rows] == [("R1", "1"), ("R2", "0"), ("R3", "")]
    assert json.loads(capsys.readouterr().out)["prior_labels"] == 2


def test_export_label_column_is_an_asreview_name(aio):
    # ASReview reads "included" as its label column (data_format docs).
    assert "included" in aio.EXPORT_COLUMNS and "included" in aio.LABEL_COLUMNS


def test_export_rejects_rows_without_text(aio, tmp_path):
    lib = tmp_path / "library.csv"
    lib.write_text("record_id,title,abstract\nR1,,\n")
    with pytest.raises(SystemExit):
        aio.main(["export", str(lib), "-o", str(tmp_path / "o.csv")])


def test_export_rejects_duplicate_ids(aio):
    with pytest.raises(SystemExit):
        aio.export_rows([{"record_id": "R1", "title": "a"}, {"record_id": "R1", "title": "b"}])


def test_import_stages_without_finalizing(aio, tmp_path, capsys):
    exp = tmp_path / "asreview_export.csv"
    exp.write_text(ASREVIEW_EXPORT)
    out = tmp_path / "asreview_decisions.csv"
    assert aio.main(["import", str(exp), "-o", str(out)]) == 0
    counts = json.loads(capsys.readouterr().out)
    assert counts["relevant"] == 1 and counts["irrelevant"] == 1 and counts["not_seen"] == 1
    assert counts["exclude_missing_reason_code"] == 1
    rows = list(csv.DictReader(out.open()))
    assert list(rows[0]) == aio.SCREENING_COLUMNS
    r1, r2 = rows
    assert r1 == {"record_id": "R1", "stage": "title_abstract", "screener": "Ann", "decision": "include",
                  "reason_code": "", "reason_note": "on topic", "date": "2026-10-01", "consensus": ""}
    assert r2["decision"] == "exclude" and r2["reason_code"] == "" and r2["screener"] == "asreview"
    assert "R3" not in {r["record_id"] for r in rows}  # not seen is not an exclude


def test_import_screener_override_and_tsv_semicolon(aio, tmp_path):
    tsv = tmp_path / "e.tsv"
    tsv.write_text("lrs_record_id\ttitle\tasreview_label\nR1\tx\t1.0\n")
    staged, _ = aio.import_rows(aio._read(tsv), screener="B")
    assert staged[0]["screener"] == "B" and staged[0]["decision"] == "include"
    semi = tmp_path / "e.csv"
    semi.write_text("lrs_record_id;title;asreview_label\nR1;x;0\n")
    staged, _ = aio.import_rows(aio._read(semi))
    assert staged[0]["decision"] == "exclude"


def test_import_requires_id_and_label(aio):
    with pytest.raises(SystemExit):
        aio.import_rows([{"title": "x", "asreview_label": "1"}])
    with pytest.raises(SystemExit):
        aio.import_rows([{"lrs_record_id": "R1", "title": "x"}])


def test_round_trip_ids(aio, tmp_path):
    lib = tmp_path / "library.csv"
    lib.write_text(LIBRARY)
    rows = aio.export_rows(aio._read(lib))
    for i, r in enumerate(rows):
        r["asreview_label"] = str(i % 2)
    staged, _ = aio.import_rows(rows)
    assert [s["record_id"] for s in staged] == ["R1", "R2", "R3"]
