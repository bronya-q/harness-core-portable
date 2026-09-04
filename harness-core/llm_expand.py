#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_expand.py — LLM 查询扩展（生成相关词 + 关键词检索 union）。"""
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

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"


def _llm(prompt, num_predict=64):
    payload = {"model": MODEL, "prompt": prompt, "stream": False,
               "options": {"temperature": 0.4, "num_predict": num_predict}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d.get("response", "")


def _search(query, scope, limit):
    p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "memory_store.py"), "search",
                        "--query", query, "--scope", scope, "--limit", str(limit)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    try:
        return json.loads(p.stdout)
    except Exception:
        return []


def main():
    global MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--scope", default="default")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()
    MODEL = args.model

    # LLM 生成相关词
    prompt = ("对于查询“%s”，生成 4 个同义/相关中文查询词，用逗号分隔，不要解释。" % args.query)
    gen = _llm(prompt)
    terms = [t.strip() for t in gen.replace("，", ",").split(",") if t.strip()][:6]
    queries = [args.query] + terms
    seen = {}
    for qx in queries:
        rows = _search(qx, args.scope, 30)
        for i, r in enumerate(rows):
            rid = str(r.get("id"))
            score = i + 1
            if rid not in seen or score < seen[rid][1]:
                seen[rid] = (r, score)
    out = [v[0] for k, v in sorted(seen.items(), key=lambda kv: kv[1][1])]
    print(json.dumps({"ok": True, "terms": terms, "results": out[:args.limit]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    main()
