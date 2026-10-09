#!/usr/bin/env python3
"""Cohen's kappa for two independent screeners.

Bands follow Landis and Koch, Biometrics, 1977:
poor (<0), slight (0-0.20), fair (0.21-0.40), moderate (0.41-0.60),
substantial (0.61-0.80), almost perfect (0.81-1).
When expected agreement is 1, kappa is undefined.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def interpret(kappa):
    if kappa is None:
        return "undefined"
    if kappa < 0:
        return "poor"
    if kappa <= 0.20:
        return "slight"
    if kappa <= 0.40:
        return "fair"
    if kappa <= 0.60:
        return "moderate"
    if kappa <= 0.80:
        return "substantial"
    return "almost_perfect"


def cohen_kappa(labels_a, labels_b) -> dict:
    if len(labels_a) != len(labels_b):
        raise ValueError("label sequences differ in length")
    n = len(labels_a)
    if n == 0:
        raise ValueError("no items to compare")
    left = [str(item).strip().lower() for item in labels_a]
    right = [str(item).strip().lower() for item in labels_b]
    categories = sorted(set(left) | set(right))
    index = {label: pos for pos, label in enumerate(categories)}
    matrix = [[0 for _ in categories] for _ in categories]
    for a_lab, b_lab in zip(left, right):
        matrix[index[a_lab]][index[b_lab]] += 1
    agree = sum(matrix[i][i] for i in range(len(categories)))
    observed = agree / n
    expected = 0.0
    for i in range(len(categories)):
        row_sum = sum(matrix[i]) / n
        col_sum = sum(matrix[r][i] for r in range(len(categories))) / n
        expected += row_sum * col_sum
    if abs(expected - 1.0) < 1e-12:
        kappa = None
    else:
        kappa = (observed - expected) / (1.0 - expected)
    confusion = {}
    for i, row_label in enumerate(categories):
        confusion[row_label] = {
            categories[j]: matrix[i][j] for j in range(len(categories))
        }
    return {
        "n": n,
        "observed_agreement": observed,
        "expected_agreement": expected,
        "kappa": kappa,
        "interpretation": interpret(kappa),
        "categories": categories,
        "confusion": confusion,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Cohen's kappa for two screening columns.")
    parser.add_argument("--csv", required=True, help="CSV with one row per record")
    parser.add_argument("--a", required=True, help="Column of screener A decisions")
    parser.add_argument("--b", required=True, help="Column of screener B decisions")
    parser.add_argument("--out", required=True, help="Path for the JSON result")
    args = parser.parse_args(argv)
    path = Path(args.csv)
    if not path.is_file():
        print("error: file not found: %s" % path, file=sys.stderr)
        return 1
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        print("error: no rows in %s" % path, file=sys.stderr)
        return 1
    missing = [name for name in (args.a, args.b) if name not in rows[0]]
    if missing:
        print("error: missing column(s): %s" % ", ".join(missing), file=sys.stderr)
        return 1
    try:
        result = cohen_kappa([row[args.a] for row in rows], [row[args.b] for row in rows])
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if result["kappa"] is None:
        print("kappa: undefined (%s)" % result["interpretation"])
    else:
        print("kappa: %.4f (%s)" % (result["kappa"], result["interpretation"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
