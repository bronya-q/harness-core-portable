# -*- coding: utf-8 -*-
"""Repeated real-runtime checks for the synthetic golden path.

These tests deliberately call the actual CLI subprocess + SQLite path
(not the expected-trace fixture). They are safe, offline, synthetic-only.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()


def _env(home):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["DSH_HOME"] = str(home / ".dsh")
    env.pop("MEMORY_EMOTION_DATA_DIR", None)
    return env


def _run(args, env, cwd=None):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, cwd=cwd or str(ROOT), timeout=60)


class RealGoldenPathTest(unittest.TestCase):
    def test_offline_demo_exits_zero_with_auto_disabled(self):
        home = Path(tempfile.mkdtemp())
        env = _env(home)
        try:
            p = _run([sys.executable, str(ROOT / "harness.py"), "demo", "--offline"], env=env)
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            self.assertIn("自动执行：DISABLED", p.stdout)
            self.assertIn("网络上传：NONE", p.stdout)
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_memory_write_confirmation_undo_restore(self):
        home = Path(tempfile.mkdtemp())
        env = _env(home)
        try:
            # cancelled path: no --yes, EOF -> cancelled, no note
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "write",
                      "--scope", "character:demo-alice", "--text", "未确认的测试记忆"], env=env)
            self.assertIn('"status": "cancelled"', p.stdout)
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "list",
                      "--scope", "character:demo-alice"], env=env)
            d = json.loads(p.stdout)
            self.assertEqual(d.get("notes", []), [])

            # confirmed path
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "write",
                      "--scope", "character:demo-alice", "--text", "已确认的测试记忆", "--yes"], env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr[-300:])
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "list",
                      "--scope", "character:demo-alice"], env=env)
            d = json.loads(p.stdout)
            self.assertEqual(len(d.get("notes", [])), 1)
            nid = d["notes"][0]["id"]
            self.assertEqual(d["notes"][0]["status"], "active")

            # undo -> archived
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "undo",
                      "--id", nid, "--yes"], env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr[-300:])
            self.assertIn('"status": "archived"', p.stdout)
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "list",
                      "--scope", "character:demo-alice"], env=env)
            d = json.loads(p.stdout)
            self.assertEqual(d.get("notes", []), [])

            # restore from version 1 -> active restored note
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "restore",
                      "--scope", "character:demo-alice", "--version", "1"], env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr[-300:])
            p = _run([sys.executable, str(ROOT / "harness.py"), "memory", "list",
                      "--scope", "character:demo-alice"], env=env)
            d = json.loads(p.stdout)
            self.assertEqual(len(d.get("notes", [])), 1)
            self.assertEqual(d["notes"][0]["kind"], "restored")
            self.assertEqual(d["notes"][0]["status"], "active")
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_humanization_candidate_requires_manual_approval(self):
        home = Path(tempfile.mkdtemp())
        env = _env(home)
        try:
            init = _run([sys.executable, str(ROOT / "harness-core" / "humanization.py"), "init"], env=env)
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout[-300:])
            add = _run([sys.executable, str(ROOT / "harness-core" / "humanization.py"),
                        "initiative-add", "--scope", "character:demo-alice",
                        "--trigger", "synthetic_test", "--action", "test_action",
                        "--reason", "合成候选，用于真实trace", "--risk", "low"], env=env)
            self.assertEqual(add.returncode, 0, add.stderr + add.stdout[-300:])
            d = json.loads(add.stdout)
            self.assertEqual(d["status"], "shadow")
            self.assertIn("no automatic sending; manual approval only", d["note"])
            cid = d["id"]

            # manually approve
            dec = _run([sys.executable, str(ROOT / "harness-core" / "humanization.py"),
                        "decide", "--kind", "initiative", "--id", cid, "--action", "approve"], env=env)
            self.assertEqual(dec.returncode, 0, dec.stderr + dec.stdout[-300:])
            d2 = json.loads(dec.stdout)
            self.assertTrue(d2["ok"])

            # assert persisted status is approved
            db = home / ".dsh" / "memory-emotion" / "humanization_sidecar.db"
            self.assertTrue(db.exists(), "humanization_sidecar.db not created")
            import sqlite3
            con = sqlite3.connect(str(db))
            try:
                row = con.execute(
                    "SELECT status FROM initiative_candidates WHERE id=?",
                    (cid,),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], "approved")
            finally:
                con.close()
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
