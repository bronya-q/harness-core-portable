#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ecosystem_status.py — Agent 生态兼容矩阵状态。"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CONFIG = Path(__file__).resolve().parent.parent / "docs" / "AGENT_COMPATIBILITY.json"


def main():
    if not CONFIG.exists():
        print(json.dumps({"ok": False, "error": "missing_agent_compatibility_json"}, ensure_ascii=False))
        return 1
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    print(json.dumps({"ok": True, "mode": "ecosystem_status", "entries": cfg.get("entries", [])},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
