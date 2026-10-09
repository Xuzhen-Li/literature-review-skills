#!/usr/bin/env python3
"""Write the cover letter as a docx using the same path as the manuscript export.

The file is a small Office Open XML package so the letter is a word-processor
file even when pandoc is not installed. It does not log in or submit.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path
from typing import List, Optional, Sequence
from xml.sax.saxutils import escape

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""


def paragraphs(markdown: str) -> List[str]:
    blocks = []
    for block in re.split(r"\n\s*\n", markdown.strip()):
        line = re.sub(r"\s+", " ", block).strip()
        if line:
            blocks.append(line)
    return blocks


def document_xml(markdown: str) -> str:
    body = []
    for paragraph in paragraphs(markdown):
        body.append(
            "<w:p><w:r><w:t xml:space=\"preserve\">"
            + escape(paragraph)
            + "</w:t></w:r></w:p>"
        )
    if not body:
        body.append("<w:p><w:r><w:t></w:t></w:r></w:p>")
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
        "<w:body>"
        + "".join(body)
        + "</w:body></w:document>"
    )


def docx_bytes(markdown: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES)
        package.writestr("_rels/.rels", RELS)
        package.writestr("word/_rels/document.xml.rels", DOC_RELS)
        package.writestr("word/document.xml", document_xml(markdown))
    return buffer.getvalue()


def docx_plain_text(data: bytes) -> Optional[str]:
    """Return the visible text of a docx, or None when the bytes are not one."""
    if not data.startswith(b"PK"):
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            xml = package.read("word/document.xml").decode("utf-8")
    except (KeyError, zipfile.BadZipFile, UnicodeDecodeError):
        return None
    parts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)
    return unescape_xml("".join(parts))


def unescape_xml(text: str) -> str:
    return (
        text.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&amp;", "&")
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    data = docx_bytes(args.markdown.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    if docx_plain_text(data) is None:
        print("ERROR cover letter docx could not be read back", file=sys.stderr)
        return 1
    print("OK cover letter")
    return 0


if __name__ == "__main__":
    sys.exit(main())
