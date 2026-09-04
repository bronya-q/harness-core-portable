#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vector_worker.py — 异步消费 vector_queue，失败可重试，不影响主记忆写入。"""
import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import memory_store as ms
from nine_dim import _embed, _pack, VEC_DB
from vector_queue import QUEUE_DB, _connect


def run(limit=50, retry_failed=False, stale_seconds=600, skip_unavailable=False):
    q = _connect()
    main = sqlite3.connect(str(ms.db_path()))
    vec = sqlite3.connect(str(VEC_DB))
    now = time.time()
    # worker 中途退出时，超时 processing 项自动回到 pending。
    q.execute("UPDATE queue SET processing_at=NULL WHERE done_at IS NULL AND processing_at IS NOT NULL AND processing_at<?",
              (now - stale_seconds,))
    where = "done_at IS NULL AND processing_at IS NULL"
    if not retry_failed:
        where += " AND attempts < 5"
    rows = q.execute(f"SELECT memory_id FROM queue WHERE {where} ORDER BY enqueued_at LIMIT ?", (limit,)).fetchall()
    done = failed = skipped = 0
    for (mid,) in rows:
        q.execute("UPDATE queue SET processing_at=? WHERE memory_id=? AND done_at IS NULL", (time.time(), mid))
        row = main.execute("SELECT scope,content FROM memories WHERE id=? AND archived=0", (mid,)).fetchone()
        if not row:
            q.execute("UPDATE queue SET done_at=?,processing_at=NULL,last_error=? WHERE memory_id=?", (time.time(), "missing_or_archived", mid))
            skipped += 1
            continue
        try:
            vec.execute("INSERT OR REPLACE INTO vec(memory_id,scope,ts,vec) VALUES(?,?,?,?)",
                        (mid, row[0], time.time(), _pack(_embed(row[1]))))
            q.execute("UPDATE queue SET done_at=?,processing_at=NULL,attempts=attempts+1,last_error=NULL WHERE memory_id=?", (time.time(), mid))
            done += 1
        except Exception as exc:
            message = str(exc)[:500]
            if skip_unavailable and ('WinError 10061' in message or 'Connection refused' in message):
                q.execute("UPDATE queue SET done_at=?,processing_at=NULL,last_error=? WHERE memory_id=?", (time.time(), 'vector_unavailable:'+message, mid))
                skipped += 1
            else:
                q.execute("UPDATE queue SET processing_at=NULL,attempts=attempts+1,last_error=? WHERE memory_id=?", (message, mid))
                failed += 1
    vec.commit(); q.commit(); vec.close(); main.close(); q.close()
    return done, failed, skipped, len(rows)


def serve(limit=50, interval=30, retry_failed=False, once=False):
    total = {'done': 0, 'failed': 0, 'skipped': 0, 'scanned': 0}
    while True:
        result = run(limit, retry_failed)
        for key, value in zip(total, result): total[key] += value
        if once: return total
        time.sleep(max(1, interval))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=50)
    ap.add_argument('--skip-unavailable', action='store_true')
    ap.add_argument('--retry-failed', action='store_true')
    ap.add_argument('--stale-seconds', type=int, default=600)
    ap.add_argument('--loop', action='store_true')
    ap.add_argument('--interval', type=int, default=30)
    args = ap.parse_args()
    if args.loop:
        result = serve(args.limit, args.interval, args.retry_failed)
        return 0 if result['failed'] == 0 else 1
    result = run(args.limit, args.retry_failed, args.stale_seconds, args.skip_unavailable)
    print('[vector_worker] done=%d failed=%d skipped=%d scanned=%d' % result)
    return 0 if result[1] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
