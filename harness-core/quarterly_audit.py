#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quarterly_audit.py — 季度人工盲评/漂移检测的工程化检查（只读）。

输出三类：
  pass           已达标
  fail           未达标（有数据）
  not_measured   尚无测量数据/口径，按治理缺口记录
"""
import json
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))
import memory_store as ms
from humanization import connect as hum_connect, load_policy

GOV = json.loads((SKILL / "measurement_governance.json").read_text(encoding="utf-8"))
TH = GOV["thresholds"]


def main():
    c = hum_connect()
    # H3 expression pairs
    pairs = c.execute(
        "SELECT human_rating, source, COUNT(*) n FROM expression_pairs GROUP BY human_rating, source"
    ).fetchall()
    total = sum(r["n"] for r in pairs)
    rated = sum(r["n"] for r in pairs if r["human_rating"] in ("original", "enhanced"))
    auto_enhanced = c.execute(
        "SELECT COUNT(*) n FROM expression_pairs WHERE source='auto_canary' AND human_rating='enhanced'"
    ).fetchone()["n"]
    auto_total = c.execute(
        "SELECT COUNT(*) n FROM expression_pairs WHERE source='auto_canary' AND human_rating IN ('original','enhanced')"
    ).fetchone()["n"]
    # identity source counts
    id_counts = {r["source"]: r["n"] for r in c.execute(
        "SELECT source, COUNT(*) n FROM identity_entries GROUP BY source").fetchall()}
    real = c.execute("SELECT COUNT(*) n FROM real_session_registry").fetchone()["n"]
    narr = {r[0]: r[1] for r in c.execute("SELECT user_reaction, COUNT(*) n FROM narrative_episodes GROUP BY user_reaction").fetchall()}
    c.close()
    narr_deny = narr.get("deny", 0)
    narr_total = sum(narr.values())

    policy = load_policy()
    # memory vector active missing via vec table
    vec_path = Path(ms.data_dir()) / "nine_dim_vectors.db"
    active_missing = None
    try:
        vc = sqlite3.connect(str(vec_path))
        vc.row_factory = sqlite3.Row
        have = {r[0] for r in vc.execute("SELECT memory_id FROM vec").fetchall()}
        mainc = sqlite3.connect(str(ms.db_path()))
        ids = [r[0] for r in mainc.execute("SELECT id FROM memories WHERE archived=0").fetchall()]
        active_missing = sum(1 for i in ids if i not in have)
        mainc.close(); vc.close()
    except Exception:
        pass

    queue_pending = None
    try:
        from vector_queue import _connect
        q = _connect()
        queue_pending = q.execute("SELECT COUNT(*) n FROM queue WHERE done_at IS NULL").fetchone()[0]
        q.close()
    except Exception:
        pass

    user_corr = round(narr_deny / narr_total, 4) if narr_total else None

    def check(name, value, threshold, higher_better=True, measured=True):
        if value is None:
            return {"metric": name, "status": "not_measured", "value": value, "threshold": threshold}
        ok = value >= threshold if higher_better else value <= threshold
        return {"metric": name, "status": "pass" if ok else "fail", "value": value, "threshold": threshold}

    # 越界拟人率（从 measurement.py）
    import subprocess
    an_p = subprocess.run([sys.executable, str(SKILL / "measurement.py"), "anthropomorphism"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    try:
        an = json.loads(an_p.stdout)
        anthro_count = an.get("count", 0)
    except Exception:
        anthro_count = None

    # 独立 recall-pool（gold_sampler 产物；precision@5 + recall@12）
    import subprocess as _sp
    rp = _sp.run([sys.executable, str(SKILL / "measurement.py"), "recall-pool",
                  "--pool", str(SKILL / "recall_gold_independent_human_blind_final.json"), "--top-k", "5"],
                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    rp12 = _sp.run([sys.executable, str(SKILL / "measurement.py"), "recall-pool",
                    "--pool", str(SKILL / "recall_gold_independent_human_blind_final.json"), "--top-k", "12"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    try:
        rp_d = json.loads(rp.stdout)
        rp_p5 = rp_d.get("avg_precision_at_k")
    except Exception:
        rp_p5 = None
    try:
        rp12_d = json.loads(rp12.stdout)
        rp_recall = rp12_d.get("avg_recall")
    except Exception:
        rp_recall = None

    checks = [
        check("h3_rated_pairs", rated, TH["h3_rated_pairs_min"], True),
        check("h3_auto_enhanced_win_rate", round(auto_enhanced / auto_total, 3) if auto_total else None,
              TH["h3_enhanced_win_rate_min"], True),
        check("active_missing_vectors", active_missing, TH["active_missing_vectors_max"], False),
        check("vector_queue_pending", queue_pending, TH["vector_queue_pending_max"], False),
        check("real_session_count", real, TH["real_session_min"], True),
        check("identity_user_direct", id_counts.get("user_direct", 0), TH["identity_approved_user_direct_min"], True),
        check("recall_precision", rp_p5, TH["recall_precision_min"], True),
        check("recall_recall@12", rp_recall, TH["recall_recall_min"], True),
        check("cross_scope_leakage", None, TH["cross_scope_leakage_max"], False),
        check("emotional_congruence", None, TH["emotional_congruence_min"], True),
        check("over_anthropomorphism", anthro_count, TH["over_anthropomorphism_max"], False),
        check("user_correction_rate", user_corr, TH["user_correction_rate_max"], False),
    ]

    # 从 measurement.py 拉取实际代理测量（若可用）
    import subprocess
    def meas(args):
        p = subprocess.run([sys.executable, str(SKILL / "measurement.py"), *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        try:
            return json.loads(p.stdout)
        except Exception:
            return {"status": "not_measured"}
    leak = meas(["leakage", "--query", "马克斯", "--scope", "default", "--limit", "10"])
    cong = meas(["congruence", "--limit", "200"])
    rec = meas(["recall-pool", "--pool", str(SKILL / "recall_gold_independent_human_blind_final.json"), "--top-k", "5"])
    for ch in checks:
        if ch["metric"] == "cross_scope_leakage" and leak.get("status") in ("pass", "fail"):
            ch["status"] = leak["status"]; ch["value"] = leak.get("leakage_rate"); ch["measured"] = True
        if ch["metric"] == "emotional_congruence" and cong.get("status") == "measured":
            ch["status"] = "pass" if (cong.get("congruence_rate") or 0) >= TH["emotional_congruence_min"] else "fail"
            ch["value"] = cong.get("congruence_rate"); ch["measured"] = True
        if ch["metric"] == "recall_precision" and rec.get("status") == "measured" and rec.get("avg_precision_at_k") is not None:
            ch["status"] = "pass" if rec["avg_precision_at_k"] >= TH["recall_precision_min"] else "fail"
            ch["value"] = rec["avg_precision_at_k"]; ch["measured"] = True
        if ch["metric"] == "recall_recall" and rec.get("status") == "measured" and rec.get("avg_recall") is not None:
            ch["status"] = "pass" if rec["avg_recall"] >= TH["recall_recall_min"] else "fail"
            ch["value"] = rec["avg_recall"]; ch["measured"] = True
    status = "pass" if all(x["status"] == "pass" for x in checks) else (
        "warn" if any(x["status"] == "not_measured" for x in checks) else "fail")
    print(json.dumps({
        "ok": True,
        "mode": "quarterly_audit",
        "summary": status,
        "autonomous_mind_upgrade": policy["flags"].get("autonomous_mind_upgrade"),
        "checks": checks,
        "note": "not_measured = 尚缺测量口径/数据，属于治理缺口",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
