# -*- coding: utf-8 -*-
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()


class EngineeringReleaseBatchTest(unittest.TestCase):
    def test_migration_apply_creates_schema_table(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["DSH_HOME"] = str(home)
        try:
            mem_dir = home / "memory-emotion"
            mem_dir.mkdir(parents=True, exist_ok=True)
            db = mem_dir / "memory.db"
            con = sqlite3.connect(str(db))
            con.execute("CREATE TABLE memories(id INTEGER PRIMARY KEY)")
            con.commit()
            con.close()
            p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "migration", "apply", "--backup"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env=env, timeout=30)
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            d = json.loads(p.stdout)
            self.assertTrue(d["ok"])
            self.assertTrue(any(a["database"] == "memory.db" for a in d["applied"]))
            con = sqlite3.connect(str(db))
            ver = con.execute("SELECT version FROM schema_version ORDER BY rowid DESC LIMIT 1").fetchone()
            self.assertEqual(ver[0], 1)
            con.close()
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_private_docs_no_private_names(self):
        for rel in ("HYBRID_FUNCTIONAL_PERSONA.md", "ENGINEERING_ROLES.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            for bad in ("本机综合人格 A", "本机知识管理员 A", "本机知识管理员 B"):
                self.assertNotIn(bad, text, f"{rel} still contains {bad}")

    def test_adapter_permission_schema_validates_example(self):
        p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "schema", "validate",
                            "--adapter-permission", str(ROOT / "harness-core" / "adapters.example.json")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["ok"])

    def test_dashboard_has_adapter_matrix(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["DSH_HOME"] = str(home)
        try:
            p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "dashboard", "build"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env=env, timeout=60)
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            out = home / "harness-dashboard" / "index.html"
            s = out.read_text(encoding="utf-8")
            self.assertIn("Adapter 权限矩阵", s)
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
