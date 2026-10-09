#!/usr/bin/env python3
"""Write an original SVG and PDF for each original item in the figure plan.

Adapted and reused items are not drawn. Published figures are not cropped.
Fig. 1 is an argument map. Tables and boxes are column schematics, not copied cells.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from xml.sax.saxutils import escape

ITEM_RE = re.compile(r"^## ((?:Fig\.|Table|Box) \d+[a-z]?)\s*$", re.M)
BULLET_RE = re.compile(r"^-\s+([^:]+):\s*(.*)$")
EVIDENCE_RE = re.compile(r"\bE\d{3,}\b")
KIND = {"Fig.": "fig", "Table": "table", "Box": "box"}


def slug(item_id: str) -> str:
    match = re.fullmatch(r"(Fig\.|Table|Box) (\d+[a-z]?)", item_id)
    if match is None:
        raise ValueError(f"bad item id: {item_id}")
    return f"{KIND[match.group(1)]}-{match.group(2)}"


def parse_plan(text: str) -> List[dict]:
    matches = list(ITEM_RE.finditer(text))
    items = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        fields: Dict[str, str] = {}
        for line in text[start:end].splitlines():
            bullet = BULLET_RE.match(line.strip())
            if bullet:
                fields[bullet.group(1).strip()] = bullet.group(2).strip()
        panels = [
            part.strip()
            for part in re.split(r";", fields.get("Panels or columns", ""))
            if part.strip()
        ]
        items.append(
            {
                "id": match.group(1),
                "message": fields.get("Message", ""),
                "type": fields.get("Type", "").lower(),
                "evidence_ids": EVIDENCE_RE.findall(fields.get("Evidence IDs", "")),
                "panels": panels,
                "do_not_copy": fields.get("Do not copy", ""),
            }
        )
    return items


def _read_ledger(text: str) -> List[dict]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
    rows = []
    for row in reader:
        rows.append({key: (value or "").strip() for key, value in row.items() if key})
    return rows


def _pdf_safe(text: str) -> str:
    cleaned = "".join(character if 32 <= ord(character) <= 126 else "?" for character in text)
    return cleaned.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_lines(lines: Sequence[str], width: int = 90) -> List[str]:
    """Keep every character. A long evidence line is split, not dropped."""
    wrapped: List[str] = []
    for line in lines:
        text = line or ""
        if len(text) <= width:
            wrapped.append(text)
            continue
        while text:
            wrapped.append(text[:width])
            text = text[width:]
    return wrapped


def _asks_to_crop(message: str) -> bool:
    """A request to crop fails. A warning not to crop does not."""
    if re.search(r"\b(?:do not|don't|not a)\s+crop\b", message, re.I):
        return False
    return re.search(r"\bcrop(?:p(?:ed|ing))?\b", message, re.I) is not None


def build_pdf(lines: Sequence[str]) -> bytes:
    """One-page PDF with uncompressed Helvetica text."""
    safe = [_pdf_safe(line) for line in _wrap_lines(lines)] or ["original"]
    commands = ["BT", "/F1 11 Tf", "50 750 Td"]
    for index, line in enumerate(safe):
        if index:
            commands.append("0 -14 Td")
        commands.append(f"({line}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        b"4 0 obj\n<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    header = b"%PDF-1.4\n"
    chunks = [header]
    offsets = [0]
    cursor = len(header)
    for part in objects:
        offsets.append(cursor)
        chunks.append(part)
        cursor += len(part)
    xref = [f"xref\n0 {len(offsets)}\n", "0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n")
    trailer = (
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{cursor}\n%%EOF\n"
    )
    return b"".join(chunks) + "".join(xref).encode("ascii") + trailer.encode("ascii")


def build_svg(item: dict) -> str:
    kind = "argument map" if item["id"] == "Fig. 1" else "original schematic"
    if item["id"].startswith("Table") or item["id"].startswith("Box"):
        note = "Column headings only. Cell values stay in the evidence table."
    else:
        note = "Not a crop of a published figure."
    evidence = ", ".join(item["evidence_ids"])
    panels = item["panels"] or [item["message"] or kind]
    y = 88
    shapes: List[str] = []
    for panel in panels:
        shapes.append(
            f'<rect x="40" y="{y}" width="520" height="46" fill="#f4f4f4" stroke="#222"/>'
            f'<text x="52" y="{y + 28}" font-size="14">{escape(panel)}</text>'
        )
        y += 58
    height = y + 48
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{height}" '
        f'viewBox="0 0 600 {height}">\n'
        f"  <title>{escape(item['id'])}</title>\n"
        f"  <desc>{escape(kind)}. {escape(note)} Evidence IDs: {escape(evidence)}</desc>\n"
        f'  <text x="40" y="36" font-size="18">{escape(item["id"])}: {escape(kind)}</text>\n'
        f'  <text x="40" y="62" font-size="12">{escape(item["message"])}</text>\n'
        f"  {''.join(shapes)}\n"
        f'  <text x="40" y="{y + 20}" font-size="12">Evidence IDs: {escape(evidence)}</text>\n'
        "</svg>\n"
    )


def _pdf_lines(item: dict) -> List[str]:
    kind = "argument map" if item["id"] == "Fig. 1" else "original schematic"
    lines = [
        f"{item['id']}: {kind}",
        item["message"],
        "Evidence IDs: " + ", ".join(item["evidence_ids"]),
        "Not a crop of a published figure.",
    ]
    lines.extend(item["panels"])
    return lines


def plan_errors(items: Sequence[dict], ledger_rows: Sequence[dict]) -> List[str]:
    errors: List[str] = []
    by_id = {item["id"]: item for item in items}
    if len(by_id) != len(items):
        errors.append("duplicate item headings in the figure plan")
    ledger_ids = [row.get("id", "") for row in ledger_rows]
    if set(by_id) != set(ledger_ids):
        errors.append("plan headings and ledger ids must be the same set")
    for row in ledger_rows:
        item = by_id.get(row.get("id", ""))
        if item is None:
            continue
        if item["type"] != (row.get("type") or "").lower():
            errors.append(f"{item['id']} plan type does not match the ledger")
        if item["type"] not in {"original", "adapted", "reused"}:
            errors.append(f"{item['id']} type must be original, adapted, or reused")
        if _asks_to_crop(item["message"]):
            errors.append(f"{item['id']} refusing to crop a published figure")
        if item["type"] == "original" and not item["evidence_ids"]:
            errors.append(f"{item['id']} original item needs evidence IDs on the plan")
        if item["id"] == "Fig. 1" and item["type"] != "original":
            errors.append("Fig. 1 must stay an original argument map")
    return errors


def draw(plan_text: str, ledger_text: str, out_dir: Path) -> List[str]:
    """Write SVG and PDF files. Return errors and write nothing when any error exists."""
    items = parse_plan(plan_text)
    ledger_rows = _read_ledger(ledger_text)
    errors = plan_errors(items, ledger_rows)
    if errors:
        return errors
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        if item["type"] != "original":
            continue
        stem = slug(item["id"])
        (out_dir / f"{stem}.svg").write_text(build_svg(item), encoding="utf-8")
        (out_dir / f"{stem}.pdf").write_bytes(build_pdf(_pdf_lines(item)))
    return []


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        errors = draw(
            args.plan.read_text(encoding="utf-8"),
            args.ledger.read_text(encoding="utf-8"),
            args.out,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("OK originals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
