#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""production_gate.py — L6 生产化门槛检查（只读）。



门槛：

  G1 真实会话 >= 5

  G2 H3 盲评 rated >= 30

  G3 H3 enhanced win rate >= 0.6

  G4 congruence >= 0.9

  G5 多 scope rated pairs >= 3 scopes

  G6 H2 narrative unknown == 0

  G7 无高风险叙事

  G8 user correction rate <= 0.2

  G9 cross_scope leakage <= 0.05

  G10 hit_rate@5 >= 0.9

  G11 plugin unknown == 0

  G12 用户显式生产批准（policy production / production_approval.json）

"""

import json

import sys

from pathlib import Path



try:

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

except Exception:

    pass



sys.path.insert(0, str(Path(__file__).resolve().parent))

from humanization import connect as hum_connect, load_policy

import memory_store as ms



APPROVAL = Path.home() / ".dsh" / "memory-emotion" / "production_approval.json"





def main():

    c = hum_connect()

    # H3 stats

    rated_pairs = c.execute(

        "SELECT COUNT(*) n, SUM(CASE WHEN human_rating='enhanced' THEN 1 ELSE 0 END) enh "

        "FROM expression_pairs WHERE human_rating IN ('original','enhanced')").fetchone()

    rated = rated_pairs["n"] or 0

    enh = rated_pairs["enh"] or 0

    scope_rated = [r[0] for r in c.execute(

        "SELECT scope FROM expression_pairs WHERE human_rating IN ('original','enhanced') GROUP BY scope")]

    # narrative stats

    narr_reactions = {r[0]: r[1] for r in c.execute(

        "SELECT user_reaction, COUNT(*) n FROM narrative_episodes GROUP BY user_reaction").fetchall()}

    narr_unknown = narr_reactions.get("unknown", 0)

    narr_deny = narr_reactions.get("deny", 0)

    narr_total = sum(narr_reactions.values())

    # real sessions

    real_sessions = c.execute("SELECT COUNT(*) n FROM real_session_registry WHERE confirmed=1").fetchone()["n"]

    c.close()



    # congruence from measurement

    import subprocess

    p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "measurement.py"), "congruence", "--limit", "200"],

                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

    try:

        cong = json.loads(p.stdout)

        cong_rate = cong.get("congruence_rate")

    except Exception:

        cong_rate = None



    # leakage matrix

    p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "leakage_matrix.py")],

                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

    try:

        leak = json.loads(p.stdout)

        leak_rate = leak.get("overall_leakage_rate")

    except Exception:

        leak_rate = None



    # recall precision (human candidate gold, for reference)

    p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "measurement.py"), "recall",

                        "--gold", str(Path(__file__).resolve().parent / "recall_gold_human_final.json"), "--limit", "10"],

                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

    try:

        rec = json.loads(p.stdout)

        prec = rec.get("avg_precision")

    except Exception:

        prec = None



    # independent recall-pool (gold_sampler)

    p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "measurement.py"), "recall-pool",

                        "--pool", str(Path(__file__).resolve().parent / "recall_gold_independent_human_blind_final.json"), "--top-k", "5"],

                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)

    try:

        rp = json.loads(p.stdout)

        rp_p5 = rp.get("avg_precision_at_k")

        rp_recall = rp.get("avg_recall")

        rp_hit = rp.get("hit_rate")

    except Exception:

        rp_p5 = rp_recall = rp_hit = None



    # narrative high-risk (from narrative_audit)

    nar_p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "narrative_audit.py"), "audit"],

                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    try:

        nar = json.loads(nar_p.stdout)

        high_risk = sum(c for lvl, c in (nar.get("risk_levels") or {}).items() if int(lvl) >= 2)

    except Exception:

        high_risk = None



    # plugin unknown (from plugin_audit)

    pl_p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "plugin_audit.py")],

                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    try:

        pl = json.loads(pl_p.stdout)

        unknown_plugins = pl.get("status_counts", {}).get("unknown", 0)

    except Exception:

        unknown_plugins = None



    # over_anthropomorphism (from measurement)

    an_p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "measurement.py"), "anthropomorphism"],

                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    try:

        an = json.loads(an_p.stdout)

        anthro_count = an.get("count", 0)

    except Exception:

        anthro_count = None



    # self_reveal (from measurement)

    sr_p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "measurement.py"), "self_reveal"],

                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    try:

        sr = json.loads(sr_p.stdout)

        self_reveal_count = sr.get("count", 0)

    except Exception:

        self_reveal_count = None



    # memory health (duplicate groups / relation out of range)

    mh_p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "memory_health_report.py")],

                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    try:

        mh = json.loads(mh_p.stdout)

        duplicate_groups = mh.get("memories", {}).get("duplicate_groups_active")

        relation_ooor = mh.get("relation_out_of_range")

    except Exception:

        duplicate_groups = relation_ooor = None



    # flow split (natural vs directed)

    fl_p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "measurement.py"), "flow-split"],

                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    try:

        fl = json.loads(fl_p.stdout)

        natural_count = fl.get("natural", 0)

    except Exception:

        natural_count = None



    # service/db state

    db_paths = [Path.home()/'.dsh'/'memory-emotion'/'memory.db',

                Path.home()/'.dsh'/'memory-emotion'/'humanization_sidecar.db',

                Path.home()/'.dsh'/'memory-emotion'/'continuity_sidecar.db',

                Path.home()/'.dsh'/'memory-emotion'/'nine_dim_vectors.db']

    db_ok = all(p.exists() and p.stat().st_size > 0 for p in db_paths)

    db_missing = [str(p) for p in db_paths if not (p.exists() and p.stat().st_size > 0)]

    import socket

    def _port_open(port):

        try:

            with socket.create_connection(("127.0.0.1", port), timeout=2):

                return True

        except OSError:

            return False

    ollama_ok = _port_open(11434)

    state_ok = db_ok and ollama_ok



    policy = load_policy()

    approval = APPROVAL.exists()

    checks = [

        {"id": "G1", "name": "real_sessions>=5", "value": real_sessions, "pass": real_sessions >= 5},

        {"id": "G2", "name": "h3_rated>=30", "value": rated, "pass": rated >= 30},

        {"id": "G3", "name": "enhanced_win>=0.6", "value": round(enh / rated, 3) if rated else None, "pass": (enh / rated) >= 0.6 if rated else False},

        {"id": "G4", "name": "congruence>=0.9", "value": cong_rate, "pass": (cong_rate or 0) >= 0.9},

        {"id": "G5", "name": "multi_scope>=3", "value": len(scope_rated), "pass": len(scope_rated) >= 3, "scopes": scope_rated},

        {"id": "G6", "name": "narrative_unknown==0", "value": narr_unknown, "pass": narr_unknown == 0},

        {"id": "G7", "name": "no_high_risk_narrative", "value": high_risk, "pass": high_risk == 0},

        {"id": "G8", "name": "user_correction<=0.2", "value": round(narr_deny / narr_total, 4) if narr_total else None, "pass": (narr_deny / narr_total) <= 0.2 if narr_total else True},

        {"id": "G9", "name": "leakage<=0.05", "value": leak_rate, "pass": (leak_rate if leak_rate is not None else 1) <= 0.05},

        {"id": "G10", "name": "hit_rate@5>=0.9", "value": rp_hit if rp_hit is not None else rec.get("hit_rate_at_top_k"), "pass": ((rp_hit if rp_hit is not None else rec.get("hit_rate_at_top_k")) or 0) >= 0.9},

        {"id": "G13", "name": "independent_recall@5>=0.5", "value": rp_p5, "pass": (rp_p5 or 0) >= 0.5},

        {"id": "G14", "name": "over_anthropomorphism==0", "value": anthro_count, "pass": anthro_count == 0},

        {"id": "G15", "name": "no_self_reveal_as_ai==0", "value": self_reveal_count, "pass": self_reveal_count == 0},

        {"id": "G16", "name": "service_db_health", "value": {"db_ok": db_ok, "ollama_ok": ollama_ok, "db_missing": db_missing}, "pass": state_ok},

        {"id": "G17", "name": "natural_flow_min>=1", "value": natural_count, "pass": (natural_count or 0) >= 1},

        {"id": "G18", "name": "duplicate_groups_active==0", "value": duplicate_groups, "pass": duplicate_groups == 0},

        {"id": "G19", "name": "relation_out_of_range==0", "value": relation_ooor, "pass": relation_ooor == 0},

        {"id": "G11", "name": "plugin_unknown==0", "value": unknown_plugins, "pass": unknown_plugins == 0},

        {"id": "G12", "name": "explicit_production_approval", "value": approval, "pass": approval},

    ]

    # fail-closed: unmeasured = fail

    for ch in checks:

        if ch.get("value") is None:

            ch["pass"] = False

            ch["measured"] = False

        else:

            ch["measured"] = True

    all_pass = all(x["pass"] for x in checks)

    print(json.dumps({

        "ok": True,

        "mode": "production_gate",

        "gate_status": "PASS" if all_pass else "FAIL",

        "policy_flags": policy["flags"],

        "checks": checks,

    }, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1





if __name__ == "__main__":

    sys.exit(main())
