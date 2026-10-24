#!/usr/bin/env python3
"""Check a review .docx before delivery: citation fields, bibliography, numbering.

FAIL (exit 1) on: unbalanced field codes; Zotero CSL_CITATION with unparseable
JSON; duplicate citationID; more than one CSL_BIBLIOGRAPHY; HTML escapes or tags
(&amp; &lt; <i> ...) shown in bibliography text; and, with --baseline, any loss
of Zotero citations, the Zotero bibliography, EndNote EN.CITE fields, or the
EndNote EN.REFLIST, or more plain-text (flattened) citations than the original.
WARN (exit 0) on: plain-text citations outside fields; placeholders (XXX, TODO,
[NEEDS SOURCE], [VERIFY], ??); figure/table references without a caption,
captions never referenced, or first mentions out of order.
Exit 2 on unreadable input. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional, Sequence

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PARTS = re.compile(r"^word/(document|footnotes|endnotes|header\d*|footer\d*)\.xml$")
PLAIN_CITE = re.compile(
    r"\((?:[A-Z][A-Za-z'\-]+(?: et al\.?| and [A-Z][A-Za-z'\-]+)?,? (?:19|20)\d{2}[a-z]?"
    r"(?:; ?)?)+\)|\[\d+(?:[,\u2013\-]\s?\d+)*\]")
PLACEHOLDER = re.compile(r"\bXXX+\b|\bTODO\b|\bTBD\b|\[NEEDS SOURCE\]|\[VERIFY\]|\?\?")
HTML_ESC = re.compile(r"&(?:amp|lt|gt|quot|#\d+);|</?(?:i|b|sup|sub|span|div)\b[^>]*>")
REF = re.compile(r"\b(Fig(?:ure)?s?\.?|Tables?)\s+(S?\d+)", re.I)
CAPTION = re.compile(r"^\s*(Fig(?:ure)?\.?|Table)\s+(S?\d+)[.:\s]", re.I)


def _kind(word: str) -> str:
    return "table" if word.lower().startswith("tab") else "figure"


def _classify(instr: str) -> str:
    t = instr.strip()
    if "CSL_CITATION" in t:
        return "zotero"
    if "CSL_BIBLIOGRAPHY" in t:
        return "zbib"
    if t.startswith("ADDIN EN.CITE"):
        return "encite"
    if t.startswith("ADDIN EN.REFLIST"):
        return "enref"
    return "other"


def scan(path: str) -> dict:
    r = {"begin": 0, "separate": 0, "end": 0, "balanced": True, "citations": [],
         "bad_json": 0, "zbib": 0, "encite": 0, "enref": 0, "bib_text": "",
         "plain_cites": [], "placeholders": [], "paras": []}
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if PARTS.match(n)]
        if "word/document.xml" not in names:
            raise ValueError("not a Word document (no word/document.xml)")
        for name in sorted(names, key=lambda n: n != "word/document.xml"):
            root = ET.fromstring(zf.read(name))
            stack: list[dict] = []  # open fields: {"instr": [...], "kind": str|None}
            for p in root.iter(W + "p"):
                plain, bib = [], []
                for el in p.iter():
                    tag = el.tag
                    if tag == W + "fldChar":
                        typ = el.get(W + "fldCharType")
                        if typ in ("begin", "separate", "end"):
                            r[typ] += 1
                        if typ == "begin":
                            stack.append({"instr": [], "kind": None})
                        elif typ == "separate" and stack:
                            _close_instr(stack[-1], r)
                        elif typ == "end":
                            if not stack:
                                r["balanced"] = False
                                continue
                            f = stack.pop()
                            if f["kind"] is None:
                                _close_instr(f, r)
                    elif tag == W + "instrText" and stack and stack[-1]["kind"] is None:
                        stack[-1]["instr"].append(el.text or "")
                    elif tag == W + "fldSimple":
                        f = {"instr": [el.get(W + "instr") or ""], "kind": None}
                        _close_instr(f, r)
                    elif tag == W + "t":
                        txt = el.text or ""
                        kinds = {f["kind"] for f in stack}
                        if kinds & {"zbib", "enref"}:
                            bib.append(txt)
                        elif not kinds & {"zotero", "encite"}:
                            plain.append(txt)
                text = "".join(plain)
                r["bib_text"] += "".join(bib) + "\n" if bib else ""
                if name == "word/document.xml":
                    r["paras"].append(text)
                r["plain_cites"] += PLAIN_CITE.findall(text)
                r["placeholders"] += PLACEHOLDER.findall(text + "".join(bib))
            for f in stack:
                if f["kind"] is None:
                    _close_instr(f, r)
            if stack:
                r["balanced"] = False
    return r


def _close_instr(f: dict, r: dict) -> None:
    instr = "".join(f["instr"])
    f["kind"] = k = _classify(instr)
    if k == "zotero":
        payload = instr.split("CSL_CITATION", 1)[1].strip()
        try:
            r["citations"].append(str(json.loads(payload).get("citationID", "")))
        except ValueError:
            r["bad_json"] += 1
            r["citations"].append("")
    elif k in ("zbib", "encite", "enref"):
        r[k] += 1


def numbering(paras: list[str]) -> list[str]:
    caps, refs, order = {}, set(), []
    for t in paras:
        m = CAPTION.match(t)
        if m:
            caps[(_kind(m.group(1)), m.group(2).upper())] = True
            body = t[m.end():]
        else:
            body = t
        for w, n in REF.findall(body):
            key = (_kind(w), n.upper())
            refs.add(key)
            if key not in order:
                order.append(key)
    out = []
    for k in sorted(refs - set(caps)):
        out.append(f"{k[0]} {k[1]} is cited in text but has no caption")
    for k in sorted(set(caps) - refs):
        out.append(f"{k[0]} {k[1]} has a caption but is never cited in text")
    for kind in ("figure", "table"):
        seq = [int(n) for kd, n in order if kd == kind and n.isdigit()]
        if seq != sorted(seq):
            out.append(f"{kind}s first cited out of order: {seq}")
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("docx")
    ap.add_argument("--baseline", help="original .docx to compare against")
    args = ap.parse_args(argv)
    try:
        cur = scan(args.docx)
        base = scan(args.baseline) if args.baseline else None
    except (OSError, zipfile.BadZipFile, ValueError, ET.ParseError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    fails, warns = [], []
    if not (cur["balanced"] and cur["begin"] == cur["end"] and cur["separate"] <= cur["begin"]):
        fails.append(f"unbalanced fields: begin={cur['begin']} separate={cur['separate']} end={cur['end']}")
    if cur["bad_json"]:
        fails.append(f"{cur['bad_json']} CSL_CITATION field(s) with unparseable JSON")
    ids = [i for i in cur["citations"] if i]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        fails.append("duplicate citationID: " + ", ".join(dups))
    if cur["zbib"] > 1:
        fails.append(f"{cur['zbib']} CSL_BIBLIOGRAPHY fields (expected 0 or 1)")
    esc = sorted(set(HTML_ESC.findall(cur["bib_text"])))
    if esc:
        fails.append("HTML escapes/tags visible in bibliography: " + " ".join(esc))
    if base is not None:
        for key, label in (("citations", "Zotero citation fields"), ("encite", "EndNote EN.CITE fields")):
            a = len(base[key]) if key == "citations" else base[key]
            b = len(cur[key]) if key == "citations" else cur[key]
            if b < a:
                fails.append(f"{label} lost: original {a}, now {b}")
        for key, label in (("zbib", "Zotero CSL_BIBLIOGRAPHY"), ("enref", "EndNote EN.REFLIST")):
            if base[key] and not cur[key]:
                fails.append(f"{label} field lost")
        if len(cur["plain_cites"]) > len(base["plain_cites"]):
            fails.append(f"citations flattened to plain text: original {len(base['plain_cites'])}, "
                         f"now {len(cur['plain_cites'])} ({'; '.join(cur['plain_cites'][:5])})")
    elif cur["plain_cites"]:
        warns.append(f"{len(cur['plain_cites'])} plain-text citation(s) outside fields: "
                     + "; ".join(cur["plain_cites"][:5]))
    if cur["placeholders"]:
        warns.append("placeholders: " + ", ".join(sorted(set(cur["placeholders"]))))
    warns += numbering(cur["paras"])
    print(f"zotero_citations={len(cur['citations'])} zotero_bibliography={cur['zbib']} "
          f"endnote_cites={cur['encite']} endnote_reflist={cur['enref']} "
          f"plain_text_cites={len(cur['plain_cites'])} "
          f"fields begin/separate/end={cur['begin']}/{cur['separate']}/{cur['end']}")
    for w in warns:
        print("WARN " + w)
    for f in fails:
        print("FAIL " + f)
    if not fails:
        print("OK citation fields")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
