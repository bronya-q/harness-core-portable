#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""user_model_signals.py — 用户模型候选信号存储（boundary/otherness/技术主线等）。"""
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

DB = Path.home() / ".dsh" / "memory-emotion" / "user_model_signals.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS user_model_signals(
      id TEXT PRIMARY KEY, signal TEXT, metric TEXT, value TEXT, source TEXT,
      status TEXT DEFAULT 'shadow', note TEXT, created_at REAL)""")
    return c

def add(args):
    c = connect()
    sid = uuid.uuid4().hex[:16]
    c.execute("INSERT INTO user_model_signals(id,signal,metric,value,source,status,note,created_at) VALUES(?,?,?,?,?,?,?,?)",
              (sid, args.signal, args.metric, args.value, args.source, args.status, args.note, time.time()))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "id": sid, "signal": args.signal}, ensure_ascii=False))
    return 0

def list_signals(args):
    c = connect()
    rows = c.execute("SELECT * FROM user_model_signals ORDER BY created_at DESC").fetchall()
    c.close()
    print(json.dumps({"ok": True, "signals": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add"); p.add_argument("--signal", required=True); p.add_argument("--metric", required=True)
    p.add_argument("--value", required=True); p.add_argument("--source", default="deepseek")
    p.add_argument("--status", default="shadow"); p.add_argument("--note", default="")
    p.set_defaults(fn=add)
    p = sub.add_parser("list"); p.set_defaults(fn=list_signals)
    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
