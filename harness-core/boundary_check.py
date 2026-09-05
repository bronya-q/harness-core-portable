#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""boundary_check.py — 公共边界扫描（私人标识/绝对路径/overlay 引用）。"""
import json
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", "docs/images", "build", "dist", "tests"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pyc", ".db", ".lock", ".zip"}
# 这些文件中的命中是“有意提及/示例”，不应算作泄漏。
ALLOWED_FILES = {".gitignore", "PUBLIC_CONTENT_BOUNDARY.md", "knowledge-sources.example.json",
                 "KNOWLEDGE_STEWARDSHIP.md", "ROADMAP.md",
                 "docs/tasks/2026-09-04-alpha4-implementation-progress.md",
                 "docs/tasks/2026-09-04-whole-project-progress-audit.md",
                 "docs/tasks/2026-09-04-remaining-gaps.md",
                 "docs/tasks/2026-09-04-partial-implementation-inventory.md",
                 "docs/tasks/2026-09-04-private-document-migration.md",
                 "docs/tasks/2026-09-04-public-release-alpha2-design.md",
                 "examples/agent-integrations/AGENTS.md",
                 "harness-core/boundary_check.py",
                 "harness-core/dashboard.py",
                 "harness-core/runtime_resolver.py",
                 "harness-core/mind_evolution.py"}
PATTERNS = [
    (r"本机知识管理员 A", "private_steward_a"),
    (r"本机知识管理员 B", "private_steward_b"),
    (r"本机综合人格 A", "private_hybrid_a"),
    (r"local-persona-[ab]\b", "local_persona_ref"),
    (r"[Cc]:\\Users|C:/Users", "windows_abs_path"),
    (r"\.dsh/harness-local", "private_overlay"),
    (r"personas\.local\.json", "private_overlay"),
]


def scan():
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(tuple(SKIP_SUFFIXES)):
                continue
            f = Path(dirpath) / fn
            rel = str(f.relative_to(ROOT)).replace("\\", "/")
            if rel in ALLOWED_FILES:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat, name in PATTERNS:
                for m in re.finditer(pat, text):
                    hits.append({"file": str(f.relative_to(ROOT)), "type": name,
                                 "snippet": text[max(0, m.start()-20):m.end()+20]})
    return hits


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "boundary-check":
        pass
    hits = scan()
    print(json.dumps({"ok": len(hits) == 0, "mode": "boundary_check",
                      "hits": hits[:30], "note": "辅助扫描；命中需人工确认是否属于边界文档/示例。"},
                     ensure_ascii=False, indent=2))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
