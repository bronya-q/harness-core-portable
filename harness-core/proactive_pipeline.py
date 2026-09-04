#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proactive_pipeline.py — P3: candidate -> decision -> delivery 主动陪伴管线。"""
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

DB = Path.home() / ".dsh" / "memory-emotion" / "proactive_sidecar.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS proactive_candidates(
      id TEXT PRIMARY KEY, scope TEXT, content TEXT, trigger TEXT,
      status TEXT DEFAULT 'pending', created_at REAL
    );
    CREATE TABLE IF NOT EXISTS proactive_decisions(
      id TEXT PRIMARY KEY, candidate_id TEXT, decision TEXT, reason TEXT,
      created_at REAL
    );
    CREATE TABLE IF NOT EXISTS proactive_deliveries(
      id TEXT PRIMARY KEY, decision_id TEXT, channel TEXT, status TEXT,
      created_at REAL
    );
    """)
    return c

def candidate_add(args):
    c = connect()
    cid = uuid.uuid4().hex[:16]
    c.execute("INSERT INTO proactive_candidates(id,scope,content,trigger,status,created_at) VALUES(?,?,?,?,?,?)",
              (cid, args.scope, args.content, args.trigger, "pending", time.time()))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "candidate_id": cid}, ensure_ascii=False))
    return 0

def decide(args):
    c = connect()
    cand = c.execute("SELECT * FROM proactive_candidates WHERE id=?", (args.candidate_id,)).fetchone()
    if not cand:
        c.close()
        print(json.dumps({"ok": False, "error": "candidate_not_found"}, ensure_ascii=False))
        return 1
    did = uuid.uuid4().hex[:16]
    c.execute("INSERT INTO proactive_decisions(id,candidate_id,decision,reason,created_at) VALUES(?,?,?,?,?)",
              (did, args.candidate_id, args.decision, args.reason, time.time()))
    c.execute("UPDATE proactive_candidates SET status=? WHERE id=?", (args.decision, args.candidate_id))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "decision_id": did, "decision": args.decision}, ensure_ascii=False))
    return 0

def deliver(args):
    c = connect()
    did = uuid.uuid4().hex[:16]
    c.execute("INSERT INTO proactive_deliveries(id,decision_id,channel,status,created_at) VALUES(?,?,?,?,?)",
              (did, args.decision_id, args.channel, args.status, time.time()))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "delivery_id": did, "channel": args.channel, "status": args.status}, ensure_ascii=False))
    return 0

def status(args):
    c = connect()
    cans = c.execute("SELECT status,COUNT(*) n FROM proactive_candidates GROUP BY status").fetchall()
    decs = c.execute("SELECT decision,COUNT(*) n FROM proactive_decisions GROUP BY decision").fetchall()
    dels = c.execute("SELECT status,COUNT(*) n FROM proactive_deliveries GROUP BY status").fetchall()
    c.close()
    print(json.dumps({"ok": True, "candidates": {r["status"]: r["n"] for r in cans},
                      "decisions": {r["decision"]: r["n"] for r in decs},
                      "deliveries": {r["status"]: r["n"] for r in dels}}, ensure_ascii=False, indent=2))
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("candidate-add"); p.add_argument("--scope", required=True); p.add_argument("--content", required=True); p.add_argument("--trigger", default=""); p.set_defaults(fn=candidate_add)
    p = sub.add_parser("decide"); p.add_argument("--candidate-id", required=True); p.add_argument("--decision", choices=("approve","deny","defer")); p.add_argument("--reason", default=""); p.set_defaults(fn=decide)
    p = sub.add_parser("deliver"); p.add_argument("--decision-id", required=True); p.add_argument("--channel", required=True); p.add_argument("--status", default="sent"); p.set_defaults(fn=deliver)
    p = sub.add_parser("status"); p.set_defaults(fn=status)
    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
