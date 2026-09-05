#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""user_test_commands.py — 首次用户测试（First-time user testing）辅助入口。

用法：
  python harness.py user-test checklist
  python harness.py user-test template [--write]
"""
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "user-testing"

TASKS = [
    "下载/克隆仓库",
    "运行 `python harness.py demo --offline`",
    "运行 `python harness.py dashboard build`",
    "用 `python harness.py memory list --scope character:alice` 找到一条记忆",
    "用 `python harness.py memory correct ...` 纠正它",
    "用 `python harness.py memory forget --id ...` 忘记某条",
    "用 `python harness.py memory restore ...` 恢复一个版本",
    "判断一条记忆属于哪个角色/scope",
    "确认本地控制台不自动上传",
    "找到本地数据目录",
    "运行 `python harness.py demo --reset` 清理演示数据",
]

RECORD_FIELDS = [
    "participant_id",
    "completion (pass/fail)",
    "time_seconds",
    "where_stuck",
    "wrong_commands_count",
    "understood_shadow (yes/no)",
    "misread_gate_fail_as_install_failure (yes/no)",
    "successfully_deleted_data (yes/no)",
]


def cmd_checklist():
    print(json.dumps({"ok": True, "mode": "user_test_checklist",
                      "tasks": TASKS, "record_fields": RECORD_FIELDS,
                      "protocol": "docs/user-testing/PROTOCOL.md",
                      "note": "找 5 个没接触过项目的人；结果脱敏后存入 docs/user-testing/。"},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_template(write=False):
    ts = time.strftime("%Y%m%d-%H%M%S")
    md = [
        "# 首次用户测试记录 " + ts,
        "",
        "> 所有结果脱敏；不记录真实用户名、路径、私人角色。",
        "",
        "## 任务清单",
        "",
    ]
    for i, task in enumerate(TASKS, 1):
        md.append(f"{i}. {task}")
    md += ["", "## 记录字段", ""]
    for f in RECORD_FIELDS:
        md.append(f"- {f}:")
    md += ["", "## 结果（每个参与者一行）", "",
           "| participant_id | completion | time_seconds | where_stuck | wrong_commands_count | understood_shadow | misread_gate_fail | successfully_deleted_data |",
           "|---|---|---|---|---|---|---|---|",
           "| p1 | | | | | | | |", ""]
    content = "\n".join(md) + "\n"
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / ("results-" + ts + ".md")
        out.write_text(content, encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(out), "note": "已生成结果模板。"},
                         ensure_ascii=False, indent=2))
        return 0
    print(json.dumps({"ok": True, "content": content}, ensure_ascii=False, indent=2))
    return 0


def cmd_simulate(write=True):
    """模拟首测流程：跑 demo + dashboard + 找记忆，生成一份标记为 simulated 的结果文件。
    这不是真实用户结果，只用于测试 pipeline。
    """
    import subprocess
    home = Path.home() / ".dsh"
    env = dict(__import__("os").environ)
    results = []
    steps = []
    def run(*args):
        p = subprocess.run([sys.executable, str(ROOT / "harness.py"), *args],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env, timeout=120)
        steps.append({"args": list(args), "rc": p.returncode})
        results.append({"pass": p.returncode == 0})
        return p
    run("demo", "--offline", "--keep")
    run("dashboard", "build")
    run("memory", "list", "--scope", "character:alice")
    ts = time.strftime("%Y%m%d-%H%M%S")
    md = [
        "# 首次用户测试模拟记录 " + ts,
        "",
        "> ⚠️ 这是 **simulated** 自动管线演示，不是真实用户结果。",
        "",
        "## 步骤",
        "",
    ]
    for st in steps:
        md.append("- `" + " ".join(st["args"]) + "` rc=" + str(st["rc"]))
    md += ["", "## 结果（模拟）", "",
           "| participant_id | completion | time_seconds | where_stuck | wrong_commands_count | ... |",
           "|---|---|---|---|---|---|",
           "| simulated-p1 | pass | n/a | n/a | 0 | ... |", ""]
    content = chr(10).join(md) + chr(10)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / ("simulated-" + ts + ".md")
    out.write_text(content, encoding="utf-8")
    print(json.dumps({"ok": True, "mode": "user_test_simulate", "output": str(out),
                      "steps": len(steps), "all_pass": all(r["pass"] for r in results),
                      "note": "模拟管线；不是真实用户。"}, ensure_ascii=False, indent=2))
    return 0 if all(r["pass"] for r in results) else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if args and args[0] == "user-test":
        args = args[1:]
    if not args:
        print(__doc__)
        return 0
    sub = args[0]
    if sub == "checklist":
        return cmd_checklist()
    if sub == "template":
        return cmd_template("--write" in args)
    if sub == "simulate":
        return cmd_simulate()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
