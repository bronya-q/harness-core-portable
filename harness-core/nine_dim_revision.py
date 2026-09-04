#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nine_dim_revision.py — 九维修订版“只读候选 sidecar”（2026-08-30）

定位：B 类新增 sidecar，不改 nine_dim.py 主引擎、不写 memory.db 主库、不自动改人格/关系。
只在自己的 sidecar 库 `~/.dsh/memory-emotion/nine_dim_revision.db` 保存观测。

实现范围（修订版中经 Evil Review 后认为可安全落地的部分）：
  1. needs   ：修订版 3.4 U→V 独立惯性（tau_U / tau_V）的候选投影
  2. conflict：修订版 4.4 冲突指数的轻量代理（记忆六维距离 + 双极性）
  3. baseline：给定 need_baseline 时输出候选需求漂移（只读）

不实现（仅参考）：完整 NT 空间、Wasserstein-2 协方差、生理器官、噪声、
行为倾向概率、24h 自校准、蛰伏唤醒。
"""
import argparse
import json
import math
import sqlite3
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms  # noqa: E402
import nine_dim as nd       # noqa: E402
from need_projection import project as g6_project  # noqa: E402

SIDE_DB = Path(ms.data_dir()) / "nine_dim_revision.db"
EMOTION_KEYS = ("joy", "anger", "sad", "fear", "surprise", "disgust")
NEED_KEYS = ("security", "possessiveness", "attachment")

# 修订版 3.4 的经验 W 矩阵（仅作为候选参数，不是心理事实）
W = [
    [0.4, -0.2, -0.5, -0.7, 0.1, -0.4],
    [-0.3, 0.6, 0.5, 0.4, 0.2, -0.1],
    [0.6, -0.3, 0.5, -0.4, 0.2, -0.5],
]
TAU_U = 1.0
TAU_V = 8.0


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _connect():
    con = sqlite3.connect(str(SIDE_DB))
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS needs_state(
        scope TEXT PRIMARY KEY, v TEXT, ts REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS observations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scope TEXT, kind TEXT, sixdim TEXT, baseline TEXT, output TEXT,
        status TEXT, ts REAL)""")
    return con


def _normalize_sixdim(sd):
    out = {}
    for k in EMOTION_KEYS:
        v = sd.get(k)
        if v is None and k == "sad":
            v = sd.get("sadness")
        out[k] = max(-100.0, min(100.0, _num(v)))
    return out


def _current_sixdim(scope, sixdim_json=None):
    if sixdim_json:
        try:
            sd = json.loads(sixdim_json)
            return _normalize_sixdim(sd), "input"
        except Exception:
            pass
    st = nd._read_state(scope)
    sd, der = nd._sixdim_for_scope(scope, st)
    return _normalize_sixdim(sd), der


def _revised_v_raw(u):
    vec = [u[k] for k in EMOTION_KEYS]
    return [sum(w * x for w, x in zip(row, vec)) for row in W]


def _inertia_v(scope, v_raw, store=True):
    """Apply the revised-model independent inertia layer in the sidecar only."""
    con = _connect()
    try:
        row = con.execute("SELECT v FROM needs_state WHERE scope=?", (scope,)).fetchone()
        prior = json.loads(row[0]) if row else None
    except Exception:
        prior = None
    if prior:
        v = [
            (1.0 - 1.0 / TAU_V) * prior[i] + (1.0 / TAU_U) * v_raw[i]
            for i in range(3)
        ]
    else:
        v = list(v_raw)
    v = [max(-100.0, min(100.0, x)) for x in v]
    if store:
        con.execute("INSERT OR REPLACE INTO needs_state(scope,v,ts) VALUES(?,?,?)",
                    (scope, json.dumps(v, ensure_ascii=False), time.time()))
        con.commit()
    con.close()
    return v


def _guard():
    return {
        "writes_performed": False,
        "personality_mutation": False,
        "relationship_mutation": False,
        "llm_inference_used": False,
        "do_not_use_for": [
            "psychology_diagnosis",
            "consequential_decisions",
            "automatic_personality_rewrite",
            "automatic_possessiveness_or_attachment_behavior",
        ],
    }


def cmd_needs(args):
    u, der = _current_sixdim(args.scope, args.sixdim)
    v_raw = _revised_v_raw(u)
    v = _inertia_v(args.scope, v_raw, store=not args.no_store)
    g6 = g6_project(u, baseline=json.loads(args.baseline) if args.baseline else None,
                    scope=args.scope, source="nine_dim_revision")
    explicit = bool(args.sixdim)
    if explicit and der == "input":
        status = "candidate_low_confidence"
        confidence = 0.35
        limitations = ["no_evidence_provenance", "input_sixdim_without_evidence_ids"]
    elif der == "stored":
        status = "candidate_observation"
        confidence = 0.5
        limitations = ["stored_sixdim_without_provenance"]
    else:
        status = "synthetic_observation"
        confidence = 0.2
        limitations = ["synthetic_sixdim", "no_evidence_provenance"]
    if not args.baseline:
        limitations.append("need_baseline_not_provided")
    out = {
        "ok": True,
        "scope": args.scope,
        "mode": "read_only_candidate_projection",
        "formula_id": "revised-u-to-v-inertia-v1",
        "raw_sixdim": {k: round(u[k], 2) for k in EMOTION_KEYS},
        "sixdim_derivation": der,
        "candidate_needs_revised": {
            NEED_KEYS[i]: round(v[i], 2) for i in range(3)
        },
        "g6_candidate_for_comparison": g6.get("candidate_needs"),
        "inertia": {"tau_U": TAU_U, "tau_V": TAU_V, "initial_prior": bool(_get_prior(args.scope))},
        "status": status,
        "confidence": confidence,
        "limitations": limitations,
        "baseline": json.loads(args.baseline) if args.baseline else None,
        "governance": _guard(),
    }
    con = _connect()
    con.execute("INSERT INTO observations(scope,kind,sixdim,baseline,output,status,ts) VALUES(?,?,?,?,?,?,?)",
                (args.scope, "needs", json.dumps(u, ensure_ascii=False), args.baseline,
                 json.dumps(out, ensure_ascii=False), status, time.time()))
    con.commit()
    con.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))


def _get_prior(scope):
    con = _connect()
    try:
        row = con.execute("SELECT v FROM needs_state WHERE scope=?", (scope,)).fetchone()
        return json.loads(row[0]) if row else None
    finally:
        con.close()


def cmd_conflict(args):
    u, der = _current_sixdim(args.scope, args.sixdim)
    con = sqlite3.connect(str(ms.db_path()))
    rows = con.execute(
        "SELECT sixdim, importance FROM memories WHERE scope=? AND archived=0 "
        "AND sixdim IS NOT NULL AND sixdim != '' ORDER BY id DESC LIMIT ?",
        (args.scope, args.mem_limit)).fetchall()
    con.close()
    vectors = []
    for r in rows:
        try:
            sd = json.loads(r[0])
            vectors.append(_normalize_sixdim(sd))
        except Exception:
            continue
    rho = None
    if len(vectors) >= 2:
        dists = []
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                d2 = sum((vectors[i][k] - vectors[j][k]) ** 2 for k in EMOTION_KEYS)
                dists.append(math.sqrt(d2) / 200.0)  # 0..~1 normalized proxy
        rho = round(sum(dists) / len(dists), 4) if dists else None
    # simple bipolarity proxy from current sixdim (candidate signal only)
    positive = max(0.0, u["joy"])
    negative = max(0.0, u["anger"], u["sad"], u["fear"], u["disgust"])
    bipolar = round(min(positive, negative) / 100.0, 4) if positive > 0 and negative > 0 else 0.0
    if rho is None:
        status = "insufficient_memory_sixdim"
        confidence = 0.0
        limitations = ["need_at_least_two_sixdim_memories"]
    elif len(vectors) < 5:
        status = "candidate_low_confidence"
        confidence = 0.3
        limitations = ["few_memory_samples", "no_provenance_fields"]
    else:
        status = "candidate_observation"
        confidence = 0.45
        limitations = ["proxy_not_wasserstein", "no_provenance_fields"]
    out = {
        "ok": True,
        "scope": args.scope,
        "mode": "read_only_conflict_proxy",
        "formula_id": "revised-conflict-proxy-v1",
        "raw_sixdim": {k: round(u[k], 2) for k in EMOTION_KEYS},
        "sixdim_derivation": der,
        "rho_proxy": rho,
        "bipolar_proxy": bipolar,
        "sample_memories": len(vectors),
        "conflict_flag_candidate": bool(rho is not None and (rho > 0.45 or bipolar > 0.3)),
        "status": status,
        "confidence": confidence,
        "limitations": limitations,
        "governance": _guard(),
    }
    con = _connect()
    con.execute("INSERT INTO observations(scope,kind,sixdim,baseline,output,status,ts) VALUES(?,?,?,?,?,?,?)",
                (args.scope, "conflict", json.dumps(u, ensure_ascii=False), None,
                 json.dumps(out, ensure_ascii=False), status, time.time()))
    con.commit()
    con.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_baseline(args):
    if not args.baseline:
        print(json.dumps({"ok": False, "scope": args.scope,
                          "error": "baseline_not_provided",
                          "note": "use --baseline '{security:60,possessiveness:40,attachment:55}'"},
                         ensure_ascii=False, indent=2))
        return 1
    base = json.loads(args.baseline)
    u, der = _current_sixdim(args.scope, args.sixdim)
    v_raw = _revised_v_raw(u)
    v = _inertia_v(args.scope, v_raw, store=not args.no_store)
    drift = {}
    for k in NEED_KEYS:
        b = _num(base.get(k, 0.0))
        drift[k] = round(v[NEED_KEYS.index(k)] - b, 2)
    out = {
        "ok": True,
        "scope": args.scope,
        "mode": "read_only_baseline_drift_candidate",
        "candidate_needs": {NEED_KEYS[i]: round(v[i], 2) for i in range(3)},
        "need_baseline": base,
        "drift_candidate": drift,
        "status": "candidate_observation",
        "confidence": 0.4,
        "limitations": ["baseline_from_argument_not_persona_file",
                        "needs_are_candidate_not_personality_fact"],
        "governance": _guard(),
    }
    con = _connect()
    con.execute("INSERT INTO observations(scope,kind,sixdim,baseline,output,status,ts) VALUES(?,?,?,?,?,?,?)",
                (args.scope, "baseline", json.dumps(u, ensure_ascii=False), args.baseline,
                 json.dumps(out, ensure_ascii=False), out["status"], time.time()))
    con.commit()
    con.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args):
    con = _connect()
    rows = con.execute("SELECT id,scope,kind,status,ts FROM observations WHERE scope=? ORDER BY id DESC LIMIT ?",
                       (args.scope, args.limit)).fetchall()
    con.close()
    print(json.dumps({"ok": True, "scope": args.scope,
                      "observations": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="九维修订版只读候选 sidecar")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("needs")
    p.add_argument("--scope", required=True)
    p.add_argument("--sixdim", default=None)
    p.add_argument("--baseline", default=None)
    p.add_argument("--no-store", action="store_true")
    p.set_defaults(fn=cmd_needs)
    p = sub.add_parser("conflict")
    p.add_argument("--scope", required=True)
    p.add_argument("--sixdim", default=None)
    p.add_argument("--mem-limit", type=int, default=50)
    p.set_defaults(fn=cmd_conflict)
    p = sub.add_parser("baseline")
    p.add_argument("--scope", required=True)
    p.add_argument("--sixdim", default=None)
    p.add_argument("--baseline", required=True)
    p.add_argument("--no-store", action="store_true")
    p.set_defaults(fn=cmd_baseline)
    p = sub.add_parser("status")
    p.add_argument("--scope", required=True)
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(fn=cmd_status)
    args = ap.parse_args()
    rc = args.fn(args)
    if rc:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
