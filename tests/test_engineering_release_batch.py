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

    def test_business_migration_adds_columns(self):
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
            con.execute("CREATE TABLE memories(id INTEGER PRIMARY KEY, content TEXT)")
            con.commit()
            con.close()
            p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "migration", "apply", "--backup"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env=env, timeout=30)
            d = json.loads(p.stdout)
            business = [a for a in d["applied"] if a["action"] == "business_columns" and a["database"] == "memory.db"]
            self.assertTrue(business, "should apply business columns for memory.db")
            self.assertIn("memories.sixdim", business[0]["columns"])
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_adapter_gate_denies_when_env_set(self):
        # Run MCP server with HARNESS_MCP_ADAPTER_ID set to an adapter without memory_read in example? example has memory_read.
        # Use a fake adapter id to force deny.
        env = dict(os.environ)
        env["HARNESS_MCP_ADAPTER_ID"] = "no-such-adapter"
        import sys
        sys.path.insert(0, str(ROOT / "harness-core"))
        sys.path.insert(0, str(ROOT))
        from harness_core.adapter_gate import can, get_adapter_id
        os.environ["HARNESS_MCP_ADAPTER_ID"] = "no-such-adapter"
        os.environ.pop("HARNESS_ALLOW_UNCONFIGURED", None)
        self.assertFalse(can("no-such-adapter", "memory_read"))
        self.assertEqual(get_adapter_id(), "no-such-adapter")
        # restore
        os.environ.pop("HARNESS_MCP_ADAPTER_ID", None)

    def test_adapter_gate_fail_closed_when_unconfigured(self):
        import sys
        sys.path.insert(0, str(ROOT / "harness-core"))
        sys.path.insert(0, str(ROOT))
        from harness_core.adapter_gate import can
        saved_id = os.environ.get("HARNESS_MCP_ADAPTER_ID")
        saved_allow = os.environ.get("HARNESS_ALLOW_UNCONFIGURED")
        os.environ.pop("HARNESS_MCP_ADAPTER_ID", None)
        os.environ.pop("HARNESS_ALLOW_UNCONFIGURED", None)
        self.assertFalse(can(None, "usage_read"), "unconfigured adapter must deny")
        os.environ["HARNESS_ALLOW_UNCONFIGURED"] = "1"
        self.assertTrue(can(None, "usage_read"), "explicit allow should grant")
        if saved_id is not None:
            os.environ["HARNESS_MCP_ADAPTER_ID"] = saved_id
        else:
            os.environ.pop("HARNESS_MCP_ADAPTER_ID", None)
        if saved_allow is not None:
            os.environ["HARNESS_ALLOW_UNCONFIGURED"] = saved_allow
        else:
            os.environ.pop("HARNESS_ALLOW_UNCONFIGURED", None)

    def test_mcp_http_server_refuses_non_loopback(self):
        p = subprocess.run([sys.executable, "-m", "harness_core.adapters.mcp_http_server",
                            "--host", "0.0.0.0", "--port", "0"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=15)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr[-300:])

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
