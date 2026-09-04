#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""story_core.py — Kimi Agent Swarm 启发：共享 story core（多角色/多任务共同引用）。"""
import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DB = Path.home() / ".dsh" / "memory-emotion" / "story_core.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS story_core(
      id TEXT PRIMARY KEY, namespace TEXT, content TEXT, version INTEGER,
      created_at REAL, updated_at REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS story_core_history(
      id INTEGER PRIMARY KEY AUTOINCREMENT, namespace TEXT, content TEXT, version INTEGER,
      created_at REAL)""")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_story_core_namespace ON story_core(namespace)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_story_core_history_ns_ver ON story_core_history(namespace, version)")
    return c

def set_core(args):
    c = connect()
    row = c.execute("SELECT * FROM story_core WHERE namespace=?", (args.namespace,)).fetchone()
    if row:
        c.execute("UPDATE story_core SET content=?, version=version+1, updated_at=? WHERE id=?", (args.content, time.time(), row["id"]))
        ver = row["version"] + 1
        c.execute("INSERT INTO story_core_history(namespace,content,version,created_at) VALUES(?,?,?,?)", (args.namespace, args.content, ver, time.time()))
    else:
        import uuid
        c.execute("INSERT INTO story_core(id,namespace,content,version,created_at,updated_at) VALUES(?,?,?,1,?,?)",
                  (uuid.uuid4().hex[:16], args.namespace, args.content, time.time(), time.time()))
        c.execute("INSERT INTO story_core_history(namespace,content,version,created_at) VALUES(?,?,1,?)", (args.namespace, args.content, time.time()))
    c.commit(); c.close()
    row2 = connect().execute("SELECT * FROM story_core WHERE namespace=?", (args.namespace,)).fetchone()
    print(json.dumps({"ok": True, "namespace": args.namespace, "version": row2["version"]}, ensure_ascii=False))
    return 0

def get_core(args):
    c = connect()
    row = c.execute("SELECT * FROM story_core WHERE namespace=?", (args.namespace,)).fetchone()
    c.close()
    print(json.dumps({"ok": True, "namespace": args.namespace, "core": dict(row) if row else None}, ensure_ascii=False, indent=2))
    return 0


def history(args):
    c = connect()
    rows = c.execute("SELECT * FROM story_core_history WHERE namespace=? ORDER BY version DESC", (args.namespace,)).fetchall()
    c.close()
    print(json.dumps({"ok": True, "namespace": args.namespace, "history": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0


def diff(args):
    import difflib
    c = connect()
    rows = c.execute("SELECT * FROM story_core_history WHERE namespace=? ORDER BY version DESC LIMIT 2", (args.namespace,)).fetchall()
    c.close()
    if len(rows) < 2:
        print(json.dumps({"ok": False, "error": "need_at_least_two_versions"}, ensure_ascii=False))
        return 1
    a = rows[1]["content"]; b = rows[0]["content"]
    diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(), "v%d" % rows[1]["version"], "v%d" % rows[0]["version"], lineterm=""))
    print(json.dumps({"ok": True, "namespace": args.namespace, "diff": diff}, ensure_ascii=False, indent=2))
    return 0



def restore(args):
    import uuid
    c = connect()
    target = c.execute("SELECT * FROM story_core_history WHERE namespace=? AND version=?", (args.namespace, args.version)).fetchone()
    if not target:
        c.close()
        print(json.dumps({"ok": False, "error": "version_not_found"}, ensure_ascii=False))
        return 1
    row = c.execute("SELECT * FROM story_core WHERE namespace=?", (args.namespace,)).fetchone()
    if row:
        ver = row["version"] + 1
        c.execute("UPDATE story_core SET content=?, version=?, updated_at=? WHERE id=?", (target["content"], ver, time.time(), row["id"]))
    else:
        ver = 1
        c.execute("INSERT INTO story_core(id,namespace,content,version,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                  (uuid.uuid4().hex[:16], args.namespace, target["content"], ver, time.time(), time.time()))
    c.execute("INSERT INTO story_core_history(namespace,content,version,created_at) VALUES(?,?,?,?)",
              (args.namespace, target["content"], ver, time.time()))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "namespace": args.namespace, "version": ver, "restored_from": target["version"]}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("set"); p.add_argument("--namespace", required=True); p.add_argument("--content", required=True); p.set_defaults(fn=set_core)
    p = sub.add_parser("get"); p.add_argument("--namespace", required=True); p.set_defaults(fn=get_core)
    p = sub.add_parser("history"); p.add_argument("--namespace", required=True); p.set_defaults(fn=history)
    p = sub.add_parser("diff"); p.add_argument("--namespace", required=True); p.set_defaults(fn=diff)
    p = sub.add_parser("restore"); p.add_argument("--namespace", required=True); p.add_argument("--version", type=int, required=True); p.set_defaults(fn=restore)
    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
