#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomic_fact_retriever.py — B 臂：原子事实+实体+时间检索。"""
import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms

DB = Path.home() / ".dsh" / "memory-emotion" / "atomic_facts_sidecar.db"

def _bigrams(text):
    t = "".join(text.split()).lower()
    return [t[i:i+2] for i in range(len(t)-1)] if t else []

def _recency(updated_at):
    try:
        from datetime import datetime, timezone
        days = (datetime.now(timezone.utc) - datetime.fromisoformat(updated_at)).days
        return max(0.0, 1.0/(1.0+abs(days)))
    except Exception:
        return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--scope", default=None)
    args = ap.parse_args()

    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    rows = c.execute("SELECT * FROM atomic_facts").fetchall()
    c.close()
    if args.scope:
        # filter via memory scope? atomic_facts doesn't store scope; skip
        pass
    # BM25 over atomics
    q_bg = _bigrams(args.query) or [args.query.lower()]
    doc_bg = [_bigrams(r["fact"]) for r in rows]
    N = len(rows)
    avgdl = max(1, sum(len(d) for d in doc_bg) / max(1, N))
    df = {bg: sum(1 for d in doc_bg if bg in d) for bg in set(q_bg)}
    k1, b = 1.5, 0.75
    tok = [t for t in args.query.split() if len(t) >= 2]
    scores = {}
    for i, r in enumerate(rows):
        dbg = doc_bg[i]
        s = 0.0
        for bg in q_bg:
            tf = dbg.count(bg)
            if tf == 0: continue
            idf = math.log(1 + (N - df.get(bg,0) + 0.5) / (df.get(bg,0) + 0.5))
            denom = tf + k1 * (1 - b + b * len(dbg) / avgdl)
            s += idf * (tf*(k1+1)) / denom
        ent = (r["entity"] or "").lower()
        tags = (r["tags"] or "").lower()
        ent_hit = 1.0 if any(t in ent for t in tok) or any(t in tags for t in tok) else 0.0
        temp = _recency(r["updated_at"])
        final = 0.6*s + 0.25*ent_hit + 0.15*temp
        mid = r["memory_id"]
        if mid not in scores or final > scores[mid][0]:
            scores[mid] = (final, r["fact"], r["entity"], r["updated_at"])
    ranked = sorted(scores.items(), key=lambda kv: -kv[1][0])[:args.limit]
    # entity linking 扩展：把 top 结果的同 entity 其他原子事实也纳入
    top_entities = {v[2] for _, v in ranked if v[2]}
    expanded = {}
    for r in rows:
        mid = r["memory_id"]
        if mid in scores:
            continue
        if (r["entity"] or "") in top_entities:
            exp_score = scores.get(mid, (0,"","", ""))[0] + 0.15
            expanded[mid] = (exp_score, r["fact"], r["entity"], r["updated_at"])
    combined = dict(scores)
    combined.update(expanded)
    ranked2 = sorted(combined.items(), key=lambda kv: -kv[1][0])[:args.limit]
    results = [{"id": int(k), "content": v[1], "entity": v[2], "updated_at": v[3], "score": round(v[0],4)} for k,v in ranked2]
    print(json.dumps({"ok": True, "results": results}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
