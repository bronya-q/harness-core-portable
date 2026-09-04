# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class MCPServerTest(unittest.TestCase):
    def test_initialize_and_tools_list(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = dict(os.environ)
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            env["DSH_HOME"] = str(home / ".dsh")
            payload = (json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n" +
                       json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n")
            p = subprocess.run([sys.executable, str(ROOT / "harness.py"), "mcp", "serve"],
                               input=payload, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=env, timeout=30)
            self.assertEqual(p.returncode, 0)
            lines = [json.loads(x) for x in p.stdout.splitlines() if x.strip()]
            self.assertEqual(lines[0]["result"]["serverInfo"]["name"], "harness-core-mcp")
            tools = lines[1]["result"]["tools"]
            self.assertGreaterEqual(len(tools), 3)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
