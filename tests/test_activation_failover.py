# -*- coding: utf-8 -*-
"""tests/test_activation_failover.py — activation failure injection test."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness.py"


def _env(home):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["DSH_HOME"] = str(Path(home) / ".dsh")
    return env


def _run(home, *args):
    p = subprocess.run([sys.executable, str(HARNESS), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=_env(home), timeout=60)
    return p.returncode, p.stdout


def _write_pkg(home, pid, name):
    d = Path(home) / pid
    d.mkdir(parents=True, exist_ok=True)
    (d / "package-manifest.json").write_text(
        json.dumps({"schema_version": 1, "persona_id": pid, "display_name": name,
                    "scope": "character:" + pid, "distribution": "private_local",
                    "visibility": "private_local"}),
        encoding="utf-8")
    return d


class ActivationFailoverTest(unittest.TestCase):
    def test_simulate_failure_rolls_back(self):
        home = Path(tempfile.mkdtemp(prefix="harness-activation-test-"))
        try:
            _run(home, "character", "install", str(_write_pkg(home, "demo-x", "Demo X")))
            _run(home, "character", "install", str(_write_pkg(home, "demo-y", "Demo Y")))
            rc, _ = _run(home, "character", "activate", "demo-x")
            self.assertEqual(rc, 0)
            rc, out = _run(home, "character", "activate", "demo-y", "--simulate-failure")
            self.assertNotEqual(rc, 0)
            self.assertIn("activation_failed", out)
            rc, out = _run(home, "character", "status")
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(data["state"], "activation_failed")
            self.assertEqual(data["active"]["persona_id"], "demo-x")
            rc, out = _run(home, "character", "recover")
            self.assertEqual(rc, 0)
            rc, out = _run(home, "character", "status")
            data = json.loads(out)
            self.assertEqual(data["state"], "active")
            self.assertEqual(data["active"]["persona_id"], "demo-x")
        finally:
            for p in home.rglob("*"):
                if p.is_file():
                    try:
                        p.unlink()
                    except Exception:
                        pass
            home.rmdir() if not list(home.iterdir()) else None


if __name__ == "__main__":
    unittest.main()
