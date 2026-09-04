# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path.cwd()


class MCPServerTest(unittest.TestCase):
    def test_initialize_notification_tools_list(self):
        home = Path(tempfile.mkdtemp())
        try:
            env = dict(os.environ)
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            env["DSH_HOME"] = str(home / ".dsh")
            init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "test", "version": "0.1"}}}
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            tools = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            payload = json.dumps(init) + "\n" + json.dumps(notif) + "\n" + json.dumps(tools) + "\n"
            p = subprocess.run([sys.executable, "-m", "harness_core.adapters.mcp_server"],
                               input=payload, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=env, timeout=30)
            self.assertEqual(p.returncode, 0)
            lines = [json.loads(x) for x in p.stdout.splitlines() if x.strip()]
            init_resp = next((l for l in lines if isinstance(l.get("result"), dict) and "serverInfo" in l.get("result", {})), None)
            self.assertIsNotNone(init_resp, "missing initialize result: " + p.stdout[:300])
            self.assertEqual(init_resp["result"]["serverInfo"]["name"], "harness-core-mcp")
            tools_resp = next((l for l in lines if isinstance(l.get("result"), dict) and "tools" in l.get("result", {})), None)
            self.assertIsNotNone(tools_resp, "missing tools result: " + p.stdout[:500])
            self.assertGreaterEqual(len(tools_resp["result"]["tools"]), 3)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
