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
    con.execute("""CREATE TABLE IF NOT EXISTS queue (
        memory_id INTEGER PRIMARY KEY,
        enqueued_at REAL NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        processing_at REAL,
        done_at REAL
    )""")
    # 兼容旧队列表，只增加列，不迁移或删除已有数据。
    cols = {r[1] for r in con.execute("PRAGMA table_info(queue)")}
    if "processing_at" not in cols:
        con.execute("ALTER TABLE queue ADD COLUMN processing_at REAL")
        con.commit()
    return con


def enqueue(memory_id):
    """Best-effort enqueue. Never raises to the primary memory writer."""
    try:
        con = _connect()
        con.execute(
            "INSERT OR IGNORE INTO queue(memory_id,enqueued_at) VALUES(?,?)",
            (int(memory_id), time.time()),
        )
        con.commit()
        con.close()
        return True
    except Exception:
        return False


def queue_status():
    """返回向量队列的持续监控摘要（不修改队列状态）。"""
    try:
        con = _connect()
        total = con.execute("SELECT COUNT(*) FROM queue").fetchone()[0]
        pending = con.execute("SELECT COUNT(*) FROM queue WHERE done_at IS NULL AND processing_at IS NULL").fetchone()[0]
        processing = con.execute("SELECT COUNT(*) FROM queue WHERE done_at IS NULL AND processing_at IS NOT NULL").fetchone()[0]
        done = con.execute("SELECT COUNT(*) FROM queue WHERE done_at IS NOT NULL").fetchone()[0]
        failed = con.execute("SELECT COUNT(*) FROM queue WHERE done_at IS NULL AND attempts>=5").fetchone()[0]
        stale = con.execute("SELECT COUNT(*) FROM queue WHERE done_at IS NULL AND processing_at IS NOT NULL AND processing_at<?",
                            (time.time() - 600,)).fetchone()[0]
        con.close()
        return {"ok": True, "total": total, "pending": pending, "processing": processing,
                "done": done, "failed": failed, "stale": stale, "available": QUEUE_DB.exists()}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "available": QUEUE_DB.exists()}
