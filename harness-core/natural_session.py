#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""natural_session.py — 自然真实流样本采集器。"""

import argparse

import subprocess

import sys

from pathlib import Path



try:

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

except Exception:

    pass



ROLEPLAY = Path.home() / "Documents" / "harness" / "whale-sister" / "roleplay_memory_chat.py"





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument("--persona", required=True, choices=("demo-alice", "demo-storykeeper", "demo-bob"))

    ap.add_argument("--num-predict", type=int, default=64)

    args = ap.parse_args()

    print("=== 自然真实流采集：" + args.persona + " ===")

    print("直接输入你的话；输入 exit 或 quit 结束。")

    count = 0

    while True:

        try:

            line = input("\n> ").strip()

        except EOFError:

            break

        if not line:

            print("\n[提示] 请输入内容，或输入 exit 退出。", flush=True)

            continue

        if line.lower() in ("exit", "quit"):

            break

        count += 1

        print("\n[roleplay %d]（生成中，请稍候...）" % count, flush=True)

        cmd = [

            sys.executable, str(ROLEPLAY),

            "--persona", args.persona,

            "--prompt", line,

            "--expression-packet", "--canary-pair",

            "--session-kind", "real",

            "--source-kind", "natural",

            "--num-predict", str(args.num_predict),

            "--canary-select", "enhanced",

        ]

        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, stdin=subprocess.DEVNULL)

        print(r.stdout.strip()[:800], flush=True)

        if r.returncode != 0:

            print("ERR rc=%s stdout=%r stderr=%r" % (r.returncode, r.stdout[-300:], r.stderr[-300:]), flush=True)

    print("\n完成：共 %d 条自然真实会话。" % count, flush=True)





if __name__ == "__main__":

    main()

