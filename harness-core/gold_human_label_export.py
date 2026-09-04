#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gold_human_label_export.py — 导出人工标注抽样 CSV（relevance 独立 gold）。

用法：
  python gold_human_label_export.py --n 8 --out recall_gold_independent_human_label.csv
"""
import argparse
import csv
import json
import random
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="recall_gold_independent_v2.json")
    ap.add_argument("--n", type=int, default=8, help="每 query 抽取条数")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="recall_gold_independent_human_label.csv")
    args = ap.parse_args()

    data = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    rng = random.Random(args.seed)
    rows = []
    for entry in data:
        items = entry["items"]
        pos = [i for i in items if i.get("relevance") == 1]
        neg = [i for i in items if i.get("relevance") == 0]
        half = max(1, args.n // 2)
        rng.shuffle(pos)
        rng.shuffle(neg)
        chosen = pos[:min(half, len(pos))] + neg[:min(args.n - min(half, len(pos)), len(neg))]
        for it in chosen:
            rows.append({
                "query": entry["query"],
                "scope": entry.get("scope", "default"),
                "expected_id": it["id"],
                "ai_relevance": it.get("relevance", ""),
                "content": "",
                "human_relevance": "",
            })
    # fill content from memory db
    import memory_store as ms
    import sqlite3
    con = sqlite3.connect(str(ms.db_path()))
    con.row_factory = sqlite3.Row
    for r in rows:
        row = con.execute("SELECT content FROM memories WHERE id=?", (r["expected_id"],)).fetchone()
        if row:
            r["content"] = (row["content"] or "")[:120]
    con.close()
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({"ok": True, "out": args.out, "rows": len(rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
