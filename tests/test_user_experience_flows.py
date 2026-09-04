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
SKILL = ROOT / "harness-core"


def _env(home):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["DSH_HOME"] = str(home)
    return env


class UserExperienceFlowsTest(unittest.TestCase):
    def test_start_first_run_consent(self):
        home = Path(tempfile.mkdtemp())
        try:
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "start"],
                input="y\ny\ny\ny\n0\n", capture_output=True, text=True,
                encoding="utf-8", errors="replace", env=_env(home), timeout=30,
            )
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            consent = home / "harness" / "consent.json"
            self.assertTrue(consent.exists())
            data = json.loads(consent.read_text(encoding="utf-8"))
            self.assertTrue(data["items"]["memory"])
            self.assertEqual(data["scope"], "first-run")
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_memory_write_preview_then_undo(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = _env(home)
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "memory", "write",
                 "--scope", "character:demo-archivist", "--text", "要撤销的条目", "--yes"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            self.assertIn("写入预览", p.stdout)
            text = p.stdout[p.stdout.index("{"):]
            d = json.loads(text)
            nid = d["id"]
            p2 = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "memory", "undo", "--id", nid],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p2.returncode, 0, p2.stderr + p2.stdout[-300:])
            p3 = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "memory", "list", "--scope", "character:demo-archivist"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            notes = json.loads(p3.stdout)["notes"]
            self.assertEqual(notes, [])
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_high_risk_forget_requires_confirmation(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = _env(home)
            w = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "memory", "write",
                 "--scope", "character:demo-archivist", "--text", "要忘记的条目", "--yes"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            d = json.loads(w.stdout[w.stdout.index("{"):])
            nid = d["id"]
            # 不确认 → 取消
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "memory", "forget", "--id", nid],
                input="n" + chr(10), capture_output=True, text=True, encoding="utf-8",
                errors="replace", env=env, timeout=30,
            )
            self.assertEqual(p.returncode, 1, p.stderr + p.stdout[-300:])
            self.assertIn("cancelled", p.stdout)
            # 确认 → 归档
            p2 = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "memory", "forget", "--id", nid, "--yes"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p2.returncode, 0, p2.stderr + p2.stdout[-300:])
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_privacy_export_preview_and_confirm(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = _env(home)
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "privacy", "export"],
                input="n" + chr(10), capture_output=True, text=True, encoding="utf-8",
                errors="replace", env=env, timeout=30,
            )
            self.assertEqual(p.returncode, 1, p.stderr + p.stdout[-300:])
            self.assertIn("导出预览", p.stdout)
            self.assertIn("cancelled", p.stdout)
            self.assertFalse((home / "harness-dashboard" / "privacy-export.json").exists())
            p2 = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "privacy", "export", "--yes"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p2.returncode, 0, p2.stderr + p2.stdout[-300:])
            self.assertTrue((home / "harness-dashboard" / "privacy-export.json").exists())
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_knowledge_access_read_only_snippet(self):
        home = Path(tempfile.mkdtemp())
        try:
            char_dir = home / "harness" / "characters" / "demo-archivist"
            kb_dir = home / "local" / "kb-a"
            char_dir.mkdir(parents=True, exist_ok=True)
            kb_dir.mkdir(parents=True, exist_ok=True)
            (char_dir / "package-manifest.json").write_text(
                json.dumps({
                    "persona_id": "demo-archivist", "display_name": "档案管理员",
                    "scope": "character:demo-archivist",
                    "knowledge_bindings": [{"domain_id": "local:knowledge-source-a",
                                            "source_ref": "local:knowledge-source-a",
                                            "role": "steward"}],
                }, ensure_ascii=False), encoding="utf-8",
            )
            (kb_dir / "theory.md").write_text("女性主义理论强调差异性。", encoding="utf-8")
            (home / "harness" / "knowledge-sources.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "sources": [{
                        "source_id": "local:knowledge-source-a",
                        "display_name": "女性主义理论库",
                        "kind": "directory", "root": str(kb_dir),
                        "portable": False, "private": True, "default_access": "deny",
                        "content_types": ["女性主义"], "stewards": ["demo-archivist"],
                    }],
                }, ensure_ascii=False), encoding="utf-8",
            )
            env = _env(home)
            p = subprocess.run(
                [sys.executable, str(ROOT / "harness.py"), "knowledge", "access",
                 "--role", "demo-archivist", "--source", "local:knowledge-source-a",
                 "--query", "女性主义"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            d = json.loads(p.stdout)
            self.assertTrue(d["ok"])
            self.assertTrue(d["allowed"])
            self.assertTrue(any("女性主义理论强调差异性" in m.get("snippet", "") for m in d["matches"]))
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
