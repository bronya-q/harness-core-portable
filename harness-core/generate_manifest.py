#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_manifest.py — 生成统一 manifest.json。

目的：为 resolver/registry/Modelfile/launcher 提供单一可检引用面。
当前是“只读生成 + 校验”的第一步，不自动改任何生产配置。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))
import runtime_resolver as rr  # noqa: E402

OUT = SKILL / "manifest.json"


def dsh_version():
    try:
        p = subprocess.run([os.environ.get("COMSPEC", "cmd"), "/c", "dsh", "--version"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
        return p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    except Exception:
        return ""


def main():
    entries = {}
    for pid, e in rr.ENTRIES.items():
        entries[pid] = {
            "persona_id": pid,
            "scope": e["scope"],
            "model": e.get("model"),
            "source": str(e["source"]),
            "entrypoint": str(e["entrypoint"]),
            "source_exists": Path(str(e["source"])).exists(),
            "entrypoint_exists": Path(str(e["entrypoint"])).exists(),
        }
    routes = []
    routes_path = SKILL / "project-routes.json"
    if routes_path.exists():
        routes = json.loads(routes_path.read_text(encoding="utf-8")).get("routes", [])
    manifest = {
        "schema_version": 1,
        "generated_at": Path(__file__).stat().st_mtime,
        "dsh_version": dsh_version(),
        "profiles": ["web", "headless"],
        "personas": entries,
        "project_routes": routes,
        "policy_files": {
            "runtime_policy": str(Path.home() / ".dsh" / "memory-emotion" / "runtime-policy.json"),
            "humanization_policy": str(Path.home() / ".dsh" / "memory-emotion" / "humanization-policy.json"),
        },
    }
    # 心智自进化（P0-P3）共享沉淀目录：跨 skill 发现入口
    me_root = Path.home() / "Documents" / "harness" / "_mind-evolution"
    me_scripts = {
        "mind_evolution": str(SKILL / "mind_evolution.py"),
        "mind_precipitate": str(SKILL / "mind_precipitate.py"),
        "session_ingest": str(SKILL / "session_ingest.py"),
        "history_backfill": str(SKILL / "history_backfill.py"),
        "phenomenological_review": str(SKILL / "phenomenological_review.py"),
        "nine_dim_revision": str(SKILL / "nine_dim_revision.py"),
        "user_model": str(SKILL / "user_model.py"),
        "health_board": str(SKILL / "health_board.py"),
        "quarterly_audit": str(SKILL / "quarterly_audit.py"),
        "measurement": str(SKILL / "measurement.py"),
        "leakage_matrix": str(SKILL / "leakage_matrix.py"),
        "persona_drift": str(SKILL / "persona_drift.py"),
        "blind_review_export": str(SKILL / "blind_review_export.py"),
        "gold_labeler": str(SKILL / "gold_labeler.py"),
        "congruence_probe": str(SKILL / "congruence_probe.py"),
        "plugin_audit": str(SKILL / "plugin_audit.py"),
        "narrative_audit": str(SKILL / "narrative_audit.py"),
        "production_gate": str(SKILL / "production_gate.py"),
        "user_confirmed_intake": str(SKILL / "user_confirmed_intake.py"),
        "rating_snapshot": str(SKILL / "rating_snapshot.py"),
        "daily_report": str(SKILL / "daily_report.py"),
        "tools_inventory": str(SKILL / "tools_inventory.py"),
        "facts": str(SKILL / "facts.py"),
        "proactive_pipeline": str(SKILL / "proactive_pipeline.py"),
        "p4_experiment": str(SKILL / "p4_experiment.py"),
        "mind_review": str(SKILL / "mind_review.py"),
        "psych_validity_probe": str(SKILL / "psych_validity_probe.py"),
        "user_model_signals": str(SKILL / "user_model_signals.py"),
        "cross_character_consistency": str(SKILL / "cross_character_consistency.py"),
        "cognitive_dynamics": str(SKILL / "cognitive_dynamics.py"),
        "identity_store": str(SKILL / "identity_store.py"),
        "harness_selfcheck": str(SKILL / "harness_selfcheck.py"),
        "perspective_card": str(SKILL / "perspective_card.py"),
        "natural_session": str(SKILL / "natural_session.py"),
        "wechat_adapter": str(SKILL / "wechat_adapter.py"),
    }
    manifest["mind_evolution"] = {
        "root": str(me_root),
        "readme": str(me_root / "README.md"),
        "index": str(me_root / "index.json"),
        "assets": str(me_root / "assets"),
        "scripts": me_scripts,
        "existence": {
            "root": me_root.exists(),
            "readme": (me_root / "README.md").exists(),
            "index": (me_root / "index.json").exists(),
            "assets": (me_root / "assets").exists(),
        },
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "manifest": str(OUT), "persona_count": len(entries),
                      "mind_evolution_root": str(me_root)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
