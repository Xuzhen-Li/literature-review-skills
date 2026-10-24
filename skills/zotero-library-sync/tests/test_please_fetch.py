import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import please_fetch as pf  # noqa: E402

STATUS = [
    {"record_id": "R1", "doi": "10.1000/a", "title": "Have it", "local_path": "04-library/pdfs/R1.pdf"},
    {"record_id": "R2", "doi": "https://doi.org/10.1000/B", "title": "Key trial", "local_path": ""},
    {"record_id": "R3", "doi": "10.1000/c", "title": "Background", "local_path": ""},
    {"record_id": "R4", "doi": "10.1000/d", "title": "Main cohort", "local_path": ""},
    {"record_id": "R5", "doi": "10.1000/e", "title": "Uploaded", "local_path": ""},
]
NEED = [
    {"record_id": "R2", "doi": "10.1000/b", "need": "essential", "why": "only RCT of the main exposure", "rank": "2"},
    {"record_id": "R3", "doi": "10.1000/c", "need": "abstract_ok", "why": "background", "rank": ""},
    {"record_id": "R4", "doi": "10.1000/d", "need": "Essential", "why": "largest cohort; effect sizes", "rank": "1"},
    {"record_id": "R5", "doi": "10.1000/e", "need": "essential", "why": "x", "rank": "3"},
]


def test_only_essential_missing_ranked(tmp_path):
    up = tmp_path / "uploads"
    up.mkdir()
    (up / "R5.pdf").write_bytes(b"%PDF-1.4")
    fetch, abstract, untriaged, over = pf.build(STATUS, NEED, up, 15)
    assert [r["record_id"] for r in fetch] == ["R4", "R2"]
    assert fetch[1]["doi"] == "10.1000/b" and fetch[0]["save_as"] == "04-library/uploads/R4.pdf"
    assert [r["record_id"] for r in abstract] == ["R3"] and not untriaged and not over


def test_cap_moves_overflow_to_abstract_only():
    fetch, abstract, _, over = pf.build(STATUS, NEED, None, 1)
    assert [r["record_id"] for r in fetch] == ["R4"]
    assert {r["record_id"] for r in over} == {"R2", "R5"}
    assert {r["need"] for r in abstract if r["record_id"] != "R3"} == {"essential_over_cap"}


def test_doi_match_without_record_id():
    st = [{"doi": "10.1000/X", "title": "t", "local_path": ""}]
    nd = [{"doi": "https://doi.org/10.1000/x", "need": "essential", "why": "w", "rank": "1"}]
    fetch, *_ = pf.build(st, nd, None, 5)
    assert fetch[0]["doi"] == "10.1000/x"


@pytest.mark.parametrize("bad", [{"need": "maybe"}, {"rank": "high"}, {"why": ""}])
def test_bad_triage_rejected(bad):
    nd = [{**NEED[1], "record_id": "R4", "need": "essential", "why": "w", "rank": "1", **bad}]
    with pytest.raises(ValueError):
        pf.build([STATUS[3]], nd, None, 5)


def _write(path, rows):
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def test_main_untriaged_exit_2(tmp_path, capsys):
    s, n = tmp_path / "s.tsv", tmp_path / "n.tsv"
    _write(s, STATUS)
    _write(n, NEED[:2])
    assert pf.main(["--status", str(s), "--need", str(n), "--out-dir", str(tmp_path / "o")]) == 2
    assert "R4" in capsys.readouterr().err and not (tmp_path / "o").exists()


def test_main_writes_md(tmp_path):
    s, n, o = tmp_path / "s.tsv", tmp_path / "n.tsv", tmp_path / "o"
    _write(s, STATUS)
    _write(n, NEED)
    assert pf.main(["--status", str(s), "--need", str(n), "--out-dir", str(o)]) == 0
    md = (o / "please_fetch.md").read_text()
    assert md.index("10.1000/d") < md.index("10.1000/b")
    assert "Why: largest cohort; effect sizes" in md and "10.1000/c" not in md
    rows = list(csv.DictReader((o / "please_fetch.tsv").open(), delimiter="\t"))
    assert [r["priority"] for r in rows] == ["1", "2", "3"]


def test_nothing_to_fetch_message():
    assert "Nothing to fetch" in pf.render_md([], 0)


def test_intro_count_is_substituted():
    fetch, _, _, _ = pf.build(STATUS, NEED, None, 15)
    md = pf.render_md(fetch, 0)
    assert f"I could not get these {len(fetch)} papers" in md
    assert "{len" not in md and "{" not in md.split("\n")[2]


def test_useful_with_why_is_not_handed_to_user():
    status = STATUS + [{"record_id": "R6", "doi": "10.1000/f", "title": "Nice to have", "local_path": ""}]
    need = NEED + [{"record_id": "R6", "doi": "10.1000/f", "need": "useful",
                    "why": "extra detail on methods", "rank": "1"}]
    fetch, abstract, _, _ = pf.build(status, need, None, 15)
    assert "R6" not in {r["record_id"] for r in fetch}
    assert [r["need"] for r in abstract if r["record_id"] == "R6"] == ["useful"]


def test_html_saved_as_pdf_in_uploads_does_not_count(tmp_path):
    up = tmp_path / "uploads"
    up.mkdir()
    (up / "R5.pdf").write_bytes(b"<!DOCTYPE html><html>Sign in</html>")
    fetch, _, _, _ = pf.build(STATUS, NEED, up, 15)
    assert "R5" in {r["record_id"] for r in fetch}


def test_plain_doi_rows_get_a_real_upload_name(tmp_path):
    status = [{"doi": "10.1000/Weird(1)/x", "title": "No id", "local_path": ""}]
    need = [{"doi": "10.1000/weird(1)/x", "need": "essential", "why": "core", "rank": "1"}]
    fetch, _, _, _ = pf.build(status, need, None, 15)
    save_as = fetch[0]["save_as"]
    assert "<" not in save_as and save_as.startswith("04-library/uploads/10.1000_weird_1_x-")
    assert save_as.endswith(".pdf")
    stem = Path(save_as).stem
    assert stem == pf.upload_stem("", "https://doi.org/10.1000/WEIRD(1)/x")
    up = tmp_path / "uploads"
    up.mkdir()
    (up / f"{stem}.pdf").write_bytes(b"%PDF-1.7")
    assert pf.build(status, need, up, 15)[0] == []
