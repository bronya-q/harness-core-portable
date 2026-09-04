#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gold_labeler.py — 人工 gold 集标注工作流。

export：把 recall_gold.json 展开成 CSV（query, expected_id, content, keep）。
        人工在 keep 列填 1/0，或直接修改列。
import：读取人工标注后的 CSV，生成 recall_gold_human.json。
"""
import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms


def _content(mid):
    con = sqlite3.connect(str(ms.db_path()))
    r = con.execute("SELECT content FROM memories WHERE id=?", (mid,)).fetchone()
    con.close()
    return r[0][:120] if r else ""


def export(args):
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    out = args.out
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["query", "scope", "expected_id", "content", "keep"])
        for item in gold:
            for mid in item.get("expected_ids", []):
                w.writerow([item["query"], item.get("scope", "default"), mid, _content(mid), ""])
    print(json.dumps({"ok": True, "exported": sum(len(x.get("expected_ids", [])) for x in gold),
                      "path": out, "note": "mark keep=1 for accepted gold rows"},
                     ensure_ascii=False, indent=2))


def import_(args):
    rows = []
    _fh = None
    for _enc in ("utf-8-sig", "gbk", "gb18030"):
        try:
            _fh = open(args.file, newline="", encoding=_enc)
            rd = csv.DictReader(_fh)
            # force read one row to validate encoding
            next(rd)
            _fh.seek(0)
            break
        except Exception:
            continue
    if _fh is None:
        raise SystemExit("cannot read csv")
    _fh.seek(0)
    rd = csv.DictReader(_fh)
    for r in rd:
            if str(r.get("keep", "")).strip() in ("1", "true", "yes", "y", "TRUE"):
                rows.append({"query": r["query"], "scope": r.get("scope", "default"),
                             "expected_ids": [int(r["expected_id"])] if r.get("expected_id") else []})
    _fh.close()
    # merge same query expected ids
    merged = {}
    for r in rows:
        merged.setdefault(r["query"], {"query": r["query"], "scope": r["scope"], "expected_ids": []})
        merged[r["query"]]["expected_ids"].extend(r["expected_ids"])
    gold = list(merged.values())
    out = args.out
    Path(out).write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "imported_queries": len(gold), "path": out}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export")
    p.add_argument("--gold", default="recall_gold.json")
    p.add_argument("--out", default="recall_gold_label.csv")
    p.set_defaults(fn=export)
    p = sub.add_parser("import")
    p.add_argument("--file", default="recall_gold_label.csv")
    p.add_argument("--out", default="recall_gold_human.json")
    p.set_defaults(fn=import_)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
