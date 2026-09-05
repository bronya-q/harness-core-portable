# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()


class UserTestCommandsTest(unittest.TestCase):
    def test_checklist(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["DSH_HOME"] = str(home)
        try:
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "user-test", "checklist"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            d = json.loads(p.stdout)
            self.assertTrue(d["ok"])
            self.assertGreaterEqual(len(d["tasks"]), 10)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
