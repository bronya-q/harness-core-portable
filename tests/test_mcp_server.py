# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path.cwd()


class MCPServerTest(unittest.TestCase):
    def test_initialize_notification_tools_list(self):
        home = Path(tempfile.mkdtemp())
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["DSH_HOME"] = str(home / ".dsh")
        proc = subprocess.Popen(
            [sys.executable, "-m", "harness_core.adapters.mcp_server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", env=env,
        )
        try:
            def send(obj):
                proc.stdin.write(json.dumps(obj) + "\n")
                proc.stdin.flush()

            def read_line(timeout=10):
                line = proc.stdout.readline()
                if not line:
                    raise AssertionError("server closed stdout: " + proc.stderr.read(-1)[-300:])
                return json.loads(line)

            send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                             "clientInfo": {"name": "test", "version": "0.1"}}})
            init_resp = read_line()
            self.assertIn("serverInfo", init_resp.get("result", {}))
            send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            time.sleep(0.1)
            send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            tools_resp = read_line()
            self.assertIn("tools", tools_resp.get("result", {}))
            self.assertGreaterEqual(len(tools_resp["result"]["tools"]), 3)
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
            try:
                proc.stdout.close()
            except Exception:
                pass
            try:
                proc.stderr.close()
            except Exception:
                pass
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            import shutil
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
