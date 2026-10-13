"""Tests for export_refs.py (BibTeX + CSL-JSON). Offline only."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE.parents[0] / "scripts" / "export_refs.py"
SCHEMA = HERE / "fixtures" / "csl-data.schema.json"

LIBRARY = (
    "record_id,title,year,authors,journal,doi,pmid,abstract\n"
    'R1,Nanometre-scale thermometry in a living cell,2013,"Kucsko, G.; Maurer, P. C.; Yao, N. Y.",Nature,'
    "https://doi.org/10.1038/NATURE12373,23903748,We measure 50% & more.\n"
    'R2,"Costs & benefits of {braces}: a_test",2020,"Lovelace, Ada",J. Hist. Comp.,,,\n'
    'R3,Second Lovelace paper,2020,"Lovelace, Ada; Babbage C",J. Hist. Comp.,10.1/x,,\n'
    "R4,,2021,Nobody,J,,,\n"
    'R5,Müller study,2019,"Müller A; World Health Organization Consortium",Lancet,,,\n'
)

INCLUDED = (
    "record_id\tdoi\tpmid\ttitle\tyear\tfirst_author\tn_authors\tvenue\tcitation_key\n"
    "R1\t10.1038/nature12373\t23903748\tNanometre-scale thermometry in a living cell\t2013\tKucsko\t3\tNature\tKucsko2013\n"
    "R9\t\t\tSolo paper\t2018\tSolo\t1\tJ\tSolo2018\n"
    "R8\t\t\tTeam paper\t2017\tTeam\t4\tJ\tTeam2017\n"
)


@pytest.fixture(scope="module")
def er():
    spec = importlib.util.spec_from_file_location("lrs_export_refs", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_bib(text):
    """Minimal BibTeX reader for round-trip checks (one level of braces)."""
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),\n(.*?)\n\}", text, re.S):
        fields = {}
        for f in re.finditer(r"^  (\w+) = \{(.*)\},?$", m.group(3), re.M):
            fields[f.group(1)] = f.group(2)
        entries[m.group(2)] = (m.group(1), fields)
    return entries


def unescape(s):
    return (s.replace(r"\textbackslash{}", "\\").replace(r"\textasciitilde{}", "~")
             .replace(r"\textasciicircum{}", "^")
             .replace("\\{", "{").replace("\\}", "}").replace("\\&", "&").replace("\\%", "%")
             .replace("\\$", "$").replace("\\#", "#").replace("\\_", "_"))


@pytest.fixture
def library_csv(tmp_path):
    p = tmp_path / "library.csv"
    p.write_text(LIBRARY, encoding="utf-8")
    return p


def test_name_parsing(er):
    assert er.parse_name("Kucsko, G.") == {"family": "Kucsko", "given": "G."}
    assert er.parse_name("Babbage C") == {"family": "Babbage", "given": "C."}
    assert er.parse_name("Maurer PC") == {"family": "Maurer", "given": "P. C."}
    assert er.parse_name("World Health Organization Consortium") == {"literal": "World Health Organization Consortium"}


def test_keys_follow_family_year_with_suffix(er, library_csv):
    recs, skipped = er.build_records(er.read_table(library_csv))
    assert [r["citation_key"] for r in recs] == ["Kucsko2013", "Lovelace2020", "Lovelace2020a", "Muller2019"]
    assert skipped == ["R4"]


def test_bibtex_round_trip(er, library_csv):
    recs, _ = er.build_records(er.read_table(library_csv))
    bib = parse_bib(er.to_bibtex(recs, with_abstract=True))
    assert set(bib) == {"Kucsko2013", "Lovelace2020", "Lovelace2020a", "Muller2019"}
    typ, k = bib["Kucsko2013"]
    assert typ == "article"
    assert k["author"] == "Kucsko, G. and Maurer, P. C. and Yao, N. Y."
    assert k["doi"] == "10.1038/nature12373" and k["pmid"] == "23903748" and k["year"] == "2013"
    assert unescape(k["abstract"]) == "We measure 50% & more."
    t = bib["Lovelace2020"][1]["title"]
    assert "\\&" in t and "\\_" in t and "\\{" in t
    assert unescape(t) == "Costs & benefits of {braces}: a_test"
    assert bib["Muller2019"][1]["author"] == "Müller, A. and {World Health Organization Consortium}"


def test_bibtex_braces_balanced(er, library_csv):
    recs, _ = er.build_records(er.read_table(library_csv))
    text = er.to_bibtex(recs, with_abstract=True)
    stripped = text.replace("\\{", "").replace("\\}", "")
    assert stripped.count("{") == stripped.count("}")


def test_csl_matches_schema_and_values(er, library_csv):
    jsonschema = pytest.importorskip("jsonschema")
    recs, _ = er.build_records(er.read_table(library_csv))
    items = er.to_csl(recs, with_abstract=True)
    jsonschema.validate(items, json.loads(SCHEMA.read_text()))
    first = items[0]
    assert first["id"] == first["citation-key"] == "Kucsko2013"
    assert first["type"] == "article-journal"
    assert first["issued"] == {"date-parts": [[2013]]}
    assert first["DOI"] == "10.1038/nature12373" and first["PMID"] == "23903748"
    assert first["author"][1] == {"family": "Maurer", "given": "P. C."}
    assert "DOI" not in items[1]  # empty fields omitted, never invented


def test_csl_round_trip_through_json(er, library_csv):
    recs, _ = er.build_records(er.read_table(library_csv))
    items = er.to_csl(recs)
    back = json.loads(json.dumps(items, ensure_ascii=False))
    assert back == items
    assert all("abstract" not in i for i in items)


def test_included_tsv_keeps_keys_and_uses_library(er, tmp_path, library_csv, capsys):
    inc = tmp_path / "included.tsv"
    inc.write_text(INCLUDED, encoding="utf-8")
    assert er.main([str(inc), "--library", str(library_csv)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["exported"] == 3 and report["authors_incomplete"] == ["Team2017"]
    bib = parse_bib((tmp_path / "refs.bib").read_text())
    assert bib["Kucsko2013"][1]["author"].startswith("Kucsko, G. and Maurer")
    assert bib["Kucsko2013"][1]["journal"] == "Nature"
    assert bib["Solo2018"][1]["author"] == "Solo"
    assert bib["Team2017"][1]["author"] == "Team and others"
    items = json.loads((tmp_path / "refs.json").read_text())
    assert [i["id"] for i in items] == ["Kucsko2013", "Solo2018", "Team2017"]


def test_duplicate_explicit_keys_fail(er, tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("citation_key,title,year\nA2020,One,2020\nA2020,Two,2020\n")
    with pytest.raises(SystemExit):
        er.build_records(er.read_table(p))


def test_no_author_no_year_key(er, tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("record_id,title\nR1,Untitled report\n")
    recs, _ = er.build_records(er.read_table(p))
    assert recs[0]["citation_key"] == "Anonnd"
    assert "author" not in er.to_csl(recs)[0]


def test_quoted_multiline_abstract(er, tmp_path):
    lib = tmp_path / "library.csv"
    lib.write_text('record_id,title,year,authors,abstract\nR1,T,2020,"Doe, J","First line,\nsecond line."\nR2,U,2021,"Roe, K",x\n',
                   encoding="utf-8")
    rows = er.read_table(lib)
    assert [r["record_id"] for r in rows] == ["R1", "R2"]
    assert rows[0]["abstract"] == "First line,\nsecond line."
