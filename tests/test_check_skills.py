import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_skills", ROOT / "scripts" / "check_skills.py")
cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cs)


def make(tmp, folder, frontmatter, body="body\n"):
    d = Path(tmp) / folder
    d.mkdir(parents=True)
    p = d / "SKILL.md"
    p.write_text("---\n" + frontmatter + "---\n" + body, encoding="utf-8")
    return p


class CheckSkillsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_repo_skills_pass(self):
        self.assertEqual(cs.main([str(ROOT / "skills")]), 0)

    def test_valid_all_portable_fields(self):
        p = make(self.tmp, "good-skill", "name: good-skill\ndescription: >\n  Does a thing.\n  Second line.\n"
                 "license: MIT\ncompatibility: python3\nmetadata:\n  version: \"1\"\nallowed-tools: Read\n")
        self.assertEqual(cs.check_skill(p), [])
        fields, _ = cs.parse_frontmatter(p.read_text())
        self.assertEqual(fields["description"], "Does a thing. Second line.")

    def test_name_folder_mismatch(self):
        p = make(self.tmp, "folder-a", "name: folder-b\ndescription: x\n")
        self.assertTrue(any("does not match folder" in e for e in cs.check_skill(p)))

    def test_name_bad_chars(self):
        p = make(self.tmp, "Bad_Name", "name: Bad_Name\ndescription: x\n")
        self.assertTrue(any("lowercase" in e for e in cs.check_skill(p)))

    def test_missing_description(self):
        p = make(self.tmp, "a", "name: a\n")
        self.assertTrue(any("'description' is required" in e for e in cs.check_skill(p)))

    def test_missing_name(self):
        p = make(self.tmp, "a", "description: x\n")
        self.assertTrue(any("'name' is required" in e for e in cs.check_skill(p)))

    def test_description_too_long(self):
        p = make(self.tmp, "a", "name: a\ndescription: " + "x" * 1537 + "\n")
        self.assertTrue(any("max 1536" in e for e in cs.check_skill(p)))

    def test_description_at_limit(self):
        p = make(self.tmp, "a", "name: a\ndescription: " + "x" * 1536 + "\n")
        self.assertEqual(cs.check_skill(p), [])

    def test_non_portable_field(self):
        p = make(self.tmp, "a", "name: a\ndescription: x\nwhen_to_use: y\n")
        self.assertTrue(any("'when_to_use' is not a portable field" in e for e in cs.check_skill(p)))

    def test_missing_frontmatter(self):
        d = Path(self.tmp) / "a"
        d.mkdir()
        (d / "SKILL.md").write_text("# no frontmatter\n")
        self.assertTrue(any("missing frontmatter" in e for e in cs.check_skill(d / "SKILL.md")))

    def test_too_many_lines(self):
        p = make(self.tmp, "a", "name: a\ndescription: x\n", body="l\n" * 500)
        self.assertTrue(any("lines" in e for e in cs.check_skill(p)))

    def test_quoted_name(self):
        p = make(self.tmp, "a", "name: \"a\"\ndescription: 'x'\n")
        self.assertEqual(cs.check_skill(p), [])

    def test_main_fails_on_bad_fixture(self):
        make(self.tmp, "a", "name: b\ndescription: x\n")
        self.assertEqual(cs.main([self.tmp]), 1)

    def test_main_empty_dir(self):
        self.assertEqual(cs.main([self.tmp]), 1)


if __name__ == "__main__":
    unittest.main()
