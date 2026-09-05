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


class RoleCommunicationTest(unittest.TestCase):
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

    def test_letter_send_and_list(self):
        home = Path(tempfile.mkdtemp())
        env = self._env(home)
        try:
            p = self._run(env, "letter", "send", "--from", "character:demo-archivist",
                          "--to", "character:demo-storykeeper", "--subject", "请审阅", "--body", "正文")
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            p2 = self._run(env, "letter", "list", "--scope", "character:demo-storykeeper")
            d = json.loads(p2.stdout)
            self.assertGreaterEqual(len(d["letters"]), 1)
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_letter_thread_builds_chain(self):
        home = Path(tempfile.mkdtemp())
        env = self._env(home)
        try:
            p = self._run(env, "letter", "send", "--from", "character:demo-archivist",
                          "--to", "character:demo-storykeeper", "--subject", "请审阅", "--body", "正文")
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            list_out = self._run(env, "letter", "list", "--scope", "character:demo-storykeeper")
            lid = json.loads(list_out.stdout)["letters"][0]["id"]
            # 直接调 thread 比较简单，避免解析更多
            p2 = self._run(env, "letter", "thread", "--scope", "character:demo-storykeeper")
            d = json.loads(p2.stdout)
            self.assertTrue(d["ok"])
            self.assertGreaterEqual(len(d["threads"]), 1)
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_situated_includes_user_relation_and_role_division(self):
        home = Path(tempfile.mkdtemp())
        env = self._env(home)
        try:
            p = self._run(env, "situated", "--scope", "character:demo-archivist")
            d = json.loads(p.stdout)
            self.assertIn("user_relation", d)
            self.assertIn("role_division", d)
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_dashboard_has_letters_card(self):
        home = Path(tempfile.mkdtemp())
        env = self._env(home)
        try:
            p = self._run(env, "dashboard", "build")
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
            s = (home / "harness-dashboard" / "index.html").read_text(encoding="utf-8")
            self.assertIn("角色信件", s)
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
