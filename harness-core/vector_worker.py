#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vector_worker.py — 异步消费 vector_queue，失败可重试，不影响主记忆写入。

语义：
- `skip_unavailable` 不再把队列项直接标记为 done；
  而是标记为 `deferred` 并设置 `next_retry_at`，在以后的重试窗口中继续尝试。
- 非不可用错误在 `max_attempts` 内保留重试；超过后标记 `failed`。
- `--retry-failed` 会把 `failed` 项重新打开为 `pending`。
"""
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


def run(limit=50, retry_failed=False, stale_seconds=600, skip_unavailable=False,
        retry_interval=300, max_attempts=5, backoff=True):
    q = _connect()
    main = sqlite3.connect(str(ms.db_path()))
    vec = sqlite3.connect(str(VEC_DB))
    now = time.time()

    # worker 中途退出时，超时 processing 项自动回到 pending。
    q.execute(
        "UPDATE queue SET processing_at=NULL, status='pending' WHERE "
        "done_at IS NULL AND status='processing' AND processing_at<?",
        (now - stale_seconds,),
    )
    # 主动重试已 failed 的项。
    if retry_failed:
        q.execute(
            "UPDATE queue SET status='pending', attempts=0, retry_count=0, "
            "processing_at=NULL, next_retry_at=NULL "
            "WHERE done_at IS NULL AND status='failed'",
        )

    where = "done_at IS NULL AND status IN ('pending','deferred') AND (next_retry_at IS NULL OR next_retry_at<=?)"
    params = [now]
    if not retry_failed:
        where += " AND attempts < ?"
        params.append(max_attempts)
    rows = q.execute(
        f"SELECT memory_id FROM queue WHERE {where} ORDER BY enqueued_at LIMIT ?",
        params + [limit],
    ).fetchall()

    done = failed = skipped = deferred = 0
    for (mid,) in rows:
        q.execute(
            "UPDATE queue SET processing_at=?, status='processing' WHERE memory_id=? AND done_at IS NULL",
            (now, mid),
        )
        row = main.execute("SELECT scope,content FROM memories WHERE id=? AND archived=0", (mid,)).fetchone()
        if not row:
            q.execute(
                "UPDATE queue SET done_at=?, status='done', processing_at=NULL, attempts=attempts+1, "
                "last_error=? WHERE memory_id=?",
                (now, "missing_or_archived", mid),
            )
            skipped += 1
            continue
        try:
            vec.execute(
                "INSERT OR REPLACE INTO vec(memory_id,scope,ts,vec) VALUES(?,?,?,?)",
                (mid, row[0], time.time(), _pack(_embed(row[1]))),
            )
            q.execute(
                "UPDATE queue SET done_at=?, status='done', processing_at=NULL, attempts=attempts+1, "
                "last_error=NULL, next_retry_at=NULL WHERE memory_id=?",
                (now, mid),
            )
            done += 1
        except Exception as exc:
            message = str(exc)[:500]
            is_unavailable = (
                "WinError 10061" in message
                or "Connection refused" in message
                or "Connection reset" in message
                or "connect" in message.lower() and "refused" in message.lower()
            )
            if skip_unavailable and is_unavailable:
                attempts = (q.execute("SELECT attempts FROM queue WHERE memory_id=?", (mid,)).fetchone()[0] or 0) + 1
                retry_delay = retry_interval * (1 if not backoff else min(6, 2 ** (attempts - 1)))
                q.execute(
                    "UPDATE queue SET processing_at=NULL, status='deferred', attempts=?, retry_count=retry_count+1, "
                    "last_error=?, next_retry_at=? WHERE memory_id=?",
                    (attempts, "vector_unavailable:" + message, now + retry_delay, mid),
                )
                deferred += 1
            else:
                attempts = (q.execute("SELECT attempts FROM queue WHERE memory_id=?", (mid,)).fetchone()[0] or 0) + 1
                if attempts >= max_attempts or message.startswith("vector_unavailable"):
                    q.execute(
                        "UPDATE queue SET processing_at=NULL, status='failed', attempts=?, last_error=?, "
                        "next_retry_at=NULL WHERE memory_id=?",
                        (attempts, message, mid),
                    )
                    failed += 1
                else:
                    q.execute(
                        "UPDATE queue SET processing_at=NULL, status='pending', attempts=?, retry_count=retry_count+1, "
                        "last_error=?, next_retry_at=? WHERE memory_id=?",
                        (attempts, message, now + retry_interval, mid),
                    )
                    deferred += 1
    vec.commit()
    q.commit()
    vec.close()
    main.close()
    q.close()
    return done, failed, skipped, deferred, len(rows)


def serve(limit=50, interval=30, retry_failed=False, skip_unavailable=False,
          retry_interval=300, once=False):
    total = {"done": 0, "failed": 0, "skipped": 0, "deferred": 0, "scanned": 0}
    while True:
        result = run(limit, retry_failed, 600, skip_unavailable, retry_interval)
        for key, value in zip(total, result):
            total[key] += value
        if once:
            return total
        time.sleep(max(1, interval))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--skip-unavailable", action="store_true")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--stale-seconds", type=int, default=600)
    ap.add_argument("--retry-interval", type=int, default=300)
    ap.add_argument("--max-attempts", type=int, default=5)
    ap.add_argument("--no-backoff", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=30)
    args = ap.parse_args()
    if args.loop:
        result = serve(args.limit, args.interval, args.retry_failed, args.skip_unavailable,
                       args.retry_interval)
        return 0 if result["failed"] == 0 else 1
    result = run(args.limit, args.retry_failed, args.stale_seconds, args.skip_unavailable,
                 args.retry_interval, args.max_attempts, not args.no_backoff)
    print("[vector_worker] done=%d failed=%d skipped=%d deferred=%d scanned=%d" % result)
    return 0 if result[1] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
