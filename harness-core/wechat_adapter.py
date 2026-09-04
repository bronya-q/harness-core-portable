#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wechat_adapter.py — 微信只读探测（暂不解析）。

由于微信本地数据形态未确认，本工具只扫描 D:/WeChat 顶层结构并输出可见文件，
不读取聊天内容，不导入任何数据。
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

WEIXIN = Path("D:/WeChat")


def main():
    if not WEIXIN.exists():
        print(json.dumps({"ok": False, "error": "wechat_path_not_found", "path": str(WEIXIN)}, ensure_ascii=False, indent=2))
        return 1
    top = []
    for child in sorted(WEIXIN.iterdir()):
        if child.is_dir():
            top.append({"type": "dir", "name": child.name, "path": str(child)})
        else:
            top.append({"type": "file", "name": child.name, "size": child.stat().st_size})
    print(json.dumps({
        "ok": True,
        "mode": "wechat_readonly_probe",
        "root": str(WEIXIN),
        "entries": top[:50],
        "note": "只做结构探测；未解析聊天内容，需用户确认接口后再接入。",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    main()
