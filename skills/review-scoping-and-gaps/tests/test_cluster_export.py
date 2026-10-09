"""Tests for the optional post-export cluster pass."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from cluster_export import main, render_clusters  # noqa: E402

GRAPE = [
    {"record_id": "R1", "title": "Grape aroma pathways", "abstract": "Linalool in grape berries"},
    {"record_id": "R2", "title": "Grape aroma glycosides", "abstract": "Bound aroma in grape juice"},
    {"record_id": "R3", "title": "Warehouse pallet inventory", "abstract": "Pallet counts in a warehouse"},
]


def test_disjoint_titles_split_and_only_real_titles_are_copied():
    text = render_clusters(GRAPE, "grape aroma compounds")
    assert "Grape aroma pathways" in text
    assert "Warehouse pallet inventory" in text
    assert "Invented review of grape" not in text
    assert "topic_lock:" not in text
    assert text.count("## Cluster") >= 2
    assert "Ask whether to reopen the topic lock" not in text


def test_unrelated_question_asks_to_reopen_without_clearing_the_lock():
    text = render_clusters(GRAPE, "zebra habitat corridors")
    assert "Ask whether to reopen the topic lock" in text
    assert "Do not clear topic_lock in this file." in text
    assert "topic_lock: true" not in text
    assert "topic_lock: false" not in text


def test_cli_writes_the_cluster_file(tmp_path):
    library = tmp_path / "library.csv"
    library.write_text(
        "record_id,title,abstract\nR1,Grape aroma pathways,linalool\n",
        encoding="utf-8",
    )
    out = tmp_path / "export_clusters.md"
    assert main(["--library", str(library), "--question", "grape aroma", "--out", str(out)]) == 0
    assert "Grape aroma pathways" in out.read_text(encoding="utf-8")
