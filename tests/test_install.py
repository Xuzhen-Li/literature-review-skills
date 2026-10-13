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


SKILL_NAMES = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
TARGET_DIRS = {
    "claude": [".claude/skills"],
    "codex": [".agents/skills"],
    "cursor": [".cursor/skills"],
    "agents": [".agents/skills"],
    "all": [".claude/skills", ".agents/skills"],
}
ALL_DIRS = [".claude/skills", ".agents/skills", ".cursor/skills", ".codex/skills"]


def run_raw(home, *args, check=True):
    env = dict(os.environ, HOME=str(home))
    return subprocess.run(
        ["bash", str(ROOT / "install.sh"), *args],
        env=env, capture_output=True, text=True, check=check,
    )


def assert_installed(base, target, mode):
    for rel in ALL_DIRS:
        root = base / rel
        if rel in TARGET_DIRS[target]:
            assert sorted(p.name for p in root.iterdir()) == SKILL_NAMES
            for name in SKILL_NAMES:
                dest = root / name
                assert (dest / "SKILL.md").is_file()
                if mode == "link":
                    assert dest.is_symlink()
                    assert dest.resolve() == (ROOT / "skills" / name).resolve()
                else:
                    assert not dest.is_symlink()
                    assert (dest / ".lrs-installed").is_file()
                    assert (dest / "shared" / "gates.md").is_file()
        else:
            assert not root.exists(), rel


def assert_uninstalled(base, target):
    for rel in TARGET_DIRS[target]:
        root = base / rel
        assert not root.exists() or not any(root.iterdir()), rel


def assert_shared_resolves(base, target, mode):
    files = sorted(p.name for p in (ROOT / "shared").iterdir() if p.is_file())
    for rel in TARGET_DIRS[target]:
        for name in SKILL_NAMES:
            skill = base / rel / name
            # Copy: <skill>/shared. Link: suite root two levels above resolved SKILL.md.
            if mode == "copy":
                shared = skill / "shared"
                assert sorted(p.name for p in shared.iterdir() if p.is_file()) == files
            else:
                shared = (skill / "SKILL.md").resolve().parents[2] / "shared"
            for ref in shared_refs(skill):
                assert (shared / ref).is_file(), (rel, name, ref)


@pytest.mark.parametrize("scope", ["user", "project"])
@pytest.mark.parametrize("mode", ["copy", "link"])
@pytest.mark.parametrize("target", sorted(TARGET_DIRS))
def test_target_mode_install_uninstall(tmp_path, target, mode, scope):
    home = tmp_path / "home"
    home.mkdir()
    extra = []
    base = home
    if scope == "project":
        base = tmp_path / "proj"
        base.mkdir()
        extra = ["--project", str(base)]
    args = ["--target", target, "--mode", mode, *extra]
    run_raw(home, *args)
    run_raw(home, *args)  # idempotent
    assert_installed(base, target, mode)
    assert_shared_resolves(base, target, mode)
    if scope == "project":
        assert not any(home.iterdir())
    dry = run_raw(home, *args, "--uninstall", "--dry-run").stdout
    assert "would remove" in dry
    assert_installed(base, target, mode)
    run_raw(home, *args, "--uninstall")
    assert_uninstalled(base, target)
    assert (ROOT / "shared" / "gates.md").is_file()
    for rel in TARGET_DIRS[target]:
        assert not list((base / rel).rglob("shared")), rel
    run_raw(home, *args, "--uninstall")  # second uninstall is a no-op


def test_uninstall_leaves_foreign_entries(tmp_path):
    root = tmp_path / ".agents" / "skills"
    root.mkdir(parents=True)
    foreign_dir = root / "review-orchestrator"
    foreign_dir.mkdir()
    (foreign_dir / "SKILL.md").write_text("mine", encoding="utf-8")
    other = tmp_path / "elsewhere"
    other.mkdir()
    (root / "journal-selection").symlink_to(other)
    (root / "unrelated").mkdir()
    out = run_raw(tmp_path, "--target", "agents", "--uninstall").stdout
    assert "skip" in out
    assert (foreign_dir / "SKILL.md").read_text(encoding="utf-8") == "mine"
    assert (root / "journal-selection").is_symlink()
    assert (root / "unrelated").is_dir()


def test_link_install_refuses_foreign_dir(tmp_path):
    (tmp_path / ".agents" / "skills" / "review-orchestrator").mkdir(parents=True)
    r = run_raw(tmp_path, "--target", "agents", "--mode", "link", check=False)
    assert r.returncode == 1


def test_project_dir_must_exist(tmp_path):
    r = run_raw(tmp_path, "--project", str(tmp_path / "missing"), check=False)
    assert r.returncode == 1
    assert not any(tmp_path.iterdir())


def test_unknown_target_rejected(tmp_path):
    r = run_raw(tmp_path, "--target", "nope", check=False)
    assert r.returncode == 2
