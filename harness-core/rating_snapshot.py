#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rating_snapshot.py — 把评级绑定到可复现快照/命令记录。

生成：
  ~/.dsh/memory-emotion/rating-snapshots/rating-<timestamp>.json
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
SNAP_DIR = Path.home() / ".dsh" / "memory-emotion" / "rating-snapshots"

KEY_FILES = [
    "production_gate.py", "measurement.py", "gold_sampler.py", "natural_session.py",
    "plugin_audit.py", "plugin_sandbox.py", "perspective_card.py", "humanization.py",
]


def _hash(path):
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _run_json(script, *args):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"returncode": p.returncode, "stdout_tail": p.stdout[-200:], "stderr_tail": p.stderr[-200:]}


def main():
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.time()
    gold_prov = SKILL / "recall_gold_independent_human_blind_final.provenance.json"
    gold_integrity = None
    if gold_prov.exists():
        try:
            gold_integrity = json.loads(gold_prov.read_text(encoding="utf-8")).get("integrity_hash")
        except Exception:
            pass
    snap = {
        "generated_at": ts,
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "gold_integrity_hash": gold_integrity,
        "db_hashes": {p.name: _hash(p) for p in [
            Path.home()/".dsh"/"memory-emotion"/"memory.db",
            Path.home()/".dsh"/"memory-emotion"/"humanization_sidecar.db",
            Path.home()/".dsh"/"memory-emotion"/"continuity_sidecar.db",
            Path.home()/".dsh"/"memory-emotion"/"nine_dim_vectors.db",
        ]},
        "file_hashes": {f: _hash(SKILL / f) for f in KEY_FILES},
        "commands": {
            "production_gate": _run_json("production_gate.py"),
            "humanization_status": _run_json("humanization.py", "status"),
            "measurement_recall_pool": _run_json("measurement.py", "recall-pool",
                                                 "--pool", str(SKILL / "recall_gold_independent_human_blind_final.json"), "--top-k", "5"),
            "plugin_audit": _run_json("plugin_audit.py"),
            "perspective_card_validate": _run_json("perspective_card.py", "validate", "--name", "w-doctor-template"),
        },
        "rating_baseline": "v14: maturity~7.0 effectiveness~6.3",
        "note": "score bound to this snapshot; rerun after any change",
    }
    out = SNAP_DIR / ("rating-%s.json" % time.strftime("%Y%m%d-%H%M%S"))
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "snapshot": str(out), "rating_baseline": snap["rating_baseline"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
