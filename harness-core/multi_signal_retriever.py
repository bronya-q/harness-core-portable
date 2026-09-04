#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multi_signal_retriever.py — 多信号检索（keyword + semantic + entity/tag）融合。

参考 Mem0 多信号检索：语义 / BM25 keyword / entity 匹配并行打分后融合。
"""
import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms

def _run(script, *args):
    p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--scope", default=None)
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--budget", type=int, default=40)
    args = ap.parse_args()

    kw = _run("memory_store.py", "search", "--query", args.query, "--scope", args.scope or "default", "--limit", str(args.budget))
    sem = _run("semantic_search.py", "--query", args.query, "--scope", args.scope or "default", "--limit", str(args.budget), "--sim-weight", "0.8")
    sem_results = sem.get("results", [])
    # keyword set
    kw_rows = kw if isinstance(kw, list) else kw.get("results", kw) if isinstance(kw, dict) else []
    kw_map = {}
    for i, r in enumerate(kw_rows):
        kw_map[str(r.get("id"))] = i
    sem_map = {}
    for i, r in enumerate(sem_results):
        sem_map[str(r.get("id"))] = (i, r.get("retrieval_score", 0))
    # entity/tag match
    con = sqlite3.connect(str(ms.db_path()))
    con.row_factory = sqlite3.Row
    q = args.query
    toks = [t for t in q.split() if len(t) >= 2]
    rows = con.execute("SELECT * FROM memories WHERE archived=0").fetchall()
    con.close()
    score = {}
    meta = {}
    for r in rows:
        mid = str(r["id"])
        ent = 1.0 if any(t in (r["entity"] or "") for t in toks) else 0.0
        tag = 1.0 if any(t in (r["tags"] or "") for t in toks) else 0.0
        e = max(ent, tag)
        s = 0.0
        if mid in kw_map:
            s += 0.5 * (1.0 / (1.0 + kw_map[mid]))
        if mid in sem_map:
            si = sem_map[mid][0]
            s += 0.35 * (1.0 / (1.0 + si))
        s += 0.2 * e
        s += 0.05 * (r["importance"] or 0.0)
        if mid not in score or s > score[mid]:
            score[mid] = s
            meta[mid] = {"id": r["id"], "content": r["content"], "entity": r["entity"], "tags": r["tags"], "score": round(s, 4)}
    ranked = sorted(meta.values(), key=lambda x: -x["score"])[:args.limit]
    print(json.dumps({"ok": True, "results": ranked}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
