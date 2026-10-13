import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED_REF = re.compile(r"`shared/([A-Za-z0-9_.-]+)`")


def run_install(home, *args):
    env = dict(os.environ, HOME=str(home))
    return subprocess.run(
        ["bash", str(ROOT / "install.sh"), "--target", "claude", *args],
        env=env, capture_output=True, text=True, check=True,
    )


def shared_refs(skill_dir):
    found = set()
    for path in skill_dir.rglob("*.md"):
        if "shared" in path.relative_to(skill_dir).parts:
            continue
        found.update(SHARED_REF.findall(path.read_text(encoding="utf-8")))
    return found


@pytest.mark.parametrize("mode", ["copy", "link"])
def test_installed_shared_refs_resolve(tmp_path, mode):
    run_install(tmp_path, "--mode", mode)
    root = tmp_path / ".claude" / "skills"
    skills = sorted(p for p in root.iterdir() if (p / "SKILL.md").exists())
    assert len(skills) == len(list((ROOT / "skills").glob("*/SKILL.md")))
    checked = 0
    for skill in skills:
        if mode == "copy":
            base = skill / "shared"
        else:
            base = skill.resolve().parents[1] / "shared"
        for name in shared_refs(skill):
            assert (base / name).is_file(), (skill.name, name)
            checked += 1
    assert checked > 0


def test_copy_install_is_repeatable(tmp_path):
    run_install(tmp_path, "--mode", "copy")
    run_install(tmp_path, "--mode", "copy")
    gates = tmp_path / ".claude" / "skills" / "review-orchestrator" / "shared" / "gates.md"
    assert gates.read_text(encoding="utf-8") == (ROOT / "shared" / "gates.md").read_text(encoding="utf-8")


def test_dry_run_writes_nothing(tmp_path):
    out = run_install(tmp_path, "--mode", "copy", "--dry-run").stdout
    assert "/shared" in out
    assert not (tmp_path / ".claude").exists()
