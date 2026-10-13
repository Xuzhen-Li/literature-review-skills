#!/usr/bin/env python3
"""Check SKILL.md frontmatter against the portable Agent Skills fields."""
import re
import sys
from pathlib import Path

ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED = ("name", "description")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_DESCRIPTION = 1536
MAX_LINES = 500
KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing frontmatter start '---'")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("missing frontmatter end '---'")
    fields, key, block, buf = {}, None, None, []

    def flush():
        if key is None:
            return
        if block is None:
            fields[key] = "\n".join(buf).strip()
        elif block.startswith(">"):
            fields[key] = " ".join(s.strip() for s in buf if s.strip())
        else:
            fields[key] = "\n".join(s.strip() for s in buf).strip()

    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#") and not raw[:1].isspace():
            if key is not None:
                buf.append("")
            continue
        m = KEY_RE.match(raw)
        if m and not raw[:1].isspace():
            flush()
            key, value = m.group(1), m.group(2).strip()
            if key in fields:
                raise ValueError(f"duplicate key '{key}'")
            block = value if value[:1] in (">", "|") else None
            buf = [] if block is not None or not value else [_unquote(value)]
        elif raw[:1].isspace() and key is not None:
            buf.append(raw)
        else:
            raise ValueError(f"unparseable frontmatter line: {raw!r}")
    flush()
    return fields, end


def _unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def check_skill(skill_md):
    path = Path(skill_md)
    errors = []
    text = path.read_text(encoding="utf-8")
    try:
        fields, _ = parse_frontmatter(text)
    except ValueError as exc:
        return [f"{path}: {exc}"]
    for key in sorted(set(fields) - ALLOWED):
        errors.append(f"{path}: field '{key}' is not a portable field")
    for key in REQUIRED:
        if not fields.get(key):
            errors.append(f"{path}: '{key}' is required")
    name = fields.get("name", "")
    if name:
        if not NAME_RE.match(name):
            errors.append(f"{path}: name '{name}' must use lowercase letters, digits and hyphens")
        if name != path.parent.name:
            errors.append(f"{path}: name '{name}' does not match folder '{path.parent.name}'")
    desc = fields.get("description", "")
    if len(desc) > MAX_DESCRIPTION:
        errors.append(f"{path}: description is {len(desc)} chars (max {MAX_DESCRIPTION})")
    n_lines = len(text.splitlines())
    if n_lines >= MAX_LINES:
        errors.append(f"{path}: {n_lines} lines (must be under {MAX_LINES})")
    return errors


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent / "skills"
    files = sorted(root.glob("*/SKILL.md"))
    if not files:
        print(f"no SKILL.md found under {root}", file=sys.stderr)
        return 1
    errors = [e for f in files for e in check_skill(f)]
    for e in errors:
        print(e, file=sys.stderr)
    print(f"checked {len(files)} skills, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
