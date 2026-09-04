#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_provenance.py — 受控、有限深度代码相似性比对（避免全量递归卡死）。

用法：
  python audit_provenance.py [--upstream-root PATH] [--max-upstream 10]
                            [--max-size-kb 100] [--depth 2] [--threshold 0.5]
"""
import argparse
import difflib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _norm(text):
    return "\n".join(line.strip().lower() for line in text.splitlines() if line.strip())


def collect_py(root, depth, max_size_kb):
    root = Path(root)
    if not root.exists():
        return []
    out = []
    base_depth = len(root.parts)
    for p in root.rglob("*.py"):
        if p.stat().st_size > max_size_kb * 1024:
            continue
        if any(part in (".git", "node_modules", ".venv", "site-packages") for part in p.parts):
            continue
        if depth is not None and len(p.parts) - base_depth > depth:
            continue
        out.append(p)
    return sorted(out)[:200]


def similarity_norm(a, b):
    if not a or not b:
        return 0.0
    return round(difflib.SequenceMatcher(None, a, b).ratio(), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-root", default=str(Path.home() / "Documents" / "harness" / "_research" / "NEKO"))
    ap.add_argument("--max-upstream", type=int, default=10)
    ap.add_argument("--max-size-kb", type=int, default=100)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()

    repo_files = collect_py(ROOT, 3, 200)
    upstream_files = collect_py(args.upstream_root, args.depth, args.max_size_kb)[:args.max_upstream]

    report = {"repo_files": len(repo_files), "upstream_files": len(upstream_files),
              "upstream_root": args.upstream_root, "threshold": args.threshold, "hits": []}
    for r in repo_files:
        try:
            rtext = _norm(r.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        best = (0.0, None)
        for u in upstream_files:
            try:
                utext = _norm(u.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            sim = similarity_norm(rtext, utext)
            if sim > best[0]:
                best = (sim, str(u))
        if best[0] >= args.threshold:
            report["hits"].append({"file": str(r), "score": best[0], "upstream": best[1]})
    report["conclusion"] = "受控比对完成；高相似度命中见上。"
    (ROOT / "provenance_audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "repo_files": report["repo_files"], "upstream_files": report["upstream_files"],
                      "hits": len(report["hits"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
