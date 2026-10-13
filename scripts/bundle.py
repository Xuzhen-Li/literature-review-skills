#!/usr/bin/env python3
"""Build paste-ready bundles of the skills for chat products without a file system.

Outputs (default --out dist):
  dist/chatgpt/instructions.md        custom GPT instructions (hard limit 8,000 characters)
  dist/chatgpt/knowledge/*.md         knowledge files: shared rules + one file per skill (at most 20 files)
  dist/deepseek/literature-review-skills.md
                                      one long-context file: instructions + shared + every skill

Sources: platform/ templates, platform/budgets.json, shared/*.md, skills/<name>/SKILL.md
and skills/<name>/references/*. Scripts and tests are not bundled.

Placeholders of the form [[TODO-TEXT:id]] are allowed. While any remain, sizes are also
checked as "projected": the placeholder is counted at its budget from platform/budgets.json.
Every placeholder must have a budget.

Output is deterministic: sorted inputs, LF line endings, UTF-8, no timestamps.
Exit status 1 if a limit is exceeded or a placeholder has no budget.

Usage:
  python3 scripts/bundle.py [--out DIR]
  python3 scripts/bundle.py --check          # build into a temporary directory, check only
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORM = ROOT / "platform"

GPT_INSTRUCTIONS_LIMIT = 8000      # characters, custom GPT instructions
GPT_INSTRUCTIONS_TARGET = 7500     # projected size must stay under this, leaving room for edits
GPT_KNOWLEDGE_MAX_FILES = 20
DEEPSEEK_LIMIT = 400_000           # characters, conservative cap for one pasted/attached file

PLACEHOLDER = re.compile(r"\[\[TODO-TEXT:([a-z0-9-]+)\]\]")
TEXT_SUFFIXES = {".md", ".csv", ".example", ".yaml", ".yml", ".txt"}


# ---------------------------------------------------------------- sources
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML frontmatter reader for `key: value` and folded `key: >` blocks."""
    if not text.startswith("---\n"):
        return {}
    block = text[4:text.index("\n---", 4)]
    out: dict[str, str] = {}
    key = None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            out[key] = "" if val in (">", "|", ">-", "|-") else val.strip("'\"")
        elif key and line.startswith(" "):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def skills() -> list[Path]:
    return sorted(p.parent for p in (ROOT / "skills").glob("*/SKILL.md"))


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]


def fence(path: Path, body: str) -> str:
    lang = {".csv": "csv", ".yaml": "yaml", ".yml": "yaml", ".example": "yaml"}.get(path.suffix, "")
    return f"```{lang}\n{body.rstrip()}\n```\n"


def section(path: Path, level: int) -> str:
    rel = path.relative_to(ROOT).as_posix()
    body = read(path)
    if path.suffix != ".md":
        body = fence(path, body)
    return f"{'#' * level} File: {rel}\n\n{body.rstrip()}\n"


def references(skill: Path) -> list[Path]:
    ref = skill / "references"
    if not ref.is_dir():
        return []
    return sorted(p for p in ref.iterdir() if p.is_file() and p.suffix in TEXT_SUFFIXES)


# ---------------------------------------------------------------- products
def skill_index() -> str:
    lines = []
    for s in skills():
        fm = frontmatter(read(s / "SKILL.md"))
        lines.append(f"- `{fm.get('name', s.name)}`: {first_sentence(fm.get('description', ''))}")
    return "\n".join(lines)


def instructions() -> str:
    tmpl = read(PLATFORM / "chatgpt" / "instructions.md.tmpl")
    return tmpl.replace("{{SKILL_INDEX}}", skill_index()).rstrip() + "\n"


def shared_doc() -> str:
    parts = ["# Shared rules\n"]
    parts += [section(p, 2) for p in sorted((ROOT / "shared").glob("*.md"))]
    return "\n".join(parts)


def skill_doc(skill: Path, level: int = 1) -> str:
    parts = [f"{'#' * level} Skill: {skill.name}\n", section(skill / "SKILL.md", level + 1)]
    parts += [section(p, level + 1) for p in references(skill)]
    return "\n".join(parts)


def deepseek_doc() -> str:
    toc = ["- Instructions", "- Shared rules"] + [f"- Skill: {s.name}" for s in skills()]
    head = read(PLATFORM / "deepseek" / "header.md.tmpl").replace("{{TOC}}", "\n".join(toc)).rstrip()
    body = [head, "\n# Instructions\n", instructions().split("\n", 1)[1].strip(), "", shared_doc()]
    body += [skill_doc(s) for s in skills()]
    return "\n".join(body).rstrip() + "\n"


def build(out: Path) -> dict[Path, str]:
    files: dict[Path, str] = {
        out / "chatgpt" / "instructions.md": instructions(),
        out / "chatgpt" / "knowledge" / "00-shared.md": shared_doc(),
        out / "deepseek" / "literature-review-skills.md": deepseek_doc(),
    }
    for i, s in enumerate(skills(), start=1):
        files[out / "chatgpt" / "knowledge" / f"{i:02d}-{s.name}.md"] = skill_doc(s)
    for d in ("chatgpt", "deepseek"):
        if (out / d).exists():
            shutil.rmtree(out / d)
    for path, text in sorted(files.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return files


# ---------------------------------------------------------------- checks
def budgets() -> dict[str, int]:
    data = json.loads(read(PLATFORM / "budgets.json"))
    return {k: int(v) for k, v in data.items() if not k.startswith("_")}


def projected(text: str, budget: dict[str, int]) -> tuple[int, list[str]]:
    """Length with each placeholder counted at its budget; also returns ids without a budget."""
    ids = PLACEHOLDER.findall(text)
    missing = sorted({i for i in ids if i not in budget})
    size = len(PLACEHOLDER.sub("", text)) + sum(budget.get(i, 0) for i in ids)
    return size, missing


def check(files: dict[Path, str], out: Path) -> list[str]:
    errors: list[str] = []
    budget = budgets()
    rows = []

    def limit(path: Path, hard: int, target: int | None = None) -> None:
        text = files[path]
        size, missing = projected(text, budget)
        rows.append((path.relative_to(out).as_posix(), len(text), size, hard))
        if missing:
            errors.append(f"{path.name}: placeholders without a budget: {', '.join(missing)}")
        if len(text) > hard:
            errors.append(f"{path.name}: {len(text)} characters > limit {hard}")
        if size > (target or hard):
            errors.append(f"{path.name}: projected {size} characters > {'target' if target else 'limit'} {target or hard}")

    limit(out / "chatgpt" / "instructions.md", GPT_INSTRUCTIONS_LIMIT, GPT_INSTRUCTIONS_TARGET)
    limit(out / "deepseek" / "literature-review-skills.md", DEEPSEEK_LIMIT)
    knowledge = sorted(p for p in files if p.parent == out / "chatgpt" / "knowledge")
    if len(knowledge) > GPT_KNOWLEDGE_MAX_FILES:
        errors.append(f"knowledge: {len(knowledge)} files > {GPT_KNOWLEDGE_MAX_FILES}")
    for p in knowledge:
        rows.append((p.relative_to(out).as_posix(), len(files[p]), projected(files[p], budget)[0], None))

    print(f"{'file':52s} {'chars':>8s} {'projected':>10s} {'limit':>8s}")
    for name, n, size, hard in rows:
        print(f"{name:52s} {n:8d} {size:10d} {hard if hard else '-':>8}")
    print(f"knowledge files: {len(knowledge)} (max {GPT_KNOWLEDGE_MAX_FILES})")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build ChatGPT and DeepSeek bundles of the skills.")
    ap.add_argument("--out", type=Path, default=ROOT / "dist", help="output directory (default: dist/)")
    ap.add_argument("--check", action="store_true", help="build into a temporary directory and only check limits")
    args = ap.parse_args(argv)
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            errors = check(build(out), out)
    else:
        out = args.out.resolve()
        errors = check(build(out), out)
    for e in errors:
        print("error:", e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
