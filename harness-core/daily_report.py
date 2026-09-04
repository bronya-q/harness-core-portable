#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_report.py — 生成每日工程摘要（rating_snapshot + health + quarterly）。

输出：
  ~/.dsh/memory-emotion/daily-reports/daily-YYYYMMDD.md
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
OUT = Path.home() / ".dsh" / "memory-emotion" / "daily-reports"


def _run(script, *args, timeout=200):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"returncode": p.returncode, "stdout_tail": p.stdout[-200:], "stderr_tail": p.stderr[-200:]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    st = _run("rating_snapshot.py")
    health = _run("memory_health_report.py")
    qa = _run("quarterly_audit.py")
    gate = _run("production_gate.py")
    date = datetime.now().strftime("%Y-%m-%d")
    path = OUT / ("daily-%s.md" % date)
    lines = [
        "# Daily Report " + date, "",
        "## production_gate",
        "```", (json.dumps({k: gate.get(k) for k in ("gate_status", "checks")}, ensure_ascii=False, indent=2) if isinstance(gate, dict) else str(gate)[:300]), "```", "",
        "## quarterly_audit",
        "```", (json.dumps({k: qa.get(k) for k in ("summary", "checks")}, ensure_ascii=False, indent=2) if isinstance(qa, dict) else str(qa)[:300]), "```", "",
        "## health",
        "```", (json.dumps(health, ensure_ascii=False, indent=2) if isinstance(health, dict) else str(health)[:300]), "```", "",
        "## rating_snapshot",
        "```", (json.dumps({"snapshot": st.get("snapshot"), "baseline": st.get("rating_baseline")} if isinstance(st, dict) else st, ensure_ascii=False, indent=2)), "```", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"ok": True, "report": str(path), "gate": (gate.get("gate_status") if isinstance(gate, dict) else None),
                      "quarterly": (qa.get("summary") if isinstance(qa, dict) else None)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
