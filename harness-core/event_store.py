#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""event_store.py — 统一事件信封与 Token Usage 存储。

提供：
  event add|list
  usage record|list

底层：~/.dsh/memory-emotion/events.db
"""
import json
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"
DB = DATA_DIR / "events.db"


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.execute("PRAGMA busy_timeout=5000")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS events(
      event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, scope TEXT NOT NULL,
      occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL, session_id TEXT,
      source_ids TEXT, root_source_ids TEXT, content_type TEXT, visibility TEXT,
      consent_scope TEXT, retention TEXT, derived_artifact_ids TEXT, version INTEGER DEFAULT 1)""")
    c.execute("CREATE TABLE IF NOT EXISTS token_usage("
              "id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, usage_source TEXT, model_id TEXT, "
              "tokenizer_id TEXT, context_window INTEGER, components TEXT, actual_tokens INTEGER, "
              "baseline_id TEXT, baseline_tokens INTEGER, estimated_avoided_tokens INTEGER, created_at REAL)")
    return c


def _json_load(s):
    try:
        return json.loads(s) if s else None
    except Exception:
        return None


def record_event(event):
    eid = event.get("event_id") or "evt_" + uuid.uuid4().hex[:16]
    c = _connect()
    occurred = event.get("occurred_at") or time.strftime("%Y-%m-%dT%H:%M:%S")
    c.execute("INSERT INTO events(event_id,event_type,scope,occurred_at,recorded_at,session_id,source_ids,"
              "root_source_ids,content_type,visibility,consent_scope,retention,derived_artifact_ids,version) "
              "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (eid, event.get("event_type"), event.get("scope"), occurred,
               event.get("recorded_at") or time.strftime("%Y-%m-%dT%H:%M:%S"),
               event.get("session_id"), json.dumps(event.get("source_ids", []), ensure_ascii=False),
               json.dumps(event.get("root_source_ids", []), ensure_ascii=False),
               event.get("content_type"), event.get("visibility", "private"),
               json.dumps(event.get("consent_scope", {}), ensure_ascii=False),
               json.dumps(event.get("retention", {}), ensure_ascii=False),
               json.dumps(event.get("derived_artifact_ids", []), ensure_ascii=False),
               event.get("version", 1)))
    c.commit(); c.close()
    return eid


def list_events(limit=20, scope=None):
    c = _connect()
    if scope:
        rows = c.execute("SELECT * FROM events WHERE scope=? ORDER BY recorded_at DESC LIMIT ?", (scope, limit)).fetchall()
    else:
        rows = c.execute("SELECT * FROM events ORDER BY recorded_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        for k in ["source_ids", "root_source_ids", "consent_scope", "retention", "derived_artifact_ids"]:
            d[k] = _json_load(d.get(k))
        out.append(d)
    return out


def record_usage(usage):
    c = _connect()
    cur = c.execute("INSERT INTO token_usage(event_id,usage_source,model_id,tokenizer_id,context_window,components,"
                    "actual_tokens,baseline_id,baseline_tokens,estimated_avoided_tokens,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (usage.get("event_id"), usage.get("usage_source"), usage.get("model_id"),
                     usage.get("tokenizer_id"), usage.get("context_window"),
                     json.dumps(usage.get("components", {}), ensure_ascii=False),
                     usage.get("actual_tokens"), usage.get("baseline_id"), usage.get("baseline_tokens"),
                     usage.get("estimated_avoided_tokens"), time.time()))
    uid = cur.lastrowid
    c.commit(); c.close()
    return uid


def list_usage(limit=20):
    c = _connect()
    rows = c.execute("SELECT * FROM token_usage ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        d["components"] = _json_load(d.get("components"))
        out.append(d)
    return out
