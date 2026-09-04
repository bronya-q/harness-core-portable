#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""retrieval_reranker.py — 语义重排器（提升记忆召回）。

对活跃记忆用 bge-m3 余弦 + importance + recency 重排，返回 top-k。
"""
import argparse
import json
import math
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms
from nine_dim import _embed, _unpack, _cos, VEC_DB


def _norm_importance(v):
    return max(0.0, min(1.0, v / 1.0))


def _norm_recency(updated_at):
    try:
        days = (datetime.now(timezone.utc) - datetime.fromisoformat(updated_at)).days
    except Exception:
        days = 999
    return max(0.0, 1.0 / (1.0 + days))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--scope", default=None)
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--sim-weight", type=float, default=0.8)
    ap.add_argument("--min-importance", type=float, default=None)
    args = ap.parse_args()

    main_db = sqlite3.connect(str(ms.db_path()))
    main_db.row_factory = sqlite3.Row
    vec_db = sqlite3.connect(str(VEC_DB))

    q = _embed(args.query)
    rows = vec_db.execute("SELECT memory_id, vec FROM vec").fetchall()
    scored = []
    for mid, blob in rows:
        mem = main_db.execute("SELECT * FROM memories WHERE id=? AND archived=0", (mid,)).fetchone()
        if not mem:
            continue
        if args.scope and mem["scope"] != args.scope:
            continue
        if args.min_importance is not None and mem["importance"] < args.min_importance:
            continue
        sim = _cos(q, _unpack(blob))
        imp = _norm_importance(mem["importance"])
        rec = _norm_recency(mem["updated_at"])
        score = args.sim_weight * sim + (1 - args.sim_weight) * (0.6 * imp + 0.4 * rec)
        scored.append({"id": mem["id"], "scope": mem["scope"], "content": mem["content"],
                       "importance": mem["importance"], "updated_at": mem["updated_at"],
                       "retrieval_score": round(score, 4), "sim": round(sim, 4)})
    scored.sort(key=lambda x: -x["retrieval_score"])
    main_db.close(); vec_db.close()
    print(json.dumps({"ok": True, "query": args.query, "results": scored[:args.limit]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
