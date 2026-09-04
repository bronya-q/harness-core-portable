#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_ingest.py — 从 Downloads 里的 dsh-session-*.zip 提取跨会话张力。

只读 zip；--write 时写入 humanization_sidecar.mind_tensions（source=cross_session_tension）。
建议默认 --dry-run 先看。
"""
import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from humanization import connect as hum_connect

KEYWORDS = ["未完成", "还缺", "还差", "继续", "问题", "待", "未做", "没做", "还没有", "下一步", "再评价", "还有"]

def list_sessions(downloads):
    return sorted(Path(downloads).glob("dsh-session*.zip"), key=lambda p: p.stat().st_size)


def user_messages_from_zip(zp, max_lines=20000):
    import zipfile
    msgs = []
    try:
        z = zipfile.ZipFile(str(zp))
        names = [n for n in z.namelist() if n.endswith(".jsonl")]
        if not names:
            return []
        with z.open(names[0]) as fh:
            for i, raw in enumerate(fh):
                if i >= max_lines:
                    break
                try:
                    obj = json.loads(raw.decode("utf-8", errors="replace"))
                except Exception:
                    continue
                if obj.get("type") == "user/message":
                    for c in obj.get("data", {}).get("content", []):
                        if isinstance(c, dict) and c.get("type") == "text":
                            msgs.append(c.get("text", ""))
                elif obj.get("type") == "agent/inbox/spliced":
                    for m in obj.get("data", {}).get("inserted", []) or []:
                        if m.get("role") == "user":
                            for c in m.get("content", []):
                                if isinstance(c, dict) and c.get("type") == "text":
                                    msgs.append(c.get("text", ""))
    except Exception:
        pass
    return msgs


def insert_tension(c, scope, statement, sid):
    if not statement.strip():
        return None
    dup = c.execute(
        "SELECT id FROM mind_tensions WHERE source_type='cross_session_tension' AND statement=?",
        (statement[:200],),
    ).fetchone()
    if dup:
        return None
    tid = uuid.uuid4().hex
    c.execute(
        "INSERT INTO mind_tensions(id,scope,source_type,statement,evidence_ids,severity,status,created_at)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (tid, scope, "cross_session_tension", statement[:200], json.dumps([sid], ensure_ascii=False),
         0.6, "open", time.time()),
    )
    c.commit()
    return tid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", default=str(Path.home() / "Downloads"))
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--max-lines", type=int, default=20000)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--register-kind", choices=("real", "auto", "demo"), default=None)
    ap.add_argument("--list-real", action="store_true")
    args = ap.parse_args()
    c = hum_connect()
    if args.list_real:
        rows = c.execute("SELECT * FROM real_session_registry ORDER BY registered_at DESC LIMIT ?",
                         (args.limit,)).fetchall()
        c.close()
        print(json.dumps({"ok": True, "real_sessions": [dict(r) for r in rows]},
                         ensure_ascii=False, indent=2))
        return 0
    zips = list_sessions(args.downloads)[:args.limit]
    total_messages = 0
    tension_ids = []
    detailed = []
    registered = []
    for zp in zips:
        msgs = user_messages_from_zip(zp, args.max_lines)
        total_messages += len(msgs)
        hits = [m for m in msgs if any(k in m for k in KEYWORDS)]
        sid = zp.stem
        if args.register_kind:
            c.execute(
                "INSERT INTO real_session_registry(session_key,kind,user_messages,confirmed,registered_at)"
                " VALUES(?,?,?,0,?) ON CONFLICT(session_key) DO UPDATE SET kind=excluded.kind, user_messages=excluded.user_messages",
                (sid, args.register_kind, len(msgs), time.time()),
            )
            c.commit()
            registered.append({"session": sid, "kind": args.register_kind, "messages": len(msgs)})
        for m in hits:
            if args.write:
                tid = insert_tension(c, "default", m, sid)
                if tid:
                    tension_ids.append(tid)
        detailed.append({"session": sid, "messages": len(msgs), "tension_candidates": len(hits)})
    c.close()
    print(json.dumps({"ok": True, "sessions_scanned": len(zips),
                      "total_user_messages": total_messages,
                      "tension_candidate_messages": sum(x["tension_candidates"] for x in detailed),
                      "tensions_written": len(tension_ids) if args.write else 0,
                      "registered": registered,
                      "sessions": detailed,
                      "write": args.write,
                      "register_kind": args.register_kind,
                      "note": "cross-session tension extraction; heuristic keywords only"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
