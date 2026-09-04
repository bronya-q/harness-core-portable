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


def _setup(home):
    char_dir = home / "harness" / "characters" / "demo-archivist"
    kb_dir = home / "local" / "kb-a"
    char_dir.mkdir(parents=True, exist_ok=True)
    kb_dir.mkdir(parents=True, exist_ok=True)
    (char_dir / "package-manifest.json").write_text(
        json.dumps({
            "persona_id": "demo-archivist",
            "display_name": "档案管理员",
            "scope": "character:demo-archivist",
            "knowledge_bindings": [{
                "domain_id": "local:knowledge-source-a",
                "source_ref": "local:knowledge-source-a",
                "role": "steward",
                "mount_mode": "read_only",
            }],
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    (home / "harness" / "knowledge-sources.json").write_text(
        json.dumps({
            "schema_version": 1,
            "sources": [{
                "source_id": "local:knowledge-source-a",
                "display_name": "女性主义理论库",
                "kind": "directory",
                "root": str(kb_dir),
                "portable": False,
                "private": True,
                "default_access": "deny",
                "content_types": ["女性主义", "理论", "伦理"],
                "stewards": ["demo-archivist"],
            }],
        }, ensure_ascii=False),
        encoding="utf-8",
    )


class KnowledgeStewardshipTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        _setup(self.home)
        self.env = dict(os.environ)
        self.env["DSH_HOME"] = str(self.home)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "harness.py"), "knowledge", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=self.env, timeout=30,
        )

    def test_health_ok_on_existing_source(self):
        p = self._run("health")
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["ok"])
        self.assertEqual(d["checks"][0]["status"], "ok")

    def test_mount_registers_read_only(self):
        p = self._run("mount", "--role", "demo-archivist", "--domain", "local:knowledge-source-a")
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["ok"])
        self.assertEqual(d["mount_mode"], "read_only")
        self.assertEqual(d["state"], "registered")
        mounts_file = self.home / "harness" / "knowledge-mounts.json"
        self.assertTrue(mounts_file.exists())
        data = json.loads(mounts_file.read_text(encoding="utf-8"))
        self.assertTrue(any(m["persona_id"] == "demo-archivist" and m["source_id"] == "local:knowledge-source-a"
                            for m in data["mounts"]))

    def test_delegate_matches_domain_and_allows_steward(self):
        p = self._run("delegate", "--question", "女性主义理论怎么理解？", "--role", "demo-archivist")
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["matched"])
        self.assertIn("demo-archivist", d["responsible_roles"])
        self.assertTrue(d["allowed"])

    def test_suggest_returns_limited_readonly_snippet(self):
        kb_dir = self.home / "local" / "kb-a"
        (kb_dir / "theory.md").write_text("女性主义理论强调差异性、情境与批判性。", encoding="utf-8")
        p = self._run("suggest", "--question", "女性主义理论怎么理解？", "--role", "demo-archivist", "--limit", "3")
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        d = json.loads(p.stdout)
        self.assertTrue(d["ok"])
        self.assertTrue(d["allowed"])
        self.assertTrue(d["delegate"]["matched"])
        self.assertTrue(any("女性主义理论强调差异性" in m.get("snippet", "") for m in d["matches"]))


if __name__ == "__main__":
    unittest.main()
