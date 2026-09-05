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

    def test_secret_scan_clean(self):
        env = dict(os.environ)
        p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "secret-scan"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, timeout=30, cwd=str(ROOT))
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["ok"])

    def test_scope_normalize(self):
        import sys
        sys.path.insert(0, str(ROOT / "harness-core"))
        from scope_utils import normalize_scope
        self.assertEqual(normalize_scope("character:alice"), "character:alice")
        self.assertEqual(normalize_scope("  char  "), "char")
        self.assertEqual(normalize_scope(""), "default")

    def test_core_runs_independent_of_adapter(self):
        env = dict(os.environ)
        p = subprocess.run(
            [sys.executable, "-c", "import harness_core.client; print('core_ok')"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, timeout=30, cwd=str(ROOT),
        )
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        self.assertIn("core_ok", p.stdout)

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
