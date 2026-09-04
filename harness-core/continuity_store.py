#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local, standard-library-only continuity telemetry sidecar.

Separate from memory.db so observability, candidate beliefs, and emotion
trajectories can be rolled back without touching durable memories.
"""
import json, os, sqlite3, time, uuid
from pathlib import Path

DATA = Path(os.environ.get("MEMORY_EMOTION_DATA_DIR", str(Path.home() / ".dsh" / "memory-emotion"))).expanduser()
DB = DATA / "continuity_sidecar.db"

def connect():
    DATA.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(str(DB)); c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS session_metrics(
      id TEXT PRIMARY KEY, scope TEXT, provider TEXT, started_at REAL, ended_at REAL,
      recall_attempted INTEGER, recall_success INTEGER, recalled_count INTEGER DEFAULT 0,
      response_generated INTEGER, memory_write_count INTEGER DEFAULT 0, error_count INTEGER DEFAULT 0,
      source TEXT, details TEXT);
    CREATE TABLE IF NOT EXISTS emotion_events(
      id TEXT PRIMARY KEY, scope TEXT, observed_at REAL, event_type TEXT, rule_id TEXT,
      evidence_ids TEXT, before_json TEXT, delta_json TEXT, after_json TEXT, source TEXT);
    CREATE TABLE IF NOT EXISTS beliefs(
      id TEXT PRIMARY KEY, scope TEXT, statement TEXT, status TEXT, confidence REAL,
      support_ids TEXT, counterexample_ids TEXT, created_at REAL, updated_at REAL, source TEXT);
    CREATE TABLE IF NOT EXISTS profile_layers(
      scope TEXT PRIMARY KEY, static_json TEXT, dynamic_json TEXT, effective_json TEXT,
      updated_at REAL, source TEXT);
    CREATE INDEX IF NOT EXISTS idx_metrics_ended ON session_metrics(ended_at);
    CREATE INDEX IF NOT EXISTS idx_emotion_scope_time ON emotion_events(scope,observed_at);
    CREATE TABLE IF NOT EXISTS round_metrics(
      id TEXT PRIMARY KEY, session_id TEXT, scope TEXT, persona_id TEXT, round_no INTEGER,
      event_type TEXT, response_generated INTEGER, recall_count INTEGER DEFAULT 0,
      memory_injected INTEGER DEFAULT 0, rating REAL, error_type TEXT, observed_at REAL,
      details TEXT);
    CREATE TABLE IF NOT EXISTS report_history(
      id INTEGER PRIMARY KEY AUTOINCREMENT, report_type TEXT, generated_at REAL,
      payload_json TEXT NOT NULL);
    """)
    cols={r[1] for r in c.execute('PRAGMA table_info(session_metrics)')}
    for name,ddl in [('session_kind','TEXT DEFAULT "unknown"'),('entrypoint','TEXT'),('error_type','TEXT'),('fallback_used','INTEGER DEFAULT 0'),('source_kind','TEXT DEFAULT "directed"')]:
        if name not in cols: c.execute('ALTER TABLE session_metrics ADD COLUMN '+name+' '+ddl)
    c.commit(); return c

def record_session(data):
    c=connect(); sid=data.get('id') or uuid.uuid4().hex
    fields={'id':sid,'scope':data.get('scope','default'),'provider':data.get('provider','unknown'),
      'started_at':data.get('started_at',time.time()),'ended_at':data.get('ended_at',time.time()),
      'recall_attempted':int(bool(data.get('recall_attempted'))),'recall_success':int(bool(data.get('recall_success'))),
      'recalled_count':int(data.get('recalled_count',0)),'response_generated':int(bool(data.get('response_generated'))),
      'memory_write_count':int(data.get('memory_write_count',0)),'error_count':int(data.get('error_count',0)),
      'source':data.get('source','runtime'),'details':json.dumps(data.get('details',{}),ensure_ascii=False),
      'session_kind':data.get('session_kind','unknown'),'entrypoint':data.get('entrypoint'),'source_kind':data.get('source_kind','directed'),
      'error_type':data.get('error_type'),'fallback_used':int(bool(data.get('fallback_used')))}
    cols=list(fields); marks=','.join('?' for _ in cols)
    c.execute('INSERT OR REPLACE INTO session_metrics ('+','.join(cols)+') VALUES ('+marks+')',[fields[x] for x in cols]); c.commit(); c.close(); return sid

def record_emotion(scope,event_type,rule_id,before,delta,after,evidence_ids=(),source='runtime'):
    c=connect(); eid=uuid.uuid4().hex
    c.execute('INSERT INTO emotion_events VALUES(?,?,?,?,?,?,?,?,?,?)',(eid,scope,time.time(),event_type,rule_id,json.dumps(list(evidence_ids)),json.dumps(before,ensure_ascii=False),json.dumps(delta,ensure_ascii=False),json.dumps(after,ensure_ascii=False),source)); c.commit(); c.close(); return eid

def record_belief(scope,statement,status='candidate',confidence=0.0,support_ids=(),counterexample_ids=(),source='manual'):
    c=connect(); bid=uuid.uuid4().hex; now=time.time()
    c.execute('INSERT INTO beliefs VALUES(?,?,?,?,?,?,?,?,?,?)',(bid,scope,statement,status,float(confidence),json.dumps(list(support_ids)),json.dumps(list(counterexample_ids)),now,now,source)); c.commit(); c.close(); return bid

def record_round(data):
    c=connect(); rid=data.get('id') or uuid.uuid4().hex
    fields={'id':rid,'session_id':data.get('session_id'),'scope':data.get('scope','default'),'persona_id':data.get('persona_id'),
      'round_no':data.get('round_no'),'event_type':data.get('event_type','response'),'response_generated':int(bool(data.get('response_generated'))),
      'recall_count':int(data.get('recall_count',0)),'memory_injected':int(bool(data.get('memory_injected'))),
      'rating':data.get('rating'),'error_type':data.get('error_type'),'observed_at':data.get('observed_at',time.time()),
      'details':json.dumps(data.get('details',{}),ensure_ascii=False)}
    cols=list(fields); c.execute('INSERT OR REPLACE INTO round_metrics ('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',[fields[x] for x in cols]); c.commit(); c.close(); return rid


def save_profile(scope,static,dynamic,effective,source='profile_builder'):
    c=connect(); c.execute('INSERT OR REPLACE INTO profile_layers VALUES(?,?,?,?,?,?)',(scope,json.dumps(static,ensure_ascii=False),json.dumps(dynamic,ensure_ascii=False),json.dumps(effective,ensure_ascii=False),time.time(),source)); c.commit(); c.close()
