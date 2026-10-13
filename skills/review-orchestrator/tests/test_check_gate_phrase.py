"""Exact gate sentences. Loose replies fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_gate_phrase import main, reply_matches  # noqa: E402


def test_exact_sentence_passes_and_loose_replies_fail():
    assert reply_matches("topic_lock", "I confirm the topic lock")
    assert reply_matches("topic_lock", "\nI confirm the topic lock\n")
    assert not reply_matches("topic_lock", "yes")
    assert not reply_matches("topic_lock", "ok")
    assert not reply_matches("topic_lock", "I confirm the topic lock.")
    assert not reply_matches("topic_lock", "yes\nI confirm the topic lock")
    assert reply_matches(
        "final_submit",
        "I confirm the package is ready for me to submit",
    )
    assert reply_matches(
        "no_download_permission",
        "I have no download permission on this computer",
    )
    assert not reply_matches("institutional_access", "I have no download permission on this computer")


def test_cli(capsys):
    assert main(["--gate", "search_lock", "--reply", "I confirm the search lock"]) == 0
    assert "OK gate phrase" in capsys.readouterr().out
    assert main(["--gate", "search_lock", "--reply", "Yes"]) == 1
    assert "I confirm the search lock" in capsys.readouterr().err
