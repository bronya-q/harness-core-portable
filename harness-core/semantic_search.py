#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""semantic_search.py — 语义检索（整改方案 P2-2 第 2 步）

与 memory_store.search_memories 的关系：**增量而非替代**。
  - 候选召回：bge-m3 余弦相似度（vec 表，fill_vec.py 回填）
  - 重排公式：与 memory_store 完全一致（importance*0.5 + 时效*0.3 + 情感显著性*0.2）
  - 读取计数：与 search_memories 相同地回写 access_count/last_access_at
子串精确匹配仍走 memory_store（不动）。本脚本解决「同义不同词」场景。

用法:
  python semantic_search.py --query "主人生病了" --limit 5
  python semantic_search.py --query "..." --scope character:demo-alice
"""
import argparse
import json
import math
import sqlite3
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
import memory_store as ms
from nine_dim import _embed, _unpack, _cos, VEC_DB


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--scope", default=None)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--min-importance", type=float, default=None)
    ap.add_argument("--sim-weight", type=float, default=0.4,
                    help="语义相似度权重（默认 0.4，其余为 retrieval 分）")
    args = ap.parse_args()

    main_db = sqlite3.connect(str(ms.db_path()))
    main_db.row_factory = sqlite3.Row
    vec_db = sqlite3.connect(str(VEC_DB))

    q = _embed(args.query)
    rows = vec_db.execute("SELECT memory_id, vec FROM vec").fetchall()
    scored = []
    for mid, blob in rows:
        mem = main_db.execute(
            "SELECT * FROM memories WHERE id=? AND archived=0", (mid,)
        ).fetchone()
        if not mem:
            continue
        if args.scope and mem["scope"] != args.scope:
            continue
        if args.min_importance is not None and mem["importance"] < args.min_importance:
            continue
        sim = _cos(q, _unpack(blob))
        # 与 memory_store 相同的时效项：1/(days+1)
        try:
            days = (datetime.now(timezone.utc) - datetime.fromisoformat(mem["updated_at"])).days
        except Exception:
            days = 0
        recency = 1.0 / (days + 1.0)
        salience = (abs(mem["valence"] or 0.0) + (mem["arousal"] or 0.0)) / 2.0
        retrieval = mem["importance"] * 0.5 + recency * 0.3 + salience * 0.2
        w = max(0.0, min(1.0, args.sim_weight))
        scored.append(((1.0 - w) * retrieval + w * sim, sim, retrieval, mem))
    scored.sort(key=lambda x: -x[0])

    out, hit_ids = [], []
    for total, sim, retrieval, mem in scored[: args.limit]:
        hit_ids.append(mem["id"])
        out.append({
            "id": mem["id"], "scope": mem["scope"], "kind": mem["kind"],
            "content": mem["content"], "importance": mem["importance"],
            "created_at": mem["created_at"],
            "sim": round(sim, 4), "retrieval_score": round(retrieval, 4),
            "final_score": round(total, 4),
        })

    # 与 search_memories 相同的读取计数回写（P0-1）
    if hit_ids:
        ids = ",".join(map(str, hit_ids))
        main_db.execute(
            f"UPDATE memories SET access_count=access_count+1, last_access_at=? WHERE id IN ({ids})",
            (ms.now_iso(),),
        )
        main_db.commit()

    print(json.dumps({"query": args.query, "candidates": len(scored), "results": out},
                     ensure_ascii=False, indent=2))
    if not scored:
        print("[semantic_search] vec 表为空或无匹配——先跑 fill_vec.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
