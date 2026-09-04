#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gold_sampler.py — 从完整记忆池独立抽样构建 relevance gold（v2）。

做法：
  对每个 query，从 active memories 随机/分层抽取 N 条，
  用“内容是否包含 query 主题词”的独立规则标注 relevance（0/1），
  不依赖任何检索 top-k 分数。

输出：
  recall_gold_independent_v2.json
  [{query, scope, items:[{id, relevance}]}]
"""
import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms

QUERIES = [
    "马克斯", "九维", "记忆", "安全", "桌宠", "DeepSeek", "回归", "方案", "历史",
    "人格", "memory", "skill", "插件", "微信", "QQ", "cmc", "妹居物语", "dot-skill",
    "沙盒", "OCR", "密钥", "权限", "依赖", "live2d", "鲸鱼", "派对", "意识", "边界",
    "马克思", "人类小姐", "环境变量", "B站", "少女乐队", "COC", "TRPG", "练车",
]


def _tokens(query):
    return [w.lower() for w in query.split() if len(w) >= 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="recall_gold_independent_v2.json")
    ap.add_argument("--queries", default=",".join(QUERIES))
    args = ap.parse_args()

    con = sqlite3.connect(str(ms.db_path()))
    con.row_factory = sqlite3.Row
    all_rows = con.execute("SELECT id, content FROM memories WHERE archived=0").fetchall()
    con.close()
    rng = random.Random(args.seed)
    queries = [q.strip() for q in args.queries.split(",") if q.strip()]

    out = []
    for q in queries:
        # 分层：先按内容是否含 query 词分桶，再从两桶各抽一部分，避免全是相关或不相关
        toks = _tokens(q)
        pos = [r for r in all_rows if any(t in (r["content"] or "").lower() for t in toks)]
        neg = [r for r in all_rows if r not in pos]
        rng.shuffle(pos)
        rng.shuffle(neg)
        # 目标：若正样本足够，抽一半正一半负；否则尽量多正
        half = args.n // 2
        chosen = pos[:max(0, min(half, len(pos)))]
        chosen += neg[:max(0, args.n - len(chosen))]
        chosen = chosen[:args.n]
        items = [{"id": r["id"], "relevance": 1 if r in pos else 0} for r in chosen]
        # 保留相关样本顺序
        items.sort(key=lambda x: -x["relevance"])
        out.append({"query": q, "scope": "default", "items": items})

    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": args.out, "queries": len(out),
                      "total_items": sum(len(x["items"]) for x in out)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
