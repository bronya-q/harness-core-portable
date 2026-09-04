# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()
SKILL = ROOT / "harness-core"


class NgramFallbackTest(unittest.TestCase):
    def test_ngram_fallback_finds_after_exact_miss(self):
        mem_dir = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["MEMORY_EMOTION_DATA_DIR"] = str(mem_dir)
        env["DSH_HOME"] = str(mem_dir / ".dsh")
        try:
            add = subprocess.run(
                [sys.executable, str(SKILL / "memory_store.py"), "add",
                 "--scope", "character:demo-archivist",
                 "--content", "今天在档案室整理了一本关于星空的旧书。",
                 "--importance", "0.8"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(add.returncode, 0, add.stderr + add.stdout[-300:])
            # 带空格的查询不会精确命中子串，应触发 fallback。
            search = subprocess.run(
                [sys.executable, str(SKILL / "ngram_fallback.py"),
                 "--query", "星空 旧书", "--scope", "character:demo-archivist", "--limit", "5"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=30,
            )
            self.assertEqual(search.returncode, 0, search.stderr + search.stdout[-300:])
            rows = json.loads(search.stdout)
            self.assertTrue(rows, "ngram fallback should return at least one row")
            self.assertTrue(any(r.get("match_method") == "ngram_fallback" for r in rows))
            self.assertGreater(rows[0].get("ngram_score", 0), 0)
        finally:
            import shutil
            shutil.rmtree(mem_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
