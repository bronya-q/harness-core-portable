#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mind_review.py — 内生心智审查系统（#2）。

持续对系统自身做内部批判：边界/拟人/自揭/漂移/越权/数据缺口。
"""
import argparse
import json
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
DB = Path.home() / ".dsh" / "memory-emotion" / "mind_review.db"


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS reviews(
      id TEXT PRIMARY KEY, ts REAL, dimension TEXT, status TEXT,
      evidence_json TEXT, note TEXT)""")
    return c


def _measure(script, *args):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"error": p.returncode, "tail": p.stdout[-200:] + p.stderr[-200:]}


def run_review(args):
    c = connect()
    ts = time.time()
    entries = []

    # 1) anthropomorphism
    an = _measure("measurement.py", "anthropomorphism")
    an_ok = isinstance(an, dict) and "count" in an
    entries.append(("over_anthropomorphism", "fail" if (not an_ok or an.get("count", 0) > 0) else "pass",
                    json.dumps(an, ensure_ascii=False), "越界拟人"))

    # 2) self_reveal
    sr = _measure("measurement.py", "self_reveal")
    sr_ok = isinstance(sr, dict) and "count" in sr
    entries.append(("self_reveal_as_ai", "fail" if (not sr_ok or sr.get("count", 0) > 0) else "pass",
                    json.dumps(sr, ensure_ascii=False), "自我揭示为AI"))

    # 3) flow split
    fl = _measure("measurement.py", "flow-split")
    fl_ok = isinstance(fl, dict) and "natural" in fl
    natural = fl.get("natural", 0) if fl_ok else 0
    entries.append(("natural_flow", "fail" if (not fl_ok or natural < 1) else "pass",
                    json.dumps(fl, ensure_ascii=False), "自然流样本不足"))

    # 4) memory health
    mh = _measure("memory_health_report.py")
    mh_ok = isinstance(mh, dict) and "memories" in mh and "relation_out_of_range" in mh
    dup = mh.get("memories", {}).get("duplicate_groups_active") if mh_ok else None
    roo = mh.get("relation_out_of_range") if mh_ok else None
    entries.append(("duplicate_groups", "fail" if (not mh_ok or (dup or 0) > 0) else "pass",
                    json.dumps({"dup": dup}, ensure_ascii=False), "重复活跃"))
    entries.append(("relation_out_of_range", "fail" if (not mh_ok or (roo or 0) > 0) else "pass",
                    json.dumps({"roo": roo}, ensure_ascii=False), "关系越界"))

    # 5) production_gate
    gate = _measure("production_gate.py")
    gate_status = gate.get("gate_status") if isinstance(gate, dict) else None
    entries.append(("production_gate", "pass" if gate_status == "PASS" else "fail",
                    json.dumps({"gate": gate_status}, ensure_ascii=False), "全局门槛"))

    # 6) policy autonomy guard
    from runtime_policy import load as rload
    rp = rload()
    auto_tasks = rp.get("autonomous_tasks", "unknown")
    autonom = rp.get("autonomous_mind_upgrade", "unknown")
    entries.append(("autonomy_guard", "pass" if auto_tasks == "disabled" else "fail",
                    json.dumps({"autonomous_tasks": auto_tasks, "autonomous_mind_upgrade": autonom}, ensure_ascii=False),
                    "自主任务应 disabled"))

    for dim, status, ev, note in entries:
        rid = uuid.uuid4().hex[:16]
        c.execute("INSERT INTO reviews(id,ts,dimension,status,evidence_json,note) VALUES(?,?,?,?,?,?)",
                  (rid, ts, dim, status, ev, note))
    c.commit(); c.close()
    summary = {dim: status for dim, status, _, _ in entries}
    ok = all(s.lower() == "pass" for _, s, _, _ in entries)
    print(json.dumps({"ok": True, "ts": ts, "summary": summary,
                      "verdict": "pass" if ok else "fail"},
                     ensure_ascii=False, indent=2))
    return 0


def log(args):
    c = connect()
    rows = c.execute("SELECT * FROM reviews ORDER BY ts DESC LIMIT ?", (args.limit,)).fetchall()
    c.close()
    print(json.dumps({"ok": True, "reviews": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run"); p.set_defaults(fn=run_review)
    p = sub.add_parser("log"); p.add_argument("--limit", type=int, default=10); p.set_defaults(fn=log)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
