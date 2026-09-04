#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cognitive_dynamics.py — #3 认知动力系统（注意力/好奇心/心情/精力）。"""
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

DB = Path.home() / ".dsh" / "memory-emotion" / "cognitive_dynamics.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS cognitive_dynamics(
      scope TEXT PRIMARY KEY, attention REAL DEFAULT 0.5,
      curiosity REAL DEFAULT 0.5, mood REAL DEFAULT 0.5,
      energy REAL DEFAULT 0.5, updated_at REAL)""")
    return c

def set_state(args):
    c = connect()
    c.execute("""INSERT INTO cognitive_dynamics(scope,attention,curiosity,mood,energy,updated_at)
      VALUES(?,?,?,?,?,?)
      ON CONFLICT(scope) DO UPDATE SET attention=excluded.attention,
        curiosity=excluded.curiosity, mood=excluded.mood, energy=excluded.energy, updated_at=excluded.updated_at""",
      (args.scope, args.attention, args.curiosity, args.mood, args.energy, time.time()))
    c.commit(); c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "state": {
        "attention": args.attention, "curiosity": args.curiosity, "mood": args.mood, "energy": args.energy}}, ensure_ascii=False))
    return 0

def status(args):
    c = connect()
    rows = c.execute("SELECT * FROM cognitive_dynamics").fetchall()
    c.close()
    print(json.dumps({"ok": True, "states": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("set"); p.add_argument("--scope", required=True)
    p.add_argument("--attention", type=float, default=0.5); p.add_argument("--curiosity", type=float, default=0.5)
    p.add_argument("--mood", type=float, default=0.5); p.add_argument("--energy", type=float, default=0.5)
    p.set_defaults(fn=set_state)
    p = sub.add_parser("status"); p.set_defaults(fn=status)
    args = ap.parse_args()
    return args.fn(args)

if __name__ == "__main__":
    sys.exit(main())
