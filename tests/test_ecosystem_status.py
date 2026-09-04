# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class EcosystemStatusTest(unittest.TestCase):
    def test_ecosystem_status(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = dict(os.environ)
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            env["DSH_HOME"] = str(home / ".dsh")
            p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "ecosystem", "status"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env=env, timeout=60)
            self.assertEqual(p.returncode, 0)
            data = json.loads(p.stdout)
            self.assertEqual(data.get("mode"), "ecosystem_status")
            self.assertTrue(len(data.get("entries", [])) >= 4)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
