#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""situated_context.py — 情境化角色上下文视图（R1）。

把 处境 / 关系 / 共同经历 / 当前状态 / 责任 / 表达 拼成一个可读视图。
这不是让所有入口都自动消费它，而是先提供一个“闭环可读”的上下文快照。
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))
from runtime_hotload import load_context  # noqa: E402


def _db_rows(path, sql, args=()):
    import sqlite3
    if not Path(path).exists():
        return []
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute(sql, args)]
        con.close()
        return rows
    except Exception:
        return []


def build(scope=None):
    ctx = load_context()
    persona_id = ctx.get("persona_id")
    mode_id = ctx.get("mode_id")
    if scope is None:
        scope = "character:" + (persona_id or "demo-archivist")
    rel = {}
    # 关系状态
    data_dir = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"
    mem = data_dir / "memory.db"
    rows = _db_rows(mem, "SELECT * FROM emotion_state WHERE scope=?", (scope,))
    if rows:
        r = rows[0]
        rel = {"rel_level": r.get("rel_level"), "affinity": r.get("affinity"),
               "trust": r.get("trust"), "label": r.get("label") or r.get("sixdim")}
    # 共同经历
    nb = data_dir / "notebooks.db"
    notes = _db_rows(nb, "SELECT content, version, created_at FROM notebooks WHERE scope=? ORDER BY version DESC LIMIT 3", (scope,))
    story = data_dir / "story_core.db"
    story_rows = _db_rows(story, "SELECT namespace, content, version FROM story_core ORDER BY id DESC LIMIT 2")
    mode_effects = None
    if mode_id:
        # 从 demo modes 或本机 modes 读取 effect
        modes_path = SKILL / "personas" / "demo-modes" / f"{persona_id}-modes.json"
        if modes_path.exists():
            try:
                d = json.loads(modes_path.read_text(encoding="utf-8"))
                for m in d.get("modes", []):
                    if m.get("mode_id") == mode_id:
                        mode_effects = {"display_name": m.get("display_name"), "effect": m.get("effect"),
                                        "capabilities": m.get("capabilities", [])}
            except Exception:
                pass
    return {"scope": scope, "persona_id": persona_id, "mode_id": mode_id,
            "situation": {"active_persona": persona_id, "active_mode": mode_id,
                          "role": "当前角色/情境模式"},
            "relationship": rel,
            "shared_experience": {"notebooks": notes[:3], "story_core": story_rows[:2]},
            "current_state": {"mode_effects": mode_effects or {},
                              "autonomous": "disabled", "network": "none"},
            "responsibility": {"note": "角色对知识域/任务域负有管理职责，不等于拥有真理。"},
            "expression": {"note": "表达由 mode + capability 决定；当前为只读视图，未强制改写 prompt。"},
            "note": "情境化上下文视图 R1；不是全入口自动消费上下文。"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default=None)
    args = ap.parse_args()
    result = build(args.scope)
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
