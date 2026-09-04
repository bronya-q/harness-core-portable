#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools_inventory.py — 生成工具清单与本地依赖图（收敛/清理用）。"""
import ast
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
LEGACY = SKILL / "tools_legacy.json"


def categories():
    return {
        "memory": ["memory_store", "memory_ingest", "history_backfill", "recall_context", "semantic_search",
                   "vector_queue", "vector_worker", "fill_vec", "memory_health_report", "memory-emotion-daemon"],
        "emotion": ["nine_dim", "nine_dim_revision", "emotion_projection", "need_projection", "congruence_probe"],
        "persona": ["humanization", "user_model", "mind_evolution", "mind_precipitate", "mind_audit",
                    "phenomenological_review", "profile_layers", "natural_session", "user_confirmed_intake"],
        "perspective": ["perspective_card", "w-doctor-scratch"],
        "audit_measure": ["measurement", "leakage_matrix", "persona_drift", "drift_matrix", "narrative_audit",
                          "blind_review_export", "gold_labeler", "gold_sampler", "gold_human_label_export",
                          "gold_human_label_import", "recall_labeling", "production_gate", "quarterly_audit",
                          "harness_selfcheck", "daily_report", "rating_snapshot", "health_board", "queue_health"],
        "plugin": ["plugin_audit", "plugin_sandbox", "plugin_runtime_verify", "deepseek_key_rotation_check"],
        "runtime": ["runtime_policy", "runtime_preflight", "runtime_resolver", "generate_manifest", "manifest_check",
                    "continuous_store", "continuity_store", "continuity_report", "session_ingest", "autonomous_tasks",
                    "belief_sidecar", "measurement_store"],
        "seed_test": [f for f in ("seed_deepseek_insights", "seed_initial_emotions", "seed_philosophy_insights",
                                  "humanization_smoke_test", "g1_shadow_test", "deepseek_regression", "review_queue")],
    }


def category_for(name):
    cats = categories()
    for cat, names in cats.items():
        if name in names:
            return cat
    return "other"


def main():
    legacy = {}
    if LEGACY.exists():
        legacy = json.loads(LEGACY.read_text(encoding="utf-8")).get("deprecated", {})
    inv = {}
    # local modules set
    local = {p.stem for p in SKILL.glob("*.py")}
    edges = set()
    for p in sorted(SKILL.glob("*.py")):
        name = p.stem
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            inv[name] = {"cat": category_for(name), "status": "parse_error", "imports": [], "deprecated": legacy.get(name, False)}
            continue
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in local and mod != name:
                        deps.append(mod)
                        edges.add((name, mod))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module.split(".")[0]
                    if mod in local and mod != name:
                        deps.append(mod)
                        edges.add((name, mod))
        inv[name] = {"cat": category_for(name), "status": "active",
                     "deprecated": legacy.get(name, False), "imports": sorted(set(deps))}
    # write inventory
    SKILL.joinpath("tools_inventory.json").write_text(
        json.dumps({"schema_version": 1, "count": len(inv), "tools": inv, "edges": [[a, b] for a, b in sorted(edges)]},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    # write dot
    dot = ["digraph tools {", "  rankdir=LR;"]
    for a, b in sorted(edges):
        dot.append('  "%s" -> "%s";' % (a, b))
    dot.append("}")
    SKILL.joinpath("tools_dependency.dot").write_text("\n".join(dot), encoding="utf-8")
    print(json.dumps({"ok": True, "count": len(inv), "deprecated": sum(1 for v in inv.values() if v["deprecated"]),
                      "edges": len(edges)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
