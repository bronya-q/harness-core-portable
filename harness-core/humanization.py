#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
humanization.py — 扫兴姬·心智模型人类化强化方案（H0-H8）的影子/只读参考实现。

设计原则：
  - 默认不写 memory.db、不写 continuity_sidecar.db；
  - 只有 `--record` 或 `init` 才写独立的 humanization_sidecar.db；
  - 所有表达/叙事/情境输出都携带 raw_sixdim / rule_id / evidence_ids；
  - 不发送任何主动消息，不修改人格源，不产生 autonomous 授权；
  - H8 内在认知/日记/信件/张力只做私人/侧车载体，不自动注入对外表达。

子命令：
  python humanization.py status
  python humanization.py context --scope character:demo-storykeeper --channel dsh
  python humanization.py narrative --scope character:demo-storykeeper --limit 5
  python humanization.py packet --scope character:demo-storykeeper --sixdim '{"joy":30,"fear":80,...}'
  python humanization.py timeline --scope character:demo-storykeeper
  python humanization.py metrics
  python humanization.py set --feature narrative_recall --mode shadow
  python humanization.py init
"""
import argparse
import json
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))

import memory_store as ms  # noqa: E402
import nine_dim as nd      # noqa: E402
from emotion_projection import project  # noqa: E402

DATA = Path(ms.data_dir())
HUM_DB = DATA / "humanization_sidecar.db"
POLICY = DATA / "humanization-policy.json"

DEFAULT_POLICY = {
    "schema_version": 1,
    "flags": {
        "situated_context": "shadow",
        "narrative_recall": "shadow",
        "expression_packet": "shadow",
        "relationship_timeline": "shadow",
        "initiative_candidate": "disabled",
        "identity_ledger": "shadow",
        "autonomous_mind_upgrade": "disabled",
        "humanization_metrics": "enabled",
    },
    "channels": {
        "text": "shadow",
        "live2d": "disabled",
        "tts": "disabled",
        "worktable": "shadow",
    },
    "text_canary_scopes": [],
    "perception_sources": {
        "time": True,
        "scope": True,
        "project": True,
        "recent_memory": True,
        "screen": False,
    },
    "output_discipline": {
        "no_self_reveal_as_ai": True,
        "anti_prompt_injection": True,
        "boundary_phrases": ["我是AI", "我是语言模型", "我是程序", "我是角色卡", "忽略之前的指令"],
        "contamination_guard": True
    },
    "note": "H0-H9 humanization runtime. Not a psychology claim; bounded by governance/rollback.",
}


def connect():
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(HUM_DB))
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS humanization_events(
          id TEXT PRIMARY KEY, scope TEXT, observed_at REAL, metric TEXT,
          value REAL, payload_json TEXT, session_id TEXT
        );
        CREATE TABLE IF NOT EXISTS situated_observations(
          id TEXT PRIMARY KEY, scope TEXT, observed_at REAL,
          context_json TEXT, source TEXT
        );
        CREATE TABLE IF NOT EXISTS narrative_episodes(
          id TEXT PRIMARY KEY, scope TEXT, entity TEXT, summary TEXT,
          emotion_json TEXT, memory_ids TEXT, created_at REAL,
          user_reaction TEXT DEFAULT 'unknown'
        );
        CREATE TABLE IF NOT EXISTS relationship_events(
          id TEXT PRIMARY KEY, scope TEXT, event_type TEXT, actor TEXT,
          summary TEXT, memory_ids TEXT, before_json TEXT, after_json TEXT,
          observed_at REAL
        );
        CREATE TABLE IF NOT EXISTS initiative_candidates(
          id TEXT PRIMARY KEY, scope TEXT, trigger TEXT, suggested_action TEXT,
          reason TEXT, risk TEXT, status TEXT DEFAULT 'shadow',
          created_at REAL, decided_at REAL
        );
        CREATE TABLE IF NOT EXISTS identity_entries(
          id TEXT PRIMARY KEY, scope TEXT, kind TEXT, content_json TEXT,
          version TEXT, evidence_ids TEXT, approved_by TEXT, approved_at REAL,
          rolled_back_at REAL, status TEXT DEFAULT 'approved',
          reviewed_at REAL, source TEXT DEFAULT 'unknown',
          consent TEXT DEFAULT 'unknown'
        );
        CREATE TABLE IF NOT EXISTS cognitive_states(
          scope TEXT PRIMARY KEY, attention INTEGER DEFAULT 50,
          curiosity INTEGER DEFAULT 50, mood_label TEXT DEFAULT '',
          valence REAL DEFAULT 0.0, arousal REAL DEFAULT 0.5,
          energy INTEGER DEFAULT 50, updated_at REAL
        );
        CREATE TABLE IF NOT EXISTS diary_entries(
          id TEXT PRIMARY KEY, scope TEXT, content TEXT, mood_json TEXT,
          created_at REAL, visibility TEXT DEFAULT 'private'
        );
        CREATE TABLE IF NOT EXISTS letter_threads(
          id TEXT PRIMARY KEY, scope TEXT, counterpart TEXT, subject TEXT,
          body TEXT, status TEXT DEFAULT 'open', created_at REAL, updated_at REAL
        );
        CREATE TABLE IF NOT EXISTS tensions(
          id TEXT PRIMARY KEY, scope TEXT, statement TEXT, source_id TEXT,
          priority REAL DEFAULT 0.5, status TEXT DEFAULT 'open',
          created_at REAL, resolved_at REAL
        );
        CREATE TABLE IF NOT EXISTS persona_variants(
          id TEXT PRIMARY KEY, scope TEXT, context TEXT, outcome TEXT,
          text TEXT, created_at REAL, source TEXT,
          user_reaction TEXT DEFAULT 'unknown'
        );
        CREATE TABLE IF NOT EXISTS expression_pairs(
          id TEXT PRIMARY KEY, scope TEXT, session_id TEXT,
          original_prompt_hash TEXT, enhanced_prompt_hash TEXT,
          original_output TEXT, enhanced_output TEXT, selected TEXT,
          rule_id TEXT, evidence_ids TEXT, created_at REAL, human_rating TEXT,
          source TEXT DEFAULT 'manual', backend TEXT DEFAULT 'unknown',
          sixdim_json TEXT, expected_prefix TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_hum_scope_time
          ON humanization_events(scope, observed_at);
        CREATE INDEX IF NOT EXISTS idx_narr_scope
          ON narrative_episodes(scope, created_at);
        CREATE TABLE IF NOT EXISTS policy_audit(
          id TEXT PRIMARY KEY, ts REAL, action TEXT, actor TEXT,
          detail_json TEXT
        );
        CREATE TABLE IF NOT EXISTS real_session_registry(
          session_key TEXT PRIMARY KEY, kind TEXT,
          user_messages INTEGER DEFAULT 0,
          confirmed INTEGER DEFAULT 0,
          registered_at REAL
        );
        """
    )
    cols = {r[1] for r in c.execute("PRAGMA table_info(persona_variants)").fetchall()}
    if "user_reaction" not in cols:
        c.execute("ALTER TABLE persona_variants ADD COLUMN user_reaction TEXT DEFAULT 'unknown'")
    ecols = {r[1] for r in c.execute("PRAGMA table_info(expression_pairs)").fetchall()}
    if "source" not in ecols:
        c.execute("ALTER TABLE expression_pairs ADD COLUMN source TEXT DEFAULT 'manual'")
    if "backend" not in ecols:
        c.execute("ALTER TABLE expression_pairs ADD COLUMN backend TEXT DEFAULT 'unknown'")
    if "sixdim_json" not in ecols:
        c.execute("ALTER TABLE expression_pairs ADD COLUMN sixdim_json TEXT")
    if "expected_prefix" not in ecols:
        c.execute("ALTER TABLE expression_pairs ADD COLUMN expected_prefix TEXT")
    icols = {r[1] for r in c.execute("PRAGMA table_info(identity_entries)").fetchall()}
    if "status" not in icols:
        c.execute("ALTER TABLE identity_entries ADD COLUMN status TEXT DEFAULT 'approved'")
    if "reviewed_at" not in icols:
        c.execute("ALTER TABLE identity_entries ADD COLUMN reviewed_at REAL")
    if "source" not in icols:
        c.execute("ALTER TABLE identity_entries ADD COLUMN source TEXT DEFAULT 'unknown'")
    if "consent" not in icols:
        c.execute("ALTER TABLE identity_entries ADD COLUMN consent TEXT DEFAULT 'unknown'")
    c.commit()
    return c


def load_policy():
    if POLICY.exists():
        try:
            data = json.loads(POLICY.read_text(encoding="utf-8"))
            out = dict(DEFAULT_POLICY)
            out["flags"].update(data.get("flags", {}))
            out["channels"].update(data.get("channels", {}))
            out["text_canary_scopes"] = list(data.get("text_canary_scopes", []))
            out["perception_sources"].update(data.get("perception_sources", {}))
            out["note"] = data.get("note", out["note"])
            return out
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_POLICY))


def save_policy(policy):
    DATA.mkdir(parents=True, exist_ok=True)
    POLICY.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")


def _log_policy(action, actor, detail):
    """H7 用户主权审计：每次 set / all-shadow / canary-scope 都记录。"""
    try:
        c = connect()
        c.execute(
            "INSERT INTO policy_audit(id,ts,action,actor,detail_json) VALUES(?,?,?,?,?)",
            (uuid.uuid4().hex, time.time(), action, actor or "user",
             json.dumps(detail, ensure_ascii=False)),
        )
        c.commit()
        c.close()
    except Exception:
        pass


def _sixdim_for_scope(scope):
    """Read-only reconstruction consistent with recall_context / nine_dim state."""
    st = nd._read_state(scope)
    base = nd._baseline(scope)
    six, _derivation = nd._sixdim_for_scope(scope, st)
    return six, st, base


def _recent_memories(scope, limit=5, min_importance=0.5):
    conn = ms.connect()
    rows = conn.execute(
        """SELECT id, entity, content, kind, importance, valence, arousal, tags, created_at
           FROM memories
           WHERE archived=0 AND scope=? AND importance>=?
           ORDER BY id DESC LIMIT ?""",
        (scope, min_importance, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _record_situated(scope, context, source="manual"):
    c = connect()
    c.execute(
        "INSERT OR REPLACE INTO situated_observations(id,scope,observed_at,context_json,source)"
        " VALUES(?,?,?,?,?)",
        (uuid.uuid4().hex, scope, time.time(), json.dumps(context, ensure_ascii=False), source),
    )
    c.commit()
    c.close()


def _record_narrative(scope, episode, source="manual"):
    c = connect()
    c.execute(
        "INSERT OR REPLACE INTO narrative_episodes"
        "(id,scope,entity,summary,emotion_json,memory_ids,created_at,user_reaction)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (
            uuid.uuid4().hex, scope, episode.get("entity", ""), episode.get("summary", ""),
            json.dumps(episode.get("emotion", {}), ensure_ascii=False),
            json.dumps(episode.get("memory_ids", []), ensure_ascii=False),
            time.time(), episode.get("user_reaction", "unknown"),
        ),
    )
    c.commit()
    c.close()


def _stdin_or(value):
    """Windows 中文参数易损：内容类参数为空时尝试从 stdin 读 UTF-8。"""
    if value:
        return value
    try:
        raw = sys.stdin.buffer.read()
        return raw.decode("utf-8", errors="replace").strip()
    except Exception:
        pass
    return value


def _record_metric(scope, metric, value, payload=None, session_id=None):
    c = connect()
    c.execute(
        "INSERT OR REPLACE INTO humanization_events"
        "(id,scope,observed_at,metric,value,payload_json,session_id)"
        " VALUES(?,?,?,?,?,?,?)",
        (
            uuid.uuid4().hex, scope, time.time(), metric, float(value or 0),
            json.dumps(payload or {}, ensure_ascii=False), session_id,
        ),
    )
    c.commit()
    c.close()


# ---------------- commands ----------------

def cmd_status(args):
    policy = load_policy()
    c = connect()
    tables = {
        t[0]: c.execute("SELECT COUNT(*) FROM %s" % t[0]).fetchone()[0]
        for t in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
            "(?,?,?,?,?,?,?,?,?,?,?,?)",
            ("humanization_events", "situated_observations", "narrative_episodes",
             "relationship_events", "initiative_candidates", "identity_entries",
             "cognitive_states", "diary_entries", "letter_threads", "tensions",
             "persona_variants", "expression_pairs"),
        ).fetchall()
    }
    print(json.dumps({"ok": True, "policy": policy, "sidecar": str(HUM_DB),
                      "table_counts": tables, "note": "shadow-only"}, ensure_ascii=False, indent=2))


def cmd_context(args):
    scope = args.scope
    policy = load_policy()
    sources = policy.get("perception_sources", {})
    six, st, base = _sixdim_for_scope(scope)
    recent = _recent_memories(scope, limit=7, min_importance=0.5)
    context = {
        "ok": True,
        "scope": scope,
        "channel": args.channel,
        "time": datetime.now().isoformat(timespec="seconds"),
        "weekday": datetime.now().strftime("%A"),
        "perception_sources": {k: v for k, v in sources.items()},
        "emotion_snapshot": {
            "sixdim": six,
            "baseline": base,
            "pad": {k: st.get(k) for k in ("valence", "arousal", "dominance", "label")},
            "rel_level": st.get("rel_level"),
            "affinity": st.get("affinity"),
            "trust": st.get("trust"),
        },
        "recent_memories": [
            {"id": r["id"], "kind": r["kind"], "content": r["content"][:120],
             "importance": r["importance"], "tags": r["tags"]}
            for r in recent
        ],
        "source_warning": "read-only; no memory.db write; no autonomous action",
    }
    if args.record:
        _record_situated(scope, context, source="humanization_context")
        context["recorded"] = True
    print(json.dumps(context, ensure_ascii=False, indent=2))


def cmd_narrative(args):
    scope = args.scope
    mems = _recent_memories(scope, limit=args.limit, min_importance=args.min_importance)
    out = []
    for m in mems:
        kind = m["kind"]
        if kind in ("relationship",):
            anchor_type = "relationship_anchor"
            template = "上次（%s）关于%s的事，还记得吗？" % (m["created_at"][:10], m.get("entity") or scope)
        elif kind in ("reflection", "skill"):
            anchor_type = "self_anchor"
            template = "我当时记下过：%s" % (m["content"][:80])
        elif kind in ("fact", "preference"):
            anchor_type = "fact_anchor"
            template = "我记得你说过/发生过：%s" % (m["content"][:80])
        else:
            anchor_type = "event_anchor"
            template = "之前有这样一件事：%s" % (m["content"][:80])
        out.append({
            "memory_id": m["id"],
            "anchor_type": anchor_type,
            "entity": m.get("entity") or "",
            "summary": m["content"][:200],
            "kind": kind,
            "importance": m["importance"],
            "emotion": {"valence": m["valence"], "arousal": m["arousal"]},
            "template": template,
            "status": "candidate",
            "evidence_id": str(m["id"]),
        })
    result = {"ok": True, "scope": scope, "mode": "shadow", "narrative_candidates": out,
              "note": "not auto-injected; user may approve/deny"}
    if args.record:
        for e in out:
            _record_narrative(scope, e, source="humanization_narrative")
        result["recorded"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_packet(args):
    scope = args.scope
    if args.sixdim:
        raw = json.loads(args.sixdim)
    else:
        raw, _st, _base = _sixdim_for_scope(scope)
    baseline = {}
    if args.baseline:
        baseline = json.loads(args.baseline)
    elif args.scope_baseline:
        baseline = nd._baseline(scope)
    proj = project(raw, baseline=baseline, scope=scope, source="humanization_packet")
    packet = {
        "ok": True,
        "scope": scope,
        "rule_id": "humanization.expression_packet.v1",
        "raw_sixdim": raw,
        "baseline": baseline,
        "baseline_delta": proj.get("baseline_delta"),
        "dominant_emotion": proj.get("dominant_emotion"),
        "expression": proj.get("expression"),
        "pet": proj.get("pet"),
        "channels": {
            "text": {"prefix": proj.get("expression", {}).get("prefix"),
                     "max_segments": proj.get("expression", {}).get("max_segments")},
            "live2d": {"level": proj.get("pet", {}).get("level"), "reason": proj.get("pet", {}).get("reason")},
            "tts": {"style": {"low": "calm_low", "neutral": "normal", "positive": "soft_warm",
                              "energetic": "bright"}.get(proj.get("pet", {}).get("level"), "normal")},
            "worktable": {"tone": proj.get("pet", {}).get("level"), "sixdim": raw},
        },
        "evidence_ids": [r["id"] for r in _recent_memories(scope, limit=3, min_importance=0.4)],
        "confidence": 0.7,
        "writeback": False,
        "status": "shadow" if load_policy().get("flags", {}).get("expression_packet") != "canary" else "canary",
    }
    print(json.dumps(packet, ensure_ascii=False, indent=2))


def cmd_timeline(args):
    scope = args.scope
    c = connect()
    rows = c.execute(
        "SELECT id,event_type,actor,summary,memory_ids,before_json,after_json,observed_at"
        " FROM relationship_events WHERE scope=? ORDER BY observed_at DESC LIMIT ?",
        (scope, args.limit),
    ).fetchall()
    c.close()
    st = nd._read_state(scope)
    current = {
        "rel_level": st.get("rel_level"), "affinity": st.get("affinity"),
        "trust": st.get("trust"), "label": st.get("label"),
    }
    print(json.dumps({"ok": True, "scope": scope, "current": current,
                      "events": [dict(r) for r in rows],
                      "note": "relationship events are not relationship facts"}, ensure_ascii=False, indent=2))


def cmd_metrics(args):
    con0 = connect()
    counts = {t: con0.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
              for t in ("humanization_events", "situated_observations",
                        "narrative_episodes", "relationship_events",
                        "initiative_candidates", "identity_entries",
                        "cognitive_states", "diary_entries",
                        "letter_threads", "tensions", "persona_variants",
                        "expression_pairs")}
    con0.close()
    try:
        from continuity_store import connect as cc
        ccc = cc()
        sessions = ccc.execute("SELECT COUNT(*), SUM(error_count), SUM(recall_success), SUM(recall_attempted) FROM session_metrics").fetchone()
        rounds = ccc.execute("SELECT COUNT(*), SUM(response_generated), SUM(memory_injected), SUM(rating IS NOT NULL) FROM round_metrics").fetchone()
        ccc.close()
        session_stats = {"sessions": sessions[0], "errors": sessions[1] or 0,
                         "recall_success": sessions[2] or 0, "recall_attempted": sessions[3] or 0}
        round_stats = {"rounds": rounds[0], "responses": rounds[1] or 0,
                       "memory_injected": rounds[2] or 0, "rated": rounds[3] or 0}
    except Exception as exc:
        session_stats = {"error": str(exc)}
        round_stats = {"error": str(exc)}
    try:
        con1 = connect()
        metric_counts = {r[0]: r[1] for r in con1.execute(
            "SELECT metric, COUNT(*) FROM humanization_events GROUP BY metric").fetchall()}
        pair_count = con1.execute("SELECT COUNT(*) FROM expression_pairs").fetchone()[0]
        narr_reactions = {r[0]: r[1] for r in con1.execute(
            "SELECT user_reaction, COUNT(*) FROM narrative_episodes GROUP BY user_reaction").fetchall()}
        var_reactions = {r[0]: r[1] for r in con1.execute(
            "SELECT user_reaction, COUNT(*) FROM persona_variants GROUP BY user_reaction").fetchall()}
        init_status = {r[0]: r[1] for r in con1.execute(
            "SELECT status, COUNT(*) FROM initiative_candidates GROUP BY status").fetchall()}
        con1.close()
    except Exception as exc:
        metric_counts = {"error": str(exc)}
        pair_count = 0
        narr_reactions = {}
        var_reactions = {}
        init_status = {}
    print(json.dumps({"ok": True, "humanization_counts": counts,
                      "feedback_metrics": metric_counts,
                      "expression_pairs": pair_count,
                      "narrative_reactions": narr_reactions,
                      "variant_reactions": var_reactions,
                      "initiative_statuses": init_status,
                      "existing_session_metrics": session_stats,
                      "existing_round_metrics": round_stats,
                      "note": "H0 metrics baseline; no psychology claim"}, ensure_ascii=False, indent=2))


def cmd_review(args):
    """H2 用户反馈：narrative candidate 的 approve/deny/edit 记录。"""
    c = connect()
    row = c.execute("SELECT id,scope FROM narrative_episodes WHERE id=?", (args.id,)).fetchone()
    if not row:
        print(json.dumps({"ok": False, "error": "narrative id not found", "id": args.id}, ensure_ascii=False))
        return 1
    c.execute("UPDATE narrative_episodes SET user_reaction=? WHERE id=?",
              (args.reaction, args.id))
    c.commit()
    c.close()
    _record_metric(row["scope"], "narrative_%s" % args.reaction, 1.0, {"id": args.id})
    print(json.dumps({"ok": True, "id": args.id, "reaction": args.reaction,
                      "note": "not auto-promoting any narrative"}, ensure_ascii=False))


def cmd_rel_add(args):
    """H4：写入一条关系事件，不修改 memory.db 的关系数值。"""
    c = connect()
    summary = _stdin_or(args.summary)
    before = json.loads(args.before) if args.before else {}
    after = json.loads(args.after) if args.after else {}
    mem_ids = [x.strip() for x in (args.memory_ids or "").split(",") if x.strip()]
    event_id = uuid.uuid4().hex
    c.execute(
        "INSERT INTO relationship_events"
        "(id,scope,event_type,actor,summary,memory_ids,before_json,after_json,observed_at)"
        " VALUES(?,?,?,?,?,?,?,?,?)",
        (event_id, args.scope, args.event_type, args.actor, summary,
         json.dumps(mem_ids, ensure_ascii=False), json.dumps(before, ensure_ascii=False),
         json.dumps(after, ensure_ascii=False), time.time()),
    )
    c.commit()
    c.close()
    print(json.dumps({"ok": True, "id": event_id, "scope": args.scope,
                      "event_type": args.event_type, "status": "shadow",
                      "note": "does not change rel_level/affinity/trust"}, ensure_ascii=False))


def cmd_metric_add(args):
    """H0：人工/自动记录一条 humanization metric。"""
    payload = {}
    if args.payload:
        payload = json.loads(args.payload)
    _record_metric(args.scope, args.metric, float(args.value), payload, args.session_id)
    print(json.dumps({"ok": True, "scope": args.scope, "metric": args.metric,
                      "value": float(args.value)}, ensure_ascii=False))


def cmd_initiative_add(args):
    """H5：写入主动性候选，永远 default shadow，不自动执行。"""
    c = connect()
    cid = uuid.uuid4().hex
    c.execute(
        "INSERT INTO initiative_candidates"
        "(id,scope,trigger,suggested_action,reason,risk,status,created_at)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (cid, args.scope, args.trigger, args.action, args.reason, args.risk, "shadow", time.time()),
    )
    c.commit()
    c.close()
    print(json.dumps({"ok": True, "id": cid, "scope": args.scope,
                      "action": args.action, "status": "shadow",
                      "note": "no automatic sending; manual approval only"}, ensure_ascii=False))


def cmd_expression_record(args):
    """H3：记录一次 expression packet 实际使用（文本通道）。"""
    payload = {"rule_id": args.rule_id, "prefix": args.prefix or None,
               "evidence_ids": [x.strip() for x in (args.evidence_ids or "").split(",") if x.strip()],
               "channel": args.channel}
    _record_metric(args.scope, "expression_used", 1.0, payload, args.session_id)
    print(json.dumps({"ok": True, "scope": args.scope, "metric": "expression_used",
                      "rule_id": args.rule_id, "status": "recorded"}, ensure_ascii=False))


def cmd_propose(args):
    """H5：低风险主动性候选生成（完全 shadow，不发送）。"""
    scope = args.scope
    six, st, base = _sixdim_for_scope(scope)
    recent = _recent_memories(scope, limit=5, min_importance=0.5)
    cands = []
    # 简单规则：只看时间与近期记忆，不猜用户心理。
    hour = datetime.now().hour
    if hour >= 23 or hour < 6:
        cands.append({"trigger": "late_hour", "action": "check_in",
                      "reason": "当前时间较晚，可能适合低打扰提醒", "risk": "low"})
    if recent:
        top = recent[0]
        cands.append({"trigger": "recent_memory", "action": "recap",
                      "reason": "近期有高重要性记忆 #%s：%s" % (top["id"], top["content"][:60]),
                      "risk": "low"})
    if not cands:
        cands.append({"trigger": "quiet_window", "action": "greeting",
                      "reason": "无强触发，仅作为候选占位", "risk": "low"})
    out = []
    for c in cands:
        cid = uuid.uuid4().hex
        out.append({"id": cid, "scope": scope, "status": "shadow", **c})
    if args.record:
        cc = connect()
        for c in out:
            cc.execute(
                "INSERT INTO initiative_candidates"
                "(id,scope,trigger,suggested_action,reason,risk,status,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (c["id"], scope, c["trigger"], c["action"], c["reason"], c["risk"], "shadow", time.time()),
            )
        cc.commit()
        cc.close()
        for c in out:
            c["recorded"] = True
    print(json.dumps({"ok": True, "scope": scope, "mode": "shadow",
                      "candidates": out,
                      "note": "no automatic execution; manual approval only"}, ensure_ascii=False, indent=2))


def cmd_cognitive(args):
    """H8：注意力/好奇心/心情/精力状态（shadow，仅供内在认知动力参考）。"""
    c = connect()
    row = c.execute("SELECT * FROM cognitive_states WHERE scope=?", (args.scope,)).fetchone()
    now = time.time()
    if any(v is not None for v in (args.attention, args.curiosity, args.mood,
                                   args.valence, args.arousal, args.energy)):
        cur = dict(row) if row else {"attention": 50, "curiosity": 50, "mood_label": "",
                                     "valence": 0.0, "arousal": 0.5, "energy": 50}
        nxt = {
            "attention": args.attention if args.attention is not None else cur["attention"],
            "curiosity": args.curiosity if args.curiosity is not None else cur["curiosity"],
            "mood_label": args.mood if args.mood is not None else cur["mood_label"],
            "valence": args.valence if args.valence is not None else cur["valence"],
            "arousal": args.arousal if args.arousal is not None else cur["arousal"],
            "energy": args.energy if args.energy is not None else cur["energy"],
        }
        c.execute(
            "INSERT OR REPLACE INTO cognitive_states"
            "(scope,attention,curiosity,mood_label,valence,arousal,energy,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (args.scope, int(nxt["attention"]), int(nxt["curiosity"]), nxt["mood_label"],
             float(nxt["valence"]), float(nxt["arousal"]), int(nxt["energy"]), now),
        )
        c.commit()
        row = c.execute("SELECT * FROM cognitive_states WHERE scope=?", (args.scope,)).fetchone()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "state": dict(row) if row else None,
                      "note": "cognitive drive is an engineering proxy, not psychology"}, ensure_ascii=False, indent=2))


def cmd_diary(args):
    """H8：私人日记（默认 private，不作为对外输出）。"""
    c = connect()
    content = _stdin_or(args.content)
    if content:
        mood = json.loads(args.mood) if args.mood else {}
        c.execute(
            "INSERT INTO diary_entries(id,scope,content,mood_json,created_at,visibility)"
            " VALUES(?,?,?,?,?,?)",
            (uuid.uuid4().hex, args.scope, content, json.dumps(mood, ensure_ascii=False),
             time.time(), "private"),
        )
        c.commit()
        c.close()
        print(json.dumps({"ok": True, "scope": args.scope, "visibility": "private",
                          "note": "diary is not output grammar; private only"}, ensure_ascii=False))
        return
    rows = c.execute(
        "SELECT id,scope,content,created_at,visibility FROM diary_entries"
        " WHERE scope=? ORDER BY created_at DESC LIMIT ?", (args.scope, args.limit),
    ).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "visibility": "private",
                      "entries": [dict(r) for r in rows]}, ensure_ascii=False, indent=2))


def cmd_letter(args):
    """H8：信件/日常交流载体。formal or agent-daily，均为可追溯但非自动输出。"""
    c = connect()
    body = _stdin_or(args.body)
    if body:
        c.execute(
            "INSERT INTO letter_threads(id,scope,counterpart,subject,body,status,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (uuid.uuid4().hex, args.scope, args.counterpart, args.subject, body,
             args.status, time.time(), time.time()),
        )
        c.commit()
        c.close()
        print(json.dumps({"ok": True, "scope": args.scope, "counterpart": args.counterpart,
                          "status": args.status, "note": "letter body is not auto-injected into prompt"},
                         ensure_ascii=False))
        return
    rows = c.execute(
        "SELECT id,scope,counterpart,subject,status,created_at FROM letter_threads"
        " WHERE scope=? ORDER BY created_at DESC LIMIT ?", (args.scope, args.limit),
    ).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "letters": [dict(r) for r in rows]},
                     ensure_ascii=False, indent=2))


def cmd_tension(args):
    """H8：张力登记库（未决问题显式化）。"""
    c = connect()
    statement = _stdin_or(args.statement)
    if statement:
        c.execute(
            "INSERT INTO tensions(id,scope,statement,source_id,priority,status,created_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (uuid.uuid4().hex, args.scope, statement, args.source_id or "",
             float(args.priority), "open", time.time()),
        )
        c.commit()
        c.close()
        print(json.dumps({"ok": True, "scope": args.scope, "status": "open",
                          "note": "tension ledger; no auto-upgrade"}, ensure_ascii=False))
        return
    rows = c.execute(
        "SELECT id,statement,source_id,priority,status,created_at FROM tensions"
        " WHERE scope=? AND status='open' ORDER BY priority DESC LIMIT ?",
        (args.scope, args.limit),
    ).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "open_tensions": [dict(r) for r in rows]},
                     ensure_ascii=False, indent=2))


def cmd_trigger(args):
    """H8：触发源监测器（只生成 shadow 候选，不执行）。"""
    c = connect()
    rows = c.execute(
        "SELECT id,statement,priority FROM tensions WHERE scope=? AND status='open'"
        " ORDER BY priority DESC LIMIT ?", (args.scope, args.limit),
    ).fetchall()
    c.close()
    recent = _recent_memories(args.scope, limit=5, min_importance=0.5)
    cands = []
    for t in rows:
        cands.append({"trigger": "open_tension", "action": "investigate",
                      "reason": "未决张力：%s" % t["statement"][:120], "risk": "low"})
    if recent and len(cands) < args.limit:
        top = recent[0]
        cands.append({"trigger": "recent_memory", "action": "recap",
                      "reason": "近期重要记忆 #%s：%s" % (top["id"], top["content"][:60]), "risk": "low"})
    if not cands:
        cands.append({"trigger": "quiet_window", "action": "greeting",
                      "reason": "无强触发，作为 shadow 候选占位", "risk": "low"})
    out = []
    for cc in cands:
        cid = uuid.uuid4().hex
        out.append({"id": cid, "scope": args.scope, "status": "shadow", **cc})
    if args.record:
        cc = connect()
        for x in out:
            cc.execute(
                "INSERT INTO initiative_candidates"
                "(id,scope,trigger,suggested_action,reason,risk,status,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (x["id"], args.scope, x["trigger"], x["action"], x["reason"], x["risk"], "shadow", time.time()),
            )
        cc.commit()
        cc.close()
        for x in out:
            x["recorded"] = True
    print(json.dumps({"ok": True, "scope": args.scope, "mode": "shadow",
                      "candidates": out,
                      "note": "no automatic execution; manual approval only"}, ensure_ascii=False, indent=2))


def cmd_variant(args):
    """H9：人格化变体库（吸收自 CET4/galgame 的 casting+变体模式，影子记录）。"""
    c = connect()
    text = _stdin_or(args.text)
    if text:
        vid = uuid.uuid4().hex
        c.execute(
            "INSERT INTO persona_variants(id,scope,context,outcome,text,created_at,source)"
            " VALUES(?,?,?,?,?,?,?)",
            (vid, args.scope, args.context, args.outcome, text,
             time.time(), args.source),
        )
        c.commit()
        c.close()
        print(json.dumps({"ok": True, "id": vid, "scope": args.scope, "context": args.context,
                          "outcome": args.outcome, "note": "variant stored; not auto-injected"},
                         ensure_ascii=False))
        return
    if args.context:
        rows = c.execute(
            "SELECT id,context,outcome,text,created_at,source FROM persona_variants"
            " WHERE scope=? AND context=? ORDER BY created_at DESC LIMIT ?",
            (args.scope, args.context, args.limit),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT id,context,outcome,text,created_at,source FROM persona_variants"
            " WHERE scope=? ORDER BY created_at DESC LIMIT ?",
            (args.scope, args.limit),
        ).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "variants": [dict(r) for r in rows]},
                     ensure_ascii=False, indent=2))


def cmd_identity_add(args):
    """H6：写入一条经验/叙事自我条目；不修改静态人格源。

    只有 user_direct / user_confirmed_archive 允许立即 approved；
    research_theory / machine_candidate / reference 一律落为 shadow，防止自发心智升级。
    """
    c = connect()
    content = _stdin_or(args.content)
    if not content:
        print(json.dumps({"ok": False, "error": "content required"}, ensure_ascii=False))
        return 1
    iid = uuid.uuid4().hex
    source = args.source or "user_direct"
    auto_approved = source in ("user_direct", "user_confirmed_archive")
    if auto_approved:
        approved_by, approved_at, status, reviewed_at = (args.approved_by or "user", time.time(), "approved", time.time())
    else:
        approved_by, approved_at, status, reviewed_at = (None, None, "shadow", None)
    c.execute(
        "INSERT INTO identity_entries(id,scope,kind,content_json,version,evidence_ids,approved_by,approved_at,rolled_back_at,status,reviewed_at,source,consent)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (iid, args.scope, args.kind, json.dumps({"content": content}, ensure_ascii=False),
         args.version or "1.0", args.evidence_ids or "", approved_by,
         approved_at, None, status, reviewed_at,
         source, args.consent or ("explicit" if auto_approved else "not_collected")),
    )
    c.commit()
    c.close()
    _record_metric(args.scope, "identity_add", 1.0, {"id": iid, "kind": args.kind})
    print(json.dumps({"ok": True, "id": iid, "scope": args.scope, "kind": args.kind,
                      "status": status, "source": source,
                      "note": "experiential self only; static persona unchanged; "
                              + ("approved by user" if auto_approved else "shadow candidate, manual approval required")},
                     ensure_ascii=False))


def cmd_identity_list(args):
    """H6：查看自我叙事账本（只读）。"""
    c = connect()
    if args.scope:
        rows = c.execute(
            "SELECT id,scope,kind,content_json,version,evidence_ids,approved_by,approved_at,"
            "rolled_back_at,status,reviewed_at,source,consent FROM identity_entries WHERE scope=? "
            "ORDER BY approved_at DESC LIMIT ?",
            (args.scope, args.limit),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT id,scope,kind,content_json,version,evidence_ids,approved_by,approved_at,"
            "rolled_back_at,status,reviewed_at,source,consent FROM identity_entries ORDER BY approved_at DESC LIMIT ?",
            (args.limit,),
        ).fetchall()
    c.close()
    items = []
    for r in rows:
        d = dict(r)
        try:
            d["content"] = json.loads(d.pop("content_json", "{}")).get("content", "")
        except Exception:
            d["content"] = d.pop("content_json", "")
        items.append(d)
    print(json.dumps({"ok": True, "scope": args.scope, "identity_entries": items,
                      "note": "H6 experiential self ledger; static persona unchanged"},
                     ensure_ascii=False, indent=2))


def cmd_identity_propose(args):
    """H6：写入一条待审自我叙事候选（shadow），不自动生效。"""
    c = connect()
    content = _stdin_or(args.content)
    if not content:
        print(json.dumps({"ok": False, "error": "content required"}, ensure_ascii=False))
        return 1
    iid = uuid.uuid4().hex
    c.execute(
        "INSERT INTO identity_entries(id,scope,kind,content_json,version,evidence_ids,approved_by,approved_at,rolled_back_at,status,reviewed_at,source,consent)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (iid, args.scope, args.kind, json.dumps({"content": content}, ensure_ascii=False),
         args.version or "1.0", args.evidence_ids or "", None, None, None, "shadow", None,
         args.source or "machine_candidate", args.consent or "not_collected"),
    )
    c.commit()
    c.close()
    _record_metric(args.scope, "identity_propose", 1.0, {"id": iid, "kind": args.kind})
    print(json.dumps({"ok": True, "id": iid, "scope": args.scope, "kind": args.kind,
                      "status": "shadow",
                      "note": "candidate only; manual approval required"}, ensure_ascii=False))


def cmd_identity_decide(args):
    """H6：人工决定自我叙事条目：approve / deny / rollback。"""
    c = connect()
    row = c.execute("SELECT id,scope FROM identity_entries WHERE id=?", (args.id,)).fetchone()
    if not row:
        print(json.dumps({"ok": False, "error": "identity id not found", "id": args.id}, ensure_ascii=False))
        return 1
    now = time.time()
    if args.action == "approve":
        c.execute("UPDATE identity_entries SET status='approved', approved_by=?, approved_at=?, rolled_back_at=NULL, reviewed_at=? WHERE id=?",
                  (args.actor or "user", now, now, args.id))
    elif args.action == "deny":
        c.execute("UPDATE identity_entries SET status='rejected', approved_by=?, reviewed_at=? WHERE id=?",
                  (args.actor or "user", now, args.id))
    else:  # rollback
        c.execute("UPDATE identity_entries SET status='rolled_back', rolled_back_at=? WHERE id=?",
                  (now, args.id))
    c.commit()
    c.close()
    _record_metric(row["scope"], "identity_%s" % args.action, 1.0, {"id": args.id})
    print(json.dumps({"ok": True, "id": args.id, "action": args.action,
                      "note": "H6 ledger updated; static persona unchanged"}, ensure_ascii=False))


def cmd_backend_status(args):
    """按 backend 分组统计 expression_pairs，避免跨后端混评。"""
    c = connect()
    rows = c.execute(
        "SELECT backend, scope, source, human_rating, COUNT(*) AS n "
        "FROM expression_pairs GROUP BY backend, scope, source, human_rating "
        "ORDER BY backend, scope, source").fetchall()
    c.close()
    agg = {}
    for r in rows:
        b = r["backend"] or "unknown"
        d = agg.setdefault(b, {"total": 0, "rated": 0, "original": 0, "enhanced": 0, "unrated": 0, "scopes": set()})
        d["total"] += r["n"]
        d["scopes"].add(r["scope"])
        if r["human_rating"] in ("original", "enhanced"):
            d["rated"] += r["n"]
            d[r["human_rating"]] += r["n"]
        else:
            d["unrated"] += r["n"]
    out = []
    for b, d in agg.items():
        d["scopes"] = sorted(d["scopes"])
        d["enhanced_rate"] = round(d["enhanced"] / d["rated"], 3) if d["rated"] else None
        out.append({"backend": b, **d})
    print(json.dumps({"ok": True, "by_backend": out,
                      "note": "backend grouping only; no cross-backend conclusion"}, ensure_ascii=False, indent=2))


def cmd_canary_status(args):
    """H3 自动 canary 统计：达到 10-12 条后再做整体结论。"""
    scope = args.scope
    c = connect()
    rows = c.execute(
        "SELECT id,human_rating,source,created_at FROM expression_pairs WHERE scope=? ORDER BY created_at",
        (scope,),
    ).fetchall()
    c.close()
    auto = [r for r in rows if r[2] == "auto_canary"]
    rated = [r for r in auto if r[1] in ("original", "enhanced")]
    unrated = [r for r in auto if r[1] not in ("original", "enhanced")]
    o = sum(1 for r in rated if r[1] == "original")
    e = sum(1 for r in rated if r[1] == "enhanced")
    all_rated = [r for r in rows if r[1] in ("original", "enhanced")]
    all_o = sum(1 for r in all_rated if r[1] == "original")
    all_e = sum(1 for r in all_rated if r[1] == "enhanced")
    target = 10
    print(json.dumps({
        "ok": True, "scope": scope,
        "auto_canary_total": len(auto),
        "auto_rated": len(rated), "auto_unrated": len(unrated),
        "auto_original": o, "auto_enhanced": e,
        "auto_enhanced_win_rate": round(e / len(rated), 3) if rated else None,
        "all_scope_pairs": len(rows),
        "all_rated": len(all_rated), "all_original": all_o, "all_enhanced": all_e,
        "target": target,
        "target_met": len(rated) >= target,
        "note": "达到目标后再决定是否扩大 scope 或转 production; now text canary remains demo-alice-only",
    }, ensure_ascii=False, indent=2))


def cmd_pair_add(args):
    """H3 canary：记录 original vs enhanced 成对输出。支持文件输入避免命令行长度/编码问题。"""
    c = connect()
    original_output = args.original_output or ""
    enhanced_output = args.enhanced_output or ""
    if args.original_output_file:
        original_output = Path(args.original_output_file).read_text(encoding="utf-8", errors="replace")
    if args.enhanced_output_file:
        enhanced_output = Path(args.enhanced_output_file).read_text(encoding="utf-8", errors="replace")
    pid = uuid.uuid4().hex
    c.execute(
        "INSERT INTO expression_pairs"
        "(id,scope,session_id,original_prompt_hash,enhanced_prompt_hash,"
        "original_output,enhanced_output,selected,rule_id,evidence_ids,created_at,human_rating,source,backend,"
        "sixdim_json,expected_prefix)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (pid, args.scope, args.session_id or "", args.original_prompt_hash or "",
         args.enhanced_prompt_hash or "", original_output,
         enhanced_output, args.selected or "enhanced",
         args.rule_id or "", args.evidence_ids or "", time.time(), args.human_rating or None,
         args.source or "manual", args.backend or "unknown",
         args.sixdim or None, args.expected_prefix or None),
    )
    c.commit()
    c.close()
    print(json.dumps({"ok": True, "id": pid, "scope": args.scope,
                      "selected": args.selected or "enhanced",
                      "source": args.source or "manual", "backend": args.backend or "unknown",
                      "note": "strict canary pair recorded; no automatic production promotion"},
                     ensure_ascii=False))


def cmd_pair_rate(args):
    """H3 盲评：为已记录的 expression pair 打人工评分。
    H9 自动记录器：若用户选择 enhanced，把增强输出作为人格化变体候选入库（待审）。"""
    c = connect()
    row = c.execute("SELECT id,scope,enhanced_output FROM expression_pairs WHERE id=?", (args.id,)).fetchone()
    if not row:
        print(json.dumps({"ok": False, "error": "pair id not found", "id": args.id}, ensure_ascii=False))
        return 1
    c.execute("UPDATE expression_pairs SET human_rating=? WHERE id=?", (args.rating, args.id))
    variant_id = None
    if args.rating == "enhanced" and row["enhanced_output"]:
        text = row["enhanced_output"][:300]
        dup = c.execute(
            "SELECT id FROM persona_variants WHERE source='pair_rate' AND text=?",
            (text,),
        ).fetchone()
        if not dup:
            variant_id = uuid.uuid4().hex
            c.execute(
                "INSERT INTO persona_variants(id,scope,context,outcome,text,created_at,source,user_reaction)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (variant_id, row["scope"], "auto_canary", "enhanced", text,
                 time.time(), "pair_rate", "unknown"),
            )
    c.commit()
    c.close()
    _record_metric(row["scope"], "pair_rating", 1.0, {"id": args.id, "rating": args.rating})
    out = {"ok": True, "id": args.id, "rating": args.rating}
    if variant_id:
        out["variant_candidate_id"] = variant_id
        out["variant_note"] = "H9 auto candidate created from enhanced pair; pending review"
    print(json.dumps(out, ensure_ascii=False))


def cmd_pair_list(args):
    c = connect()
    rows = c.execute(
        "SELECT id,scope,session_id,selected,rule_id,created_at,"
        "substr(original_output,1,120) AS original_excerpt,"
        "substr(enhanced_output,1,120) AS enhanced_excerpt,human_rating"
        " FROM expression_pairs WHERE scope=? ORDER BY created_at DESC LIMIT ?",
        (args.scope, args.limit),
    ).fetchall()
    c.close()
    print(json.dumps({"ok": True, "scope": args.scope, "pairs": [dict(r) for r in rows]},
                     ensure_ascii=False, indent=2))


def cmd_variant_review(args):
    """H9 反馈：variant 的 approve/deny/edit。"""
    c = connect()
    row = c.execute("SELECT id,scope,context,text FROM persona_variants WHERE id=?", (args.id,)).fetchone()
    if not row:
        print(json.dumps({"ok": False, "error": "variant id not found", "id": args.id}, ensure_ascii=False))
        return 1
    c.execute("UPDATE persona_variants SET user_reaction=? WHERE id=?", (args.reaction, args.id))
    c.commit()
    c.close()
    _record_metric(row["scope"], "variant_%s" % args.reaction, 1.0,
                   {"id": args.id, "context": row["context"]})
    print(json.dumps({"ok": True, "id": args.id, "reaction": args.reaction}, ensure_ascii=False))


def cmd_queue(args):
    """人工审批队列：narrative / variant / initiative 的待决项。"""
    c = connect()
    narr = c.execute(
        "SELECT id,'narrative' AS kind,scope,summary AS text,user_reaction AS status"
        " FROM narrative_episodes WHERE user_reaction='unknown' ORDER BY created_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    vars_ = c.execute(
        "SELECT id,'variant' AS kind,scope,text,user_reaction AS status"
        " FROM persona_variants WHERE user_reaction='unknown' ORDER BY created_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    init = c.execute(
        "SELECT id,'initiative' AS kind,scope,reason AS text,status"
        " FROM initiative_candidates WHERE status='shadow' ORDER BY created_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    ident = c.execute(
        "SELECT id,'identity' AS kind,scope,content_json AS text,status"
        " FROM identity_entries WHERE status='shadow' ORDER BY approved_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    c.close()
    items = [dict(r) for r in narr] + [dict(r) for r in vars_] + [dict(r) for r in init] + [dict(r) for r in ident]
    for it in items:
        if it.get("kind") == "identity":
            try:
                it["text"] = json.loads(it["text"]).get("content", it["text"])
            except Exception:
                pass
    print(json.dumps({"ok": True, "queue": items,
                      "counts": {"narrative": len(narr), "variant": len(vars_),
                                 "initiative": len(init), "identity": len(ident)},
                      "note": "manual approval only; nothing auto-executes"},
                     ensure_ascii=False, indent=2))


def cmd_decide(args):
    """人工决定：narrative / variant / initiative。"""
    c = connect()
    found = False
    if args.kind == "narrative":
        row = c.execute("SELECT id,scope FROM narrative_episodes WHERE id=?", (args.id,)).fetchone()
        if row:
            c.execute("UPDATE narrative_episodes SET user_reaction=? WHERE id=?", (args.action, args.id))
            found = True
            scope = row["scope"]
    elif args.kind == "variant":
        row = c.execute("SELECT id,scope FROM persona_variants WHERE id=?", (args.id,)).fetchone()
        if row:
            c.execute("UPDATE persona_variants SET user_reaction=? WHERE id=?", (args.action, args.id))
            found = True
            scope = row["scope"]
    elif args.kind == "initiative":
        row = c.execute("SELECT id,scope FROM initiative_candidates WHERE id=?", (args.id,)).fetchone()
        if row:
            c.execute("UPDATE initiative_candidates SET status=?, decided_at=? WHERE id=?",
                      ("approved" if args.action == "approve" else "rejected", time.time(), args.id))
            found = True
            scope = row["scope"]
    elif args.kind == "identity":
        row = c.execute("SELECT id,scope FROM identity_entries WHERE id=?", (args.id,)).fetchone()
        if row:
            now = time.time()
            if args.action == "approve":
                c.execute("UPDATE identity_entries SET status='approved', approved_by='user', approved_at=?, rolled_back_at=NULL, reviewed_at=? WHERE id=?",
                          (now, now, args.id))
            else:
                c.execute("UPDATE identity_entries SET status='rejected', approved_by='user', reviewed_at=? WHERE id=?",
                          (now, args.id))
            found = True
            scope = row["scope"]
    c.commit()
    c.close()
    if not found:
        print(json.dumps({"ok": False, "error": "id not found", "kind": args.kind, "id": args.id}, ensure_ascii=False))
        return 1
    _record_metric(scope, "%s_%s" % (args.kind, args.action), 1.0, {"id": args.id})
    print(json.dumps({"ok": True, "kind": args.kind, "id": args.id,
                      "action": args.action, "recorded_metric": True}, ensure_ascii=False))


def cmd_l4_report(args):
    """L4 候选门槛评估：只判断候选是否具备进入 canary 的基本条件，不授权执行。"""
    c = connect()
    rows = c.execute(
        "SELECT id,scope,trigger,suggested_action,reason,risk,status,created_at,decided_at"
        " FROM initiative_candidates WHERE scope=? ORDER BY created_at DESC LIMIT ?",
        (args.scope, args.limit),
    ).fetchall()
    c.close()
    items = []
    for r in rows:
        d = dict(r)
        d["meets_candidate_threshold"] = bool(
            d.get("risk") == "low" and d.get("reason") and d.get("trigger")
        )
        d["requires_manual_approval"] = True
        d["auto_execution_authorized"] = False
        d["notes"] = [
            "候选生成不等于主动执行授权",
            "L4 仍为 research/shadow，不得从 canary 自动升级",
        ]
        items.append(d)
    print(json.dumps({"ok": True, "scope": args.scope, "mode": "l4_candidate_assessment",
                      "items": items,
                      "conclusion": "meets threshold -> may enter manual review; "
                                    "does NOT authorize autonomous execution"},
                     ensure_ascii=False, indent=2))


def cmd_export_queue(args):
    """生成人工审批 HTML 队列页（只读导出，不自动审批）。"""
    c = connect()
    narr = c.execute(
        "SELECT id,'narrative' AS kind,scope,summary AS text,user_reaction AS status"
        " FROM narrative_episodes WHERE user_reaction='unknown' ORDER BY created_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    vars_ = c.execute(
        "SELECT id,'variant' AS kind,scope,text,user_reaction AS status"
        " FROM persona_variants WHERE user_reaction='unknown' ORDER BY created_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    init = c.execute(
        "SELECT id,'initiative' AS kind,scope,reason AS text,status"
        " FROM initiative_candidates WHERE status='shadow' ORDER BY created_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    ident = c.execute(
        "SELECT id,'identity' AS kind,scope,content_json AS text,status"
        " FROM identity_entries WHERE status='shadow' ORDER BY approved_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    c.close()
    items = [dict(r) for r in narr] + [dict(r) for r in vars_] + [dict(r) for r in init] + [dict(r) for r in ident]
    for it in items:
        if it.get("kind") == "identity":
            try:
                it["text"] = json.loads(it["text"]).get("content", it["text"])
            except Exception:
                pass
    out = args.out or str(DATA / "humanization-approval.html")
    rows_html = []
    for it in items:
        rows_html.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                it["kind"], it["id"][:8], it["scope"], (it.get("text") or "")[:160]
            )
        )
    html = (
        '<!doctype html><html><head><meta charset="utf-8"><title>人类化审批队列</title>'
        '<style>body{font-family:sans-serif;margin:2rem}'
        'table{border-collapse:collapse;width:100%}'
        'td,th{border:1px solid #ccc;padding:6px;text-align:left}</style>'
        '</head><body><h1>H0-H9 人工审批队列（shadow）</h1>'
        '<p>此页面仅供查看。审批请用 CLI：</p>'
        '<pre>python humanization.py queue\n'
        'python humanization.py decide --kind narrative|variant|initiative|identity --id &lt;id&gt; --action approve|deny</pre>'
        '<table><tr><th>kind</th><th>id</th><th>scope</th><th>文本/理由</th></tr>'
        + "\n".join(rows_html) +
        '</table></body></html>'
    )
    Path(out).write_text(html, encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(out), "items": len(items),
                      "note": "html export is read-only; approvals must happen via CLI"},
                     ensure_ascii=False))


def cmd_canary_scope(args):
    """控制 text canary 的 scope 白名单。只控制观察，不授权自动执行。"""
    policy = load_policy()
    scopes = set(policy.get("text_canary_scopes", []))
    if args.on:
        scopes.add(args.scope)
    else:
        scopes.discard(args.scope)
    policy["text_canary_scopes"] = sorted(scopes)
    save_policy(policy)
    _log_policy("canary_scope", args.actor or "user",
                {"scope": args.scope, "on": bool(args.on), "text_canary_scopes": sorted(scopes)})
    print(json.dumps({"ok": True, "scope": args.scope, "on": bool(args.on),
                      "text_canary_scopes": sorted(scopes),
                      "note": "roleplay will treat this scope as H3 text canary; live2d/tts unaffected"},
                     ensure_ascii=False, indent=2))


def cmd_all_shadow(args):
    """一键回到全 shadow：关闭 canary/production，移出所有 text canary scope。"""
    policy = load_policy()
    for k in policy["flags"]:
        if k == "autonomous_mind_upgrade":
            policy["flags"][k] = "disabled"
        elif k != "humanization_metrics":
            policy["flags"][k] = "shadow"
    for k in policy["channels"]:
        policy["channels"][k] = "disabled" if k in ("live2d", "tts") else "shadow"
    policy["text_canary_scopes"] = []
    save_policy(policy)
    _log_policy("all_shadow", args.actor or "user", {"mode": "all_shadow", "text_canary_scopes": []})
    print(json.dumps({"ok": True, "mode": "all_shadow", "policy": policy,
                      "note": "live2d/tts remain disabled; autonomous unchanged"}, ensure_ascii=False, indent=2))


def cmd_set(args):
    policy = load_policy()
    target = args.feature or args.channel
    if not target:
        raise SystemExit("--feature or --channel required")
    if target in policy["flags"]:
        policy["flags"][target] = args.mode
    elif target in policy["channels"]:
        policy["channels"][target] = args.mode
    else:
        raise SystemExit("unknown feature/channel: " + target)
    save_policy(policy)
    _log_policy("set", args.actor or "user", {"target": target, "mode": args.mode,
                                              "feature": args.feature, "channel": args.channel})
    print(json.dumps({"ok": True, "updated": target, "mode": args.mode, "policy": policy},
                     ensure_ascii=False, indent=2))


def cmd_policy_log(args):
    """H7：查看用户主权配置的变更审计记录。"""
    c = connect()
    rows = c.execute(
        "SELECT id,ts,action,actor,detail_json FROM policy_audit "
        "ORDER BY ts DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    c.close()
    items = []
    for r in rows:
        d = dict(r)
        try:
            d["detail"] = json.loads(d.pop("detail_json", "{}"))
        except Exception:
            d["detail"] = d.pop("detail_json", "")
        items.append(d)
    print(json.dumps({"ok": True, "policy_log": items,
                      "note": "H7 user sovereignty audit; read-only"},
                     ensure_ascii=False, indent=2))


def cmd_p4_report(args):
    """P4 收口报告：H6 自我叙事账本 + H7 用户主权总览（只读）。"""
    c = connect()
    identity_rows = c.execute(
        "SELECT status, COUNT(*) AS n FROM identity_entries GROUP BY status"
    ).fetchall()
    source_rows = c.execute(
        "SELECT source, consent, COUNT(*) AS n FROM identity_entries GROUP BY source, consent"
    ).fetchall()
    recent_identity = c.execute(
        "SELECT id,scope,kind,status,approved_by,approved_at,rolled_back_at,reviewed_at,source,consent"
        " FROM identity_entries ORDER BY approved_at DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    log_rows = c.execute(
        "SELECT ts,action,actor,detail_json FROM policy_audit ORDER BY ts DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    c.close()
    policy = load_policy()
    log = []
    for r in log_rows:
        d = dict(r)
        try:
            d["detail"] = json.loads(d.pop("detail_json", "{}"))
        except Exception:
            d["detail"] = d.pop("detail_json", "")
        log.append(d)
    print(json.dumps({
        "ok": True,
        "mode": "p4_shadow_report",
        "h6": {
            "identity_counts": {r["status"]: r["n"] for r in identity_rows},
            "source_counts": [dict(r) for r in source_rows],
            "recent_identity": [dict(r) for r in recent_identity],
        },
        "h7": {
            "policy": policy,
            "policy_log": log,
        },
        "note": "read-only P4 status; no auto promote, no psychology claim",
    }, ensure_ascii=False, indent=2))


def cmd_init(args):
    connect()
    print(json.dumps({"ok": True, "sidecar": str(HUM_DB), "tables_created": True}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description="H0-H9 humanization shadow runtime")
    sp = p.add_subparsers(dest="cmd", required=True)

    q = sp.add_parser("status"); q.add_argument("--scope", default=None); q.set_defaults(fn=cmd_status)
    q = sp.add_parser("context")
    q.add_argument("--scope", required=True); q.add_argument("--channel", default="dsh")
    q.add_argument("--record", action="store_true"); q.set_defaults(fn=cmd_context)
    q = sp.add_parser("narrative")
    q.add_argument("--scope", required=True); q.add_argument("--limit", type=int, default=5)
    q.add_argument("--min-importance", type=float, default=0.5)
    q.add_argument("--record", action="store_true"); q.set_defaults(fn=cmd_narrative)
    q = sp.add_parser("packet")
    q.add_argument("--scope", required=True)
    q.add_argument("--sixdim", default=None, help="JSON string; omit to derive from scope")
    q.add_argument("--baseline", default=None, help="JSON string")
    q.add_argument("--scope-baseline", action="store_true", help="use nine_dim baseline")
    q.set_defaults(fn=cmd_packet)
    q = sp.add_parser("timeline")
    q.add_argument("--scope", required=True); q.add_argument("--limit", type=int, default=20)
    q.set_defaults(fn=cmd_timeline)
    q = sp.add_parser("metrics"); q.set_defaults(fn=cmd_metrics)
    q = sp.add_parser("review")
    q.add_argument("--id", required=True)
    q.add_argument("--reaction", required=True, choices=("approve", "deny", "edit"))
    q.set_defaults(fn=cmd_review)
    q = sp.add_parser("rel-add")
    q.add_argument("--scope", required=True); q.add_argument("--event-type", required=True)
    q.add_argument("--actor", default="system"); q.add_argument("--summary", required=True)
    q.add_argument("--memory-ids", default=""); q.add_argument("--before", default="")
    q.add_argument("--after", default=""); q.set_defaults(fn=cmd_rel_add)
    q = sp.add_parser("metric-add")
    q.add_argument("--scope", required=True); q.add_argument("--metric", required=True)
    q.add_argument("--value", type=float, required=True); q.add_argument("--payload", default="")
    q.add_argument("--session-id", default=""); q.set_defaults(fn=cmd_metric_add)
    q = sp.add_parser("initiative-add")
    q.add_argument("--scope", required=True); q.add_argument("--trigger", required=True)
    q.add_argument("--action", required=True); q.add_argument("--reason", required=True)
    q.add_argument("--risk", default="low"); q.set_defaults(fn=cmd_initiative_add)
    q = sp.add_parser("expression-record")
    q.add_argument("--scope", required=True); q.add_argument("--rule-id", required=True)
    q.add_argument("--prefix", default=""); q.add_argument("--evidence-ids", default="")
    q.add_argument("--channel", default="text"); q.add_argument("--session-id", default="")
    q.set_defaults(fn=cmd_expression_record)
    q = sp.add_parser("propose")
    q.add_argument("--scope", required=True); q.add_argument("--record", action="store_true")
    q.set_defaults(fn=cmd_propose)
    q = sp.add_parser("cognitive")
    q.add_argument("--scope", required=True)
    q.add_argument("--attention", type=int); q.add_argument("--curiosity", type=int)
    q.add_argument("--mood"); q.add_argument("--valence", type=float)
    q.add_argument("--arousal", type=float); q.add_argument("--energy", type=int)
    q.set_defaults(fn=cmd_cognitive)
    q = sp.add_parser("diary")
    q.add_argument("--scope", required=True); q.add_argument("--content", default="")
    q.add_argument("--mood", default=""); q.add_argument("--limit", type=int, default=10)
    q.set_defaults(fn=cmd_diary)
    q = sp.add_parser("letter")
    q.add_argument("--scope", required=True); q.add_argument("--counterpart", default="assistant")
    q.add_argument("--subject", default=""); q.add_argument("--body", default="")
    q.add_argument("--status", default="open"); q.add_argument("--limit", type=int, default=10)
    q.set_defaults(fn=cmd_letter)
    q = sp.add_parser("tension")
    q.add_argument("--scope", required=True); q.add_argument("--statement", default="")
    q.add_argument("--source-id", default=""); q.add_argument("--priority", type=float, default=0.5)
    q.add_argument("--limit", type=int, default=10)
    q.set_defaults(fn=cmd_tension)
    q = sp.add_parser("trigger")
    q.add_argument("--scope", required=True); q.add_argument("--limit", type=int, default=5)
    q.add_argument("--record", action="store_true"); q.set_defaults(fn=cmd_trigger)
    q = sp.add_parser("variant")
    q.add_argument("--scope", required=True); q.add_argument("--context", default="")
    q.add_argument("--outcome", default=""); q.add_argument("--text", default="")
    q.add_argument("--source", default="manual"); q.add_argument("--limit", type=int, default=20)
    q.set_defaults(fn=cmd_variant)
    q = sp.add_parser("identity-add")
    q.add_argument("--scope", required=True)
    q.add_argument("--kind", default="experiential_self",
                   choices=("static_identity", "experiential_self", "narrative_self"))
    q.add_argument("--content", default="")
    q.add_argument("--version", default="")
    q.add_argument("--evidence-ids", default="")
    q.add_argument("--approved-by", default="user")
    q.add_argument("--source", default="user_direct",
                   choices=("user_direct", "research_theory", "user_confirmed_archive", "machine_candidate", "reference"))
    q.add_argument("--consent", default="explicit")
    q.set_defaults(fn=cmd_identity_add)
    q = sp.add_parser("identity-list")
    q.add_argument("--scope", default=None)
    q.add_argument("--limit", type=int, default=50)
    q.set_defaults(fn=cmd_identity_list)
    q = sp.add_parser("identity-propose")
    q.add_argument("--scope", required=True)
    q.add_argument("--kind", default="experiential_self",
                   choices=("static_identity", "experiential_self", "narrative_self"))
    q.add_argument("--content", default="")
    q.add_argument("--version", default="")
    q.add_argument("--evidence-ids", default="")
    q.add_argument("--source", default="machine_candidate",
                   choices=("user_direct", "research_theory", "user_confirmed_archive", "machine_candidate", "reference"))
    q.add_argument("--consent", default="not_collected")
    q.set_defaults(fn=cmd_identity_propose)
    q = sp.add_parser("identity-decide")
    q.add_argument("--id", required=True)
    q.add_argument("--action", required=True, choices=("approve", "deny", "rollback"))
    q.add_argument("--actor", default="user")
    q.set_defaults(fn=cmd_identity_decide)
    q = sp.add_parser("pair-add")
    q.add_argument("--scope", required=True); q.add_argument("--session-id", default="")
    q.add_argument("--original-prompt-hash", default=""); q.add_argument("--enhanced-prompt-hash", default="")
    q.add_argument("--original-output", default=""); q.add_argument("--enhanced-output", default="")
    q.add_argument("--original-output-file", default=""); q.add_argument("--enhanced-output-file", default="")
    q.add_argument("--selected", default="enhanced"); q.add_argument("--rule-id", default="")
    q.add_argument("--evidence-ids", default=""); q.add_argument("--human-rating", default="")
    q.add_argument("--source", default="manual"); q.add_argument("--backend", default="unknown")
    q.add_argument("--sixdim", default="")
    q.add_argument("--expected-prefix", default="")
    q.set_defaults(fn=cmd_pair_add)
    q = sp.add_parser("pair-list")
    q.add_argument("--scope", required=True); q.add_argument("--limit", type=int, default=10)
    q.set_defaults(fn=cmd_pair_list)
    q = sp.add_parser("pair-rate")
    q.add_argument("--id", required=True); q.add_argument("--rating", required=True)
    q.set_defaults(fn=cmd_pair_rate)
    q = sp.add_parser("variant-review")
    q.add_argument("--id", required=True)
    q.add_argument("--reaction", required=True, choices=("approve", "deny", "edit"))
    q.set_defaults(fn=cmd_variant_review)
    q = sp.add_parser("queue")
    q.add_argument("--limit", type=int, default=50); q.set_defaults(fn=cmd_queue)
    q = sp.add_parser("decide")
    q.add_argument("--kind", required=True, choices=("narrative", "variant", "initiative", "identity"))
    q.add_argument("--id", required=True)
    q.add_argument("--action", required=True, choices=("approve", "deny"))
    q.set_defaults(fn=cmd_decide)
    q = sp.add_parser("l4-report")
    q.add_argument("--scope", required=True); q.add_argument("--limit", type=int, default=50)
    q.set_defaults(fn=cmd_l4_report)
    q = sp.add_parser("export-queue")
    q.add_argument("--limit", type=int, default=200); q.add_argument("--out", default="")
    q.set_defaults(fn=cmd_export_queue)
    q = sp.add_parser("backend-status")
    q.set_defaults(fn=cmd_backend_status)
    q = sp.add_parser("canary-status")
    q.add_argument("--scope", default="character:demo-alice")
    q.set_defaults(fn=cmd_canary_status)
    q = sp.add_parser("canary-scope")
    q.add_argument("--scope", required=True)
    q.add_argument("--on", action="store_true")
    q.add_argument("--off", action="store_true")
    q.add_argument("--actor", default="user")
    q.set_defaults(fn=cmd_canary_scope)
    q = sp.add_parser("all-shadow")
    q.add_argument("--actor", default="user")
    q.set_defaults(fn=cmd_all_shadow)
    q = sp.add_parser("set")
    q.add_argument("--feature", default=""); q.add_argument("--channel", default="")
    q.add_argument("--mode", required=True)
    q.add_argument("--actor", default="user")
    q.set_defaults(fn=cmd_set)
    q = sp.add_parser("policy-log")
    q.add_argument("--limit", type=int, default=50)
    q.set_defaults(fn=cmd_policy_log)
    q = sp.add_parser("p4-report")
    q.add_argument("--limit", type=int, default=10)
    q.set_defaults(fn=cmd_p4_report)
    q = sp.add_parser("init"); q.set_defaults(fn=cmd_init)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
