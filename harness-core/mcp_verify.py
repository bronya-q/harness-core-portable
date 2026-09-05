#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mcp_verify.py — MCP 自检（stdio 单测 + HTTP loopback 冒烟）。"""
import json
import os
import subprocess
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent


def _run_http_verify():
    from harness_core.adapters.mcp_http_server import Handler
    import random
    # HTTP smoke 使用已配置 adapter，避免 fail-closed 把冒烟误判为失败。
    old = os.environ.get("HARNESS_MCP_ADAPTER_ID")
    if not old:
        os.environ["HARNESS_MCP_ADAPTER_ID"] = "harness-core-mcp"
    port = random.randint(18000, 20000)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        def post(method, params=None):
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                               "params": params or {}}).encode()
            req = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        init = post("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {}})
        tools = post("tools/list")
        call = post("tools/call", {"name": "usage_summary", "arguments": {}})
        return init, tools, call
    finally:
        server.shutdown()
        server.server_close()
        if not old:
            os.environ.pop("HARNESS_MCP_ADAPTER_ID", None)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "mcp-verify":
        pass
    checks = []
    # stdio unit test
    p = subprocess.run([sys.executable, "-m", "unittest", "tests.test_mcp_server"],
                       cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    checks.append({"name": "stdio_unittest", "ok": p.returncode == 0, "detail": p.stdout[-200:]})
    # http smoke
    try:
        init, tools, call = _run_http_verify()
        ok = bool(init.get("result", {}).get("serverInfo")) and bool(tools.get("result", {}).get("tools")) and "result" in call
        checks.append({"name": "http_loopback_smoke", "ok": ok,
                       "detail": "tools=%d call=%s" % (len(tools.get("result", {}).get("tools", [])), ok)})
    except Exception as e:
        checks.append({"name": "http_loopback_smoke", "ok": False, "detail": repr(e)})
    # Fail-closed 专项：未配置 adapter 必须拒绝，只有显式 HARNESS_ALLOW_UNCONFIGURED=1 才放行。
    from harness_core.adapter_gate import can
    saved = os.environ.get("HARNESS_MCP_ADAPTER_ID")
    saved_allow = os.environ.get("HARNESS_ALLOW_UNCONFIGURED")
    os.environ.pop("HARNESS_MCP_ADAPTER_ID", None)
    os.environ.pop("HARNESS_ALLOW_UNCONFIGURED", None)
    deny_when_unconfigured = not can(None, "usage_read")
    os.environ["HARNESS_ALLOW_UNCONFIGURED"] = "1"
    allow_when_explicit = can(None, "usage_read")
    if saved is not None:
        os.environ["HARNESS_MCP_ADAPTER_ID"] = saved
    else:
        os.environ.pop("HARNESS_MCP_ADAPTER_ID", None)
    if saved_allow is not None:
        os.environ["HARNESS_ALLOW_UNCONFIGURED"] = saved_allow
    else:
        os.environ.pop("HARNESS_ALLOW_UNCONFIGURED", None)
    checks.append({"name": "adapter_gate_fail_closed",
                   "ok": deny_when_unconfigured and allow_when_explicit,
                   "detail": "deny_unconfigured=%s allow_explicit=%s" % (deny_when_unconfigured, allow_when_explicit)})

    ok_all = all(c["ok"] for c in checks)
    print(json.dumps({"ok": ok_all, "mode": "mcp_verify", "checks": checks,
                      "note": "本地复现验证；不代表 Registry/真实宿主认证。"}, ensure_ascii=False, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
