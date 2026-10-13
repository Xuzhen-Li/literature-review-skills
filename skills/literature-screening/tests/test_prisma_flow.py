"""Tests for the PRISMA 2020 flow diagram script."""

import copy
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "references" / "prisma_flow_examples"
spec = importlib.util.spec_from_file_location("lrs_prisma_flow", ROOT / "scripts" / "prisma_flow.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)


@pytest.fixture()
def raw():
    return json.loads((EXAMPLES / "counts_example.json").read_text())


def errors_of(raw):
    with pytest.raises(pf.CountsError) as exc:
        pf.normalize(raw)
    return exc.value.errors


def test_example_json_and_csv_load():
    j = pf.load_counts(EXAMPLES / "counts_example.json")
    c = pf.load_counts(EXAMPLES / "counts_example.csv")
    assert j["other"]["reports_included"] == 7
    assert "other" not in c
    assert c["excluded_reasons"]["Wrong population"] == 21
    assert c["screened"] == j["screened"] == 1362


def test_optional_keys_default_to_zero(raw):
    del raw["registers"], raw["automation_removed"], raw["other"]
    raw["databases"] += 36
    raw["reports_included"] = 37
    raw["studies_included"] = 34
    c = pf.normalize(raw)
    assert c["registers"] == 0 and c["automation_removed"] == 0


def test_csv_reason_and_other_prefixes():
    raw = pf.parse_csv("key,value\ndatabases,5\nexcluded_reason:A,2\nother.websites,3\n"
                       "other.excluded_reason:B,1\n")
    assert raw == {"databases": "5", "excluded_reasons": {"A": "2"},
                   "other": {"websites": "3", "excluded_reasons": {"B": "1"}}}


def test_csv_duplicate_and_bad_rows():
    with pytest.raises(pf.CountsError) as exc:
        pf.parse_csv("databases,5\ndatabases,6\nscreened,1,2\n")
    msgs = "\n".join(exc.value.errors)
    assert "duplicate key 'databases'" in msgs and "expected 2 columns" in msgs


def test_negative_and_non_integer(raw):
    raw["not_retrieved"] = -1
    raw["sought"] = "many"
    raw["assessed"] = 1.5
    msgs = "\n".join(errors_of(raw))
    assert "not_retrieved: negative count -1" in msgs
    assert "sought: not an integer" in msgs
    assert "assessed: not an integer" in msgs


def test_missing_and_unknown_keys(raw):
    del raw["screened"]
    raw["screend"] = 3
    msgs = errors_of(raw)
    assert "screened: missing" in msgs and "screend: unknown key" in msgs


@pytest.mark.parametrize("key,delta,label", [
    ("screened", 1, "screened:"),
    ("sought", 1, "sought:"),
    ("assessed", -1, "assessed:"),
    ("reports_included", 1, "reports_included:"),
])
def test_arithmetic_errors(raw, key, delta, label):
    raw[key] += delta
    assert any(e.startswith(label) for e in errors_of(raw))


def test_other_arm_arithmetic(raw):
    raw["other"]["assessed"] = 15
    msgs = "\n".join(errors_of(raw))
    assert "other.assessed: expected" in msgs
    raw2 = copy.deepcopy(raw)
    raw2["other"]["assessed"] = 16
    raw2["other"]["sought"] = 99
    raw2["other"]["assessed"] = 97
    assert any("other.sought" in e for e in errors_of(raw2))


def test_studies_exceed_reports(raw):
    raw["studies_included"] = 45
    assert any(e.startswith("studies_included") for e in errors_of(raw))


def test_reason_label_outside_cp1252(raw):
    raw["excluded_reasons"] = {"\u975e\u82f1\u6587": 48, "No relevant outcome": 39,
                               "Wrong population": 21, "Duplicate report of same study": 6}
    assert any("Windows-1252" in e for e in errors_of(raw))


def test_wrap_keeps_counts_together():
    lines = pf.wrap("Wrong study design " + pf.n(48), 7, 92)
    assert all("(n" not in t or "48)" in t for _, t in lines)


def test_render_smoke(tmp_path):
    out = tmp_path / "flow"
    assert pf.main([str(EXAMPLES / "counts_example.json"), "--out", str(out)]) == 0
    svg = ET.parse(out.with_suffix(".svg")).getroot()
    texts = "".join(t.text or "" for t in svg.iter("{http://www.w3.org/2000/svg}text"))
    assert "Records screened (n = 1362)" in texts
    assert "Identification of studies via other methods" in texts
    widths = {r.get("stroke-width") for r in svg.iter("{http://www.w3.org/2000/svg}rect")
              if r.get("stroke")}
    assert widths == {"0.5"}
    pdf = out.with_suffix(".pdf").read_bytes()
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")


def test_pdf_embeds_arial_when_available(tmp_path):
    font = pf.find_font(None)
    if font is None:
        pytest.skip("Arial not installed")
    layout = pf.build_layout(pf.load_counts(EXAMPLES / "counts_example.csv"))
    pdf = pf.build_pdf(layout, font)
    assert b"/FontFile2" in pdf and b"/ArialMT" in pdf


def test_pdf_fallback_without_font():
    layout = pf.build_layout(pf.load_counts(EXAMPLES / "counts_example.csv"))
    pdf = pf.build_pdf(layout, None)
    assert b"/Helvetica" in pdf and b"/FontFile2" not in pdf


def test_check_mode_and_error_exit(tmp_path, capsys):
    assert pf.main([str(EXAMPLES / "counts_example.csv"), "--out", str(tmp_path / "x"),
                    "--check"]) == 0
    assert not (tmp_path / "x.svg").exists()
    bad = tmp_path / "bad.json"
    bad.write_text('{"databases": -3}')
    assert pf.main([str(bad), "--out", str(tmp_path / "y")]) == 2
    assert "ERROR databases: negative count -3" in capsys.readouterr().err
    assert not (tmp_path / "y.svg").exists()


def test_other_identified_must_equal_sought(raw):
    raw["other"]["citation_searching"] += 1
    msgs = errors_of(raw)
    assert any(e.startswith("other.sought: expected") for e in msgs)


def test_studies_equal_reports_allowed(raw):
    raw["studies_included"] = raw["reports_included"]
    assert pf.normalize(raw)["studies_included"] == 44


def test_reason_lines_fit_on_one_line():
    counts = pf.load_counts(EXAMPLES / "counts_example.json")
    counts["excluded_reasons"]["A much longer exclusion reason label"] = 0
    layout = pf.build_layout(counts)
    excl = [b for b in layout["boxes"] if b.lines and b.lines[0][1] == "Reports excluded:"]
    assert excl
    for b in excl:
        assert all("(n = " in t for _, t in b.lines[1:])


def test_caption_and_label(tmp_path):
    out = tmp_path / "flow"
    assert pf.main([str(EXAMPLES / "counts_example.csv"), "--out", str(out),
                    "--label", "Example data"]) == 0
    svg = out.with_suffix(".svg").read_text()
    assert "Adapted from the PRISMA 2020" in svg and "doi:10.1136/bmj.n71" in svg and "Example data" in svg
    assert pf.main([str(EXAMPLES / "counts_example.csv"), "--out", str(out),
                    "--no-caption"]) == 0
    assert "Adapted from" not in out.with_suffix(".svg").read_text()
