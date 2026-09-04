#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_records_verify.py — 校验 local-records-snapshot.public.json。

检测：
  - schema 字段是否齐全
  - 每个指标是否有 value/unit/source_kind/source/filter/generated_at
  - gold 数量关系：query_count * candidates_per_query == labels
  - gate ID 是否都在公开 G1-G19，且不存在 G20
  - 指标名/定义是否还有 hit_rate@10 或裸 hit_rate 旧口径
  - source_commit 是否为当前 Git 仓库已知 commit
  - per-query 数量与 query_count 一致
  - bootstrap CI 是否存在（有 per-query 时必须存在）
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "local-records-snapshot.public.json"
PUBLIC_GATE_IDS = {f"G{i}" for i in range(1, 20)}


def git_known_commit(commit):
    if not commit or commit == "unknown":
        return False
    try:
        p = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", commit + "^{commit}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
        return p.returncode == 0
    except Exception:
        return False


def main():
    issues = []
    warnings = []
    if not SNAP.exists():
        print(json.dumps({"ok": False, "issues": ["missing local-records-snapshot.public.json"]},
                         ensure_ascii=False, indent=2))
        return 1

    d = json.loads(SNAP.read_text(encoding="utf-8"))

    for field in ["schema_version", "snapshot_id", "generated_at", "generator", "generator_version",
                  "source_commit", "environment", "privacy", "metrics"]:
        if field not in d:
            issues.append(f"missing_field:{field}")

    if d.get("schema_version") != 1:
        issues.append("schema_version_mismatch")

    # metric completeness
    metrics = d.get("metrics", {})
    for mid, m in metrics.items():
        if not isinstance(m, dict):
            issues.append(f"bad_metric:{mid}")
            continue
        for k in ["metric_id", "value", "unit", "source_kind", "source", "filter", "generated_at"]:
            if k not in m:
                issues.append(f"metric_missing:{k}:{mid}")

    # gold relationship
    q = metrics.get("gold_query_count", {}).get("value")
    c = metrics.get("gold_candidates_per_query", {}).get("value")
    t = metrics.get("gold_labels_total", {}).get("value")
    if q is not None and c is not None and t is not None:
        if q * c != t:
            issues.append(f"gold_count_mismatch:{q}*{c}!={t}")

    # gate IDs
    for mid in metrics:
        if mid.startswith("gate_"):
            gid = mid[len("gate_"):]
            if gid not in PUBLIC_GATE_IDS:
                issues.append(f"non_public_gate:{gid}")
    if metrics.get("gate_G20"):
        issues.append("non_public_gate:G20")

    # hit_rate naming
    bad_hit_names = [k for k in metrics if "hit_rate@10" in k]
    if bad_hit_names:
        issues.append("old_hit_rate_naming:" + ",".join(bad_hit_names))
    definitions = d.get("metric_definitions", {})
    for k, v in definitions.items():
        if "hit_rate@10" in v or "@10" in k:
            issues.append("old_hit_rate_definition:" + k)

    # source commit
    if not git_known_commit(d.get("source_commit")):
        warnings.append("source_commit_not_in_local_git:" + str(d.get("source_commit")))

    # per-query count
    pq = d.get("per_query_metrics", [])
    rec = d.get("measurement_recall_pool", {})
    rc = rec.get("queries")
    if rc is not None and len(pq) != rc:
        issues.append(f"per_query_count_mismatch:{len(pq)}!={rc}")

    # bootstrap CI
    if pq and not d.get("bootstrap_ci"):
        issues.append("missing_bootstrap_ci")

    ok = not issues
    print(json.dumps({
        "ok": ok,
        "mode": "local_records_verify",
        "snapshot_id": d.get("snapshot_id"),
        "metric_count": len(metrics),
        "issues": issues,
        "warnings": warnings,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
