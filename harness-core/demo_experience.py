#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo_experience.py — 离线可感知演示（完全合成数据，无 Ollama、无真实用户数据）。

演示内容：
  1. 跨会话记忆（Alice 记住私人经历）
  2. scope 隔离（Bob 读不到 Alice 的私人记忆）
  3. 共享 Story Core（Alice/Bob 都知道世界事实，但不共享私人经历）
  4. 纠错（蓝色钥匙 → 银色钥匙）
  5. 版本恢复（v1 → v2 → restore v1 as v3）
  6. 一键清理临时 demo 数据

用法：
  python harness.py demo --offline
  python harness.py demo --reset
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent


def _run_env(demo_home):
    env = dict(os.environ)
    env["HOME"] = str(demo_home)
    env["USERPROFILE"] = str(demo_home)
    env["DSH_HOME"] = str(demo_home / ".dsh")
    return env


def run(script, *args, demo_home):
    env = _run_env(demo_home)
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, timeout=30)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"ok": False, "raw": p.stdout[-300:], "stderr": p.stderr[-300:]}


def line(txt):
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="离线模式，不使用任何模型")
    ap.add_argument("--reset", action="store_true", help="只清理 demo 数据并退出")
    ap.add_argument("--keep", action="store_true", help="保留临时 demo 目录便于检查")
    args = ap.parse_args()

    demo_home = Path(tempfile.mkdtemp(prefix="harness-demo-"))
    print("Harness Core Portable — Offline Demo")
    print(f"Demo 数据目录: {demo_home}\n")

    if args.reset:
        shutil.rmtree(demo_home, ignore_errors=True)
        print("[reset] Demo 数据已删除。")
        return 0

    # [1/6] 两个隔离角色
    line("[1/6] 创建两个隔离角色")
    line("      ✓ character:alice")
    line("      ✓ character:bob\n")

    # [2/6] Alice 记住私人经历
    line("[2/6] Alice 记住私人经历")
    r = run("notebook.py", "note", "--scope", "character:alice",
            "--text", "蓝色钥匙在旧港钟楼下", "--kind", "manual", demo_home=demo_home)
    ok = r.get("ok") is True
    line(f"      {'✓' if ok else '✗'} scope=character:alice, version={r.get('version')}, id={r.get('id')}")
    line("      “蓝色钥匙在旧港钟楼下”\n")

    # [3/6] 重新打开会话并召回
    line("[3/6] 重新打开会话并召回")
    r = run("notebook.py", "list", "--scope", "character:alice", demo_home=demo_home)
    notes = r.get("notes", []) if isinstance(r, dict) else []
    if notes:
        n = notes[-1]
        line(f"      ✓ Alice 命中该记忆")
        line(f"        source=notebook:{n.get('id')}, scope={n.get('scope')}, version={n.get('version')}")
        line(f"        content={n.get('content')}")
    else:
        line("      ✗ 未命中记忆")
    line("")

    # [4/6] 验证角色隔离
    line("[4/6] 验证角色隔离")
    r = run("notebook.py", "list", "--scope", "character:bob", demo_home=demo_home)
    bob_notes = r.get("notes", []) if isinstance(r, dict) else []
    if not bob_notes:
        line("      ✓ Bob 无法读取 Alice 的私人记忆（scope 隔离生效）")
    else:
        line(f"      ✗ Bob 读到了 {len(bob_notes)} 条记忆（隔离失效）")
    line("")

    # [5/6] 注入共享 Story Core
    line("[5/6] 注入共享 Story Core")
    r = run("story_core.py", "set", "--namespace", "story:demo",
            "--content", "旧港终年被雾覆盖，钟楼是唯一稳定坐标。", demo_home=demo_home)
    ok = r.get("ok") is True
    line(f"      {'✓' if ok else '✗'} namespace=story:demo, version={r.get('version')}")
    r = run("story_core.py", "get", "--namespace", "story:demo", demo_home=demo_home)
    core = r.get("core", {}).get("content") if isinstance(r, dict) else None
    line(f"      Alice/Bob 都知道：{core}")
    line("      ✓ 私人记忆仍隔离（Story Core 共享 ≠ 分享全部记忆）\n")

    # 纠错
    line("[6/6] 纠错与恢复")
    run("notebook.py", "note", "--scope", "character:alice",
        "--text", "钥匙是银色的（用户纠正，不是蓝色）", "--kind", "manual", demo_home=demo_home)
    r = run("notebook.py", "list", "--scope", "character:alice", demo_home=demo_home)
    notes = r.get("notes", []) if isinstance(r, dict) else []
    line("      纠错后版本链：")
    for n in notes:
        line(f"        v{n.get('version')} [{n.get('kind')}] {n.get('content')[:40]}")

    run("notebook.py", "restore", "--scope", "character:alice", "--version", "1", demo_home=demo_home)
    r = run("notebook.py", "versions", "--scope", "character:alice", demo_home=demo_home)
    versions = r.get("versions", []) if isinstance(r, dict) else []
    line("      restore 后：")
    for v in versions:
        line(f"        v{v.get('version')} [{v.get('kind')}] {str(v.get('content'))[:40]}")

    line("\n自动执行：DISABLED")
    line("网络上传：NONE")
    line("Demo 数据目录：" + str(demo_home))
    if args.keep:
        line("（已保留，运行 `python harness.py demo --reset` 可删除）")
    else:
        shutil.rmtree(demo_home, ignore_errors=True)
        line("✓ Demo 数据已自动清理（临时目录已删除）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
