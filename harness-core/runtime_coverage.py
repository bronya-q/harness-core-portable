#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime_coverage.py — 检查 runtime context 被哪些入口消费。"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent

ENTRIES = [
    "roleplay_memory_chat.py",
    "assets_commands.py",
    "ux_commands.py",
    "control_commands.py",
    "situated_context.py",
    "harness_core/adapters/mcp_server.py",
    "harness_core/adapters/mcp_http_server.py",
]


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "runtime-coverage":
        pass
    results = []
    for rel in ENTRIES:
        p = SKILL / rel if not rel.startswith("harness_core") else SKILL.parent / rel
        if not p.exists():
            results.append({"entry": rel, "exists": False, "consumes_runtime": False})
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        consumes = ("runtime_hotload" in text or "load_context" in text or "runtime-context" in text)
        if rel == "harness_core/adapters/mcp_http_server.py" and "mcp_server" in text:
            consumes = True  # 复用 mcp_server gated 工具函数，间接消费
        results.append({"entry": rel, "exists": True, "consumes_runtime": consumes})
    covered = sum(1 for r in results if r["consumes_runtime"])
    print(json.dumps({"ok": True, "mode": "runtime_coverage", "total_entries": len(results),
                      "consuming_entries": covered, "entries": results,
                      "note": "覆盖检查基于源码引用；不代表所有入口真正消费上下文。"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
