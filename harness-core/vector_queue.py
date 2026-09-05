#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vector_queue.py — 主记忆写入后的可失败向量队列。

只负责把 memory_id 放入 sidecar 队列，不调用模型、不阻塞主记忆写入。
worker 由 vector_worker.py 异步消费；队列损坏/不可写时返回 False，调用方继续成功。
"""
import os
import sqlite3
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"
QUEUE_DB = DATA_DIR / "vector_queue.db"


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(QUEUE_DB), timeout=0.2)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS queue (
        memory_id INTEGER PRIMARY KEY,
        enqueued_at REAL NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        processing_at REAL,
        done_at REAL,
        status TEXT,
        next_retry_at REAL,
        retry_count INTEGER NOT NULL DEFAULT 0
    )""")
    # 兼容旧队列表，只增加列，不迁移或删除已有数据。
    cols = {r[1] for r in con.execute("PRAGMA table_info(queue)")}
    for col, ddl in [
        ("processing_at", "ALTER TABLE queue ADD COLUMN processing_at REAL"),
        ("status", "ALTER TABLE queue ADD COLUMN status TEXT"),
        ("next_retry_at", "ALTER TABLE queue ADD COLUMN next_retry_at REAL"),
        ("retry_count", "ALTER TABLE queue ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0"),
    ]:
        if col not in cols:
            con.execute(ddl)
    # 旧数据若无 status，视为 pending。
    con.execute("UPDATE queue SET status='pending' WHERE status IS NULL")
    con.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL NOT NULL,
        total INTEGER, pending INTEGER, processing INTEGER,
        deferred INTEGER, done INTEGER, failed INTEGER, stale INTEGER)""")
    con.commit()
    return con


def enqueue(memory_id):
    """Best-effort enqueue. Never raises to the primary memory writer."""
    try:
        con = _connect()
        con.execute(
            "INSERT OR IGNORE INTO queue(memory_id,enqueued_at,status) VALUES(?,?,?)",
            (int(memory_id), time.time(), "pending"),
        )
        con.commit()
        con.close()
        return True
    except Exception:
        return False


def queue_history(limit=20):
    """返回向量队列历史快照（最近 limit 条）。"""
    try:
        con = _connect()
        rows = con.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        con.close()
        return {"ok": True, "history": [dict(r) for r in rows[::-1]]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def queue_alert(stale_threshold=20, failed_threshold=5):
    """返回向量队列告警列表（threshold 缺省值仅用于本地提示）。"""
    try:
        st = queue_status()
        alerts = []
        if not st.get("ok"):
            return {"ok": True, "alerts": ["queue_status_unavailable"]}
        if int(st.get("stale") or 0) >= stale_threshold:
            alerts.append("stale_count_high:%s" % st.get("stale"))
        if int(st.get("failed") or 0) >= failed_threshold:
            alerts.append("failed_count_high:%s" % st.get("failed"))
        return {"ok": True, "alerts": alerts, "thresholds": {"stale": stale_threshold, "failed": failed_threshold}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def queue_status():
    """返回向量队列的持续监控摘要（不修改队列状态）。"""
    try:
        con = _connect()
        total = con.execute("SELECT COUNT(*) FROM queue").fetchone()[0]
        pending = con.execute("SELECT COUNT(*) FROM queue WHERE status='pending' AND done_at IS NULL").fetchone()[0]
        processing = con.execute("SELECT COUNT(*) FROM queue WHERE status='processing' AND done_at IS NULL").fetchone()[0]
        deferred = con.execute("SELECT COUNT(*) FROM queue WHERE status='deferred' AND done_at IS NULL").fetchone()[0]
        failed = con.execute("SELECT COUNT(*) FROM queue WHERE status='failed' AND done_at IS NULL").fetchone()[0]
        done = con.execute("SELECT COUNT(*) FROM queue WHERE done_at IS NOT NULL").fetchone()[0]
        retryable = con.execute("SELECT COUNT(*) FROM queue WHERE done_at IS NULL AND status IN ('pending','deferred') AND (next_retry_at IS NULL OR next_retry_at<=?)",
                                (time.time(),)).fetchone()[0]
        stale = con.execute("SELECT COUNT(*) FROM queue WHERE status='processing' AND done_at IS NULL AND processing_at<?",
                            (time.time() - 600,)).fetchone()[0]
        try:
            con.execute("INSERT INTO history(ts,total,pending,processing,deferred,done,failed,stale) VALUES(?,?,?,?,?,?,?,?)",
                        (time.time(), total, pending, processing, deferred, done, failed, stale))
            con.commit()
        except Exception:
            pass
        con.close()
        return {"ok": True, "total": total, "pending": pending, "processing": processing,
                "deferred": deferred, "failed": failed, "done": done, "retryable": retryable,
                "stale": stale, "available": QUEUE_DB.exists()}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "available": QUEUE_DB.exists()}
