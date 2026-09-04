#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_rerank.py — LLM 重排（query -> top候选 -> LLM相关性打分 -> top-k）。"""
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"


def _kw(query, scope, limit):
    p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "memory_store.py"), "search",
                        "--query", query, "--scope", scope, "--limit", str(limit)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    try:
        return json.loads(p.stdout)
    except Exception:
        return []


def _llm(prompt, num_predict=256):
    payload = {"model": MODEL, "prompt": prompt, "stream": False,
               "options": {"temperature": 0.0, "num_predict": num_predict}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d.get("response", "")


def main():
    global MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--scope", default="default")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--candidate-limit", type=int, default=30)
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()
    MODEL = args.model

    cands = _kw(args.query, args.scope, args.candidate_limit)
    if not cands:
        print(json.dumps({"ok": False, "results": []}, ensure_ascii=False))
        return 1
    # build prompt
    numbered = []
    for i, r in enumerate(cands[:args.candidate_limit], 1):
        numbered.append("%d. %s" % (i, (r.get("content") or "")[:120]))
    prompt = ("你是记忆相关性判断器。判断下面哪些候选记忆与查询相关。"
              "只输出相关候选编号列表，格式: [1,3,5]。\n\n查询：%s\n\n候选：\n%s\n" % (args.query, "\n".join(numbered)))
    out = _llm(prompt)
    try:
        # extract json-like list
        import re
        m = re.search(r"\[[0-9,\s]+\]", out)
        ids = [int(x) for x in re.findall(r"\d+", m.group(0))] if m else []
    except Exception:
        ids = []
    selected = []
    if ids:
        for i in ids:
            if 1 <= i <= len(cands):
                selected.append(cands[i-1])
    # 若 LLM 没返回足够，补 keyword 其余
    for r in cands:
        if len(selected) >= args.limit:
            break
        if r not in selected:
            selected.append(r)
    print(json.dumps({"ok": True, "results": selected[:args.limit], "llm_hits": len(ids)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
