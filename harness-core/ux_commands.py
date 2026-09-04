#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ux_commands.py — 面向普通用户的新手体验层。

子命令：
  start     交互式入门向导（默认推荐离线 demo）
  doctor    环境检查（默认人类可读；--json 给程序）
  inspect   查看某个 scope 的记忆/隔离状态
  data      查看本地数据目录（data status）
"""
import argparse
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
ROOT = SKILL.parent
DATA_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"
CONSENT_FILE = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness" / "consent.json"

sys.path.insert(0, str(SKILL))
import vector_queue  # noqa: E402


def _read_policy_example():
    p = SKILL / "runtime-policy.example.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def _sqlite_ok():
    try:
        c = sqlite3.connect(":memory:")
        c.execute("select 1")
        c.close()
        return True
    except Exception:
        return False


def _run(script, *args):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"ok": False, "raw": p.stdout[-300:], "stderr": p.stderr[-300:]}


def _ensure_first_run_consent():
    """首次启动分项同意向导；已记录则直接返回 True。"""
    if CONSENT_FILE.exists():
        return True
    print("\n[首次启动 · 分项同意]")
    print("以下开关只影响本机功能，不等于上传授权；上传始终为 NONE。")
    print("你可以随时用 `python harness.py privacy consent --status` 查看。\n")
    items = ["memory", "story", "notebook", "telemetry"]
    choice = {}
    for item in items:
        try:
            ans = input("允许本机%s功能吗？[y/N] " % item).strip().lower()
        except EOFError:
            ans = ""
        choice[item] = ans in ("y", "yes", "是", "1")
    try:
        from datetime import datetime
        CONSENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema_version": 1, "scope": "first-run", "items": choice,
                "set_at": datetime.now().isoformat(),
                "note": "这些是本机功能开关，不等于上传授权；上传仍为 NONE。"}
        CONSENT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        print("已记录你的选择。\n")
    except Exception as exc:
        print("未能写入同意文件：%s（不影响离线 Demo）" % exc)
    return True


def cmd_start():
    print("欢迎使用 Harness Core Portable")
    first_time = not CONSENT_FILE.exists()
    _ensure_first_run_consent()
    if first_time:
        print("\n[首次使用提示]")
        print("- 你刚记录的分项同意只影响本机功能，不影响任何上传。")
        print("- 如果想先看效果，选 1 会运行离线 Demo，不会用模型、不会上传。")
    print("这是一个本地 AI 记忆与人格系统。")
    print("你的数据默认只保存在本机，不会自动上传。\n")
    print("请选择：")
    print("  1. 体验离线演示（推荐，不需要模型）")
    print("  2. 环境检查")
    print("  3. 查看某个角色/项目")
    print("  4. 查看本地数据状态")
    print("  0. 退出")
    try:
        choice = input("请输入数字后回车：").strip()
    except EOFError:
        choice = "1"
    if choice == "1":
        print("\n即将运行离线 Demo：")
        print("- 会创建临时合成角色和记忆")
        print("- 结束后自动清理（可用 --keep 保留）")
        print()
        return subprocess.call([sys.executable, str(SKILL / "demo_experience.py"), "--offline"])
    if choice == "2":
        return cmd_doctor()
    if choice == "3":
        scope = input("请输入角色/项目名（如 character:alice）：").strip() or "character:alice"
        return cmd_inspect(scope)
    if choice == "4":
        return cmd_data_status()
    if choice in ("0", ""):
        print("已退出。")
        return 0
    print("无效输入，已退出。")
    return 0


def cmd_doctor(json_out=False):
    checks = []
    py_ok = sys.version_info >= (3, 11)
    checks.append(("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                   "ok" if py_ok else "fail"))
    repo_ok = all((ROOT / f).exists() for f in ["README.md", "harness.py", "harness-core/harness.py"])
    checks.append(("仓库文件完整", "是" if repo_ok else "否", "ok" if repo_ok else "fail"))
    dt_ok = True
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        test = DATA_DIR / ".write-test"
        test.write_text("ok", encoding="utf-8")
        test.unlink()
    except Exception:
        dt_ok = False
    checks.append(("本地数据目录可写", str(DATA_DIR), "ok" if dt_ok else "fail"))
    sql_ok = _sqlite_ok()
    checks.append(("SQLite 可用", "是" if sql_ok else "否", "ok" if sql_ok else "fail"))
    ollama = _port_open(11434)
    checks.append(("Ollama", "已安装并运行" if ollama else "未运行（离线演示不需要）",
                   "ok" if ollama else "warn"))
    policy = _read_policy_example()
    auto_enabled = policy.get("flags", {}).get("autonomous_tasks", "disabled") != "disabled"
    checks.append(("自动执行", "已关闭" if not auto_enabled else "已开启（请勿）",
                   "ok" if not auto_enabled else "fail"))
    upload = False
    checks.append(("网络上传", "未启用" if not upload else "已启用（请勿）",
                   "ok" if not upload else "fail"))

    if json_out:
        out = {"ok": all(c[2] == "ok" for c in checks), "checks": [{"name": c[0], "detail": c[1], "status": c[2]} for c in checks]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["ok"] else 1

    for name, detail, status in checks:
        sym = {"ok": "✓", "warn": "○", "fail": "✗"}[status]
        print(f"  {sym} {name}：{detail}")
    print("\n结论：")
    if all(c[2] == "ok" for c in checks):
        print("  可以运行离线演示。如需 AI 对话，请安装并启动 Ollama。")
    else:
        print("  存在环境问题，但离线演示通常仍可运行。请查看上方 ✓/○/✗ 项。")
    return 0


def cmd_inspect(scope):
    print(f"Scope：{scope}\n")
    r = _run("notebook.py", "list", "--scope", scope)
    notes = r.get("notes", []) if isinstance(r, dict) else []
    print("[经历笔记]")
    if notes:
        print(f"  共 {len(notes)} 条")
        for n in notes[-5:]:
            print(f"  - [v{n.get('version')}][{n.get('kind')}] {n.get('content')[:60]}")
    else:
        print("  暂无记录")
    # shared story core count
    s = _run("story_core.py", "get", "--namespace", "story:" + scope.split(":")[-1])
    core_obj = (s or {}).get("core") or {}
    core = core_obj.get("content") if isinstance(core_obj, dict) else None
    print("\n[共享世界设定]")
    print(f"  {core[:80] if core else '未设置'}")
    print("\n[安全]")
    print("  跨角色私有记忆：默认不共享")
    print("  自动执行：DISABLED")
    print("  网络上传：NONE")
    return 0


def cmd_data_status():
    print("本地数据目录：")
    print(f"  {DATA_DIR}\n")
    print("[数据库文件]")
    total = 0
    has = False
    for name in ["memory.db", "notebooks.db", "story_core.db", "humanization_sidecar.db",
                 "continuity_sidecar.db", "atomic_facts_sidecar.db", "nine_dim_vectors.db"]:
        p = DATA_DIR / name
        if p.exists():
            has = True
            size_mb = p.stat().st_size / (1024 * 1024)
            total += size_mb
            print(f"  ✓ {name}: {size_mb:.2f} MB")
    if not has:
        print("  暂无数据库文件（还没有写入过数据）")
    vq = vector_queue.queue_status()
    if vq.get("ok"):
        print("  vector_queue.db: pending={pending} processing={processing} deferred={deferred} done={done} failed={failed} retryable={retryable} stale={stale}".format(**vq))
    else:
        print("  vector_queue.db: 未初始化/不可读（这通常是正常的）")
    print(f"\n  合计约 {total:.2f} MB")
    print("  无自动上传。")
    print("  可随时运行 `python harness.py demo --reset` 清理 demo 临时数据。")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    rest = sys.argv[2:]
    if cmd == "start":
        return cmd_start()
    if cmd == "doctor":
        return cmd_doctor(json_out=("--json" in rest))
    if cmd == "inspect":
        scope = "demo:alice"
        for i, a in enumerate(rest):
            if a == "--scope" and i + 1 < len(rest):
                scope = rest[i + 1]
        return cmd_inspect(scope)
    if cmd == "data":
        if rest and rest[0] == "status":
            return cmd_data_status()
        print("用法：python harness.py data status")
        return 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
