"""Tests for RIS, NBIB, and CSV deduplication."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "dedup.py"


def load_dedup():
    spec = importlib.util.spec_from_file_location("lrs_dedup", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def dedup():
    return load_dedup()


def test_normalize_doi_case_and_url_prefix(dedup):
    expected = "10.1000/abc.def"
    assert dedup.normalize_doi("HTTPS://DOI.ORG/10.1000/ABC.DEF") == expected
    assert dedup.normalize_doi("https://dx.doi.org/10.1000/ABC.DEF") == expected
    assert dedup.normalize_doi("doi:10.1000/ABC.DEF") == expected
    assert dedup.normalize_doi("  10.1000/ABC.DEF. ") == expected
    assert dedup.normalize_doi("10.1000/xyz [doi]") == "10.1000/xyz"
    assert dedup.normalize_doi("12345 [pii]") == ""


def test_normalize_title_punctuation(dedup):
    assert dedup.normalize_title("Hello, World!") == "hello world"
    assert dedup.normalize_title("Hello   World") == "hello world"
    assert dedup.normalize_title("Hello, World!") == dedup.normalize_title("Hello World")


def test_normalize_pmid(dedup):
    assert dedup.normalize_pmid("PMID: 111") == "111"
    assert dedup.normalize_pmid("https://pubmed.ncbi.nlm.nih.gov/111/") == "111"
    assert dedup.normalize_pmid("111") == "111"
    assert dedup.normalize_pmid("WOS:000123456789") == ""


def test_parse_ris_nbib_and_csv(dedup, tmp_path):
    ris = tmp_path / "wos.ris"
    ris.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Machine Learning for Crop Yield",
                "AU  - Lovelace, Ada",
                "PY  - 2020",
                "DO  - https://doi.org/10.1000/XYZ",
                "N1  - PMID: 111",
                "JO  - Theor Appl Genet",
                "ER  -",
                "",
                "TY  - JOUR",
                "T1  - Other Work",
                "PY  - 2018",
                "DI  - DOI:10.2000/QED",
                "ER  -",
                "",
            ]
        ),
        encoding="utf-8",
    )
    nbib = tmp_path / "pubmed.nbib"
    nbib.write_text(
        "\n".join(
            [
                "PMID- 111",
                "TI  - Machine Learning for",
                "      Crop Yield",
                "DP  - 2020 Jan 15",
                "AID - 10.1000/xyz [doi]",
                "AU  - Lovelace A",
                "JT  - Theor Appl Genet",
                "",
                "PMID- 333",
                "TI  - Unrelated Study",
                "DP  - 2018",
                "AU  - Hopper G",
                "",
            ]
        ),
        encoding="utf-8",
    )
    table = tmp_path / "scopus.csv"
    table.write_text(
        "\n".join(
            [
                "Document Title,Publication Year,DOI,PubMed ID,Authors,Source title",
                '"Hello, World!",2021,,,Doe J,Example Journal',
                "Hello World,2021,,,Doe J,Example Journal",
                "Other Work,2018,https://dx.doi.org/10.2000/QED,,Smith A,Other Journal",
            ]
        ),
        encoding="utf-8",
    )

    records = []
    records.extend(dedup.parse_file(ris, "wos", use_pandas=False))
    records.extend(dedup.parse_file(nbib, "pubmed", use_pandas=False))
    records.extend(dedup.parse_file(table, "scopus", use_pandas=False))
    payload, clusters = dedup.summarize(records)

    assert payload["identified_total"] == 7
    assert payload["duplicates_removed"] == 3
    assert payload["records_after_deduplication"] == 4
    assert payload["duplicates_removed_by_key"] == {"doi": 2, "pmid": 0, "title_year": 1}
    assert payload["by_source"]["pubmed"]["records_exported"] == 2
    assert payload["by_source"]["wos"]["files"] == ["wos.ris"]
    assert payload["by_source"]["scopus"]["records_exported"] == 3

    by_doi = {item["doi"]: item for item in clusters if item["doi"]}
    crop = by_doi["10.1000/xyz"]
    assert crop["n_copies"] == 2
    assert crop["title"] == "Machine Learning for Crop Yield"
    assert crop["pmid"] == "111"
    assert crop["sources"] == ["wos", "pubmed"]
    other = by_doi["10.2000/qed"]
    assert other["n_copies"] == 2
    hello = [item for item in clusters if dedup.normalize_title(item["title"]) == "hello world"]
    assert len(hello) == 1
    assert hello[0]["n_copies"] == 2
    assert hello[0]["year"] == "2021"
    assert hello[0]["identity_key"] == "title_year"


def test_priority_and_conflicting_dois(dedup):
    def rec(title, year, doi, pmid, source):
        item = dedup.new_record()
        item.update(
            {"title": title, "year": year, "doi": doi, "pmid": pmid, "source": source}
        )
        return item

    records = [
        rec("DOI paper", "2020", "https://DOI.org/10.1001/ABC", "", "pubmed"),
        rec("DOI paper retitled", "1999", "10.1001/abc", "5", "wos"),
        rec("Pmid only", "2019", "", "PMID: 42", "pubmed"),
        rec("Pmid again", "2019", "", "42", "scopus"),
        rec("Hello, World!", "2021", "", "", "scopus"),
        rec("Hello World", "2021", "", "", "wos"),
        rec("Same Title", "2017", "10.9000/one", "", "pubmed"),
        rec("Same Title", "2017", "10.9000/two", "", "wos"),
    ]
    payload, clusters = dedup.summarize(records)
    assert payload["identified_total"] == 8
    assert payload["duplicates_removed"] == 3
    assert payload["records_after_deduplication"] == 5
    assert payload["duplicates_removed_by_key"] == {"doi": 1, "pmid": 1, "title_year": 1}
    dois = sorted(item["doi"] for item in clusters if item["doi"])
    assert dois == ["10.1001/abc", "10.9000/one", "10.9000/two"]


def test_title_without_year_does_not_merge(dedup):
    def rec(title):
        item = dedup.new_record()
        item["title"] = title
        item["source"] = "pubmed"
        return item

    payload, clusters = dedup.summarize([rec("Same Title"), rec("Same Title")])
    assert payload["duplicates_removed"] == 0
    assert len(clusters) == 2


def test_cli_writes_library_and_counts(dedup, tmp_path):
    nbib = tmp_path / "pubmed.txt"
    nbib.write_text(
        "PMID- 7\nTI  - Alpha Study\nDP  - 2022\nAID - 10.5000/Alpha [doi]\nAU  - Kim S\n",
        encoding="utf-8",
    )
    table = tmp_path / "scopus.csv"
    table.write_text("title,year,doi\nAlpha Study,2022,https://doi.org/10.5000/ALPHA\n", encoding="utf-8")
    out = tmp_path / "out"
    code = dedup.main(
        [
            "--input",
            str(nbib),
            "--source",
            "pubmed",
            "--input",
            str(table),
            "--source",
            "scopus",
            "--out-dir",
            str(out),
            "--use-pandas",
            "no",
        ]
    )
    assert code == 0
    payload = json.loads((out / "prisma_counts.json").read_text(encoding="utf-8"))
    assert payload["identified_total"] == 2
    assert payload["duplicates_removed"] == 1
    assert payload["duplicates_removed_by_key"]["doi"] == 1
    assert payload["records_after_deduplication"] == 1
    assert payload["by_source"]["pubmed"]["records_exported"] == 1
    assert payload["by_source"]["scopus"]["records_exported"] == 1
    with (out / "library.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["record_id"] == "R0001"
    assert rows[0]["doi"] == "10.5000/alpha"
    assert rows[0]["pmid"] == "7"
    assert rows[0]["sources"] == "pubmed;scopus"
    assert rows[0]["n_copies"] == "2"
    assert rows[0]["identity_key"] == "doi"


def test_pandas_csv_path_matches_stdlib(dedup, tmp_path):
    if dedup.load_pandas() is None:
        pytest.skip("pandas is not importable")
    table = tmp_path / "records.csv"
    table.write_text(
        "Article Title,Year,DOI\nBeta,2020,https://doi.org/10.1000/Beta\n",
        encoding="utf-8",
    )
    via_pandas = dedup.parse_file(table, "scopus", use_pandas=True)
    via_stdlib = dedup.parse_file(table, "scopus", use_pandas=False)
    assert via_pandas == via_stdlib
    assert via_pandas[0]["doi"] == "10.1000/beta"
    assert via_pandas[0]["title"] == "Beta"


def test_doi_needs_four_digit_registrant(dedup):
    # Same rule as Crossref's recommended pattern 10.\d{4,9}/...
    assert dedup.normalize_doi("https://doi.org/10.1/Beta") == ""
    assert dedup.normalize_doi("https://doi.org/10.1000/Beta") == "10.1000/beta"


def test_pandas_csv_path_keeps_all_fields(dedup, tmp_path):
    if dedup.load_pandas() is None:
        pytest.skip("pandas is not importable")
    table = tmp_path / "records.csv"
    table.write_text(
        "Title,Year,DOI,PMID,Authors,Source Title\n"
        "Alpha,2019,doi:10.1234/ABC.1,12345,Smith J,J Test\n"
        "NA,,,0001,,\n",
        encoding="utf-8",
    )
    via_pandas = dedup.parse_file(table, "wos", use_pandas=True)
    via_stdlib = dedup.parse_file(table, "wos", use_pandas=False)
    assert via_pandas == via_stdlib
    assert via_pandas[0]["doi"] == "10.1234/abc.1"
    assert via_pandas[0]["pmid"] == "12345"
    assert via_pandas[1]["title"] == "NA"
    assert via_pandas[1]["pmid"] == "1"
