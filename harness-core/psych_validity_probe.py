#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""psych_validity_probe.py — 心理效度代理研究探针。

不是心理学效度结论；只是把可量化的“人格/关系/记忆”代理指标汇总成研究素材。
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent

def _run(script, *args):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"error": p.returncode, "tail": p.stdout[-200:] + p.stderr[-200:]}

def main():
    out = {}
    out["timestamp"] = datetime.now().isoformat()
    out["emotional_congruence"] = _run("measurement.py", "congruence", "--limit", "200")
    out["flow_split"] = _run("measurement.py", "flow-split")
    out["over_anthropomorphism"] = _run("measurement.py", "anthropomorphism")
    out["self_reveal"] = _run("measurement.py", "self_reveal")
    out["recall_pool"] = _run("measurement.py", "recall-pool", "--pool", str(SKILL / "recall_gold_independent_human_final_full.json"), "--top-k", "5")
    out["mind_review"] = _run("mind_review.py", "run")
    out["quarterly"] = _run("quarterly_audit.py")
    out["policy"] = _run("humanization.py", "status")
    # write report
    report = "# 心理效度代理研究探针\n\n"
    report += "> 时间：" + out["timestamp"] + "\n"
    report += "> 说明：非心理学效度结论，仅工程代理指标。\n\n"
    for k, v in out.items():
        report += "## " + k + "\n```json\n" + json.dumps(v, ensure_ascii=False, indent=2) + "\n```\n\n"
    path = Path.home() / "Documents" / "harness" / "docs" / "心理效度代理报告-20260901.md"
    path.write_text(report, encoding="utf-8")
    print(json.dumps({"ok": True, "report": str(path), "probes": list(out.keys())}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
