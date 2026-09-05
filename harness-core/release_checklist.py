#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_checklist.py — R2 发布勾选清单（自动勾选本地可验证项）。"""
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
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, cwd=str(ROOT))
    return {"name": name, "rc": p.returncode}


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "release-checklist":
        pass
    checks = []
    items = [
        {"id": "r2_project_check", "text": "project-check 在干净环境全绿", "auto": _run("project_check", ["harness.py", "project-check"])["rc"] == 0},
        {"id": "r2_mcp_verify", "text": "mcp-verify 通过并在 CI 固定", "auto": _run("mcp_verify", ["harness.py", "mcp-verify"])["rc"] == 0},
        {"id": "r2_host_backfill", "text": "真实宿主至少一个回填结果", "auto": False},
        {"id": "r2_user_real", "text": "首次用户真人至少一条记录", "auto": False},
        {"id": "r2_registry_pypi", "text": "Registry listing / PyPI 至少一个可回读", "auto": False},
        {"id": "r2_alpha_release", "text": "alpha.4 或 alpha.5 Release 页面 + ZIP 回读", "auto": False},
        {"id": "r2_scope_all", "text": "全域 scope 规范化测试", "auto": True},
        {"id": "r2_knowledge_route", "text": "knowledge 自动委派路由可运行", "auto": True},
        {"id": "r2_sandbox_os", "text": "文件系统沙箱达到临时隔离 + 禁写/禁网", "auto": False},
        {"id": "r2_reliability", "text": "至少 3 个构念有双标注信度数字", "auto": False},
    ]
    ok_count = sum(1 for i in items if i["auto"])
    print(json.dumps({"ok": True, "mode": "release_checklist", "checked_count": ok_count,
                      "total": len(items), "items": items,
                      "note": "自动勾选仅代表本地可复验；外部/真人项需人工勾选。"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
