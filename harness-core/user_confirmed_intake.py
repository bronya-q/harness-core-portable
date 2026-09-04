#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""user_confirmed_intake.py — 交互式收集 user_confirmed 条目。

双击运行后，逐条输入“你确认的自我理解/价值/身份/边界”；
写入 H6 identity_entries，source=user_confirmed_archive，consent=explicit。
输入 exit 退出。
"""
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HUM = Path.home() / ".agents" / "skills" / "long-term-memory-emotion" / "humanization.py"


def add(content):
    p = subprocess.run(
        [sys.executable, str(HUM), "identity-add",
         "--scope", "user:real", "--kind", "narrative_self",
         "--content", content,
         "--source", "user_confirmed_archive",
         "--consent", "explicit",
         "--approved-by", "user"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
    )
    return p.returncode == 0


def main():
    print("=== 录入 user_confirmed 条目 ===")
    print("输入你想确认的一条自我理解/价值/身份/边界；输入 exit 退出。")
    count = 0
    while True:
        try:
            line = input("\n> ").strip()
        except EOFError:
            break
        if not line:
            print("[提示] 请输入内容，或输入 exit 退出。", flush=True)
            continue
        if line.lower() in ("exit", "quit"):
            break
        if add(line):
            count += 1
            print("[OK] 已写入 user_confirmed_archive。", flush=True)
        else:
            print("[ERR] 写入失败，请查看上方输出。", flush=True)
    print("\n完成：共写入 %d 条 user_confirmed。" % count, flush=True)


if __name__ == "__main__":
    main()
