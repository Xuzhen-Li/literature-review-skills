#!/usr/bin/env python3
"""Accept a human gate only when the reply contains the exact sentence.

The whole message may be that sentence, or the message may be one line that
is that sentence. yes, ok, and paraphrases do not pass.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

PHRASES = {
    "institutional_access": "I have confirmed institutional login",
    "no_download_permission": "I have no download permission on this computer",
    "topic_lock": "I confirm the topic lock",
    "search_lock": "I confirm the search lock",
    "inclusion_lock": "I confirm the inclusion lock",
    "outline_lock": "I confirm the outline lock",
    "journal_lock": "I confirm the journal lock",
    "final_submit": "I confirm the package is ready for me to submit",
}


def reply_matches(gate: str, message: str) -> bool:
    phrase = PHRASES.get(gate)
    if phrase is None:
        return False
    text = (message or "").replace("\r\n", "\n").strip()
    if text == phrase:
        return True
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return len(lines) == 1 and lines[0] == phrase


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", required=True, choices=sorted(PHRASES))
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--reply")
    source.add_argument("--reply-file")
    args = parser.parse_args(argv)
    if args.reply_file:
        try:
            message = open(args.reply_file, encoding="utf-8").read()
        except OSError as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
    else:
        message = args.reply
    if reply_matches(args.gate, message):
        print("OK gate phrase")
        return 0
    print(f"ERROR required phrase: {PHRASES[args.gate]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
