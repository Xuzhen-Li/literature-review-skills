#!/usr/bin/env python3
"""Draw a PRISMA 2020 flow diagram as SVG and PDF from a counts file.

[[TODO-TEXT]]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

# Style (pt): 0.5 pt lines, Arial 7/8 pt, house greys.
LINE_W = 0.5
LINE = "#333333"
HEAD_FILL = "#F0F0F0"
TEXT = "#000000"
BODY_PT = 7.0
HEAD_PT = 8.0
BOX_W = 100.0
PAD = 4.0
LEAD = 1.25
GAP_X = 12.0
ARM_GAP = 16.0
GAP_Y = 14.0
PHASE_W = 14.0
MARGIN = 3.0
ARROW = 3.0

# Arial advance widths per 1000 em, ASCII 32-126.
ASCII_W = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]

FONT_PATHS = [
    "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

DB_KEYS = [
    "databases", "registers", "duplicates_removed", "automation_removed",
    "other_removed", "screened", "screened_excluded", "sought", "not_retrieved",
    "assessed", "studies_included", "reports_included",
]
DB_OPTIONAL = {"registers": 0, "automation_removed": 0, "other_removed": 0}
OTHER_KEYS = [
    "websites", "organisations", "citation_searching", "sought",
    "not_retrieved", "assessed", "reports_included",
]
OTHER_OPTIONAL = {"websites": 0, "organisations": 0, "citation_searching": 0}


class CountsError(ValueError):
    """Raised with every problem found in a counts file."""

    def __init__(self, errors: Sequence[str]):
        super().__init__("\n".join(errors))
        self.errors = list(errors)


# ---------- parsing ----------

def _as_int(key: str, value, errors: List[str]) -> Optional[int]:
    if isinstance(value, bool):
        errors.append(f"{key}: not an integer: {value!r}")
        return None
    if isinstance(value, int):
        n = value
    elif isinstance(value, float) and value.is_integer():
        n = int(value)
    elif isinstance(value, str) and value.strip().lstrip("-").isdigit():
        n = int(value.strip())
    else:
        errors.append(f"{key}: not an integer: {value!r}")
        return None
    if n < 0:
        errors.append(f"{key}: negative count {n}")
        return None
    return n


def _section(raw: dict, keys: List[str], optional: Dict[str, int], prefix: str,
             errors: List[str]) -> dict:
    out: dict = {}
    allowed = set(keys) | {"excluded_reasons"}
    for key in raw:
        if key not in allowed and not (prefix == "" and key == "other"):
            errors.append(f"{prefix}{key}: unknown key")
    for key in keys:
        if key not in raw:
            if key in optional:
                out[key] = optional[key]
            else:
                errors.append(f"{prefix}{key}: missing")
            continue
        n = _as_int(prefix + key, raw[key], errors)
        if n is not None:
            out[key] = n
    reasons = raw.get("excluded_reasons", {})
    if isinstance(reasons, list):
        try:
            reasons = {str(r["reason"]): r["n"] for r in reasons}
        except (TypeError, KeyError):
            errors.append(f"{prefix}excluded_reasons: list items need 'reason' and 'n'")
            reasons = {}
    if not isinstance(reasons, dict):
        errors.append(f"{prefix}excluded_reasons: must be an object or list")
        reasons = {}
    out["excluded_reasons"] = {}
    for label, value in reasons.items():
        if not str(label).strip():
            errors.append(f"{prefix}excluded_reasons: empty reason label")
            continue
        n = _as_int(f"{prefix}excluded_reasons[{label}]", value, errors)
        if n is not None:
            out["excluded_reasons"][str(label).strip()] = n
    return out


def normalize(raw: dict) -> dict:
    """Return typed counts or raise CountsError listing every problem."""
    if not isinstance(raw, dict):
        raise CountsError(["top level must be an object"])
    errors: List[str] = []
    counts = _section(raw, DB_KEYS, DB_OPTIONAL, "", errors)
    other = raw.get("other")
    if other is not None:
        if not isinstance(other, dict):
            errors.append("other: must be an object")
        else:
            counts["other"] = _section(other, OTHER_KEYS, OTHER_OPTIONAL, "other.", errors)
    if errors:
        raise CountsError(errors)
    validate(counts)
    return counts


def validate(c: dict) -> None:
    errors: List[str] = []

    def eq(label: str, left: int, right: int, expr: str) -> None:
        if left != right:
            errors.append(f"{label}: expected {expr} = {right}, got {left}")

    identified = c["databases"] + c["registers"]
    removed = c["duplicates_removed"] + c["automation_removed"] + c["other_removed"]
    eq("screened", c["screened"], identified - removed,
       "databases + registers - duplicates_removed - automation_removed - other_removed")
    eq("sought", c["sought"], c["screened"] - c["screened_excluded"],
       "screened - screened_excluded")
    eq("assessed", c["assessed"], c["sought"] - c["not_retrieved"], "sought - not_retrieved")
    db_excl = sum(c["excluded_reasons"].values())
    if not c["excluded_reasons"] and c["assessed"] > 0:
        errors.append("excluded_reasons: list at least one reason (use 0 counts if none)")
    db_included = c["assessed"] - db_excl
    if db_included < 0:
        errors.append(f"excluded_reasons: sum {db_excl} exceeds assessed {c['assessed']}")
    included = db_included
    o = c.get("other")
    if o:
        o_identified = o["websites"] + o["organisations"] + o["citation_searching"]
        if o["sought"] > o_identified:
            errors.append(
                f"other.sought: {o['sought']} exceeds records identified {o_identified}")
        eq("other.assessed", o["assessed"], o["sought"] - o["not_retrieved"],
           "other.sought - other.not_retrieved")
        o_excl = sum(o["excluded_reasons"].values())
        eq("other.reports_included", o["reports_included"], o["assessed"] - o_excl,
           "other.assessed - sum(other.excluded_reasons)")
        included += o["reports_included"]
    eq("reports_included", c["reports_included"], included,
       "assessed - sum(excluded_reasons)" + (" + other.reports_included" if o else ""))
    if c["studies_included"] > c["reports_included"]:
        errors.append(
            f"studies_included: {c['studies_included']} exceeds reports_included "
            f"{c['reports_included']}")
    for path, text in _labels(c):
        try:
            text.encode("cp1252")
        except UnicodeEncodeError:
            errors.append(f"{path}: characters outside Windows-1252 cannot be drawn: {text!r}")
    if errors:
        raise CountsError(errors)


def _labels(c: dict):
    for label in c["excluded_reasons"]:
        yield "excluded_reasons", label
    for label in c.get("other", {}).get("excluded_reasons", {}):
        yield "other.excluded_reasons", label


def parse_csv(text: str) -> dict:
    """Rows of key,value. Reasons: excluded_reason:<label>. Other arm: other.<key>."""
    raw: dict = {}
    errors: List[str] = []
    reader = csv.reader(io.StringIO(text))
    for lineno, row in enumerate(reader, 1):
        if not row or not "".join(row).strip() or row[0].lstrip().startswith("#"):
            continue
        if lineno == 1 and [x.strip().lower() for x in row[:2]] == ["key", "value"]:
            continue
        if len(row) != 2:
            errors.append(f"line {lineno}: expected 2 columns (key,value), got {len(row)}")
            continue
        key, value = row[0].strip(), row[1].strip()
        target = raw
        if key.startswith("other."):
            target = raw.setdefault("other", {})
            key = key[len("other."):]
        if key.startswith("excluded_reason:"):
            label = key[len("excluded_reason:"):].strip()
            reasons = target.setdefault("excluded_reasons", {})
            if label in reasons:
                errors.append(f"line {lineno}: duplicate reason {label!r}")
            reasons[label] = value
        else:
            if key in target:
                errors.append(f"line {lineno}: duplicate key {key!r}")
            target[key] = value
    if errors:
        raise CountsError(errors)
    return raw


def load_counts(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CountsError([f"{path}: invalid JSON: {exc}"]) from None
    elif suffix == ".csv":
        raw = parse_csv(text)
    else:
        raise CountsError([f"{path}: use a .json or .csv file"])
    return normalize(raw)


# ---------- layout ----------

def text_width(text: str, size: float) -> float:
    total = 0
    for ch in text:
        o = ord(ch)
        if o == 0xA0:
            o = 32
        total += ASCII_W[o - 32] if 32 <= o <= 126 else 556
    return total * size / 1000.0


def wrap(text: str, size: float, width: float, indent: float = 0.0) -> List[Tuple[float, str]]:
    """Greedy word wrap; continuation lines get a 4 pt hanging indent."""
    words = text.split(" ")
    lines: List[Tuple[float, str]] = []
    cur = ""
    cur_indent = indent
    for word in words:
        trial = f"{cur} {word}" if cur else word
        if cur and text_width(trial, size) > width - cur_indent:
            lines.append((cur_indent, cur))
            cur = word
            cur_indent = indent + 4.0
        else:
            cur = trial
    lines.append((cur_indent, cur))
    return lines


def n(v: int) -> str:
    return f"(n\u00a0=\u00a0{v})"  # no-break spaces keep the count on one line


class Box:
    def __init__(self, x: float, items: List[Tuple[str, bool]], head: bool = False,
                 width: float = BOX_W):
        self.x = x
        self.w = width
        self.head = head
        size = HEAD_PT if head else BODY_PT
        self.size = size
        self.lines: List[Tuple[float, str]] = []
        for text, indented in items:
            self.lines += [(i, t.replace("\u00a0", " "))
                           for i, t in wrap(text, size, width - 2 * PAD, 6.0 if indented else 0.0)]
        self.h = 2 * PAD + len(self.lines) * size * LEAD - (LEAD - 1) * size
        self.y = 0.0


def build_layout(c: dict) -> dict:
    o = c.get("other")
    x_main = MARGIN + PHASE_W + GAP_X / 2
    x_right = x_main + BOX_W + GAP_X
    x_omain = x_right + BOX_W + ARM_GAP
    x_oright = x_omain + BOX_W + GAP_X
    width = (x_oright if o else x_right) + BOX_W + MARGIN

    head = [Box(x_main, [("Identification of studies via databases and registers", False)],
                head=True, width=2 * BOX_W + GAP_X)]
    if o:
        head.append(Box(x_omain, [("Identification of studies via other methods", False)],
                        head=True, width=2 * BOX_W + GAP_X))

    r = c["excluded_reasons"]
    rows: List[List[Box]] = []
    row = [
        Box(x_main, [("Records identified from:", False),
                     (f"Databases {n(c['databases'])}", True),
                     (f"Registers {n(c['registers'])}", True)]),
        Box(x_right, [("Records removed before screening:", False),
                      (f"Duplicate records removed {n(c['duplicates_removed'])}", True),
                      ("Records marked as ineligible by automation tools "
                       f"{n(c['automation_removed'])}", True),
                      (f"Records removed for other reasons {n(c['other_removed'])}", True)]),
    ]
    if o:
        row.append(Box(x_omain, [("Records identified from:", False),
                                 (f"Websites {n(o['websites'])}", True),
                                 (f"Organisations {n(o['organisations'])}", True),
                                 (f"Citation searching {n(o['citation_searching'])}", True)]))
    rows.append(row)
    rows.append([Box(x_main, [(f"Records screened {n(c['screened'])}", False)]),
                 Box(x_right, [(f"Records excluded {n(c['screened_excluded'])}", False)])])
    row = [Box(x_main, [(f"Reports sought for retrieval {n(c['sought'])}", False)]),
           Box(x_right, [(f"Reports not retrieved {n(c['not_retrieved'])}", False)])]
    if o:
        row += [Box(x_omain, [(f"Reports sought for retrieval {n(o['sought'])}", False)]),
                Box(x_oright, [(f"Reports not retrieved {n(o['not_retrieved'])}", False)])]
    rows.append(row)

    def excl_box(x: float, reasons: Dict[str, int]) -> Box:
        items = [("Reports excluded:", False)]
        items += [(f"{label} {n(v)}", True) for label, v in reasons.items()]
        return Box(x, items)

    row = [Box(x_main, [(f"Reports assessed for eligibility {n(c['assessed'])}", False)]),
           excl_box(x_right, r)]
    if o:
        row += [Box(x_omain, [(f"Reports assessed for eligibility {n(o['assessed'])}", False)]),
                excl_box(x_oright, o["excluded_reasons"])]
    rows.append(row)
    rows.append([Box(x_main, [(f"Studies included in review {n(c['studies_included'])}", False),
                              (f"Reports of included studies {n(c['reports_included'])}",
                               False)])])

    y = MARGIN
    hh = max(b.h for b in head)
    for b in head:
        b.y, b.h = y, hh
    y += hh + GAP_Y * 0.7
    row_y = []
    for row in rows:
        rh = max(b.h for b in row)
        for b in row:
            b.y = y
        row_y.append((y, rh))
        y += rh + GAP_Y
    height = y - GAP_Y + MARGIN

    phases = [("Identification", row_y[0][0], row_y[0][0] + row_y[0][1]),
              ("Screening", row_y[1][0], row_y[3][0] + row_y[3][1]),
              ("Included", row_y[4][0], row_y[4][0] + row_y[4][1])]

    arrows = []
    m = [row[0] for row in rows]
    for a, b in zip(m, m[1:]):
        arrows.append([(a.x + a.w / 2, a.y + a.h), (b.x + b.w / 2, b.y)])
    for row in rows[:4]:
        a, b = row[0], row[1]
        mid = a.y + min(a.h, b.h) / 2
        arrows.append([(a.x + a.w, mid), (b.x, mid)])
    if o:
        oc = [rows[0][2], rows[2][2], rows[3][2]]
        for a, b in zip(oc, oc[1:]):
            arrows.append([(a.x + a.w / 2, a.y + a.h), (b.x + b.w / 2, b.y)])
        for row in rows[2:4]:
            a, b = row[2], row[3]
            mid = a.y + min(a.h, b.h) / 2
            arrows.append([(a.x + a.w, mid), (b.x, mid)])
        a, inc = rows[3][2], rows[4][0]
        ax = a.x + a.w / 2
        iy = inc.y + inc.h / 2
        arrows.append([(ax, a.y + a.h), (ax, iy), (inc.x + inc.w, iy)])

    boxes = head + [b for row in rows for b in row]
    return {"width": width, "height": height, "boxes": boxes, "arrows": arrows,
            "phases": phases}


# ---------- SVG ----------

def _f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def build_svg(layout: dict) -> str:
    w, h = layout["width"], layout["height"]
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(w)}pt" height="{_f(h)}pt" '
        f'viewBox="0 0 {_f(w)} {_f(h)}" font-family="Arial, Helvetica, sans-serif">',
        f'<rect x="0" y="0" width="{_f(w)}" height="{_f(h)}" fill="#FFFFFF"/>',
    ]
    for label, y0, y1 in layout["phases"]:
        x = MARGIN
        out.append(f'<rect x="{_f(x)}" y="{_f(y0)}" width="{_f(PHASE_W)}" height="{_f(y1 - y0)}" '
                   f'fill="{HEAD_FILL}" stroke="{LINE}" stroke-width="{LINE_W}"/>')
        cx, cy = x + PHASE_W / 2 + HEAD_PT * 0.35, (y0 + y1) / 2
        out.append(f'<text x="{_f(cx)}" y="{_f(cy)}" font-size="{_f(HEAD_PT)}" fill="{TEXT}" '
                   f'text-anchor="middle" transform="rotate(-90 {_f(cx)} {_f(cy)})">'
                   f'{escape(label)}</text>')
    for b in layout["boxes"]:
        fill = HEAD_FILL if b.head else "#FFFFFF"
        out.append(f'<rect x="{_f(b.x)}" y="{_f(b.y)}" width="{_f(b.w)}" height="{_f(b.h)}" '
                   f'fill="{fill}" stroke="{LINE}" stroke-width="{LINE_W}"/>')
        for i, (ind, line) in enumerate(b.lines):
            ty = b.y + PAD + b.size * 0.8 + i * b.size * LEAD
            if b.head:
                tx, anchor = b.x + b.w / 2, ' text-anchor="middle"'
            else:
                tx, anchor = b.x + PAD + ind, ""
            out.append(f'<text x="{_f(tx)}" y="{_f(ty)}" font-size="{_f(b.size)}" '
                       f'fill="{TEXT}"{anchor}>{escape(line)}</text>')
    for pts in layout["arrows"]:
        shaft, head = _arrow(pts)
        out.append('<polyline points="' + " ".join(f"{_f(x)},{_f(y)}" for x, y in shaft)
                   + f'" fill="none" stroke="{LINE}" stroke-width="{LINE_W}"/>')
        out.append('<polygon points="' + " ".join(f"{_f(x)},{_f(y)}" for x, y in head)
                   + f'" fill="{LINE}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _arrow(pts):
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / length, dy / length
    bx, by = x1 - ux * ARROW, y1 - uy * ARROW
    half = ARROW * 0.45
    head = [(x1, y1), (bx - uy * half, by + ux * half), (bx + uy * half, by - ux * half)]
    shaft = list(pts[:-1]) + [(bx, by)]
    return shaft, head


# ---------- PDF ----------

def _ttf_tables(data: bytes) -> Dict[str, bytes]:
    num = struct.unpack(">H", data[4:6])[0]
    tables = {}
    for i in range(num):
        tag, _, off, length = struct.unpack(">4sIII", data[12 + 16 * i: 28 + 16 * i])
        tables[tag.decode("latin-1")] = data[off: off + length]
    return tables


def _cmap4(cmap: bytes) -> Dict[int, int]:
    num = struct.unpack(">H", cmap[2:4])[0]
    for i in range(num):
        pid, eid, off = struct.unpack(">HHI", cmap[4 + 8 * i: 12 + 8 * i])
        if pid == 3 and eid == 1 and struct.unpack(">H", cmap[off: off + 2])[0] == 4:
            sub = cmap[off:]
            seg = struct.unpack(">H", sub[6:8])[0] // 2
            ends = struct.unpack(f">{seg}H", sub[14: 14 + 2 * seg])
            p = 16 + 2 * seg
            starts = struct.unpack(f">{seg}H", sub[p: p + 2 * seg])
            deltas = struct.unpack(f">{seg}h", sub[p + 2 * seg: p + 4 * seg])
            ro_pos = p + 4 * seg
            ros = struct.unpack(f">{seg}H", sub[ro_pos: ro_pos + 2 * seg])
            out = {}
            for s in range(seg):
                for code in range(starts[s], ends[s] + 1):
                    if code == 0xFFFF:
                        continue
                    if ros[s] == 0:
                        g = (code + deltas[s]) & 0xFFFF
                    else:
                        gp = ro_pos + 2 * s + ros[s] + 2 * (code - starts[s])
                        g = struct.unpack(">H", sub[gp: gp + 2])[0]
                        if g:
                            g = (g + deltas[s]) & 0xFFFF
                    out[code] = g
            return out
    raise ValueError("font has no Windows Unicode cmap")


def read_ttf(path: Path) -> dict:
    data = path.read_bytes()
    t = _ttf_tables(data)
    upem = struct.unpack(">H", t["head"][18:20])[0]
    bbox = struct.unpack(">hhhh", t["head"][36:44])
    asc, desc = struct.unpack(">hh", t["hhea"][4:8])
    nhm = struct.unpack(">H", t["hhea"][34:36])[0]
    adv = [struct.unpack(">H", t["hmtx"][4 * i: 4 * i + 2])[0] for i in range(nhm)]
    cmap = _cmap4(t["cmap"])
    cap = struct.unpack(">h", t["OS/2"][88:90])[0] if len(t["OS/2"]) >= 90 else asc
    widths = []
    for code in range(32, 256):
        uni = bytes([code]).decode("cp1252", errors="replace")
        g = cmap.get(ord(uni), 0)
        widths.append(round(adv[min(g, nhm - 1)] * 1000 / upem))
    s = 1000 / upem
    return {"data": data, "widths": widths, "bbox": [round(v * s) for v in bbox],
            "ascent": round(asc * s), "descent": round(desc * s), "cap": round(cap * s)}


def find_font(explicit: Optional[str]) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise FileNotFoundError(f"font not found: {explicit}")
        return p
    for cand in FONT_PATHS:
        if Path(cand).is_file():
            return Path(cand)
    return None


def _pdf_str(text: str) -> str:
    raw = text.encode("cp1252")
    return "(" + "".join(
        "\\" + chr(b) if chr(b) in "()\\" else (chr(b) if 32 <= b < 127 else f"\\{b:03o}")
        for b in raw) + ")"


def _rgb(hexcolor: str) -> str:
    return " ".join(_f(int(hexcolor[i: i + 2], 16) / 255) for i in (1, 3, 5))


def build_pdf(layout: dict, font: Optional[Path]) -> bytes:
    """One page. Embeds the TrueType file when given; else Helvetica, not embedded."""
    w, h = layout["width"], layout["height"]
    ops = [f"{LINE_W} w 0 J 0 j"]

    def Y(y: float) -> float:
        return h - y

    def rect(x, y, rw, rh, fill):
        ops.append(f"{_rgb(fill)} rg {_rgb(LINE)} RG {_f(x)} {_f(Y(y + rh))} {_f(rw)} {_f(rh)} re B")

    def text(x, y, size, s, anchor="start", rotate=False):
        tw = text_width(s, size)
        if rotate:
            ops.append(f"BT /F1 {_f(size)} Tf {_rgb(TEXT)} rg 0 1 -1 0 {_f(x)} "
                       f"{_f(Y(y) - tw / 2)} Tm {_pdf_str(s)} Tj ET")
            return
        if anchor == "middle":
            x -= tw / 2
        ops.append(f"BT /F1 {_f(size)} Tf {_rgb(TEXT)} rg {_f(x)} {_f(Y(y))} Td "
                   f"{_pdf_str(s)} Tj ET")

    for label, y0, y1 in layout["phases"]:
        rect(MARGIN, y0, PHASE_W, y1 - y0, HEAD_FILL)
        text(MARGIN + PHASE_W / 2 + HEAD_PT * 0.35, (y0 + y1) / 2, HEAD_PT, label, rotate=True)
    for b in layout["boxes"]:
        rect(b.x, b.y, b.w, b.h, HEAD_FILL if b.head else "#FFFFFF")
        for i, (ind, line) in enumerate(b.lines):
            ty = b.y + PAD + b.size * 0.8 + i * b.size * LEAD
            if b.head:
                text(b.x + b.w / 2, ty, b.size, line, "middle")
            else:
                text(b.x + PAD + ind, ty, b.size, line)
    for pts in layout["arrows"]:
        shaft, head = _arrow(pts)
        path = f"{_f(shaft[0][0])} {_f(Y(shaft[0][1]))} m " + " ".join(
            f"{_f(x)} {_f(Y(y))} l" for x, y in shaft[1:])
        ops.append(f"{_rgb(LINE)} RG {path} S")
        tri = f"{_f(head[0][0])} {_f(Y(head[0][1]))} m " + " ".join(
            f"{_f(x)} {_f(Y(y))} l" for x, y in head[1:])
        ops.append(f"{_rgb(LINE)} rg {tri} h f")
    content = zlib.compress("\n".join(ops).encode("latin-1"))

    objs: List[bytes] = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {_f(w)} {_f(h)}] "
                f"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>".encode())
    objs.append(f"<< /Length {len(content)} /Filter /FlateDecode >>\nstream\n".encode()
                + content + b"\nendstream")
    if font is None:
        objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                    b"/Encoding /WinAnsiEncoding >>")
    else:
        f = read_ttf(font)
        objs.append(("<< /Type /Font /Subtype /TrueType /BaseFont /ArialMT "
                     "/FirstChar 32 /LastChar 255 /Widths [" + " ".join(map(str, f["widths"]))
                     + "] /FontDescriptor 6 0 R /Encoding /WinAnsiEncoding >>").encode())
        objs.append((f"<< /Type /FontDescriptor /FontName /ArialMT /Flags 32 "
                     f"/FontBBox [{' '.join(map(str, f['bbox']))}] /ItalicAngle 0 "
                     f"/Ascent {f['ascent']} /Descent {f['descent']} /CapHeight {f['cap']} "
                     f"/StemV 80 /FontFile2 7 0 R >>").encode())
        packed = zlib.compress(f["data"])
        objs.append(f"<< /Length {len(packed)} /Length1 {len(f['data'])} "
                    f"/Filter /FlateDecode >>\nstream\n".encode() + packed + b"\nendstream")

    buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(buf))
        buf += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(buf)
    buf += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        buf += f"{off:010d} 00000 n \n".encode()
    buf += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
            ).encode()
    return bytes(buf)


# ---------- CLI ----------

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="PRISMA 2020 flow diagram (SVG + PDF).")
    ap.add_argument("counts", help="counts file (.json or .csv)")
    ap.add_argument("--out", required=True, help="output path stem; writes <stem>.svg and <stem>.pdf")
    ap.add_argument("--font", help="Arial TrueType file to embed in the PDF (default: search system paths)")
    ap.add_argument("--check", action="store_true", help="validate only; write nothing")
    args = ap.parse_args(argv)
    try:
        counts = load_counts(Path(args.counts))
    except CountsError as exc:
        for err in exc.errors:
            print(f"ERROR {err}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    if args.check:
        print("OK counts")
        return 0
    try:
        font = find_font(args.font)
    except FileNotFoundError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    if font is None:
        print("WARNING Arial not found; PDF uses Helvetica, not embedded", file=sys.stderr)
    layout = build_layout(counts)
    stem = Path(args.out)
    stem.parent.mkdir(parents=True, exist_ok=True)
    svg_path, pdf_path = stem.with_suffix(".svg"), stem.with_suffix(".pdf")
    svg_path.write_text(build_svg(layout), encoding="utf-8")
    pdf_path.write_bytes(build_pdf(layout, font))
    print(f"OK {svg_path} {pdf_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
