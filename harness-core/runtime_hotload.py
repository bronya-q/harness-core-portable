#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime_hotload.py — 全局 runtime context 状态中枢（R1）。

作用：把 active persona + active mode 写入一个统一运行时上下文，
让 memory/persona/MCP/workspace 等入口都能读取同一个“当前角色状态”。

诚实边界：这是**状态登记**，不是所有入口都已经真正消费该上下文。
激活标记仍不等于全入口运行时热挂载。
"""
import json
import os
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HARNESS_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness"
RUNTIME_FILE = HARNESS_DIR / "runtime-context.json"


def write_context(persona_id=None, mode_id=None, details=None):
    HARNESS_DIR.mkdir(parents=True, exist_ok=True)
    ctx = {"schema_version": 1, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "persona_id": persona_id, "mode_id": mode_id, "details": details or {},
           "note": "运行时上下文状态登记；不代表所有入口已完成全局热挂载。"}
    RUNTIME_FILE.write_text(json.dumps(ctx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ctx


def load_context():
    if not RUNTIME_FILE.exists():
        return {"schema_version": 1, "persona_id": None, "mode_id": None,
                "note": "尚无 runtime-context.json；未登记当前角色上下文。"}
    try:
        return json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"schema_version": 1, "persona_id": None, "mode_id": None}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if args and args[0] == "runtime":
        args = args[1:]
    if not args:
        print(__doc__)
        return 0
    sub = args[0]
    if sub == "status":
        print(json.dumps({"ok": True, **load_context()}, ensure_ascii=False, indent=2))
        return 0
    if sub == "clear":
        if RUNTIME_FILE.exists():
            RUNTIME_FILE.unlink()
        print(json.dumps({"ok": True, "note": "已清除运行时上下文登记。"}, ensure_ascii=False))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
