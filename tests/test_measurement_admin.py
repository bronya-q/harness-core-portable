# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()


class MeasurementAdminTest(unittest.TestCase):
    def test_measure_construct(self):
        env = dict(os.environ)
        p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "measure", "construct"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["ok"])
        self.assertGreaterEqual(d["count"], 10)

    def test_measure_reliability(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        f = home / "r.json"
        f.write_text(json.dumps({"raters": [[1, 2, 3], [1, 2, 3], [1, 2, 3]]}), encoding="utf-8")
        p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "measure", "reliability", "--file", str(f)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["ok"])
        self.assertAlmostEqual(d["krippendorff_alpha"], 1.0)
        import shutil
        shutil.rmtree(home, ignore_errors=True)

    def test_host_guide(self):
        env = dict(os.environ)
        p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "host-guide"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertIn("Claude Code", str(d["hosts"]))
        self.assertIn("Codex CLI", str(d["hosts"]))


if __name__ == "__main__":
    unittest.main()
