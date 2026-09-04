#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gold_human_label_import.py — 导入人工 relevance 标注，生成 human-approved independent gold。

用法：
  python gold_human_label_import.py --csv recall_gold_independent_human_label.csv --out recall_gold_independent_human_final.json
"""
import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="recall_gold_independent_human_label.csv")
    ap.add_argument("--out", default="recall_gold_independent_human_final.json")
    ap.add_argument("--batch-id", default="full-2160")
    ap.add_argument("--annotator", default="user")
    args = ap.parse_args()
    ts = time.time()

    rows = None
    for enc in ("utf-8-sig", "gbk", "gb18030"):
        try:
            rows = list(csv.DictReader(open(args.csv, newline="", encoding=enc)))
            break
        except Exception:
            continue
    if rows is None:
        raise SystemExit("cannot read csv")
    grouped = {}
    for r in rows:
        v = (r.get("human_relevance") or "").strip()
        if v not in ("1", "0"):
            continue
        q = r["query"]
        grouped.setdefault(q, {"query": q, "scope": r.get("scope", "default"), "items": []})
        grouped[q]["items"].append({"id": int(r["expected_id"]), "relevance": int(v)})
    out = list(grouped.values())

    # provenance
    canon = []
    for q in out:
        for it in q["items"]:
            canon.append({"query": q["query"], "id": it["id"], "relevance": it["relevance"]})
    blob = json.dumps(canon, ensure_ascii=False, sort_keys=True).encode("utf-8")
    integrity = hashlib.sha256(blob).hexdigest()[:16]
    for q in out:
        for it in q["items"]:
            it["annotator"] = args.annotator
            it["timestamp"] = ts
            it["batch_id"] = args.batch_id
            payload = (q["query"] + "|" + str(it["id"]) + "|" + str(it["relevance"])).encode("utf-8")
            it["hash"] = hashlib.sha256(payload).hexdigest()[:16]
    doc = {
        "schema_version": 2,
        "provenance": {
            "batch_id": args.batch_id,
            "annotator": args.annotator,
            "generated_at": ts,
            "count": sum(len(x["items"]) for x in out),
            "integrity_hash": integrity,
        },
        "gold": out,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": args.out, "queries": len(out),
                      "total_items": sum(len(x["items"]) for x in out), "integrity_hash": integrity},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
