#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harness_selfcheck.py — 一键全链路自检（只读）。

运行 production_gate / quarterly_audit / measurement / plugin_audit / perspective_card，
并汇总输出。
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


def _run(script, *args, timeout=200):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    try:
        return json.loads(p.stdout), p.returncode
    except Exception:
        return {"ok": False, "raw": p.stdout[-300:], "stderr": p.stderr[-300:]}, p.returncode


def main():
    out = {}
    for name, script, args in [
        ("production_gate", "production_gate.py", []),
        ("quarterly_audit", "quarterly_audit.py", []),
        ("recall_pool", "measurement.py", ["recall-pool", "--pool", str(SKILL / "recall_gold_independent_v2.json"), "--top-k", "5"]),
        ("congruence", "measurement.py", ["congruence", "--limit", "200"]),
        ("anthropomorphism", "measurement.py", ["anthropomorphism"]),
        ("plugin_audit", "plugin_audit.py", []),
        ("humanization_status", "humanization.py", ["status"]),
        ("perspective_card", "perspective_card.py", ["validate", "--name", "w-doctor-template"]),
    ]:
        out[name], out[name + "_rc"] = _run(script, *args)
    # summarize
    gate = out.get("production_gate", {})
    sum_ = out.get("quarterly_audit", {})
    ok = gate.get("gate_status") == "PASS" and sum_.get("summary") == "pass"
    print(json.dumps({
        "ok": ok,
        "mode": "harness_selfcheck",
        "production_gate_status": gate.get("gate_status"),
        "quarterly_summary": sum_.get("summary"),
        "checks": {k: ("ok" if (not isinstance(v, dict) or v.get("ok") is not False) else "fail") for k, v in out.items() if not k.endswith("_rc")},
        "raw": out,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
