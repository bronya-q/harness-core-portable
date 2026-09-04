#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_local_records.py — 生成本地记录机器可读快照。

用途：
  在原始环境中运行，读取本地 SQLite/CSV/json，生成
  local-records-snapshot.public.json（只含脱敏指标，不含原文）。
  避免 Markdown 手抄数字漂移：先跑本脚本，再把关键数字同步到 LOCAL_RECORDS.md。

在干净 clone（无私有数据）中运行会输出 ok:false reason，不写文件，退出码 0。
"""
import csv
import hashlib
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "local-records-snapshot.public.json"
MEM_DIR = Path.home() / ".dsh" / "memory-emotion"
SKILL_DIR = Path.home() / ".agents" / "skills" / "long-term-memory-emotion"


def sha256_file(path):
    data = Path(path).read_bytes().replace((chr(13) + chr(10)).encode(), chr(10).encode())
    return hashlib.sha256(data).hexdigest()


def source_commit():
    try:
        p = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
        return p.stdout.strip() if p.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def table_counts(db_path):
    import sqlite3
    if not Path(db_path).exists():
        return None
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        out = {}
        for t in tables:
            if t == "sqlite_sequence":
                continue
            try:
                out[t] = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            except Exception:
                out[t] = None
        con.close()
        return out
    except Exception:
        return None


def read_gold_csv(path):
    if not Path(path).exists():
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return None
    return {"header": rows[0], "data_rows": max(0, len(rows) - 1)}


def bootstrap_ci(values, iters=1000, seed=42):
    """给定 query-level 数值列表，返回 95% bootstrap CI。"""
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(iters):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    lo = sorted(means)[int(0.025 * iters)]
    hi = sorted(means)[int(0.975 * iters)]
    return {"mean": round(sum(values) / n, 4), "ci95_low": round(lo, 4), "ci95_high": round(hi, 4)}


def main():
    data = {}
    if not (MEM_DIR / "memory.db").exists():
        print(json.dumps({"ok": False, "reason": "private local data not found; run in the originating environment"},
                         ensure_ascii=False, indent=2))
        return 0

    # 1) memory
    mem = table_counts(MEM_DIR / "memory.db") or {}
    data["memory_db_tables"] = mem

    # 2) sidecars
    sidecars = {}
    for name in ["humanization_sidecar.db", "continuity_sidecar.db", "atomic_facts_sidecar.db",
                 "identity_sidecar.db", "proactive_sidecar.db", "cognitive_dynamics.db",
                 "nine_dim_revision.db", "notebooks.db", "mind_review.db"]:
        counts = table_counts(MEM_DIR / name)
        if counts is not None:
            sidecars[name] = counts
    data["sidecars"] = sidecars

    # 3) gold CSV
    gold = read_gold_csv(SKILL_DIR / "recall_gold_independent_blind.csv")
    data["gold_blind_csv"] = gold
    gold_v2 = None
    gv2 = SKILL_DIR / "recall_gold_independent_v2.json"
    if gv2.exists():
        try:
            d = json.loads(gv2.read_text(encoding="utf-8"))
            gold_v2 = {"queries": len(d),
                       "items_per_query": len(d[0].get("items", [])) if d else 0,
                       "total_items": sum(len(x.get("items", [])) for x in d) if isinstance(d, list) else None}
        except Exception:
            pass
    data["gold_v2"] = gold_v2

    # 4) latest rating snapshot
    snapshots = sorted((MEM_DIR / "rating-snapshots").glob("*.json"))
    latest_snapshot = None
    if snapshots:
        try:
            latest_snapshot = json.loads(snapshots[-1].read_text(encoding="utf-8"))
        except Exception:
            latest_snapshot = None
    data["rating_snapshots_count"] = len(snapshots)
    pg = None
    rec = None
    if latest_snapshot:
        pg = latest_snapshot.get("commands", {}).get("production_gate")
        rec = latest_snapshot.get("commands", {}).get("measurement_recall_pool")
        data["production_gate"] = pg
        data["measurement_recall_pool"] = rec

    # 5) plugin audit（去掉本地路径，只留可公开字段）
    pa = latest_snapshot.get("commands", {}).get("plugin_audit") if latest_snapshot else None
    if isinstance(pa, dict) and isinstance(pa.get("plugins"), list):
        pa["plugins"] = [
            {k: v for k, v in pl.items() if k not in ("path", "src", "entrypoint", "stdout", "stderr")}
            for pl in pa["plugins"]
        ]
    data["plugin_audit"] = pa

    # 6) per-query metrics and bootstrap CI
    per_query = []
    if rec and isinstance(rec.get("rows"), list):
        for row in rec["rows"]:
            per_query.append({
                "query": row.get("query"),
                "precision_at_k": row.get("precision_at_k"),
                "recall": row.get("recall"),
                "hit": row.get("hit"),
                "relevant_pool": row.get("relevant_pool"),
                "judged": row.get("judged"),
            })
    data["per_query_metrics"] = per_query
    if per_query:
        data["failure_queries"] = [
            r for r in per_query if (r.get("precision_at_k") if r.get("precision_at_k") is not None else 0) < 1.0
        ]
        data["bootstrap_ci"] = {
            "precision_at_k": bootstrap_ci([float(r["precision_at_k"]) for r in per_query if r.get("precision_at_k") is not None]),
            "recall": bootstrap_ci([float(r["recall"]) for r in per_query if r.get("recall") is not None]),
        }

    # 7) raw commitments (hash only, no content)
    commitments = {}
    for rel in ["memory.db", "humanization_sidecar.db", "continuity_sidecar.db",
                "notebooks.db", "mind_review.db"]:
        p = MEM_DIR / rel
        if p.exists():
            commitments[rel] = sha256_file(p)
    gold_csv = SKILL_DIR / "recall_gold_independent_blind.csv"
    if gold_csv.exists():
        commitments["recall_gold_independent_blind.csv"] = sha256_file(gold_csv)
    data["raw_commitments"] = commitments

    # 8) metric definitions
    data["metric_definitions"] = {
        "P@5": "top-5 中相关结果占比的平均（按 query 平均）",
        "recall": "独立池内相关结果被 top-5 召回的比例（按 query 平均）",
        "hit_rate@5": "至少 1 条相关结果出现在 top-5 的 query 占比",
        "independent": "候选池独立于检索 top-k 抽样，不是独立评价者",
    }
    data["filters"] = {
        "gold_pool": "recall_gold_independent_v2.json",
        "top_k": 5,
        "retriever": "keyword+semantic per measurement config",
        "environment": "local private",
    }
    data["denominators"] = {
        "recall_pool_queries": len(per_query),
        "gold_items": (gold or {}).get("data_rows"),
        "memory_total": data.get("memory_db_tables", {}).get("memories"),
        "rating_snapshots": len(snapshots),
    }

    snapshot = {
        "schema_version": 1,
        "snapshot_id": hashlib.sha256(datetime.now(timezone.utc).isoformat().encode()).hexdigest()[:16],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "generate_local_records.py",
        "source_commit": source_commit(),
        "environment": "local_private",
        "metric_definitions": data["metric_definitions"],
        "filters": data["filters"],
        "denominators": data["denominators"],
        "raw_commitments": data["raw_commitments"],
        "data": data,
    }
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(OUT),
                      "snapshot_id": snapshot["snapshot_id"],
                      "count": len(per_query)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
