"""Tests for verify_docx_fields.py. Also exports cite()/add_field() for fixtures."""
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import verify_docx_fields as v  # noqa: E402

NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def cite(cid, item=1, author="Smith", year=2020):
    """Instruction text of a Zotero citation field."""
    data = {"citationID": cid, "properties": {"formattedCitation": f"({author} et al., {year})"},
            "citationItems": [{"id": item, "itemData": {"id": item, "type": "article-journal",
                                                         "author": [{"family": author}],
                                                         "issued": {"date-parts": [[year]]}}}],
            "schema": "https://github.com/citation-style-language/schema/raw/master/csl-citation.json"}
    return " ADDIN ZOTERO_ITEM CSL_CITATION " + json.dumps(data) + " "


def add_field(paragraph, instr, display):
    """Append a complex field (begin/instr/separate/result/end) to a python-docx paragraph."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    def run_with(child):
        r = OxmlElement("w:r")
        r.append(child)
        paragraph._p.append(r)

    def char(t):
        c = OxmlElement("w:fldChar")
        c.set(qn("w:fldCharType"), t)
        return c
    run_with(char("begin"))
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    run_with(it)
    run_with(char("separate"))
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = display
    run_with(t)
    run_with(char("end"))


def xfield(instr, display):
    from xml.sax.saxutils import escape
    return (f'<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve">{escape(instr)}</w:instrText></w:r>'
            f'<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>{escape(display)}</w:t></w:r>'
            f'<w:r><w:fldChar w:fldCharType="end"/></w:r>')


def t(text):
    from xml.sax.saxutils import escape
    return f"<w:r><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"


BIB = xfield(' ADDIN ZOTERO_BIBL {} CSL_BIBLIOGRAPHY ', "Smith, A. (2020) Soil. J. 1, 1-2.")


def make(tmp, name, *paras):
    p = tmp / name
    body = "".join(f"<w:p>{x}</w:p>" for x in paras)
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("word/document.xml", f'<w:document {NS}><w:body>{body}</w:body></w:document>')
    return p


def good(tmp, name="o.docx"):
    return make(tmp, name, t("Cd rose (Fig. 1) ") + xfield(cite("x1"), "(Smith et al., 2020)")
                + xfield(cite("x2", 2, "Lee"), "(Lee et al., 2020)"),
                t("Figure 1. Overview."), BIB)


def test_ok(tmp_path, capsys):
    p = good(tmp_path)
    assert v.main([str(p), "--baseline", str(p)]) == 0
    out = capsys.readouterr().out
    assert "OK citation fields" in out and "WARN" not in out


def test_duplicate_id(tmp_path, capsys):
    p = make(tmp_path, "a.docx", xfield(cite("x1"), "(A)") + xfield(cite("x1"), "(A)"))
    assert v.main([str(p)]) == 1
    assert "duplicate citationID" in capsys.readouterr().out


def test_lost_and_flattened(tmp_path, capsys):
    base = good(tmp_path)
    new = make(tmp_path, "n.docx", t("Cd rose (Fig. 1) ") + xfield(cite("x1"), "(Smith et al., 2020)")
               + t(" (Lee et al., 2020)"), t("Figure 1. Overview."))
    assert v.main([str(new), "--baseline", str(base)]) == 1
    out = capsys.readouterr().out
    assert "Zotero citation fields lost" in out
    assert "CSL_BIBLIOGRAPHY field lost" in out
    assert "flattened to plain text" in out


def test_unbalanced_and_bad_json(tmp_path, capsys):
    body = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:instrText> ADDIN ZOTERO_ITEM CSL_CITATION {broken</w:instrText></w:r>')
    p = make(tmp_path, "a.docx", body)
    assert v.main([str(p)]) == 1
    out = capsys.readouterr().out
    assert "unbalanced" in out and "unparseable" in out


def test_html_escape_in_bibliography(tmp_path, capsys):
    p = make(tmp_path, "a.docx", xfield(' ADDIN ZOTERO_BIBL {} CSL_BIBLIOGRAPHY ',
                                        "Smith &amp; Lee (2020) <i>Soil</i>."))
    assert v.main([str(p)]) == 1
    assert "HTML escapes" in capsys.readouterr().out


def test_endnote_counts(tmp_path, capsys):
    en = xfield(" ADDIN EN.CITE <EndNote><Cite/></EndNote>", "[1]")
    ref = xfield(" ADDIN EN.REFLIST ", "1. Smith A. Soil. 2020.")
    base = make(tmp_path, "o.docx", en + en, ref)
    new = make(tmp_path, "n.docx", en)
    assert v.main([str(base)]) == 0
    capsys.readouterr()
    assert v.main([str(new), "--baseline", str(base)]) == 1
    out = capsys.readouterr().out
    assert "EndNote EN.CITE fields lost: original 2, now 1" in out and "EN.REFLIST field lost" in out


def test_warnings_placeholders_and_numbering(tmp_path, capsys):
    p = make(tmp_path, "a.docx", t("See Table 2 and Fig. 3, then Fig. 1. Funding: XXX [VERIFY]"),
             t("Figure 1. A."), t("Figure 2. B."), t("Table 2: C."))
    assert v.main([str(p)]) == 0
    out = capsys.readouterr().out
    assert "placeholders: XXX, [VERIFY]" in out
    assert "figure 3 is cited in text but has no caption" in out
    assert "figure 2 has a caption but is never cited" in out
    assert "figures first cited out of order: [3, 1]" in out


def test_not_docx(tmp_path):
    p = tmp_path / "x.docx"
    p.write_text("nope")
    assert v.main([str(p)]) == 2
