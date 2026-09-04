#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomic_facts_build.py — 从记忆构建原子事实索引（实体+时间）。"""
import json
import re
import sqlite3
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms

DB = Path.home() / ".dsh" / "memory-emotion" / "atomic_facts_sidecar.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.execute("DROP TABLE IF EXISTS atomic_facts")
    c.execute("""CREATE TABLE IF NOT EXISTS atomic_facts(
      id TEXT PRIMARY KEY, memory_id INTEGER, entity TEXT, fact TEXT,
      importance REAL, updated_at TEXT, tags TEXT, time_label TEXT, refs TEXT)""")
    return c

def split_clauses(text):
    parts = re.split(r'[，。；！？、\n]', text or '')
    return [p.strip() for p in parts if len(p.strip()) >= 5][:5]

def main():
    c = connect()
    main_db = sqlite3.connect(str(ms.db_path()))
    main_db.row_factory = sqlite3.Row
    rows = main_db.execute("SELECT * FROM memories WHERE archived=0").fetchall()
    c.execute("DELETE FROM atomic_facts")
    total = 0
    for r in rows:
        for clause in split_clauses(r["content"]):
            fid = uuid.uuid4().hex[:16]
            time_label = ""
            if "今天" in clause or "最近" in clause or "本周" in clause:
                time_label = "recent"
            elif r["updated_at"]:
                time_label = r["updated_at"][:7]
            c.execute("INSERT INTO atomic_facts(id,memory_id,entity,fact,importance,updated_at,tags,time_label,refs) VALUES(?,?,?,?,?,?,?,?,?)",
                      (fid, r["id"], r["entity"] or "", clause, r["importance"], r["updated_at"], r["tags"] or "", time_label, ""))
            total += 1
    c.commit(); c.close(); main_db.close()
    print(json.dumps({"ok": True, "memories": len(rows), "atomic_facts": total}, ensure_ascii=False))

if __name__ == "__main__":
    main()
