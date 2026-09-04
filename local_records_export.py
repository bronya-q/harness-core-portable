#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_records_export.py — 生成机器可读本地证据快照。

输出：local-records-snapshot.public.json
只包含脱敏聚合指标、定义、来源、口径、commitment；不含原文。

每个指标尽量记录：
  metric_id / value / unit / source_kind / source / filter / generated_at
  numerator / denominator / excluded_count / aggregation

在原始环境运行；干净 clone 中无私有数据时输出 ok:false reason，不写文件。
"""
import csv
import hashlib
import json
import platform
import random
import sqlite3
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
GENERATOR_VERSION = "1"
SCHEMA_VERSION = 1
NOW = datetime.now(timezone.utc)


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


def metric(metric_id, value, unit, source_kind, source, filt, generated_at=None,
           numerator=None, denominator=None, excluded_count=None, aggregation=None):
    return {
        "metric_id": metric_id,
        "value": value,
        "unit": unit,
        "source_kind": source_kind,
        "source": source,
        "filter": filt,
        "generated_at": (generated_at or NOW).isoformat(),
        "numerator": numerator,
        "denominator": denominator,
        "excluded_count": excluded_count,
        "aggregation": aggregation,
    }


def read_gold_csv(path):
    if not Path(path).exists():
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        rows = list(csv.reader(fh))
    return {"header": rows[0], "data_rows": max(0, len(rows) - 1)} if rows else None


def bootstrap_ci(values, iters=1000, seed=42):
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
    if not (MEM_DIR / "memory.db").exists():
        print(json.dumps({"ok": False, "reason": "private local data not found; run in the originating environment"},
                         ensure_ascii=False, indent=2))
        return 0

    mem = table_counts(MEM_DIR / "memory.db") or {}
    metrics = {}

    # memory counts
    metrics["memories_total"] = metric("memories_total", mem.get("memories"), "rows", "sqlite_count",
                                       "memory.db:memories", "all")
    # active/archived from memory_health or sqlite count
    try:
        con = sqlite3.connect(f"file:{MEM_DIR / 'memory.db'}?mode=ro", uri=True)
        active = con.execute("SELECT COUNT(*) FROM memories WHERE archived=0").fetchone()[0]
        archived = con.execute("SELECT COUNT(*) FROM memories WHERE archived=1").fetchone()[0]
        con.close()
    except Exception:
        active = archived = None
    metrics["memories_active"] = metric("memories_active", active, "rows", "sqlite_count",
                                        "memory.db:memories", "archived=0")
    metrics["memories_archived"] = metric("memories_archived", archived, "rows", "sqlite_count",
                                          "memory.db:memories", "archived=1")

    # sidecar counts
    sidecars = {}
    for name in ["humanization_sidecar.db", "continuity_sidecar.db", "atomic_facts_sidecar.db",
                 "identity_sidecar.db", "proactive_sidecar.db", "cognitive_dynamics.db",
                 "nine_dim_revision.db", "notebooks.db", "mind_review.db"]:
        counts = table_counts(MEM_DIR / name)
        if counts is not None:
            sidecars[name] = counts
            for t, c in counts.items():
                metrics[f"{name}:{t}"] = metric(f"{name}:{t}", c, "rows", "sqlite_count",
                                                f"{name}:{t}", "all")

    # gold
    gold = read_gold_csv(SKILL_DIR / "recall_gold_independent_blind.csv")
    gold_labels = gold["data_rows"] if gold else None
    if gold_labels is not None:
        metrics["gold_labels_total"] = metric("gold_labels_total", gold_labels, "count", "csv_rows",
                                              "recall_gold_independent_blind.csv", "all")
    gold_v2 = None
    gv2 = SKILL_DIR / "recall_gold_independent_v2.json"
    if gv2.exists():
        try:
            d = json.loads(gv2.read_text(encoding="utf-8"))
            gold_v2 = {"queries": len(d),
                       "items_per_query": len(d[0].get("items", [])) if d else 0,
                       "total_items": sum(len(x.get("items", [])) for x in d) if isinstance(d, list) else None}
            metrics["gold_query_count"] = metric("gold_query_count", gold_v2["queries"], "count", "json",
                                                 "recall_gold_independent_v2.json", "all")
            metrics["gold_candidates_per_query"] = metric("gold_candidates_per_query", gold_v2["items_per_query"],
                                                          "count", "json", "recall_gold_independent_v2.json",
                                                          "per_query")
            metrics["gold_expected_total"] = metric("gold_expected_total", gold_v2["total_items"], "count", "json",
                                                    "recall_gold_independent_v2.json", "queries*items")
        except Exception:
            pass

    # latest rating snapshot
    snapshots = sorted((MEM_DIR / "rating-snapshots").glob("*.json"))
    latest_snapshot = None
    if snapshots:
        try:
            latest_snapshot = json.loads(snapshots[-1].read_text(encoding="utf-8"))
        except Exception:
            latest_snapshot = None
    pg = latest_snapshot.get("commands", {}).get("production_gate") if latest_snapshot else None
    # 公开 gate 只包含 G1-G19；本地私有完整 gate 可能有 G20，不进入公共快照
    if isinstance(pg, dict) and isinstance(pg.get("checks"), list):
        public_ids = {f"G{i}" for i in range(1, 20)}
        pg["checks"] = [ch for ch in pg["checks"] if ch.get("id") in public_ids]
    rec = latest_snapshot.get("commands", {}).get("measurement_recall_pool") if latest_snapshot else None
    pa = latest_snapshot.get("commands", {}).get("plugin_audit") if latest_snapshot else None

    # sanitize plugin_audit paths
    if isinstance(pa, dict) and isinstance(pa.get("plugins"), list):
        pa["plugins"] = [
            {k: v for k, v in pl.items() if k not in ("path", "src", "entrypoint", "stdout", "stderr")}
            for pl in pa["plugins"]
        ]

    if pg:
        metrics["production_gate_status"] = metric("production_gate_status", pg.get("gate_status"), "enum",
                                                   "rating_snapshot_json", "rating-snapshots/latest", "gate")
        for ch in pg.get("checks", []):
            cid = ch.get("id")
            metrics[f"gate_{cid}"] = metric(f"gate_{cid}", ch.get("value"), "mixed", "rating_snapshot_json",
                                            "production_gate", ch.get("name"))

    if rec:
        metrics["recall_pool_p_at_5"] = metric("recall_pool_p_at_5", rec.get("avg_precision_at_k"), "ratio",
                                               "measurement_json", "measurement.recall-pool", "top_k=5")
        metrics["recall_pool_recall"] = metric("recall_pool_recall", rec.get("avg_recall"), "ratio",
                                               "measurement_json", "measurement.recall-pool", "top_k=5")
        metrics["recall_pool_hit_rate_at_5"] = metric("recall_pool_hit_rate_at_5", rec.get("hit_rate"), "ratio",
                                                      "measurement_json", "measurement.recall-pool", "top_k=5")
        metrics["recall_pool_queries"] = metric("recall_pool_queries", rec.get("queries"), "count",
                                                "measurement_json", "measurement.recall-pool", "all")
        metrics["recall_pool_zero_relevant"] = metric("recall_pool_zero_relevant", rec.get("zero_relevant_queries"),
                                                      "count", "measurement_json", "measurement.recall-pool",
                                                      "query=zero_relevant")

    # per-query
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
    failure_queries = []
    if per_query:
        failure_queries = [r for r in per_query if (r.get("precision_at_k") if r.get("precision_at_k") is not None else 0) < 1.0]

    # raw commitments
    commitments = {}
    for name in ["memory.db", "humanization_sidecar.db", "continuity_sidecar.db",
                 "notebooks.db", "mind_review.db"]:
        p = MEM_DIR / name
        if p.exists():
            commitments[name] = sha256_file(p)
    gcsv = SKILL_DIR / "recall_gold_independent_blind.csv"
    if gcsv.exists():
        commitments["recall_gold_independent_blind.csv"] = sha256_file(gcsv)

    # 对公共快照做本机私人 scope 匿名化
    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        if isinstance(obj, str):
            for old_name, new_name in [("character:demo-alice", "character:demo-alice"),
                                       ("character:demo-storykeeper", "character:demo-storykeeper"),
                                       ("character:demo-bob", "character:demo-bob")]:
                obj = obj.replace(old_name, new_name)
            return obj
        return obj

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": "local-" + NOW.strftime("%Y%m%d-%H%M%S"),
        "generated_at": NOW.isoformat(),
        "generator_version": GENERATOR_VERSION,
        "generator": "local_records_export.py",
        "source_commit": source_commit(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "model_names_disclosed": False,
        },
        "privacy": {
            "aggregate_only": True,
            "raw_data_public": False,
            "contains_pii": False,
        },
        "metrics": metrics,
        "raw_commitments": commitments,
        "per_query_metrics": per_query,
        "failure_queries": failure_queries,
        "bootstrap_ci": {
            "precision_at_k": bootstrap_ci([float(r["precision_at_k"]) for r in per_query if r.get("precision_at_k") is not None]),
            "recall": bootstrap_ci([float(r["recall"]) for r in per_query if r.get("recall") is not None]),
        } if per_query else None,
        "sidecars": sidecars,
        "production_gate": pg,
        "measurement_recall_pool": rec,
        "plugin_audit": pa,
        "metric_definitions": {
            "P@5": "top-5 中相关结果占比的平均（按 query 平均）",
            "recall": "独立池内相关结果被 top-5 召回的比例（按 query 平均）",
            "hit_rate@5": "至少 1 条相关结果出现在 top-5 的 query 占比",
            "independent": "候选池独立于检索 top-k 抽样，不是独立评价者",
        },
        "filters": {
            "gold_pool": "recall_gold_independent_v2.json",
            "top_k": 5,
            "retriever": "keyword+semantic per measurement config",
            "environment": "local private",
        },
    }
    snapshot = _sanitize(snapshot)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(OUT), "snapshot_id": snapshot["snapshot_id"],
                      "metric_count": len(metrics), "per_query_count": len(per_query)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
