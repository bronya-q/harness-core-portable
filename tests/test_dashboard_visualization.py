# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()


class DashboardVisualizationTest(unittest.TestCase):
    def test_dashboard_build_includes_visualization_cards(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["DSH_HOME"] = str(home)
        try:
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "dashboard", "build"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=60,
            )
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            out = home / "harness-dashboard" / "index.html"
            self.assertTrue(out.exists())
            s = out.read_text(encoding="utf-8")
            self.assertIn("知识域与挂载", s)
            self.assertIn("向量队列", s)
            self.assertIn("Token 来源 / Provider", s)
            self.assertIn("工程工作区 / Evidence", s)
            self.assertIn("Workspace", s)
            self.assertIn("Evidence Bundle", s)
            self.assertIn("公共边界快照", s)
            self.assertIn("hb-row", s)
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
