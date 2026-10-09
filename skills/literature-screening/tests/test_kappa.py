"""Tests for Cohen's kappa."""

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "kappa.py"


def load_kappa():
    spec = importlib.util.spec_from_file_location("lrs_kappa", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def kappa():
    return load_kappa()


def test_known_partial_agreement(kappa):
    # 5 of 6 items agree. Marginal products give expected agreement 0.5.
    result = kappa.cohen_kappa(
        ["include", "include", "include", "exclude", "exclude", "exclude"],
        ["include", "include", "exclude", "exclude", "exclude", "exclude"],
    )
    assert result["n"] == 6
    assert result["observed_agreement"] == pytest.approx(5 / 6)
    assert result["expected_agreement"] == pytest.approx(0.5)
    assert result["kappa"] == pytest.approx((5 / 6 - 0.5) / 0.5)
    assert result["interpretation"] == "substantial"


def test_casefold_and_perfect_agreement(kappa):
    result = kappa.cohen_kappa(["Include", "Exclude"], ["include", "exclude"])
    assert result["kappa"] == pytest.approx(1.0)
    assert result["interpretation"] == "almost_perfect"


def test_no_variation_is_undefined(kappa):
    result = kappa.cohen_kappa(["include", "include"], ["include", "include"])
    assert result["kappa"] is None
    assert result["interpretation"] == "undefined"
    assert result["observed_agreement"] == 1.0


def test_length_mismatch(kappa):
    with pytest.raises(ValueError):
        kappa.cohen_kappa(["include"], ["include", "exclude"])


def test_cli_writes_json(kappa, tmp_path):
    table = tmp_path / "pilot.csv"
    table.write_text(
        "record_id,screener_a,screener_b\n"
        "R0001,include,include\n"
        "R0002,include,exclude\n"
        "R0003,exclude,exclude\n",
        encoding="utf-8",
    )
    out = tmp_path / "kappa.json"
    code = kappa.main(["--csv", str(table), "--a", "screener_a", "--b", "screener_b", "--out", str(out)])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["n"] == 3
    assert payload["kappa"] == pytest.approx(0.4)
    assert payload["interpretation"] == "fair"
