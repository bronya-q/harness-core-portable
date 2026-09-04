#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

mind_evolution.py — 内生心智自进化 P0 + P1。



P0：scan / status（全域张力）

P1：candidates / review / validate / decide / candidate-status



原则：

- 不写 memory.db / personality / manifest；

- 只在 humanization_sidecar 写 mind_tensions / self_upgrade_candidates；

- 不自动应用，不自动执行。

"""

import argparse

import json

import sys

import time

import uuid

from pathlib import Path



try:

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

except Exception:

    pass



import memory_store as ms

from humanization import DATA as HUM_DATA, connect as hum_connect, load_policy

from phenomenological_review import review as pheno_review



HUM_DB = HUM_DATA / "humanization_sidecar.db"



CERTAIN_PATTERNS = ["证明", "一定是", "必然", "本质上", "绝对", "毫无疑问", "永远都是", "总是"]



SUGGESTIONS = {

    "h3_unrated": "请人工盲评剩余 expression pair，并记录评分。",

    "h5_pending": "请人工决定 H5 主动性候选：approve / deny。",

    "memory_overconfidence": "对高确定性记忆进行 Evil/现象学审查，降级或补边界。",

    "h4_sparsity": "增加历史关系事件/持续关系记录。",

    "h8_sparsity": "增加私人日记/内在记录，或从历史反思回填。",

    "h9_sparsity": "增加人格化变体候选，或从 approved enhanced pair 回填。",

    "cross_session_tension": "将跨会话遗留用户问题纳入人工审阅候选。",

    "config_drift": "修复配置漂移，并重新生成/校验 manifest。",

}





def ensure(c):

    c.execute("""CREATE TABLE IF NOT EXISTS mind_tensions(

        id TEXT PRIMARY KEY, scope TEXT, source_type TEXT, statement TEXT,

        evidence_ids TEXT, severity REAL, status TEXT DEFAULT 'open',

        created_at REAL, resolved_at REAL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS self_upgrade_candidates(

        id TEXT PRIMARY KEY, tension_id TEXT, scope TEXT, target TEXT,

        proposal_json TEXT, evidence_ids TEXT, review_json TEXT, validation_json TEXT,

        status TEXT DEFAULT 'shadow', approved_by TEXT, approved_at REAL,

        applied_at REAL, rolled_back_at REAL, created_at REAL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS mind_change_log(

        id TEXT PRIMARY KEY, candidate_id TEXT, version TEXT,

        before_json TEXT, proposal_json TEXT, after_json TEXT,

        rollback_json TEXT, applied_at REAL, rolled_back_at REAL)""")

    cols = {r[1] for r in c.execute("PRAGMA table_info(self_upgrade_candidates)").fetchall()}

    if "created_at" not in cols:

        c.execute("ALTER TABLE self_upgrade_candidates ADD COLUMN created_at REAL")

    c.commit()





def insert_tension(c, scope, source_type, statement, evidence_ids=None, severity=0.5):

    row = c.execute(

        "SELECT id FROM mind_tensions WHERE scope=? AND source_type=? AND statement=? AND status='open'",

        (scope, source_type, statement)).fetchone()

    if row:

        return None

    tid = uuid.uuid4().hex

    c.execute(

        "INSERT INTO mind_tensions(id,scope,source_type,statement,evidence_ids,severity,status,created_at)"

        " VALUES(?,?,?,?,?,?,?,?)",

        (tid, scope, source_type, statement, json.dumps(evidence_ids or [], ensure_ascii=False),

         severity, "open", time.time()))

    c.commit()

    return tid





def humanization_counts(c):

    tables = ["situated_observations", "narrative_episodes", "relationship_events",

              "initiative_candidates", "identity_entries", "diary_entries",

              "letter_threads", "tensions", "persona_variants", "expression_pairs"]

    counts = {t: c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in tables}

    unrated = c.execute("SELECT COUNT(*) FROM expression_pairs WHERE human_rating IS NULL").fetchone()[0]

    unapproved_variants = c.execute("SELECT COUNT(*) FROM persona_variants WHERE user_reaction='unknown'").fetchone()[0]

    shadow_initiative = c.execute("SELECT COUNT(*) FROM initiative_candidates WHERE status='shadow'").fetchone()[0]

    return counts, unrated, unapproved_variants, shadow_initiative





def memory_overconfidence():

    c = ms.connect()

    rows = c.execute("SELECT id,scope,content,importance FROM memories WHERE archived=0").fetchall()

    c.close()

    hits = []

    for r in rows:

        text = r["content"] or ""

        found = [p for p in CERTAIN_PATTERNS if p in text]

        if found and (r["importance"] or 0) >= 0.6:

            hits.append({"id": r["id"], "scope": r["scope"], "patterns": found, "content": text[:120]})

    return hits





def manifest_issues():

    try:

        import subprocess

        p = subprocess.run([sys.executable, str(Path(__file__).with_name("manifest_check.py"))],

                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

        return json.loads(p.stdout).get("issues", [])

    except Exception:

        return ["manifest_check_unavailable"]





def scan(args):

    c = hum_connect()

    ensure(c)

    counts, unrated, unapproved_variants, shadow_initiative = humanization_counts(c)

    overconf = memory_overconfidence()

    issues = manifest_issues()

    created = []



    def add(scope, src, stmt, evidence=None, sev=0.5):

        tid = insert_tension(c, scope, src, stmt, evidence or [], sev)

        if tid:

            created.append({"id": tid, "scope": scope, "source_type": src, "statement": stmt, "severity": sev})



    if counts["situated_observations"] < 30:

        add("global", "h1_sparsity", "H1情境观察偏少：%d" % counts["situated_observations"], ["situated_observations"], 0.4)

    if counts["relationship_events"] < 10:

        add("global", "h4_sparsity", "H4关系事件偏少：%d" % counts["relationship_events"], ["relationship_events"], 0.4)

    if counts["diary_entries"] < 10:

        add("global", "h8_sparsity", "H8私人日记偏少：%d" % counts["diary_entries"], ["diary_entries"], 0.4)

    if counts["persona_variants"] < 20:

        add("global", "h9_sparsity", "H9人格变体偏少：%d" % counts["persona_variants"], ["persona_variants"], 0.4)

    if unrated > 0:

        add("character:demo-alice", "h3_unrated", "H3有未盲评pair：%d" % unrated, ["expression_pairs"], 0.6)

    if unapproved_variants > 0:

        add("character:demo-alice", "h9_unreviewed", "H9有未审变体：%d" % unapproved_variants, ["persona_variants"], 0.5)

    if shadow_initiative > 0:

        add("character:demo-alice", "h5_pending", "H5有待审主动性候选：%d" % shadow_initiative, ["initiative_candidates"], 0.5)

    if overconf:

        add("global", "memory_overconfidence", "高重要性记忆存在过度确定性表述：%d条" % len(overconf),

            [str(x["id"]) for x in overconf[:10]], 0.7)

    for iss in issues:

        add("global", "config_drift", iss, ["manifest_check"], 0.8)



    report = {

        "humanization_counts": counts,

        "unrated_pairs": unrated,

        "unapproved_variants": unapproved_variants,

        "shadow_initiative": shadow_initiative,

        "overconfidence_hits": len(overconf),

        "overconfidence_sample": overconf[:5],

        "manifest_issues": issues,

        "tensions_created": created,

    }

    print(json.dumps({"ok": True, "mode": "P0_scan", "report": report}, ensure_ascii=False, indent=2))

    c.close()





def status(args):

    c = hum_connect()

    ensure(c)

    rows = c.execute("SELECT id,scope,source_type,statement,severity,status,created_at FROM mind_tensions WHERE status='open' ORDER BY severity DESC LIMIT 200").fetchall()

    c.close()

    print(json.dumps({"ok": True, "open_tensions": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))





def candidates(args):

    c = hum_connect()

    ensure(c)

    open_rows = c.execute("SELECT * FROM mind_tensions WHERE status='open' ORDER BY severity DESC").fetchall()

    existing = {r[0] for r in c.execute("SELECT tension_id FROM self_upgrade_candidates WHERE status!='rejected'").fetchall()}

    created = []

    for t in open_rows:

        if t["id"] in existing:

            continue

        stmt = t["statement"]

        src = t["source_type"]

        target = "humanization" if src.startswith("h") else ("memory" if src == "memory_overconfidence" else "global")

        proposal = {

            "tension_id": t["id"],

            "scope": t["scope"],

            "source_type": src,

            "statement": stmt,

            "suggested_action": SUGGESTIONS.get(src, "人工审阅该张力后决定下一步。"),

            "evidence_ids": json.loads(t["evidence_ids"] or "[]"),

        }

        cid = uuid.uuid4().hex

        c.execute(

            "INSERT INTO self_upgrade_candidates(id,tension_id,scope,target,proposal_json,evidence_ids,review_json,validation_json,status,created_at)"

            " VALUES(?,?,?,?,?,?,?,?,?,?)",

            (cid, t["id"], t["scope"], target, json.dumps(proposal, ensure_ascii=False),

             t["evidence_ids"], None, None, "shadow", time.time()))

        created.append({"id": cid, "tension_id": t["id"], "source_type": src, "statement": stmt})

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "candidates_created": created}, ensure_ascii=False, indent=2))





def _evil_review(proposal):

    checks = {

        "single_sample_overclaim": "单次/局部证据是否被写成规律？",

        "counterexample_missing": "是否缺少反例或适用边界？",

        "inference_as_fact": "是否把推断当事实？",

        "sensitive_risk": "是否涉及敏感信息或高风险授权？",

        "action_scope": "建议动作是否超出 shadow 边界？",

    }

    return checks





def review(args):

    c = hum_connect()

    ensure(c)

    row = c.execute("SELECT * FROM self_upgrade_candidates WHERE id=?", (args.id,)).fetchone()

    if not row:

        print(json.dumps({"ok": False, "error": "candidate not found"}, ensure_ascii=False))

        return 1

    proposal = json.loads(row["proposal_json"])

    pheno = pheno_review(proposal.get("statement", ""), row["scope"], "self_upgrade")

    evil = _evil_review(proposal)

    review_json = {"evil": evil, "phenomenological": pheno, "reviewed_at": time.time()}

    c.execute("UPDATE self_upgrade_candidates SET review_json=? WHERE id=?",

              (json.dumps(review_json, ensure_ascii=False), args.id))

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "id": args.id, "review": review_json}, ensure_ascii=False, indent=2))





def validate(args):

    c = hum_connect()

    ensure(c)

    row = c.execute("SELECT * FROM self_upgrade_candidates WHERE id=?", (args.id,)).fetchone()

    if not row:

        print(json.dumps({"ok": False, "error": "candidate not found"}, ensure_ascii=False))

        return 1

    validation = {

        "cross_scope": "若换到其他 scope，结论是否仍成立？需人工判断",

        "backend": "当前主要后端为 ollama；若换 predictive/local-persona 需重新验证",

        "time": "若时间推移，该张力是否仍开放？",

    }

    c.execute("UPDATE self_upgrade_candidates SET validation_json=? WHERE id=?",

              (json.dumps(validation, ensure_ascii=False), args.id))

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "id": args.id, "validation": validation}, ensure_ascii=False, indent=2))





def decide(args):

    c = hum_connect()

    ensure(c)

    row = c.execute("SELECT id FROM self_upgrade_candidates WHERE id=?", (args.id,)).fetchone()

    if not row:

        print(json.dumps({"ok": False, "error": "candidate not found"}, ensure_ascii=False))

        return 1

    status = "approved" if args.action == "approve" else "rejected"

    c.execute("UPDATE self_upgrade_candidates SET status=?, approved_by=?, approved_at=? WHERE id=?",

              (status, args.actor or "user", time.time() if status == "approved" else None, args.id))

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "id": args.id, "status": status}, ensure_ascii=False))





def candidates_status(args):

    c = hum_connect()

    ensure(c)

    rows = c.execute("SELECT id,tension_id,scope,target,status,approved_by,approved_at FROM self_upgrade_candidates ORDER BY created_at DESC LIMIT 200").fetchall()

    c.close()

    print(json.dumps({"ok": True, "candidates": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))





def batch(args):

    """批量对 self_upgrade_candidates 跑 review + validate。"""

    c = hum_connect()

    ensure(c)

    rows = c.execute("SELECT * FROM self_upgrade_candidates ORDER BY created_at DESC").fetchall()

    reviewed = validated = 0

    for row in rows:

        changed = False

        if row["review_json"] is None:

            proposal = json.loads(row["proposal_json"])

            pheno = pheno_review(proposal.get("statement", ""), row["scope"], "self_upgrade")

            evil = _evil_review(proposal)

            rj = {"evil": evil, "phenomenological": pheno, "reviewed_at": time.time()}

            c.execute("UPDATE self_upgrade_candidates SET review_json=? WHERE id=?",

                      (json.dumps(rj, ensure_ascii=False), row["id"]))

            reviewed += 1

            changed = True

        if row["validation_json"] is None:

            validation = {

                "cross_scope": "若换到其他 scope，结论是否仍成立？需人工判断",

                "backend": "当前主要后端为 ollama；若换 predictive/local-persona 需重新验证",

                "time": "若时间推移，该张力是否仍开放？",

            }

            c.execute("UPDATE self_upgrade_candidates SET validation_json=? WHERE id=?",

                      (json.dumps(validation, ensure_ascii=False), row["id"]))

            validated += 1

            changed = True

        if changed:

            pass

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "candidates_total": len(rows),

                      "reviewed": reviewed, "validated": validated}, ensure_ascii=False, indent=2))





def top(args):

    """按严重度排序输出 Top N 待审候选。"""

    c = hum_connect()

    ensure(c)

    rows = c.execute(

        "SELECT sc.id, sc.tension_id, sc.scope, sc.target, sc.status, "

        "       COALESCE(t.severity, 0.5) AS severity, "

        "       COALESCE(sc.review_json, '') AS review_json, "

        "       sc.proposal_json "

        "FROM self_upgrade_candidates sc "

        "LEFT JOIN mind_tensions t ON sc.tension_id=t.id "

        "ORDER BY severity DESC, sc.created_at DESC LIMIT ?",

        (args.limit,)).fetchall()

    c.close()

    out = []

    for r in rows:

        proposal = json.loads(r["proposal_json"])

        review = json.loads(r["review_json"]) if r["review_json"] else {}

        pheno = review.get("phenomenological", {})

        out.append({

            "candidate_id": r["id"],

            "scope": r["scope"],

            "target": r["target"],

            "severity": r["severity"],

            "status": r["status"],

            "source_type": proposal.get("source_type"),

            "statement": proposal.get("statement"),

            "pheno_verdict": pheno.get("verdict") if pheno else None,

            "reviewed": bool(r["review_json"]),

        })

    if args.out:

        Path(args.out).write_text(json.dumps({"ok": True, "top": out}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "top": out}, ensure_ascii=False, indent=2))





def apply(args):

    """P2：把 approved 候选登记为版本化应用（不改外部系统，只记录受控变更包）。"""

    c = hum_connect()

    ensure(c)

    row = c.execute("SELECT * FROM self_upgrade_candidates WHERE id=?", (args.id,)).fetchone()

    if not row:

        print(json.dumps({"ok": False, "error": "candidate not found"}, ensure_ascii=False))

        return 1

    if row["status"] != "approved":

        print(json.dumps({"ok": False, "error": "candidate must be approved first"}, ensure_ascii=False))

        return 1

    cid = uuid.uuid4().hex

    version = "v1-" + uuid.uuid4().hex[:8]

    before = {"status": row["status"], "approved_by": row["approved_by"], "approved_at": row["approved_at"]}

    proposal = json.loads(row["proposal_json"])

    after = {"status": "applied", "applied_at": time.time(), "scope": row["scope"], "target": row["target"]}

    rollback = {"action": "revert_to_approved", "candidate_id": args.id}

    c.execute(

        "INSERT INTO mind_change_log(id,candidate_id,version,before_json,proposal_json,after_json,rollback_json,applied_at)"

        " VALUES(?,?,?,?,?,?,?,?)",

        (cid, args.id, version, json.dumps(before, ensure_ascii=False), row["proposal_json"],

         json.dumps(after, ensure_ascii=False), json.dumps(rollback, ensure_ascii=False), time.time()))

    c.execute("UPDATE self_upgrade_candidates SET status='applied', applied_at=? WHERE id=?", (time.time(), args.id))

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "change_id": cid, "candidate_id": args.id, "version": version,

                      "note": "versioned change recorded; external system not modified"}, ensure_ascii=False, indent=2))





def rollback(args):

    """P2：回滚一次 applied 变更。"""

    c = hum_connect()

    ensure(c)

    row = c.execute("SELECT * FROM mind_change_log WHERE candidate_id=? ORDER BY applied_at DESC LIMIT 1", (args.id,)).fetchone()

    if not row:

        print(json.dumps({"ok": False, "error": "no applied change for candidate"}, ensure_ascii=False))

        return 1

    c.execute("UPDATE self_upgrade_candidates SET status='approved', rolled_back_at=? WHERE id=?",

              (time.time(), args.id))

    c.execute("UPDATE mind_change_log SET rolled_back_at=? WHERE id=?", (time.time(), row["id"]))

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "change_id": row["id"], "candidate_id": args.id,

                      "status": "rolled_back_to_approved"}, ensure_ascii=False))





def changes(args):

    c = hum_connect()

    ensure(c)

    rows = c.execute("SELECT id,candidate_id,version,applied_at,rolled_back_at FROM mind_change_log ORDER BY applied_at DESC LIMIT 100").fetchall()

    c.close()

    print(json.dumps({"ok": True, "changes": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))







def self_upgrade(args):

    """受控自升级：仅允许系统自动批准 research_theory 内部心智候选。



    范围：只处理 source='research_theory' 的 H6 identity 候选（内部心智视角）。

    禁止：user_direct / user_confirmed_archive / machine_candidate / 静态人格 / 关系 / 政策。

    """

    policy = load_policy()

    mode = policy["flags"].get("autonomous_mind_upgrade", "disabled")

    if mode not in ("canary", "enabled"):

        print(json.dumps({"ok": False, "error": "autonomous_mind_upgrade not enabled",

                          "mode": mode}, ensure_ascii=False, indent=2))

        return 1

    c = hum_connect()

    rows = c.execute(

        "SELECT id, scope, content_json, evidence_ids FROM identity_entries "

        "WHERE source='research_theory' AND status='shadow' "

        "ORDER BY reviewed_at DESC, approved_at DESC LIMIT ?",

        (args.limit,)

    ).fetchall()

    c.close()

    if args.dry_run:

        print(json.dumps({"ok": True, "mode": mode, "dry_run": True,

                          "candidates": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))

        return 0

    now = time.time()

    c = hum_connect()

    approved = []

    for r in rows:

        c.execute(

            "UPDATE identity_entries SET status='approved', approved_by='system_self_upgrade', "

            "approved_at=?, reviewed_at=? WHERE id=?",

            (now, now, r["id"])

        )

        approved.append(r["id"])

    # 记录自升级动作

    c.execute(

        "INSERT INTO policy_audit(id,ts,action,actor,detail_json) VALUES(?,?,?,?,?)",

        (uuid.uuid4().hex, now, "self_upgrade_research_theory", "system",

         json.dumps({"mode": mode, "count": len(approved)}, ensure_ascii=False))

    )

    c.commit()

    c.close()

    print(json.dumps({"ok": True, "mode": mode, "approved_count": len(approved),

                      "approved_ids": approved,

                      "note": "internal research_theory only; no static persona/relationship/policy change"},

                     ensure_ascii=False, indent=2))

    return 0





def main():

    ap = argparse.ArgumentParser(description="mind_evolution P0+P1")

    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("scan").set_defaults(fn=scan)

    sub.add_parser("status").set_defaults(fn=status)

    sub.add_parser("candidates").set_defaults(fn=candidates)

    sub.add_parser("candidate-status").set_defaults(fn=candidates_status)

    q = sub.add_parser("review"); q.add_argument("--id", required=True); q.set_defaults(fn=review)

    q = sub.add_parser("validate"); q.add_argument("--id", required=True); q.set_defaults(fn=validate)

    q = sub.add_parser("decide"); q.add_argument("--id", required=True)

    q.add_argument("--action", choices=("approve", "deny"), required=True)

    q.add_argument("--actor", default="user"); q.set_defaults(fn=decide)

    q = sub.add_parser("batch"); q.set_defaults(fn=batch)

    q = sub.add_parser("top"); q.add_argument("--limit", type=int, default=50)

    q.add_argument("--out", default=""); q.set_defaults(fn=top)

    q = sub.add_parser("apply"); q.add_argument("--id", required=True); q.set_defaults(fn=apply)

    q = sub.add_parser("rollback"); q.add_argument("--id", required=True); q.set_defaults(fn=rollback)

    q = sub.add_parser("changes"); q.set_defaults(fn=changes)

    q = sub.add_parser("self-upgrade")

    q.add_argument("--limit", type=int, default=10)

    q.add_argument("--dry-run", action="store_true")

    q.set_defaults(fn=self_upgrade)

    args = ap.parse_args()

    args.fn(args)





if __name__ == "__main__":

    main()

