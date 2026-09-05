#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""project_check.py — 项目一键体检（聚合多项本地检查）。"""
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent


def _run(name, args, timeout=180):
    p = subprocess.run([sys.executable, str(ROOT / args[0]), *args[1:]],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, cwd=str(ROOT))
    try:
        data = json.loads(p.stdout)
        return {"name": name, "ok": p.returncode == 0, "rc": p.returncode,
                "summary": data if isinstance(data, dict) else {"raw": str(data)[:200]}}
    except Exception:
        return {"name": name, "ok": p.returncode == 0, "rc": p.returncode,
                "summary": {"raw": p.stdout[-200:], "stderr": p.stderr[-200:]}}


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "project-check":
        pass
    checks = [
        _run("package_selfcheck", ["package_selfcheck.py"]),
        _run("mcp_verify", ["harness.py", "mcp-verify"]),
        _run("secret_scan", ["harness.py", "secret-scan"]),
        _run("migration_check", ["harness.py", "migration", "check"]),
    ]
    ok = all(c["ok"] for c in checks)
    print(json.dumps({"ok": ok, "mode": "project_check", "checks": checks,
                      "note": "聚合本地体检；不代表生产就绪或外部认证。"}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
