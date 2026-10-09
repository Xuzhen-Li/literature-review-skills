#!/usr/bin/env python3
"""Group exported titles and abstracts after the topic is already locked.

This is a token-overlap aid. It does not replace the question-first scope
report and it does not change topic_lock.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set

STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "in",
    "on",
    "for",
    "to",
    "with",
    "by",
    "from",
    "at",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "this",
    "that",
    "these",
    "those",
    "into",
    "over",
    "than",
    "not",
    "no",
}
REOPEN = (
    "Ask whether to reopen the topic lock. "
    "Do not clear topic_lock in this file."
)


def content_tokens(text: str) -> Set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if token not in STOPWORDS and len(token) > 2
    }


def cluster_rows(rows: Sequence[dict], threshold: float = 0.2) -> List[dict]:
    """Greedy groups. A row joins the best existing group only when overlap is high enough."""
    clusters: List[dict] = []
    for row in rows:
        tokens = content_tokens(f"{row.get('title') or ''} {row.get('abstract') or ''}")
        best_index = None
        best_score = 0.0
        for index, cluster in enumerate(clusters):
            union = tokens | cluster["tokens"]
            score = len(tokens & cluster["tokens"]) / len(union) if union else 0.0
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is not None and best_score >= threshold:
            cluster = clusters[best_index]
            cluster["ids"].append((row.get("record_id") or "").strip())
            cluster["titles"].append(row.get("title") or "")
            cluster["tokens"] |= tokens
        else:
            clusters.append(
                {
                    "ids": [(row.get("record_id") or "").strip()],
                    "titles": [row.get("title") or ""],
                    "tokens": set(tokens),
                }
            )
    clusters.sort(key=lambda cluster: (-len(cluster["ids"]), cluster["ids"][0] if cluster["ids"] else ""))
    return clusters


def render_clusters(rows: Sequence[dict], question: str, threshold: float = 0.2) -> str:
    clusters = cluster_rows(rows, threshold=threshold)
    question_tokens = content_tokens(question)
    lines = [
        "# Export clusters",
        "",
        "This pass does not replace the locked question and does not change topic_lock.",
        "Groups are token overlap only. They are not a topic model and they are not a new lock.",
        "",
    ]
    if not clusters:
        lines.append("No records.")
        lines.append("")
        return "\n".join(lines)
    largest = clusters[0]
    largest_blob = " ".join(largest["titles"])
    if not (question_tokens & content_tokens(largest_blob) or question_tokens & largest["tokens"]):
        lines.append(REOPEN)
        lines.append("")
    for index, cluster in enumerate(clusters, start=1):
        ranked = sorted(cluster["tokens"])
        top = ", ".join(ranked[:3]) if ranked else "(no content tokens)"
        lines.append(f"## Cluster {index}")
        lines.append("")
        lines.append(f"- Records: {len(cluster['ids'])}")
        lines.append(f"- Terms: {top}")
        lines.append("- Titles:")
        for title in cluster["titles"]:
            lines.append(f"  - {title}")
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    with args.library.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    text = render_clusters(rows, args.question)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    if "topic_lock:" in text:
        print("ERROR cluster file must not set a gate", file=sys.stderr)
        return 1
    print("OK clusters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
