#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""facts.py — 原子事实存储 + 去重 + 遗忘墓碑（P1 记忆层升级）。"""
import argparse
import hashlib
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms

def _connect():
    c = sqlite3.connect(str(ms.db_path()))
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS facts(
      id TEXT PRIMARY KEY,
      entity TEXT NOT NULL,
      content TEXT NOT NULL,
      importance REAL DEFAULT 0.5,
      evidence_id INTEGER,
      hash TEXT UNIQUE,
      created_at REAL,
      archived INTEGER DEFAULT 0,
      source TEXT DEFAULT 'manual'
    );
    CREATE TABLE IF NOT EXISTS forget_tombstones(
      id TEXT PRIMARY KEY,
      entity TEXT NOT NULL,
      cutoff REAL,
      note TEXT,
      created_at REAL,
      restored_at REAL
    );
    """)
    return c

def fact_hash(entity, content):
    return hashlib.sha256((entity + "\x00" + content).encode("utf-8")).hexdigest()

def cmd_add(args):
    c = _connect()
    h = fact_hash(args.entity, args.content)
    row = c.execute("SELECT id FROM facts WHERE hash=?", (h,)).fetchone()
    if row:
        c.close()
        print(json.dumps({"ok": True, "duplicate": True, "id": row["id"]}, ensure_ascii=False))
        return 0
    fid = uuid.uuid4().hex[:16]
    c.execute("INSERT INTO facts(id,entity,content,importance,evidence_id,hash,created_at,source) VALUES(?,?,?,?,?,?,?,?)",
              (fid, args.entity, args.content, args.importance, args.evidence_id, h, time.time(), args.source))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "duplicate": False, "id": fid, "hash": h[:12]}, ensure_ascii=False))
    return 0

def cmd_list(args):
    c = _connect()
    q = "SELECT * FROM facts WHERE archived=0"
    params = []
    if args.entity:
        q += " AND entity LIKE ?"
        params.append("%" + args.entity + "%")
    q += " ORDER BY created_at DESC LIMIT ?"
    params.append(args.limit)
    rows = c.execute(q, params).fetchall()
    c.close()
    print(json.dumps({"ok": True, "facts": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0

def cmd_stats(args):
    c = _connect()
    total = c.execute("SELECT COUNT(*) n FROM facts WHERE archived=0").fetchone()["n"]
    entities = c.execute("SELECT COUNT(DISTINCT entity) n FROM facts WHERE archived=0").fetchone()["n"]
    tombs = c.execute("SELECT COUNT(*) n FROM forget_tombstones WHERE restored_at IS NULL").fetchone()["n"]
    c.close()
    print(json.dumps({"ok": True, "facts": total, "entities": entities, "active_tombstones": tombs}, ensure_ascii=False))
    return 0

def cmd_forget(args):
    c = _connect()
    tid = uuid.uuid4().hex[:16]
    c.execute("INSERT INTO forget_tombstones(id,entity,cutoff,note,created_at) VALUES(?,?,?,?,?)",
              (tid, args.entity, time.time(), args.note, time.time()))
    c.execute("UPDATE facts SET archived=1 WHERE entity LIKE ?", ("%" + args.entity + "%",))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "tombstone_id": tid, "entity": args.entity}, ensure_ascii=False))
    return 0

def cmd_restore(args):
    c = _connect()
    t = c.execute("SELECT * FROM forget_tombstones WHERE id=?", (args.tombstone_id,)).fetchone()
    if not t:
        c.close()
        print(json.dumps({"ok": False, "error": "not_found"}, ensure_ascii=False))
        return 1
    c.execute("UPDATE forget_tombstones SET restored_at=? WHERE id=?", (time.time(), args.tombstone_id))
    c.execute("UPDATE facts SET archived=0 WHERE entity LIKE ?", ("%" + t["entity"] + "%",))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "tombstone_id": args.tombstone_id, "restored": True}, ensure_ascii=False))
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add"); p.add_argument("--entity", required=True); p.add_argument("--content", required=True)
    p.add_argument("--importance", type=float, default=0.5); p.add_argument("--evidence-id", type=int, default=None)
    p.add_argument("--source", default="manual"); p.set_defaults(fn=cmd_add)
    p = sub.add_parser("list"); p.add_argument("--entity", default=""); p.add_argument("--limit", type=int, default=20); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("stats"); p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("forget"); p.add_argument("--entity", required=True); p.add_argument("--note", default=""); p.set_defaults(fn=cmd_forget)
    p = sub.add_parser("restore"); p.add_argument("--tombstone-id", required=True); p.set_defaults(fn=cmd_restore)
    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
