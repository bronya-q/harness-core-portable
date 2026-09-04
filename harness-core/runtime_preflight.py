#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime_preflight.py — 本地运行前置检查。
默认只读；--live 才探测本地 Ollama 和现有 dsh headless DeepSeek 入口。
不自动修复，不输出凭据，不修改 profile/config/database。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOME = Path.home()
SKILL = Path(__file__).resolve().parent
DSH_HOME = Path(os.environ.get("DSH_HOME", HOME / ".dsh"))

def check_file(path):
    return {"exists": path.exists(), "path": str(path)}

def run_cmd(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout": p.stdout.strip()[-500:], "stderr": p.stderr.strip()[-500:]}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:300]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="探测本地模型服务并发起最小 DeepSeek 请求")
    args = ap.parse_args()
    result = {
        "dsh_home": str(DSH_HOME),
        "files": {
            "agents": check_file(DSH_HOME / "AGENTS.md"),
            "anchored_preset": check_file(DSH_HOME / ".agent-presets" / "anchored-standard" / "preset.yml"),
            "memory_db": check_file(DSH_HOME / "memory-emotion" / "memory.db"),
            "vector_db": check_file(DSH_HOME / "memory-emotion" / "nine_dim_vectors.db"),
            "project_routes": check_file(SKILL / "project-routes.json"),
        },
        "dsh": {},
        "live": {},
        "warnings": [],
    }
    dsh = shutil.which("dsh")
    if not dsh:
        # Windows 安装器可能不在当前 PATH；只记录缺失，不扫描/改 PATH。
        result["dsh"] = {"ok": False, "error": "dsh_not_in_path"}
        result["warnings"].append("dsh executable is not on PATH")
    else:
        result["dsh"] = {"ok": True, "version": run_cmd([dsh, "--version"])}
    # Open Design 当前以 web profile 的 MCP 客户端接入，不再要求独立 profile 目录。
    web_cordis = DSH_HOME / "profiles" / "web" / "cordis.patch.yml"
    try:
        od_configured = ("mcp-open-design" in web_cordis.read_text(encoding="utf-8", errors="replace")) or \
                        ("serverName: open-design" in web_cordis.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        od_configured = False
    if not od_configured:
        result["warnings"].append("open-design MCP server is not configured in web profile")
    if args.live:
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
                models = json.loads(r.read().decode("utf-8", "replace")).get("models", [])
            names = [m.get("name", "") for m in models]
            result["live"]["ollama"] = {"ok": True, "models": names, "bge_m3": any(n.startswith("bge-m3") for n in names)}
        except Exception as exc:
            result["live"]["ollama"] = {"ok": False, "error": type(exc).__name__}
        if dsh:
            result["live"]["deepseek_headless"] = run_cmd([dsh, "--profile", "headless", "请只回复 PREFLIGHT_DEEPSEEK_OK"], timeout=120)
        else:
            result["live"]["deepseek_headless"] = {"ok": False, "error": "dsh_not_in_path"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
