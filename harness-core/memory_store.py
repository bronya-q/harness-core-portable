#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
long-term-memory-emotion / memory_store.py
零依赖长时记忆 + 情感状态存储（SQLite + JSONL 导入导出）。

设计依据：
- ACT-R：声明性记忆 / 程序性记忆分离；情感作为提取与固化的约束。
- SOAR：经验固化为可复用技能/记忆。
- OCC：事件按目标/标准/偏好评估，形成情感标签。
- Generative Agents：记忆流 + 反思 + 按重要性/时效/情感检索。
- MemoryBank：遗忘/衰减 + 情感加权检索。
- MemGPT：记忆读写作为可调用工具，不塞进上下文。

数据默认位置：$MEMORY_EMOTION_DATA_DIR 或 ~/.dsh/memory-emotion/
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def data_dir():
    env = os.environ.get("MEMORY_EMOTION_DATA_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".dsh" / "memory-emotion"


def db_path():
    return data_dir() / "memory.db"


def connect():
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL DEFAULT 'default',
            entity TEXT,
            content TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'fact',
            importance REAL NOT NULL DEFAULT 0.5,
            valence REAL NOT NULL DEFAULT 0.0,
            arousal REAL NOT NULL DEFAULT 0.5,
            sixdim TEXT,
            tags TEXT NOT NULL DEFAULT '',
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_access_at TEXT,
            access_count INTEGER NOT NULL DEFAULT 0,
            archived INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS emotion_state (
            scope TEXT PRIMARY KEY,
            valence REAL NOT NULL DEFAULT 0.0,
            arousal REAL NOT NULL DEFAULT 0.5,
            dominance REAL NOT NULL DEFAULT 0.5,
            sixdim TEXT,
            label TEXT,
            context TEXT,
            rel_level INTEGER NOT NULL DEFAULT 0,
            affinity REAL NOT NULL DEFAULT 0.0,
            trust REAL NOT NULL DEFAULT 0.0,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope);
        CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind);
        CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);
        """
    )
    # 迁移：旧库 emotion_state 无 rel_level/affinity/trust 列时补列（关系-情感状态机 v2）
    cols = {r[1] for r in conn.execute("PRAGMA table_info(emotion_state)").fetchall()}
    for col, ddl in {
        "rel_level": "INTEGER NOT NULL DEFAULT 0",
        "affinity": "REAL NOT NULL DEFAULT 0.0",
        "trust": "REAL NOT NULL DEFAULT 0.0",
        "sixdim": "TEXT",
    }.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE emotion_state ADD COLUMN {col} {ddl}")
    # 迁移：memories 旧库无 sixdim 列时补列
    mcols = {r[1] for r in conn.execute("PRAGMA table_info(memories)").fetchall()}
    if "sixdim" not in mcols:
        conn.execute("ALTER TABLE memories ADD COLUMN sixdim TEXT")
    conn.commit()
    return conn


def row_to_dict(row):
    return dict(row)


def add_memory(args):
    # 根本修复（2026-08-17）：内容缺省时从 stdin 读，规避 Windows 下 subprocess argv 传中文
    # 走 ANSI/locale 编码导致 mojibake 入库的问题。显式按 utf-8 解码。
    if not args.content:
        try:
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        args.content = sys.stdin.read().strip()
    conn = connect()
    now = now_iso()
    # 去重（2026-08-17）：对机器自动审计（source=mind_audit）的 reflection 做精确内容查重，
    # 同 scope + 同 content 且未被遗忘时跳过，避免每次会话审计反复落库造成噪音/重复。
    if args.source == "mind_audit":
        hit = conn.execute(
            "SELECT id FROM memories WHERE archived=0 AND scope=? AND content=? LIMIT 1",
            (args.scope, args.content),
        ).fetchone()
        if hit:
            print(json.dumps({"ok": True, "id": hit["id"], "deduped": True,
                              "scope": args.scope}, ensure_ascii=False))
            conn.close()
            return
    # 情绪快照继承（2026-08-19 M3）：未显式传 valence/arousal/sixdim 时，
    # 从 emotion_state（同 scope）继承当前情绪，记忆自动带情绪上下文。
    v = args.valence
    a = args.arousal
    sd = getattr(args, "sixdim", None)
    if v is None or a is None or sd is None:
        st = conn.execute(
            "SELECT valence, arousal, sixdim FROM emotion_state WHERE scope = ?", (args.scope,)
        ).fetchone()
        if st:
            if v is None:
                v = st["valence"]
            if a is None:
                a = st["arousal"]
            if sd is None:
                sd = json.loads(st["sixdim"]) if st["sixdim"] else None
    if v is None:
        v = 0.0
    if a is None:
        a = 0.5
    cur = conn.execute(
        """
        INSERT INTO memories
            (scope, entity, content, kind, importance, valence, arousal,
             sixdim, tags, source, created_at, updated_at, last_access_at, access_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            args.scope,
            args.entity,
            args.content,
            args.kind,
            args.importance,
            v,
            a,
            json.dumps(sd, ensure_ascii=False) if sd else None,
            ",".join(args.tags),
            args.source,
            now,
            now,
            now,
        ),
    )
    conn.commit()
    memory_id = cur.lastrowid
    # P3/P2-2：异步向量索引为 best-effort；任何失败都不能影响主记忆写入。
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from vector_queue import enqueue
        enqueue(memory_id)
    except Exception:
        pass
    result = {"ok": True, "id": memory_id, "scope": args.scope}
    print(json.dumps(result, ensure_ascii=False))
    conn.close()
    return result


def search_memories(args):
    conn = connect()
    where = ["archived = 0"]
    params = []
    if args.scope:
        where.append("scope = ?")
        params.append(args.scope)
    if args.kind:
        where.append("kind = ?")
        params.append(args.kind)
    if args.min_importance is not None:
        where.append("importance >= ?")
        params.append(args.min_importance)
    if args.query:
        where.append("(instr(lower(content), lower(?)) > 0 OR instr(lower(tags), lower(?)) > 0)")
        params.extend([args.query, args.query])

    sql = f"""
        SELECT *, (
            importance * 0.5
            + (1.0 / (julianday('now') - julianday(updated_at) + 1.0)) * 0.3
            + ((abs(valence) + arousal) / 2.0) * 0.2
        ) AS retrieval_score
        FROM memories
        WHERE {' AND '.join(where)}
        ORDER BY retrieval_score DESC, id DESC
        LIMIT ?
    """
    params.append(args.limit)
    rows = conn.execute(sql, params).fetchall()
    # 2026-08-29 P0-1 补丁：回写读取计数，让「记忆是否被使用」可观测（见整改方案附录 C-1）
    if rows:
        ids = ",".join(str(r["id"]) for r in rows)
        conn.execute(
            f"UPDATE memories SET access_count=access_count+1, last_access_at=? WHERE id IN ({ids})",
            (now_iso(),),
        )
        conn.commit()
    out = []
    for r in rows:
        d = row_to_dict(r)
        d["retrieval_score"] = round(d.get("retrieval_score") or 0.0, 4)
        out.append(d)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    conn.close()


def recall(args):
    search_memories(
        argparse.Namespace(
            query="",
            scope=args.scope,
            kind=None,
            min_importance=args.min_importance,
            limit=args.limit,
        )
    )


def forget(args):
    conn = connect()
    now = now_iso()
    if args.id is not None:
        cur = conn.execute(
            "UPDATE memories SET archived=1, updated_at=? WHERE id=? AND archived=0",
            (now, args.id),
        )
    else:
        where = ["archived=0", "julianday('now') - julianday(updated_at) > ?"]
        params = [args.older_than_days]
        if args.scope:
            where.append("scope = ?")
            params.append(args.scope)
        if args.max_importance is not None:
            where.append("importance <= ?")
            params.append(args.max_importance)
        cur = conn.execute(
            f"UPDATE memories SET archived=1, updated_at=? WHERE {' AND '.join(where)}",
            [now] + params,
        )
    conn.commit()
    print(json.dumps({"ok": True, "archived": cur.rowcount}, ensure_ascii=False))
    conn.close()


def emotion_get(args):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM emotion_state WHERE scope = ?", (args.scope,)
    ).fetchone()
    if row:
        print(json.dumps(row_to_dict(row), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"scope": args.scope, "exists": False}, ensure_ascii=False, indent=2))
    conn.close()


def emotion_set(args):
    # v3（2026-08-19）：移除 stdin 读——context 为 None 时保留现有值（daemon 不传 context 不阻塞不清空）
    conn = connect()
    now = now_iso()
    # v2 修复（2026-08-18）：emotion set 不再重置关系状态——rel 参数为 None 时保留现有值
    # （emotion=即时情绪，rel=长期关系，两轴独立；此前默认 0 会误清零 rel_level/affinity/trust）
    # v3（2026-08-19）：context 为 None 时同样保留现有值（daemon 下不传 context 不再清空/阻塞）
    existing = conn.execute(
        "SELECT rel_level, affinity, trust, context, sixdim FROM emotion_state WHERE scope = ?", (args.scope,)
    ).fetchone()
    if existing:
        rel_level = args.rel_level if args.rel_level is not None else existing["rel_level"]
        affinity = args.affinity if args.affinity is not None else existing["affinity"]
        trust = args.trust if args.trust is not None else existing["trust"]
        ctx = args.context if args.context is not None else existing["context"]
        sd = getattr(args, "sixdim", None) if getattr(args, "sixdim", None) is not None else existing["sixdim"]
    else:
        rel_level = args.rel_level if args.rel_level is not None else 0
        affinity = args.affinity if args.affinity is not None else 0.0
        trust = args.trust if args.trust is not None else 0.0
        ctx = args.context
        sd = getattr(args, "sixdim", None)
    # 钳制关系值，防止 emotion_set 绕过 rel_update 的 clamp
    rel_level = max(0, min(5, rel_level if rel_level is not None else 0))
    affinity = max(-2.0, min(2.0, affinity if affinity is not None else 0.0))
    trust = max(-2.0, min(2.0, trust if trust is not None else 0.0))
    conn.execute(
        """
        INSERT INTO emotion_state (scope, valence, arousal, dominance, sixdim, label, context, rel_level, affinity, trust, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(scope) DO UPDATE SET
            valence=excluded.valence,
            arousal=excluded.arousal,
            dominance=excluded.dominance,
            sixdim=excluded.sixdim,
            label=excluded.label,
            context=excluded.context,
            rel_level=excluded.rel_level,
            affinity=excluded.affinity,
            trust=excluded.trust,
            updated_at=excluded.updated_at
        """,
        (args.scope, args.valence, args.arousal, args.dominance,
         json.dumps(sd, ensure_ascii=False) if sd else None,
         args.label, ctx, rel_level, affinity, trust, now),
    )
    conn.commit()
    print(json.dumps({"ok": True, "scope": args.scope}, ensure_ascii=False))
    conn.close()


def emotion_list(args):
    conn = connect()
    rows = conn.execute("SELECT * FROM emotion_state ORDER BY updated_at DESC").fetchall()
    print(json.dumps([row_to_dict(r) for r in rows], ensure_ascii=False, indent=2))
    conn.close()


# ── 关系-情感状态机（v2，2026-08-18，吸收自角色卡 107 样本）──────────────────
# 角色卡范式：关系档位(rel_level) 是主控变量，好感(affinity)/信任(trust) 双轴
# 驱动 persona 切换；每次交互显式回写 <好感变化:+X>。这里把该机制落成命令。

REL_LEVEL_NAMES = {
    0: "null(初始/陌生)",
    1: "verylow(冷淡/疏远)",
    2: "low(慢热/谨慎)",
    3: "medium(熟络/友好)",
    4: "high(亲近/亲密)",
    5: "special(极亲/地雷/特殊分支)",
}


def rel_get(args):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM emotion_state WHERE scope = ?", (args.scope,)
    ).fetchone()
    if row:
        d = row_to_dict(row)
        d["rel_level_name"] = REL_LEVEL_NAMES.get(d.get("rel_level"), str(d.get("rel_level")))
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"scope": args.scope, "exists": False, "rel_level": 0,
                          "rel_level_name": REL_LEVEL_NAMES[0],
                          "affinity": 0.0, "trust": 0.0}, ensure_ascii=False, indent=2))
    conn.close()


def rel_set(args):
    """设置（覆盖）某 scope 的关系状态。affinity/trust 为绝对值 -2..2，rel_level 0-5。"""
    conn = connect()
    now = now_iso()
    # 2026-08-29 P1-3 补丁：写入前一律钳制到约定区间，防越界值（如 aff=4.3）
    def _clamp_rel(rl, aff, tr):
        rl = max(0, min(5, rl if rl is not None else 0))
        aff = max(-2.0, min(2.0, aff if aff is not None else 0.0))
        tr = max(-2.0, min(2.0, tr if tr is not None else 0.0))
        return rl, aff, tr
    cur = conn.execute("SELECT * FROM emotion_state WHERE scope=?", (args.scope,)).fetchone()
    if cur:
        rel_level = args.rel_level if args.rel_level is not None else cur["rel_level"]
        affinity = args.affinity if args.affinity is not None else cur["affinity"]
        trust = args.trust if args.trust is not None else cur["trust"]
        rel_level, affinity, trust = _clamp_rel(rel_level, affinity, trust)
        conn.execute(
            """UPDATE emotion_state SET rel_level=?, affinity=?, trust=?, updated_at=?
               WHERE scope=?""",
            (rel_level, affinity, trust, now, args.scope),
        )
    else:
        rel_level, affinity, trust = _clamp_rel(args.rel_level, args.affinity, args.trust)
        conn.execute(
            """INSERT INTO emotion_state (scope, valence, arousal, dominance, label, context,
                                          rel_level, affinity, trust, updated_at)
               VALUES (?, 0.0, 0.5, 0.5, NULL, NULL, ?, ?, ?, ?)""",
            (args.scope, rel_level, affinity, trust, now),
        )
    conn.commit()
    conn.close()
    rel_get(args)


def rel_update(args):
    """增量回写（角色卡 <好感变化:+X> 语义）：
       --affinity-delta / --trust-delta 加到现值并 clamp 到 [-2,2]；
       可选 --rel-adjust 手动调整档位（如 +1 升档）。
       affinity 达 +2 自动升档、达 -2 自动降档（可被 --no-auto 关闭）。"""
    conn = connect()
    now = now_iso()
    cur = conn.execute("SELECT * FROM emotion_state WHERE scope=?", (args.scope,)).fetchone()
    affinity = cur["affinity"] if cur else 0.0
    trust = cur["trust"] if cur else 0.0
    rel_level = cur["rel_level"] if cur else 0
    affinity = max(-2.0, min(2.0, affinity + (args.affinity_delta or 0.0)))
    trust = max(-2.0, min(2.0, trust + (args.trust_delta or 0.0)))
    if args.rel_adjust:
        rel_level = max(0, min(5, rel_level + args.rel_adjust))
    if not args.no_auto:
        if affinity >= 1.8 and rel_level < 4:
            rel_level = max(rel_level, 3)
        if affinity <= -1.8 and rel_level > 1:
            rel_level = min(rel_level, 2)
    if cur:
        conn.execute(
            """UPDATE emotion_state SET affinity=?, trust=?, rel_level=?, updated_at=?
               WHERE scope=?""",
            (affinity, trust, rel_level, now, args.scope),
        )
    else:
        conn.execute(
            """INSERT INTO emotion_state (scope, valence, arousal, dominance, label, context,
                                          rel_level, affinity, trust, updated_at)
               VALUES (?, 0.0, 0.5, 0.5, NULL, NULL, ?, ?, ?, ?)""",
            (args.scope, rel_level, affinity, trust, now),
        )
    conn.commit()
    conn.close()
    rel_get(args)


def decay(args):
    conn = connect()
    cur = conn.execute(
        """
        UPDATE memories
        SET importance = ROUND(importance * ?, 4)
        WHERE archived = 0 AND julianday('now') - julianday(updated_at) > ?
        """,
        (args.factor, args.days),
    )
    conn.commit()
    print(json.dumps({"ok": True, "decayed": cur.rowcount, "factor": args.factor}, ensure_ascii=False))
    conn.close()


def export_data(args):
    conn = connect()
    lines = []
    for r in conn.execute("SELECT * FROM memories").fetchall():
        d = row_to_dict(r)
        d["table"] = "memories"
        lines.append(d)
    for r in conn.execute("SELECT * FROM emotion_state").fetchall():
        d = row_to_dict(r)
        d["table"] = "emotion_state"
        lines.append(d)
    conn.close()
    payload = "\n".join(json.dumps(x, ensure_ascii=False) for x in lines)
    if args.file:
        Path(args.file).write_text(payload + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "file": str(args.file), "records": len(lines)}, ensure_ascii=False))
    else:
        print(payload)


def import_data(args):
    conn = connect()
    count = 0
    for line in Path(args.file).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        table = obj.pop("table", None)
        if table == "memories":
            cols = [
                "id", "scope", "entity", "content", "kind", "importance",
                "valence", "arousal", "tags", "source", "created_at",
                "updated_at", "last_access_at", "access_count", "archived",
            ]
            vals = [obj.get(c) for c in cols]
            conn.execute(
                f"INSERT OR REPLACE INTO memories ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                vals,
            )
            count += 1
        elif table == "emotion_state":
            cols = ["scope", "valence", "arousal", "dominance", "label", "context",
                    "rel_level", "affinity", "trust", "updated_at"]
            vals = [obj.get(c) for c in cols]
            conn.execute(
                f"INSERT OR REPLACE INTO emotion_state ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                vals,
            )
            count += 1
    conn.commit()
    print(json.dumps({"ok": True, "imported": count}, ensure_ascii=False))
    conn.close()


def status(args):
    conn = connect()
    total = conn.execute("SELECT COUNT(*) AS c FROM memories WHERE archived=0").fetchone()["c"]
    archived = conn.execute("SELECT COUNT(*) AS c FROM memories WHERE archived=1").fetchone()["c"]
    by_kind = {
        r["kind"]: r["c"]
        for r in conn.execute("SELECT kind, COUNT(*) AS c FROM memories WHERE archived=0 GROUP BY kind")
    }
    emotions = conn.execute("SELECT COUNT(*) AS c FROM emotion_state").fetchone()["c"]
    print(
        json.dumps(
            {
                "ok": True,
                "data_dir": str(data_dir()),
                "db": str(db_path()),
                "active_memories": total,
                "archived_memories": archived,
                "by_kind": by_kind,
                "emotion_states": emotions,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    conn.close()


def review_draft(args):
    """打印 Evil Review 检查清单，供 Agent 在写入 reflection/skill 前执行对抗审查。"""
    print("=== Evil Review: Memory Draft ===")
    print("Draft:")
    print(args.draft)
    print()
    print("Attack (Evil):")
    print("1. 这是单次偶然还是可复现规律？")
    print("2. 有没有反例/前提条件没写？")
    print("3. 这是事实还是推断？")
    print("4. 写入后会误导未来决策吗？")
    print("5. 是否包含敏感信息或危险策略？")
    print("6. 被错误召回时会造成什么后果？")
    print()
    print("Rebuttal / Integration (Neuro):")
    print("对每条攻击给出：采纳 / 反驳 / 降级，并写出修订后的最终内容。")
    print()
    print("Quality Gate:")
    print("- [ ] Evil 至少提出 1 条有效攻击")
    print("- [ ] 每条攻击都有明确处置")
    print("- [ ] 最终内容包含适用条件/边界")
    print("- [ ] 敏感信息已移除或脱敏")
    print("- [ ] 落盘时 tags 含 evil_reviewed")


def build_parser():
    parser = argparse.ArgumentParser(prog="memory_store.py", description="长时记忆 + 情感状态本地存储")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="写入一条记忆")
    p_add.add_argument("--scope", default="default")
    p_add.add_argument("--entity", default=None)
    p_add.add_argument("--content", default=None, help="内容；若省略则从 stdin 读（utf-8，规避 Windows argv 中文乱码）")
    p_add.add_argument("--kind", default="fact", choices=["fact", "preference", "event", "relationship", "skill", "reflection", "emotion"])
    p_add.add_argument("--importance", type=float, default=0.5)
    p_add.add_argument("--valence", type=float, default=0.0)
    p_add.add_argument("--arousal", type=float, default=0.5)
    p_add.add_argument("--sixdim", default=None, help="六维情绪向量 JSON：{joy,anger,sadness,fear,surprise,disgust}，值域 -100~100（九维心智空间）")
    p_add.add_argument("--tags", default="", help="逗号分隔标签")
    p_add.add_argument("--source", default=None)
    p_add.set_defaults(func=add_memory)

    p_review = sub.add_parser("review", help="写入 reflection/skill 前执行 Evil Review 检查清单")
    p_review.add_argument("--draft", required=True, help="待审查的反思/技能草稿")
    p_review.set_defaults(func=review_draft)

    p_search = sub.add_parser("search", help="按内容/标签/情感/重要性检索")
    p_search.add_argument("--query", default="")
    p_search.add_argument("--scope", default=None)
    p_search.add_argument("--kind", default=None)
    p_search.add_argument("--min-importance", type=float, default=None)
    p_search.add_argument("--limit", type=int, default=10)
    p_search.set_defaults(func=search_memories)

    p_recall = sub.add_parser("recall", help="按 scope 召回近期重要记忆")
    p_recall.add_argument("--scope", default="default")
    p_recall.add_argument("--min-importance", type=float, default=None)
    p_recall.add_argument("--limit", type=int, default=10)
    p_recall.set_defaults(func=recall)

    p_forget = sub.add_parser("forget", help="软删除/遗忘记忆")
    p_forget.add_argument("--id", type=int, default=None)
    p_forget.add_argument("--scope", default=None)
    p_forget.add_argument("--older-than-days", type=float, default=30.0)
    p_forget.add_argument("--max-importance", type=float, default=None)
    p_forget.set_defaults(func=forget)

    p_emotion = sub.add_parser("emotion", help="情感状态读写")
    emotion_sub = p_emotion.add_subparsers(dest="emotion_command", required=True)
    p_emotion_get = emotion_sub.add_parser("get")
    p_emotion_get.add_argument("--scope", default="default")
    p_emotion_get.set_defaults(func=emotion_get)
    p_emotion_set = emotion_sub.add_parser("set")
    p_emotion_set.add_argument("--scope", default="default")
    p_emotion_set.add_argument("--valence", type=float, required=True)
    p_emotion_set.add_argument("--arousal", type=float, default=0.5)
    p_emotion_set.add_argument("--dominance", type=float, default=0.5)
    p_emotion_set.add_argument("--sixdim", default=None, help="六维情绪向量 JSON：{joy,anger,sadness,fear,surprise,disgust}，值域 -100~100（九维心智空间）")
    p_emotion_set.add_argument("--label", default=None)
    p_emotion_set.add_argument("--context", default=None)
    p_emotion_set.add_argument("--rel-level", type=int, default=None, help="关系档位 0-5（默认 None=不修改现有值）")
    p_emotion_set.add_argument("--affinity", type=float, default=None, help="好感度 -2..2（默认 None=不修改现有值）")
    p_emotion_set.add_argument("--trust", type=float, default=None, help="信任度 -2..2（默认 None=不修改现有值）")
    p_emotion_set.set_defaults(func=emotion_set)
    p_emotion_list = emotion_sub.add_parser("list")
    p_emotion_list.set_defaults(func=emotion_list)

    p_rel = sub.add_parser("rel", help="关系-情感状态机（角色卡范式 v2）：档位 + 好感/信任双轴")
    rel_sub = p_rel.add_subparsers(dest="rel_command", required=True)
    p_rel_get = rel_sub.add_parser("get")
    p_rel_get.add_argument("--scope", default="default")
    p_rel_get.set_defaults(func=rel_get)
    p_rel_set = rel_sub.add_parser("set")
    p_rel_set.add_argument("--scope", default="default")
    p_rel_set.add_argument("--rel-level", type=int, default=None, choices=range(0, 6))
    p_rel_set.add_argument("--affinity", type=float, default=None, help="-2..2 绝对值")
    p_rel_set.add_argument("--trust", type=float, default=None, help="-2..2 绝对值")
    p_rel_set.set_defaults(func=rel_set)
    p_rel_upd = rel_sub.add_parser("update", help="增量回写（<好感变化:+X> 语义）")
    p_rel_upd.add_argument("--scope", default="default")
    p_rel_upd.add_argument("--affinity-delta", type=float, default=None, help="好感增量，如 0.5 / -0.5")
    p_rel_upd.add_argument("--trust-delta", type=float, default=None, help="信任增量")
    p_rel_upd.add_argument("--rel-adjust", type=int, default=None, help="档位手动调整，如 +1 升档 / -1 降档")
    p_rel_upd.add_argument("--no-auto", action="store_true", help="关闭 affinity 达 ±2 自动升降档")
    p_rel_upd.set_defaults(func=rel_update)

    p_decay = sub.add_parser("decay", help="记忆衰减（MemoryBank 风格）")
    p_decay.add_argument("--days", type=float, default=30.0)
    p_decay.add_argument("--factor", type=float, default=0.9)
    p_decay.set_defaults(func=decay)

    p_export = sub.add_parser("export", help="导出 JSONL")
    p_export.add_argument("--file", default=None)
    p_export.set_defaults(func=export_data)

    p_import = sub.add_parser("import", help="导入 JSONL")
    p_import.add_argument("--file", required=True)
    p_import.set_defaults(func=import_data)

    p_status = sub.add_parser("status", help="查看统计")
    p_status.set_defaults(func=status)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "tags") and isinstance(args.tags, str):
        args.tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    args.func(args)


if __name__ == "__main__":
    main()
