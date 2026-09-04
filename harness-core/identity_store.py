#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""identity_store.py — P2: entity<-account 凭据权限层。

原则：
  - 系统只观察 account（凭据），不观察 person；
  - 权限授予 account，不授予 entity；
  - 禁止跨平台推断身份。
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

DB = Path.home() / ".dsh" / "memory-emotion" / "identity_sidecar.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS accounts(
      account_id TEXT PRIMARY KEY, entity_id TEXT, platform TEXT,
      permissions_json TEXT DEFAULT '{}', trust_level REAL DEFAULT 0.5,
      created_at REAL, updated_at REAL
    );
    CREATE TABLE IF NOT EXISTS permission_log(
      id INTEGER PRIMARY KEY AUTOINCREMENT, account_id TEXT, action TEXT,
      allowed INTEGER, ts REAL
    );
    """)
    return c

def link(args):
    c = connect()
    perms = json.loads(args.permissions_json) if args.permissions_json else {}
    c.execute("INSERT OR REPLACE INTO accounts(account_id,entity_id,platform,permissions_json,trust_level,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
              (args.account_id, args.entity_id, args.platform, json.dumps(perms, ensure_ascii=False), args.trust_level, time.time(), time.time()))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "account_id": args.account_id, "entity_id": args.entity_id, "platform": args.platform}, ensure_ascii=False))
    return 0

def perm(args):
    c = connect()
    row = c.execute("SELECT * FROM accounts WHERE account_id=?", (args.account_id,)).fetchone()
    if not row:
        c.close()
        print(json.dumps({"ok": False, "error": "account_not_found"}, ensure_ascii=False))
        return 1
    perms = json.loads(row["permissions_json"] or "{}")
    if args.action in perms:
        perms[args.action] = not args.deny if args.deny else True
    else:
        perms[args.action] = not args.deny if args.deny else True
    c.execute("UPDATE accounts SET permissions_json=?, updated_at=? WHERE account_id=?", (json.dumps(perms, ensure_ascii=False), time.time(), args.account_id))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "account_id": args.account_id, "action": args.action, "allowed": perms.get(args.action)}, ensure_ascii=False))
    return 0

def check(args):
    c = connect()
    row = c.execute("SELECT * FROM accounts WHERE account_id=?", (args.account_id,)).fetchone()
    allowed = False
    if row:
        perms = json.loads(row["permissions_json"] or "{}")
        allowed = bool(perms.get(args.action, False))
    c.execute("INSERT INTO permission_log(account_id,action,allowed,ts) VALUES(?,?,?,?)", (args.account_id, args.action, 1 if allowed else 0, time.time()))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "account_id": args.account_id, "action": args.action, "allowed": allowed}, ensure_ascii=False))
    return 0

def list_accounts(args):
    c = connect()
    rows = c.execute("SELECT * FROM accounts").fetchall()
    c.close()
    print(json.dumps({"ok": True, "accounts": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("link"); p.add_argument("--account-id", required=True); p.add_argument("--entity-id", required=True)
    p.add_argument("--platform", required=True); p.add_argument("--permissions-json", default=""); p.add_argument("--trust-level", type=float, default=0.5)
    p.set_defaults(fn=link)
    p = sub.add_parser("perm"); p.add_argument("--account-id", required=True); p.add_argument("--action", required=True); p.add_argument("--deny", action="store_true"); p.set_defaults(fn=perm)
    p = sub.add_parser("check"); p.add_argument("--account-id", required=True); p.add_argument("--action", required=True); p.set_defaults(fn=check)
    p = sub.add_parser("list"); p.set_defaults(fn=list_accounts)
    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
