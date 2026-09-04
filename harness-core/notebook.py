#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notebook.py — Kimi Agent Swarm 启发：每个 agent/role 一个持久 notebook。

- auto notes：系统/角色自动记录
- manual notes：用户手动 memo
- 带版本号，可回看
"""
import argparse
import json
import sqlite3
import sys
import time
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DB = Path.home() / ".dsh" / "memory-emotion" / "notebooks.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.execute("PRAGMA busy_timeout=5000")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS notebooks(
      id TEXT PRIMARY KEY, scope TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('auto','manual','restored')),
      content TEXT NOT NULL, version INTEGER NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL, prev_id TEXT)""")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notebooks_scope_version ON notebooks(scope, version)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notebooks_scope_kind ON notebooks(scope, kind, version)")
    return c

def _version(c, scope):
    r = c.execute("SELECT MAX(version) v FROM notebooks WHERE scope=?", (scope,)).fetchone()
    return (r["v"] or 0) + 1

def note(args):
    c = connect()
    nid = uuid.uuid4().hex[:16]
    ver = _version(c, args.scope)
    prev = c.execute("SELECT id FROM notebooks WHERE scope=? ORDER BY version DESC LIMIT 1", (args.scope,)).fetchone()
    prev_id = prev["id"] if prev else None
    c.execute("INSERT INTO notebooks(id,scope,kind,content,version,created_at,updated_at,prev_id) VALUES(?,?,?,?,?,?,?,?)",
              (nid, args.scope, args.kind, args.text, ver, time.time(), time.time(), prev_id))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "id": nid, "scope": args.scope, "version": ver, "kind": args.kind}, ensure_ascii=False))
    return 0

def list_notes(args):
    c = connect()
    rows = c.execute("SELECT * FROM notebooks WHERE scope=? ORDER BY version DESC LIMIT ?", (args.scope, args.limit)).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "notes": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0

def versions(args):
    c = connect()
    rows = c.execute("SELECT version, kind, content, created_at FROM notebooks WHERE scope=? ORDER BY version", (args.scope,)).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "versions": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0


def summary(args):
    c = connect()
    rows = c.execute("SELECT * FROM notebooks WHERE scope=? ORDER BY version DESC", (args.scope,)).fetchall()
    c.close()
    if not rows:
        print(json.dumps({"ok": True, "scope": args.scope, "summary": ""}, ensure_ascii=False))
        return 0
    lines = ["%s: %s" % (r["kind"], r["content"]) for r in rows[:args.limit]]
    summary_text = "\n".join(lines)
    print(json.dumps({"ok": True, "scope": args.scope, "summary": summary_text, "notes": len(rows)}, ensure_ascii=False))


def quote(args):
    c = connect()
    r = c.execute("SELECT * FROM notebooks WHERE id=?", (args.id,)).fetchone()
    c.close()
    if not r:
        print(json.dumps({"ok": False, "error": "not_found"}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "note": dict(r)}, ensure_ascii=False, indent=2))
    return 0


def timeline(args):
    c = connect()
    rows = c.execute("SELECT version, kind, content, created_at FROM notebooks WHERE scope=? ORDER BY version", (args.scope,)).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "timeline": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0



def restore(args):
    c = connect()
    target = c.execute("SELECT * FROM notebooks WHERE scope=? AND version=?", (args.scope, args.version)).fetchone()
    if not target:
        c.close()
        print(json.dumps({"ok": False, "error": "version_not_found"}, ensure_ascii=False))
        return 1
    ver = _version(c, args.scope)
    prev = c.execute("SELECT id FROM notebooks WHERE scope=? ORDER BY version DESC LIMIT 1", (args.scope,)).fetchone()
    prev_id = prev["id"] if prev else None
    nid = uuid.uuid4().hex[:16]
    c.execute("INSERT INTO notebooks(id,scope,kind,content,version,created_at,updated_at,prev_id) VALUES(?,?,?,?,?,?,?,?)",
              (nid, args.scope, "restored", target["content"], ver, time.time(), time.time(), prev_id))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "id": nid, "scope": args.scope, "version": ver, "restored_from": target["version"]}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("note"); p.add_argument("--scope", required=True); p.add_argument("--text", required=True); p.add_argument("--kind", default="auto", choices=("auto","manual")); p.set_defaults(fn=note)
    p = sub.add_parser("list"); p.add_argument("--scope", required=True); p.add_argument("--limit", type=int, default=20); p.set_defaults(fn=list_notes)
    p = sub.add_parser("versions"); p.add_argument("--scope", required=True); p.set_defaults(fn=versions)
    p = sub.add_parser("summary"); p.add_argument("--scope", required=True); p.add_argument("--limit", type=int, default=5); p.set_defaults(fn=summary)
    p = sub.add_parser("quote"); p.add_argument("--id", required=True); p.set_defaults(fn=quote)
    p = sub.add_parser("timeline"); p.add_argument("--scope", required=True); p.set_defaults(fn=timeline)
    p = sub.add_parser("restore"); p.add_argument("--scope", required=True); p.add_argument("--version", type=int, required=True); p.set_defaults(fn=restore)
    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
