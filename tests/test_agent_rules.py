"""Structure checks for the Cursor project rule and the root AGENTS.md."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = sorted((ROOT / ".cursor" / "rules").rglob("*"))
AGENTS = ROOT / "AGENTS.md"
SKILLS = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
PATH_REF = re.compile(r"`((?:skills|shared)/[^`<>]+)`")


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    assert text.startswith("---\n"), "rule must start with YAML frontmatter"
    end = text.index("\n---\n", 4)
    meta = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, text[end + 5:]


def test_rules_are_mdc_with_frontmatter():
    files = [p for p in RULES if p.is_file()]
    assert files, "no rule files"
    for path in files:
        assert path.suffix == ".mdc", f"{path.name}: Cursor reads only .mdc rules"
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        assert set(meta) == {"description", "globs", "alwaysApply"}
        assert meta["description"].strip('"')
        assert meta["alwaysApply"] in ("true", "false")
        assert len(body.splitlines()) < 500


def test_rule_lists_every_skill_and_paths_exist():
    text = (ROOT / ".cursor" / "rules" / "literature-review.mdc").read_text(encoding="utf-8")
    for name in SKILLS:
        assert f"`skills/{name}/SKILL.md`" in text
    for ref in PATH_REF.findall(text):
        assert (ROOT / ref).exists(), ref


def test_agents_md_lists_every_skill_and_fits_codex_cap():
    data = AGENTS.read_bytes()
    assert len(data) <= 32 * 1024  # Codex project_doc_max_bytes default
    text = data.decode("utf-8")
    for name in SKILLS:
        assert f"| `{name}` | `skills/{name}/SKILL.md` |" in text
    for ref in PATH_REF.findall(text):
        if "<name>" not in ref:
            assert (ROOT / ref).exists(), ref
