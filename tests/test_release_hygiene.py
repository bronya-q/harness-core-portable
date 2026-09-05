# -*- coding: utf-8 -*-
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()


class ReleaseHygieneTest(unittest.TestCase):
    def test_issue_templates_present(self):
        for name in ("bug-report.md", "feature-request.md", "user-feedback.md", "security.md"):
            p = ROOT / ".github" / "ISSUE_TEMPLATE" / name
            self.assertTrue(p.exists(), f"missing {p}")
            self.assertIn("---", p.read_text(encoding="utf-8"))

    def test_character_install_rejects_missing_schema_version(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["DSH_HOME"] = str(home)
        try:
            pkg = home / "bad-char"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / "character.json").write_text(
                json.dumps({"persona_id": "bad-char", "display_name": "Bad"},
                           ensure_ascii=False), encoding="utf-8")
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "character", "install", str(pkg)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p.returncode, 1, p.stderr + p.stdout[-300:])
            self.assertIn("package_schema_required", p.stdout)
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
