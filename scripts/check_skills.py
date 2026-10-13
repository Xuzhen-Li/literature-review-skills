#!/usr/bin/env python3
"""Check SKILL.md frontmatter against the Agent Skills specification."""
import re
import sys
from pathlib import Path

import yaml

ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED = ("name", "description")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_LINES = 500


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key '{key}'", key_node.start_mark)
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing frontmatter start '---'")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("missing frontmatter end '---'")
    try:
        data = yaml.load("\n".join(lines[1:end]), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML: {' '.join(str(exc).split())}")
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    return data, end


def _str_field(fields, key, limit, path, errors):
    if key not in fields:
        return None
    value = fields[key]
    if not isinstance(value, str):
        errors.append(f"{path}: '{key}' must be a string")
        return None
    value = value.strip()
    if not value:
        errors.append(f"{path}: '{key}' must not be empty")
    elif limit and len(value) > limit:
        errors.append(f"{path}: '{key}' is {len(value)} chars (max {limit})")
    return value


def check_skill(skill_md):
    path = Path(skill_md)
    errors = []
    text = path.read_text(encoding="utf-8")
    try:
        fields, _ = parse_frontmatter(text)
    except ValueError as exc:
        return [f"{path}: {exc}"]
    for key in sorted(set(map(str, fields)) - ALLOWED):
        errors.append(f"{path}: field '{key}' is not a portable field")
    for key in REQUIRED:
        if key not in fields:
            errors.append(f"{path}: '{key}' is required")
    name = _str_field(fields, "name", MAX_NAME, path, errors)
    if name:
        if not NAME_RE.match(name):
            errors.append(f"{path}: name '{name}' must use lowercase letters, digits and single hyphens")
        if name != path.parent.name:
            errors.append(f"{path}: name '{name}' does not match folder '{path.parent.name}'")
    _str_field(fields, "description", MAX_DESCRIPTION, path, errors)
    _str_field(fields, "compatibility", MAX_COMPATIBILITY, path, errors)
    _str_field(fields, "license", None, path, errors)
    _str_field(fields, "allowed-tools", None, path, errors)
    if "metadata" in fields:
        meta = fields["metadata"]
        if not isinstance(meta, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in meta.items()):
            errors.append(f"{path}: 'metadata' must map string keys to string values")
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
