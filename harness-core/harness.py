#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harness.py — 统一 CLI（收敛入口）。

用法：
  python harness.py status
  python harness.py audit
  python harness.py measure <sub> [args...]
  python harness.py plugins <sub> [args...]
  python harness.py gold <sub> [args...]
  python harness.py persona validate --name demo-storykeeper
  python harness.py snapshot
  python harness.py tools
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent

# Generic route table for simple pass-through
PASSTHROUGH = {
    "status": ["humanization.py", ["status"]],
    "snapshot": ["rating_snapshot.py", []],
    "tools": ["tools_inventory.py", []],
    "facts": ["facts.py", []],
    "identity": ["identity_store.py", []],
    "proactive": ["proactive_pipeline.py", []],
    "p4": ["p4_experiment.py", []],
    "review": ["mind_review.py", []],
    "cognitive": ["cognitive_dynamics.py", []],
    "consistency": ["cross_character_consistency.py", []],
    "psych": ["psych_validity_probe.py", []],
    "signals": ["user_model_signals.py", []],
    "notebook": ["notebook.py", []],
    "story": ["story_core.py", []],
    "roleplay": ["roleplay_memory_chat.py", []],
    "demo": ["demo_experience.py", []],
    "start": ["ux_commands.py", ["start"]],
    "doctor": ["ux_commands.py", ["doctor"]],
    "inspect": ["ux_commands.py", ["inspect"]],
    "data": ["ux_commands.py", ["data"]],
    "dashboard": ["dashboard.py", []],
    "memory": ["control_commands.py", ["memory"]],
    "privacy": ["control_commands.py", ["privacy"]],
    "backup": ["control_commands.py", ["backup"]],
    "feedback": ["control_commands.py", ["feedback"]],
    "character": ["assets_commands.py", ["character"]],
    "knowledge": ["assets_commands.py", ["knowledge"]],
    "workspace": ["assets_commands.py", ["workspace"]],
    "schema": ["schema_commands.py", ["schema"]],
    "event": ["event_commands.py", ["event"]],
    "usage": ["event_commands.py", ["usage"]],
    "ab": ["comparison_commands.py", ["ab"]],
    "evidence": ["comparison_commands.py", ["evidence"]],
    "ecosystem": ["ecosystem_status.py", ["ecosystem"]],
}

# Fine-grained subcommands
GOLD_MAP = {
    "export": ["gold_labeler.py", ["export"]],
    "import": ["gold_labeler.py", ["import"]],
    "sample": ["gold_sampler.py", []],
    "human-export": ["gold_human_label_export.py", []],
    "human-import": ["gold_human_label_import.py", []],
}

PLUGINS_MAP = {
    "status": ["plugin_sandbox.py", ["status"]],
    "audit": ["plugin_audit.py", []],
    "verify": ["plugin_runtime_verify.py", []],
    "set": ["plugin_sandbox.py", ["set"]],
    "run": ["plugin_sandbox.py", ["run"]],
}

MEASURE_MAP = {
    "recall": ["measurement.py", ["recall"]],
    "recall-pool": ["measurement.py", ["recall-pool"]],
    "congruence": ["measurement.py", ["congruence"]],
    "anthropomorphism": ["measurement.py", ["anthropomorphism"]],
    "self-reveal": ["measurement.py", ["self_reveal"]],
    "leakage": ["leakage_matrix.py", []],
    "narrative": ["narrative_audit.py", ["audit"]],
}


def _run_script(script, extra):
    sys.path.insert(0, str(SKILL))
    import runpy
    sys.argv = [str(SKILL / script)] + extra
    runpy.run_path(str(SKILL / script), run_name="__main__")


def _subprocess_json(script, args):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    try:
        return json.loads(p.stdout), p.returncode
    except Exception:
        return {"raw": p.stdout[-300:], "stderr": p.stderr[-300:]}, p.returncode


def audit():
    """聚合 production_gate + quarterly + health + snapshot。"""
    gate, gate_rc = _subprocess_json("production_gate.py", [])
    qa, qa_rc = _subprocess_json("quarterly_audit.py", [])
    health, _ = _subprocess_json("memory_health_report.py", [])
    snap, _ = _subprocess_json("rating_snapshot.py", [])
    print(json.dumps({
        "ok": gate_rc == 0 and qa_rc == 0,
        "mode": "audit",
        "production_gate": gate.get("gate_status"),
        "quarterly": qa.get("summary"),
        "health_summary": "pass" if isinstance(health, dict) and not (health.get("warnings") or health.get("relation_out_of_range")) else "warn",
        "snapshot": snap.get("snapshot"),
        "gate_checks": gate.get("checks", []),
        "quarterly_checks": qa.get("checks", []),
    }, ensure_ascii=False, indent=2))
    return 0 if (gate_rc == 0 and qa_rc == 0) else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    if cmd == "audit":
        return audit()
    if cmd == "measure":
        sub = sys.argv[2] if len(sys.argv) > 2 else "congruence"
        if sub in MEASURE_MAP:
            script, base_args = MEASURE_MAP[sub]
            _run_script(script, base_args + sys.argv[3:])
            return 0
        # default: forward to measurement.py
        _run_script("measurement.py", sys.argv[2:])
        return 0
    if cmd == "gold":
        sub = sys.argv[2] if len(sys.argv) > 2 else "export"
        if sub in GOLD_MAP:
            script, base_args = GOLD_MAP[sub]
            _run_script(script, base_args + sys.argv[3:])
            return 0
        _run_script("gold_labeler.py", sys.argv[2:])
        return 0
    if cmd == "plugins":
        sub = sys.argv[2] if len(sys.argv) > 2 else "status"
        if sub in PLUGINS_MAP:
            script, base_args = PLUGINS_MAP[sub]
            _run_script(script, base_args + sys.argv[3:])
            return 0
        _run_script("plugin_sandbox.py", sys.argv[2:])
        return 0
    if cmd in PASSTHROUGH:
        script, base_args = PASSTHROUGH[cmd]
        _run_script(script, base_args + sys.argv[2:])
        return 0
    # persona default: perspective_card
    if cmd == "persona":
        _run_script("perspective_card.py", sys.argv[2:])
        return 0
    print("unknown command:", cmd, file=sys.stderr)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
