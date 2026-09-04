#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ngram_fallback.py — 字符 n-gram 低门槛检索 fallback。

设计边界（不冒充语义/向量检索）：
- 只在精确子串命中不足时作为补充；
- 使用字符 bigram 重叠率，不调用模型、不访问网络；
- 输出会标注 `match_method: ngram_fallback`，供测量脚本区分。
"""
import argparse
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import memory_store as ms


def char_ngrams(text, n=2):
    text = re.sub(r"\s+", "", (text or "").lower())
    if len(text) < n:
        return {text} if text else set()
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def ngram_score(content, query):
    qn = char_ngrams(query)
    cn = char_ngrams(content)
    if not qn:
        return 0.0
    return round(len(qn & cn) / len(qn), 4)


def search(query, scope=None, limit=10, kind=None, min_importance=None, use_memory_store=False):
    """先走 memory_store 精确子串；若为空，再按 n-gram 打分排序。"""
    conn = ms.connect()
    exact_rows = []
    if query:
        where = ["archived = 0"]
        params = []
        if scope:
            where.append("scope = ?")
            params.append(scope)
        if kind:
            where.append("kind = ?")
            params.append(kind)
        if min_importance is not None:
            where.append("importance >= ?")
            params.append(min_importance)
        where.append("(instr(lower(content), lower(?)) > 0 OR instr(lower(tags), lower(?)) > 0)")
        params.extend([query, query])
        exact_rows = conn.execute(
            "SELECT * FROM memories WHERE " + " AND ".join(where) + " ORDER BY id DESC LIMIT ?",
            params + [limit],
        ).fetchall()
    if exact_rows:
        out = []
        for r in exact_rows:
            d = dict(r)
            d["match_method"] = "exact_substring"
            out.append(d)
        conn.close()
        return out

    where = ["archived = 0"]
    params = []
    if scope:
        where.append("scope = ?")
        params.append(scope)
    if kind:
        where.append("kind = ?")
        params.append(kind)
    if min_importance is not None:
        where.append("importance >= ?")
        params.append(min_importance)
    cand = conn.execute("SELECT * FROM memories WHERE " + " AND ".join(where) + " LIMIT 1000", params).fetchall()
    scored = []
    for r in cand:
        sc = ngram_score(r["content"], query or "")
        if sc > 0:
            d = dict(r)
            d["ngram_score"] = sc
            d["retrieval_score"] = sc
            d["match_method"] = "ngram_fallback"
            scored.append(d)
    scored.sort(key=lambda d: (d["ngram_score"], d.get("importance", 0.0)), reverse=True)
    conn.close()
    return scored[:limit]


def main():
    ap = argparse.ArgumentParser(description="字符 n-gram fallback 检索")
    ap.add_argument("--query", required=True)
    ap.add_argument("--scope", default=None)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--kind", default=None)
    ap.add_argument("--min-importance", type=float, default=None)
    args = ap.parse_args()
    rows = search(args.query, args.scope, args.limit, args.kind, args.min_importance)
    print(__import__("json").dumps(rows, ensure_ascii=False, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
