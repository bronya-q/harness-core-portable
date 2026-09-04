#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deep_fusion_retriever.py — 深度融合检索（BM25 + 语义 + 实体链接 + 时间）。

参考 Mem0：
  - BM25 关键词打分
  - qwen3-embedding 语义相似
  - entity/tag 实体链接
  - 时间感知
四点并行后融合。
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


def _bigrams(text):
    t = "".join(text.split()).lower()
    return [t[i:i+2] for i in range(len(t)-1)] if t else []


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
    ap.add_argument("--w-bm25", type=float, default=0.4)
    ap.add_argument("--w-sem", type=float, default=0.35)
    ap.add_argument("--w-ent", type=float, default=0.15)
    ap.add_argument("--w-temp", type=float, default=0.10)
    args = ap.parse_args()

    main_db = sqlite3.connect(str(ms.db_path()))
    main_db.row_factory = sqlite3.Row
    vec_db = sqlite3.connect(str(VEC_DB))

    rows = main_db.execute("SELECT * FROM memories WHERE archived=0").fetchall()
    # scope filter
    if args.scope:
        rows = [r for r in rows if r["scope"] == args.scope]

    # ------------- BM25 -------------
    q_bigrams = _bigrams(args.query)
    if not q_bigrams:
        q_bigrams = [args.query.lower()]
    doc_bigrams = []
    N = len(rows)
    avgdl = 0
    for r in rows:
        bg = _bigrams(r["content"] or "")
        doc_bigrams.append(bg)
        avgdl += len(bg)
    avgdl = max(1, avgdl / max(1, N))
    df = {}
    for bg in set(q_bigrams):
        df[bg] = sum(1 for dbg in doc_bigrams if bg in dbg)
    k1, b = 1.5, 0.75
    bm25_scores = {}
    for idx, r in enumerate(rows):
        dbg = doc_bigrams[idx]
        score = 0.0
        for bg in q_bigrams:
            tf = dbg.count(bg)
            if tf == 0:
                continue
            idf = math.log(1 + (N - df.get(bg, 0) + 0.5) / (df.get(bg, 0) + 0.5))
            denom = tf + k1 * (1 - b + b * len(dbg) / avgdl)
            score += idf * (tf * (k1 + 1)) / denom
        bm25_scores[r["id"]] = score

    # ------------- semantic -------------
    q_emb = _embed(args.query)
    sem_scores = {}
    vec_rows = vec_db.execute("SELECT memory_id, vec FROM vec").fetchall()
    for mid, blob in vec_rows:
        try:
            sem_scores[mid] = max(0.0, _cos(q_emb, _unpack(blob)))
        except Exception:
            sem_scores[mid] = 0.0

    # ------------- entity linking -------------
    ent_scores = {}
    q_lower = args.query.lower()
    tokens = [t for t in args.query.split() if len(t) >= 2]
    for r in rows:
        ent = (r["entity"] or "").lower()
        tags = (r["tags"] or "").lower()
        score = 0.0
        if any(t in ent for t in tokens) or any(t in tags for t in tokens) or q_lower in ent or q_lower in tags:
            score = 1.0
        ent_scores[r["id"]] = score

    # ------------- temporal -------------
    temp_scores = {r["id"]: _norm_recency(r["updated_at"]) for r in rows}

    # ------------- fusion -------------
    max_bm25 = max(bm25_scores.values()) if bm25_scores else 0
    bm25_norm = {k: (v / max_bm25 if max_bm25 else 0) for k, v in bm25_scores.items()}
    results = []
    for r in rows:
        mid = r["id"]
        s = (args.w_bm25 * bm25_norm.get(mid, 0) +
             args.w_sem * sem_scores.get(mid, 0) +
             args.w_ent * ent_scores.get(mid, 0) +
             args.w_temp * temp_scores.get(mid, 0))
        results.append({"id": mid, "content": r["content"], "scope": r["scope"],
                        "entity": r["entity"], "tags": r["tags"], "score": round(s, 4),
                        "bm25": round(bm25_norm.get(mid, 0), 4),
                        "sem": round(sem_scores.get(mid, 0), 4),
                        "ent": ent_scores.get(mid, 0),
                        "temp": round(temp_scores.get(mid, 0), 4)})
    results.sort(key=lambda x: -x["score"])
    main_db.close(); vec_db.close()
    print(json.dumps({"ok": True, "query": args.query, "results": results[:args.limit]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
