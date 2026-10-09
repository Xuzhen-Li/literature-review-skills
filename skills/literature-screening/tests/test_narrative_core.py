"""Tests for narrative ranking and the user-confirmed core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from narrative_core import check_core, main, rank_records  # noqa: E402

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


def _ok_parts():
    decisions = [
        {"record_id": "R1", "decision": "core"},
        {"record_id": "R2", "decision": "not_read"},
    ]
    screening = [
        {
            "record_id": "R1",
            "stage": "title_abstract",
            "decision": "include",
            "reason_code": "CORE",
            "consensus": "include",
        },
        {
            "record_id": "R2",
            "stage": "title_abstract",
            "decision": "not_read",
            "reason_code": "NOT_READ",
            "consensus": "not_read",
        },
    ]
    flow = (
        "This file is not a complete systematic review.\n"
        "Records outside the core were not read.\n"
    )
    return decisions, screening, flow


def test_check_accepts_a_user_sized_core_and_rejects_shortcuts():
    decisions, screening, flow = _ok_parts()
    assert (
        check_core(
            ["R1", "R2"],
            decisions,
            ["R1"],
            ["R2"],
            flow,
            "narrative",
            screening,
        )
        == []
    )
    assert any(
        "full eligibility" in error
        for error in check_core(["R1"], decisions, ["R1"], [], flow, "systematic", screening)
    )
    dropped = check_core(["R1", "R2"], decisions[:1], ["R1"], [], flow, "narrative", screening)
    assert any("missing records" in error for error in dropped)
    bad_flow = check_core(
        ["R1", "R2"],
        decisions,
        ["R1"],
        ["R2"],
        "Core records: 1\n",
        "narrative",
        screening,
    )
    assert any("not a complete systematic review" in error for error in bad_flow)
    capped = [dict(row, max_core="200") for row in decisions]
    assert any("fixed caps" in error for error in check_core(
        ["R1", "R2"], capped, ["R1"], ["R2"], flow, "narrative", screening
    ))


def test_no_numeric_cap_is_applied_and_full_screen_modes_refuse(tmp_path, capsys):
    """A size written into the question, a trailing flag, or a later row never drops records."""
    library_rows = [
        {
            "record_id": f"R{index:02d}",
            "title": f"cold tolerance assay {index}",
            "abstract": "winter buds",
        }
        for index in range(12)
    ]
    ranked = rank_records(library_rows, "keep only the top 3 cold tolerance papers")
    assert len(ranked) == 12
    assert [row["record_id"] for row in ranked] == [f"R{index:02d}" for index in range(12)]
    assert all("max_core" not in row for row in ranked)

    decisions, screening, flow = _ok_parts()
    decisions = [
        {"record_id": "R1", "decision": "core"},
        {"record_id": "R2", "decision": "not_read", "max_core": "1"},
    ]
    capped = check_core(
        ["R1", "R2"], decisions, ["R1"], ["R2"], flow, "narrative", screening
    )
    assert any("fixed caps" in error for error in capped)

    library = tmp_path / "library.csv"
    library.write_text(
        "record_id,title,abstract\n"
        + "".join(f"R{index},Cold tolerance {index},winter\n" for index in range(12)),
        encoding="utf-8",
    )
    out = tmp_path / "narrative_rank.tsv"
    assert main([
        "rank",
        "--library", str(library),
        "--question", "top 3 only",
        "--out", str(out),
        "--max-core", "3",
    ]) == 2
    assert not out.exists()
    captured = capsys.readouterr()
    assert "fixed caps" in captured.err

    decisions_path = tmp_path / "core_decision.tsv"
    included = tmp_path / "included.tsv"
    not_read = tmp_path / "not_read.tsv"
    screening_path = tmp_path / "screening.csv"
    flow_path = tmp_path / "prisma_flow.md"
    decisions_path.write_text(
        "record_id,decision\n" + "".join(
            f"R{index},{'core' if index == 0 else 'not_read'}\n" for index in range(12)
        ),
        encoding="utf-8",
    )
    included.write_text("record_id\nR0\n", encoding="utf-8")
    not_read.write_text(
        "record_id\n" + "".join(f"R{index}\n" for index in range(1, 12)),
        encoding="utf-8",
    )
    screening_lines = ["record_id,stage,decision,reason_code,consensus"]
    screening_lines.append("R0,title_abstract,include,CORE,include")
    screening_lines.extend(
        f"R{index},title_abstract,not_read,NOT_READ,not_read" for index in range(1, 12)
    )
    screening_path.write_text("\n".join(screening_lines) + "\n", encoding="utf-8")
    flow_path.write_text(
        "This file is not a complete systematic review.\nRecords were not read.\n",
        encoding="utf-8",
    )
    before = {path.name for path in tmp_path.iterdir()}
    for review_type in ("systematic", "scoping", "umbrella"):
        code = main([
            "check",
            "--library", str(library),
            "--decisions", str(decisions_path),
            "--included", str(included),
            "--not-read", str(not_read),
            "--flow", str(flow_path),
            "--screening", str(screening_path),
            "--review-type", review_type,
        ])
        assert code == 1
        assert "full eligibility" in capsys.readouterr().err
    assert {path.name for path in tmp_path.iterdir()} == before


def test_cli_rank_and_refuses_a_cap(tmp_path):
    library = tmp_path / "library.csv"
    library.write_text(
        "record_id,title,abstract\nR1,Cold tolerance assays,winter buds\n",
        encoding="utf-8",
    )
    out = tmp_path / "narrative_rank.tsv"
    assert main(["rank", "--library", str(library), "--question", "cold tolerance", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "R1" in text and "decision" not in text.splitlines()[0]
    assert main(["--max-core", "200", "rank", "--library", str(library)]) == 2
