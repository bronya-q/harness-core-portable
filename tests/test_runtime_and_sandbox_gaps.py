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


class RuntimeAndSandboxGapsTest(unittest.TestCase):
    def _env(self, home):
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["DSH_HOME"] = str(home)
        return env

    def _run(self, env, *args):
        return subprocess.run([sys.executable, str(ROOT / "harness.py"), *args],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, timeout=30)

    def test_runtime_context_written_by_mode_switch(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = self._env(home)
            p = self._run(env, "character", "mode", "switch", "--persona", "demo-archivist", "--mode", "archival-research")
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            ctx = json.loads((home / "harness" / "runtime-context.json").read_text(encoding="utf-8"))
            self.assertEqual(ctx["persona_id"], "demo-archivist")
            self.assertEqual(ctx["mode_id"], "archival-research")
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_activate_crash_simulation_and_recover(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = self._env(home)
            char_dir = home / "harness" / "characters" / "demo-archivist"
            char_dir.mkdir(parents=True, exist_ok=True)
            (char_dir / "package-manifest.json").write_text(
                json.dumps({"schema_version": 1, "persona_id": "demo-archivist",
                            "display_name": "档案管理员", "scope": "character:demo-archivist"},
                           ensure_ascii=False), encoding="utf-8")
            p = self._run(env, "character", "activate", "demo-archivist", "--simulate-crash")
            self.assertEqual(p.returncode, 1, p.stderr + p.stdout[-300:])
            self.assertIn("crash_simulated", p.stdout)
            self.assertTrue((home / "harness" / "activate.lock").exists())
            p2 = self._run(env, "character", "recover")
            self.assertEqual(p2.returncode, 0, p2.stderr + p2.stdout[-300:])
            self.assertFalse((home / "harness" / "activate.lock").exists())
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_knowledge_index_and_health_reports_indexed(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = self._env(home)
            char_dir = home / "harness" / "characters" / "demo-archivist"
            kb_dir = home / "local" / "kb"
            char_dir.mkdir(parents=True, exist_ok=True)
            kb_dir.mkdir(parents=True, exist_ok=True)
            (char_dir / "package-manifest.json").write_text(
                json.dumps({"schema_version": 1, "persona_id": "demo-archivist",
                            "knowledge_bindings": [{"domain_id": "local:k", "source_ref": "local:k", "role": "steward"}]},
                           ensure_ascii=False), encoding="utf-8")
            (kb_dir / "a.md").write_text("女性主义理论强调差异性。", encoding="utf-8")
            (home / "harness" / "knowledge-sources.json").write_text(
                json.dumps({"schema_version": 1, "sources": [{
                    "source_id": "local:k", "display_name": "理论库", "kind": "directory",
                    "root": str(kb_dir), "portable": False, "private": True,
                    "default_access": "deny", "stewards": ["demo-archivist"]}]},
                    ensure_ascii=False), encoding="utf-8")
            p = self._run(env, "knowledge", "index", "--source", "local:k")
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            self.assertTrue(json.loads(p.stdout)["ok"])
            h = self._run(env, "knowledge", "health")
            checks = json.loads(h.stdout)["checks"]
            self.assertTrue(checks[0]["indexed"])
            self.assertEqual(checks[0]["indexed_file_count"], 1)
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_public_hcp_rejects_html_svg(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = self._env(home)
            pkg = home / "bad-html"
            pkg.mkdir(parents=True, exist_ok=True)
            (pkg / "character.json").write_text(
                json.dumps({"schema_version": 1, "persona_id": "bad-html", "display_name": "Bad",
                            "distribution": "public", "license_status": "verified"},
                           ensure_ascii=False), encoding="utf-8")
            (pkg / "evil.html").write_text("<script>alert(1)</script>", encoding="utf-8")
            p = self._run(env, "character", "validate", "--package", str(pkg), "--target", "public")
            self.assertEqual(p.returncode, 1, p.stderr + p.stdout[-300:])
            self.assertIn("untrusted_html_svg", p.stdout)
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
