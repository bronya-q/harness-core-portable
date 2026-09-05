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


class CardGameTest(unittest.TestCase):
    def test_deck_has_public_pairs_and_distractors(self):
        p = subprocess.run(
            [sys.executable, str(SKILL / "card_game.py"), "deck"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        obj = json.loads(p.stdout)
        deck = obj["cards"] if isinstance(obj, dict) else obj
        self.assertEqual(len(deck), 14)
        pair_count = sum(1 for c in deck if c["thread_id"])
        self.assertEqual(pair_count, 10)

    def test_auto_play_smoke(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["DSH_HOME"] = str(home)
        p = subprocess.run(
            [sys.executable, str(SKILL / "card_game.py"), "play", "--auto", "--seed", "42",
             "--rounds", "1", "--hand-size", "4"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, timeout=30,
        )
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-300:])
        self.assertIn("游戏结束", p.stdout)
        try:
            import shutil
            shutil.rmtree(home, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
