#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""migration_commands.py — 本地 SQLite schema 版本检查与迁移计划（基础版）。

用法：
  python harness.py migration status
  python harness.py migration check
  python harness.py migration dry-run
  python harness.py migration policy
  python harness.py migration prepare --backup
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"
MIN_SCHEMA = 1

DB_FILES = [
    "memory.db",
    "notebooks.db",
    "story_core.db",
    "events.db",
    "vector_queue.db",
]


def _schema_of(path):
    if not Path(path).exists():
        return {"path": str(path), "exists": False, "schema_version": None}
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'").fetchall()
        ver = None
        if rows:
            r = con.execute("SELECT version FROM schema_version ORDER BY rowid DESC LIMIT 1").fetchone()
            ver = r[0] if r else 1
        con.close()
        return {"path": str(path), "exists": True, "schema_version": ver,
                "has_schema_table": bool(rows)}
    except Exception as e:
        return {"path": str(path), "exists": True, "schema_version": None, "error": str(e)}


def cmd_status():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dbs = []
    for name in DB_FILES:
        dbs.append(_schema_of(DATA_DIR / name))
    print(json.dumps({"ok": True, "mode": "migration_status", "min_schema": MIN_SCHEMA,
                      "data_dir": str(DATA_DIR), "databases": dbs}, ensure_ascii=False, indent=2))
    return 0


def cmd_check():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    issues = []
    for name in DB_FILES:
        p = DATA_DIR / name
        if not p.exists():
            continue
        info = _schema_of(p)
        ver = info.get("schema_version")
        if ver is None and info.get("exists") and not info.get("has_schema_table"):
            # 旧库没有 schema_version 表，按 0 处理，提示需要迁移。
            issues.append(f"{name}:missing_schema_version_table")
        elif ver is not None and ver < MIN_SCHEMA:
            issues.append(f"{name}:schema_version_{ver}<{MIN_SCHEMA}")
    print(json.dumps({"ok": len(issues) == 0, "mode": "migration_check",
                      "issues": issues, "note": "仅检查本地 SQLite；不改变任何数据。"},
                     ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def cmd_dry_run():
    issues = []
    plan = []
    for name in DB_FILES:
        p = DATA_DIR / name
        if not p.exists():
            continue
        info = _schema_of(p)
        ver = info.get("schema_version")
        if not info.get("has_schema_table"):
            plan.append({"database": name, "action": "add_schema_version_table",
                         "current_version": None, "target_version": MIN_SCHEMA})
            issues.append(f"{name}:missing_schema_version_table")
        elif ver is None or ver < MIN_SCHEMA:
            plan.append({"database": name, "action": "migrate",
                         "current_version": ver, "target_version": MIN_SCHEMA})
            issues.append(f"{name}:needs_migration")
    print(json.dumps({"ok": len(issues) == 0, "mode": "migration_dry_run",
                      "plan": plan, "note": "只读计划，未执行任何写入。"}, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def cmd_policy():
    policy = {
        "schema_version": 1,
        "minimum_core_version": "0.1.0",
        "compatibility_window": "保留上一 schema 版本；跨主版本需显式迁移再使用",
        "deprecation": "弃用功能会先在文档标注，再至少保留一个版本窗口",
        "backup_before_migrate": True,
        "dry_run_before_apply": True,
        "note": "当前为策略声明；实际迁移动作尚未逐库实现，不能声称已完成生产迁移。",
    }
    print(json.dumps({"ok": True, "mode": "migration_policy", "policy": policy},
                     ensure_ascii=False, indent=2))
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == "migration":
        args = args[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0]
    if cmd == "status":
        return cmd_status()
    if cmd == "check":
        return cmd_check()
    if cmd == "dry-run":
        return cmd_dry_run()
    if cmd == "policy":
        return cmd_policy()
    if cmd == "prepare" and "--backup" in sys.argv[2:]:
        # 简单备份：复制 events.db / memory.db 到 backup 目录
        import shutil
        backup_root = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness-backups" / ("pre-migrate-" + time.strftime("%Y%m%d-%H%M%S"))
        backup_root.mkdir(parents=True, exist_ok=True)
        copied = []
        for name in DB_FILES:
            p = DATA_DIR / name
            if p.exists():
                shutil.copy2(p, backup_root / name)
                copied.append(name)
        print(json.dumps({"ok": True, "mode": "migration_prepare", "backup": str(backup_root),
                          "copied": copied, "note": "迁移前备份已创建；实际迁移未执行。"},
                         ensure_ascii=False, indent=2))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
