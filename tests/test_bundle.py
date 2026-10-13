"""Tests for scripts/bundle.py: limits, reproducibility and coverage."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("bundle", ROOT / "scripts" / "bundle.py")
bundle = importlib.util.module_from_spec(spec)
sys.modules["bundle"] = bundle
spec.loader.exec_module(bundle)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One build shared by every test in this module; tests only read it."""
    out = tmp_path_factory.mktemp("bundle") / "dist"
    return out, bundle.build(out)


def tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_rebuild_is_byte_identical(built, tmp_path):
    first, _ = built
    second = tmp_path / "dist"
    bundle.build(second)
    bundle.build(second)  # a rebuild over an existing output must not leave stale files
    assert tree(first) == tree(second)
    assert tree(first)


def test_limits_pass(built):
    out, files = built
    assert bundle.check(files, out) == []


def test_instructions_within_gpt_limit(built):
    out, files = built
    text = files[out / "chatgpt" / "instructions.md"]
    assert len(text) <= bundle.GPT_INSTRUCTIONS_LIMIT
    size, missing = bundle.projected(text, bundle.budgets())
    assert missing == []
    assert size <= bundle.GPT_INSTRUCTIONS_TARGET


def test_overflow_is_reported(built, monkeypatch):
    out, files = built
    monkeypatch.setattr(bundle, "GPT_INSTRUCTIONS_LIMIT", 100)
    errors = bundle.check(files, out)
    assert any("instructions.md" in e and "limit 100" in e for e in errors)


def with_placeholder(out, files, slot="gpt-role"):
    key = out / "chatgpt" / "instructions.md"
    return {**files, key: files[key] + f"\n[[TODO-TEXT:{slot}]]\n"}


def test_budget_overflow_is_reported(built, monkeypatch):
    out, files = built
    files = with_placeholder(out, files)
    real = bundle.budgets()
    monkeypatch.setattr(bundle, "budgets", lambda: {k: 10_000 if k == "gpt-role" else v for k, v in real.items()})
    errors = bundle.check(files, out)
    assert any("projected" in e and "instructions.md" in e for e in errors)


def test_placeholder_without_budget_is_reported(built, monkeypatch):
    out, files = built
    files = with_placeholder(out, files)
    real = bundle.budgets()
    monkeypatch.setattr(bundle, "budgets", lambda: {k: v for k, v in real.items() if k != "gpt-role"})
    errors = bundle.check(files, out)
    assert any("without a budget" in e and "gpt-role" in e for e in errors)


def test_projected_counts_budget_not_placeholder():
    size, missing = bundle.projected("ab [[TODO-TEXT:x]] cd", {"x": 50})
    assert (size, missing) == (len("ab  cd") + 50, [])


def test_every_skill_is_bundled(built):
    out, files = built
    names = [p.name for p in bundle.skills()]
    assert len(names) >= 1
    knowledge = sorted(p.name for p in (out / "chatgpt" / "knowledge").iterdir())
    assert len(knowledge) == len(names) + 1 <= bundle.GPT_KNOWLEDGE_MAX_FILES
    instructions = files[out / "chatgpt" / "instructions.md"]
    single = files[out / "deepseek" / "literature-review-skills.md"]
    for n in names:
        assert any(k.endswith(f"-{n}.md") for k in knowledge)
        assert f"`{n}`" in instructions
        assert f"# Skill: {n}\n" in single
        assert f"File: skills/{n}/SKILL.md" in single
    for p in sorted((ROOT / "shared").glob("*.md")):
        assert f"File: shared/{p.name}" in single


def test_no_scripts_or_absolute_paths(built):
    out, files = built
    for text in files.values():
        headers = [line for line in text.splitlines() if line.startswith("#") and " File: " in line]
        assert not any("/scripts/" in h or "/tests/" in h for h in headers)
        assert str(ROOT) not in text


def test_cli_check_exit_status():
    assert bundle.main(["--check"]) == 0
