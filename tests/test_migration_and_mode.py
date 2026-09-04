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


class MigrationAndModeTest(unittest.TestCase):
    def test_migration_status_check_dry_run(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["DSH_HOME"] = str(home)
        try:
            for sub in ("status", "check", "dry-run"):
                p = subprocess.run(
                    [sys.executable, str(ROOT / "harness.py"), "migration", sub],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    env=env, timeout=30,
                )
                self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
                d = json.loads(p.stdout)
                self.assertTrue(d["ok"])
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_character_mode_diff(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["DSH_HOME"] = str(home)
        try:
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "character", "mode", "diff",
                 "--persona", "demo-archivist", "--mode-a", "companion", "--mode-b", "archival-research"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            d = json.loads(p.stdout)
            self.assertTrue(d["ok"])
            self.assertIn("capabilities", d["differences"])
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
