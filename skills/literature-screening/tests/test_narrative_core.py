"""Tests for narrative ranking and the project cap."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from narrative_core import (  # noqa: E402
    cap_from_project_yaml,
    check_core,
    main,
    rank_records,
    split_by_cap,
)

LIBRARY = [
    {
        "record_id": "R2",
        "title": "Grape aroma pathways",
        "abstract": "Terpene profiles in berries",
    },
    {
        "record_id": "R1",
        "title": "Cold tolerance assays",
        "abstract": "Bud cold tolerance during winter",
    },
    {
        "record_id": "R3",
        "title": "Unrelated warehouse inventory",
        "abstract": "Pallet counts",
    },
]


def test_rank_keeps_every_row_and_orders_by_overlap_then_id():
    ranked = rank_records(LIBRARY, "cold tolerance assays")
    assert [row["record_id"] for row in ranked] == ["R1", "R2", "R3"]
    assert ranked[0]["rank"] == "1"
    assert int(ranked[0]["overlap_score"]) > int(ranked[1]["overlap_score"])
    assert "decision" not in ranked[0]
    tied = rank_records(
        [
            {"record_id": "R3", "title": "Other topic", "abstract": ""},
            {"record_id": "R2", "title": "Another topic", "abstract": ""},
        ],
        "cold tolerance",
    )
    assert [row["record_id"] for row in tied] == ["R2", "R3"]


def test_cap_reads_only_the_project_value():
    assert cap_from_project_yaml("narrative_core_cap: 500\n") == 500
    try:
        cap_from_project_yaml("title: x\n")
    except ValueError as exc:
        assert "exactly once" in str(exc)
    else:
        raise AssertionError("missing cap should fail")


def test_ties_at_the_cutoff_stay_and_the_rest_are_below_cap():
    ranked = [
        {"record_id": "A", "overlap_score": "3", "rank": "1"},
        {"record_id": "B", "overlap_score": "2", "rank": "2"},
        {"record_id": "C", "overlap_score": "2", "rank": "3"},
        {"record_id": "D", "overlap_score": "1", "rank": "4"},
    ]
    decisions, overflow = split_by_cap(ranked, 2)
    by_id = {row["record_id"]: row for row in decisions}
    assert by_id["A"]["decision"] == "core" and by_id["A"]["reason"] == ""
    assert by_id["B"]["decision"] == "core"
    assert by_id["C"]["decision"] == "core" and by_id["C"]["reason"] == "tie-at-cutoff"
    assert overflow == ["C"]
    assert by_id["D"]["decision"] == "not_read" and by_id["D"]["reason"] == "below-cap"
    small, no_overflow = split_by_cap(ranked[:2], 500)
    assert [row["decision"] for row in small] == ["core", "core"]
    assert no_overflow == []


def _flow():
    return (
        "This file is not a complete systematic review.\n"
        "Records marked not read were outside the cap.\n"
    )


def test_check_accepts_the_project_cap_and_rejects_a_different_size():
    ranked = rank_records(LIBRARY, "cold tolerance assays")
    decisions, overflow = split_by_cap(ranked, 1)
    core_ids = [row["record_id"] for row in decisions if row["decision"] == "core"]
    not_read = [row["record_id"] for row in decisions if row["decision"] == "not_read"]
    screening = []
    for row in decisions:
        if row["decision"] == "core":
            screening.append(
                {
                    "record_id": row["record_id"],
                    "stage": "title_abstract",
                    "decision": "include",
                    "reason_code": "CORE",
                    "consensus": "include",
                }
            )
        else:
            screening.append(
                {
                    "record_id": row["record_id"],
                    "stage": "title_abstract",
                    "decision": "not_read",
                    "reason_code": "below-cap",
                    "consensus": "not_read",
                }
            )
    assert (
        check_core(
            ["R1", "R2", "R3"],
            decisions,
            core_ids,
            not_read,
            _flow(),
            "narrative",
            screening,
            ranked=ranked,
            cap=1,
            overflow_ids=overflow,
        )
        == []
    )
    shrunk = [row for row in decisions if row["record_id"] != "R2"]
    assert any(
        "missing records" in error
        for error in check_core(
            ["R1", "R2", "R3"],
            shrunk,
            core_ids,
            not_read,
            _flow(),
            "narrative",
            screening,
            ranked=ranked,
            cap=1,
            overflow_ids=overflow,
        )
    )
    assert any(
        "full eligibility" in error
        for error in check_core(
            ["R1"],
            decisions,
            core_ids,
            [],
            _flow(),
            "systematic",
            None,
            ranked=ranked,
            cap=1,
            overflow_ids=[],
        )
    )


def test_cli_apply_uses_the_cap_and_refuses_a_substitute_flag(tmp_path, capsys):
    library = tmp_path / "library.csv"
    library.write_text(
        "record_id,title,abstract\n"
        "R1,Cold tolerance assays,winter buds\n"
        "R2,Cold tolerance notes,winter\n"
        "R3,Warehouse inventory,pallets\n",
        encoding="utf-8",
    )
    decisions = tmp_path / "core_decision.tsv"
    not_read = tmp_path / "not_read.tsv"
    overflow = tmp_path / "cap_overflow.tsv"
    rank_out = tmp_path / "narrative_rank.tsv"
    assert main([
        "apply",
        "--library", str(library),
        "--question", "cold tolerance",
        "--cap", "1",
        "--decisions", str(decisions),
        "--not-read", str(not_read),
        "--overflow", str(overflow),
        "--rank-out", str(rank_out),
    ]) == 0
    text = decisions.read_text(encoding="utf-8")
    assert "below-cap" in text
    assert "R3" in not_read.read_text(encoding="utf-8")
    assert main(["--max-core", "3", "rank", "--library", str(library)]) == 2
    assert "project.yaml" in capsys.readouterr().err


def test_full_screen_modes_refuse_the_cap(tmp_path, capsys):
    library = tmp_path / "library.csv"
    library.write_text(
        "record_id,title,abstract\nR1,Cold tolerance assays,winter buds\n",
        encoding="utf-8",
    )
    rank_out = tmp_path / "narrative_rank.tsv"
    decisions = tmp_path / "core_decision.tsv"
    not_read = tmp_path / "not_read.tsv"
    overflow = tmp_path / "cap_overflow.tsv"
    included = tmp_path / "included.tsv"
    screening = tmp_path / "screening.csv"
    flow = tmp_path / "prisma_flow.md"
    main([
        "apply",
        "--library", str(library),
        "--question", "cold tolerance",
        "--cap", "500",
        "--decisions", str(decisions),
        "--not-read", str(not_read),
        "--overflow", str(overflow),
        "--rank-out", str(rank_out),
    ])
    included.write_text("record_id\nR1\n", encoding="utf-8")
    screening.write_text(
        "record_id,stage,decision,reason_code,consensus\n"
        "R1,title_abstract,include,CORE,include\n",
        encoding="utf-8",
    )
    flow.write_text(
        "This file is not a complete systematic review.\nRecords were not read.\n",
        encoding="utf-8",
    )
    before = {path.name for path in tmp_path.iterdir()}
    for review_type in ("systematic", "scoping", "umbrella"):
        code = main([
            "check",
            "--library", str(library),
            "--decisions", str(decisions),
            "--included", str(included),
            "--not-read", str(not_read),
            "--flow", str(flow),
            "--screening", str(screening),
            "--rank", str(rank_out),
            "--overflow", str(overflow),
            "--cap", "500",
            "--review-type", review_type,
        ])
        assert code == 1
        assert "full eligibility" in capsys.readouterr().err
    assert {path.name for path in tmp_path.iterdir()} == before
