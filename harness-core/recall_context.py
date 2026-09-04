#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recall_context.py — long-term-memory-emotion 会话启动召回辅助。

用途：
  在 DSH / Agent 会话开始时，把当前 scope 近期重要记忆压缩成一小段上下文，
  供注入 system prompt 或让 Agent 先读再干活。只读、不写入、不联网。

用法：
  python recall_context.py --scope default --limit 5 --min-importance 0.5
  python recall_context.py --scope character:demo-alice --format text

输出：
  默认 text：适合直接作为“记忆上下文”片段；
  --format json：原样结构化输出，适合程序处理。
说明：不改变记忆内容；召回会按 P0-1 回写访问计数（access_count/last_access_at），以便观察记忆是否真正被使用。
"""
import argparse
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout, redirect_stderr

# 允许从任意 CWD 运行：优先用本文件所在目录的 memory_store.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory_store as ms  # noqa: E402
import nine_dim as nd  # noqa: E402  九维情绪引擎（读状态用，只读不写）


def _call(fn, **kwargs):
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        fn(argparse.Namespace(**kwargs))
    text = out.getvalue().strip()
    if not text:
        raise RuntimeError(f"memory_store call produced no output: {err.getvalue().strip()}")
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description="Generate a compact recall context from local long-term memory.")
    parser.add_argument("--scope", default="default", help="memory scope (default: default)")
    parser.add_argument("--limit", type=int, default=5, help="max memories (default: 5)")
    parser.add_argument("--min-importance", type=float, default=None, help="minimum importance filter")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="output format")
    parser.add_argument("--semantic-query", default=None,
                        help="可选：用 bge-m3 做语义召回；不指定时保持原有 recall 行为")
    parser.add_argument("--sim-weight", type=float, default=0.4,
                        help="语义召回混合权重（仅 --semantic-query 生效）")
    parser.add_argument("--narrative", action="store_true",
                        help="可选：额外生成 H2 叙事候选（只读 shadow）")
    args = parser.parse_args()

    try:
        if args.semantic_query:
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "semantic_search.py")
            cmd = [sys.executable, script, "--query", args.semantic_query,
                   "--scope", args.scope, "--limit", str(args.limit),
                   "--sim-weight", str(args.sim_weight)]
            if args.min_importance is not None:
                cmd.extend(["--min-importance", str(args.min_importance)])
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "semantic search failed")
            semantic_data = json.loads(proc.stdout)
            memories = semantic_data.get("results", [])
            data = {"results": memories}
        else:
            data = _call(
                ms.recall,
                scope=args.scope,
                min_importance=args.min_importance,
                limit=args.limit,
            )
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    # memory_store.recall 返回结构通常是 {"results": [...]} 或 {"memories": [...]}
    memories = data if isinstance(data, list) else (data.get("results") or data.get("memories") or [])
    narrative_candidates = []
    if getattr(args, "narrative", False):
        try:
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "humanization.py")
            proc = subprocess.run(
                [sys.executable, script, "narrative", "--scope", args.scope, "--limit", str(args.limit)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            if proc.returncode == 0:
                ndata = json.loads(proc.stdout)
                narrative_candidates = ndata.get("narrative_candidates", []) or []
        except Exception:
            narrative_candidates = []
    # ---- 此刻的心情（九维状态 + 关系档位，只读） ----
    mood = None
    try:
        st = nd._read_state(args.scope)
        six, derivation = nd._sixdim_for_scope(args.scope, st)
        mood = {
            "sixdim": six,
            "derivation": derivation,
            "label": st.get("label"),
            "rel_level": st.get("rel_level"),
            "affinity": st.get("affinity"),
            "trust": st.get("trust"),
        }
    except Exception as exc:  # noqa: BLE001
        mood = {"error": str(exc)}
    if args.format == "json":
        out = {"ok": True, "scope": args.scope, "mood": mood, "memories": memories}
        if narrative_candidates:
            out["narrative_candidates"] = narrative_candidates
        print(json.dumps(out, ensure_ascii=False))
        return 0

    lines = [f"[memory recall scope={args.scope}]"]
    if mood and "sixdim" in mood:
        sx = mood["sixdim"]
        top = sorted(sx.items(), key=lambda kv: -kv[1])[:2]
        feel = "、".join(f"{k}{v}" for k, v in top)
        rel = f"，关系档位 Lv{mood.get('rel_level')}，好感 {mood.get('affinity')}" if mood.get("rel_level") is not None else ""
        label = f"（{mood.get('label')}）" if mood.get("label") else ""
        lines.append(f"[此刻的心情{label}] {feel}{rel}")
    for m in memories:
        content = m.get("content") or m.get("text") or ""
        kind = m.get("kind") or "fact"
        importance = m.get("importance")
        tags = m.get("tags") or ""
        meta = f"kind={kind}"
        if importance is not None:
            meta += f", importance={importance}"
        if tags:
            meta += f", tags={tags}"
        lines.append(f"- ({meta}) {content}")
    if narrative_candidates:
        lines.append("[叙事候选（只读，不自动注入）]")
        for c in narrative_candidates[:3]:
            lines.append(f"- [{c.get('anchor_type')}] {c.get('summary', '')[:90]}")
    if not lines:
        lines.append("(no memories)")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
