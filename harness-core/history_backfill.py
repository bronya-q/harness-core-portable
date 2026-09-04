#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
history_backfill.py — 从已有历史记忆（含可选归档）回填 H1/H2/H4/H8/H9。

不写 memory.db；只在 --write 时写 humanization_sidecar。
"""
import argparse
import json
import sys
import time
import uuid
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import memory_store as ms
from humanization import connect as hum_connect


def load_memories(limit, min_importance, include_archived):
    c = ms.connect()
    where = "importance>=?" if not include_archived else "1=1"
    sql = (
        "SELECT id,scope,entity,content,kind,importance,tags,created_at "
        "FROM memories WHERE %s ORDER BY importance DESC, id DESC LIMIT ?" % where
    )
    params = [min_importance] if not include_archived else []
    params.append(limit)
    rows = c.execute(sql, params).fetchall()
    c.close()
    return [dict(r) for r in rows]


def existing_text(table, field):
    c = hum_connect()
    rows = c.execute("SELECT %s FROM %s" % (field, table)).fetchall()
    c.close()
    return {r[0] for r in rows}


def backfill_narrative(c, memories, write):
    existing = existing_text("narrative_episodes", "summary")
    added = 0
    for m in memories:
        summary = (m["content"] or "")[:200]
        if summary in existing:
            continue
        if write:
            c.execute(
                "INSERT INTO narrative_episodes(id,scope,entity,summary,emotion_json,memory_ids,created_at,user_reaction)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, m["scope"], m.get("entity") or "", summary,
                 json.dumps({"importance": m["importance"]}, ensure_ascii=False),
                 json.dumps([m["id"]], ensure_ascii=False), time.time(), "unknown"))
        existing.add(summary)
        added += 1
    return added


def backfill_situated(c, memories, write):
    existing = existing_text("situated_observations", "id")
    added = 0
    for m in memories:
        if m["kind"] not in ("event", "emotion", "reflection"):
            continue
        cid = "hist-" + str(m["id"])
        if cid in existing:
            continue
        if write:
            c.execute(
                "INSERT OR REPLACE INTO situated_observations(id,scope,observed_at,context_json,source)"
                " VALUES(?,?,?,?,?)",
                (cid, m["scope"], time.time(),
                 json.dumps({"time": m["created_at"], "scope": m["scope"], "kind": m["kind"],
                             "content_preview": (m["content"] or "")[:120]}, ensure_ascii=False),
                 "history_backfill"))
        existing.add(cid)
        added += 1
    return added


def backfill_relationship(c, memories, write):
    existing = existing_text("relationship_events", "summary")
    added = 0
    for m in memories:
        if m["kind"] != "relationship" and not any(k in (m.get("tags") or "") for k in ("关系", "好感", "信任")):
            continue
        summary = (m["content"] or "")[:200]
        if summary in existing:
            continue
        if write:
            c.execute(
                "INSERT INTO relationship_events(id,scope,event_type,actor,summary,memory_ids,before_json,after_json,observed_at)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, m["scope"], "historical_inferred", "system", summary,
                 json.dumps([m["id"]], ensure_ascii=False), "{}", "{}", time.time()))
        existing.add(summary)
        added += 1
    return added


def backfill_diary(c, memories, write):
    existing = existing_text("diary_entries", "content")
    added = 0
    for m in memories:
        if m["kind"] not in ("reflection", "skill") and "反思" not in (m.get("tags") or ""):
            continue
        content = "历史回填：%s" % ((m["content"] or "")[:200])
        if content in existing:
            continue
        if write:
            c.execute(
                "INSERT INTO diary_entries(id,scope,content,mood_json,created_at,visibility)"
                " VALUES(?,?,?,?,?,?)",
                (uuid.uuid4().hex, m["scope"], content,
                 json.dumps({"source": "history_backfill"}, ensure_ascii=False), time.time(), "private"))
        existing.add(content)
        added += 1
    return added


def backfill_variants(c, memories, write):
    existing = existing_text("persona_variants", "text")
    added = 0
    for m in memories:
        if "card-game" not in (m.get("tags") or ""):
            continue
        text = (m["content"] or "")[:300]
        if not text or text in existing:
            continue
        if write:
            c.execute(
                "INSERT INTO persona_variants(id,scope,context,outcome,text,created_at,source,user_reaction)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex, m["scope"], "card_game_history", "neutral", text,
                 time.time(), "history_backfill", "unknown"))
        existing.add(text)
        added += 1
    return added


def cross_session_report(memories):
    tags = Counter()
    kinds = Counter()
    scopes = Counter()
    for m in memories:
        for t in (m.get("tags") or "").split(","):
            t = t.strip()
            if t:
                tags[t] += 1
        kinds[m["kind"]] += 1
        scopes[m["scope"]] += 1
    return {
        "top_tags": tags.most_common(30),
        "kind_distribution": dict(kinds),
        "scope_distribution": dict(scopes),
        "note": "cross-session theme from historical memory; not psychology conclusion",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--min-importance", type=float, default=0.5)
    ap.add_argument("--include-archived", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    memories = load_memories(args.limit, args.min_importance, args.include_archived)
    report = cross_session_report(memories)
    c = hum_connect()
    n = backfill_narrative(c, memories, args.write)
    s = backfill_situated(c, memories, args.write)
    r = backfill_relationship(c, memories, args.write)
    d = backfill_diary(c, memories, args.write)
    v = backfill_variants(c, memories, args.write)
    if args.write:
        c.commit()
    c.close()
    print(json.dumps({"ok": True, "memories_scanned": len(memories),
                      "narrative_added": n, "situated_added": s,
                      "relationship_added": r, "diary_added": d, "variant_added": v,
                      "write": args.write, "cross_session_report": report},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
