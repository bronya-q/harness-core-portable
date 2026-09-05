#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""secret_scan.py — 极简“无密钥进入 trace”扫描。

扫描仓库中常见的密钥/令牌形态，命中则报警。
不保证穷尽；是辅助检查，不是安全认证。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", "docs/images", "build", "dist"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pyc", ".db", ".lock"}
PATTERNS = [
    (r"\bsk-[A-Za-z0-9]{20,}", "openai_sk"),
    (r"\bghp_[A-Za-z0-9]{20,}", "github_pat"),
    (r"\bgithub_pat_[A-Za-z0-9_]{20,}", "github_fine_grained"),
    (r"\bapi[_-]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9_-]{16,}", "api_key_literal"),
    (r"\bAKIA[0-9A-Z]{16}", "aws_access_key"),
]


def scan():
    hits = []
    for dirpath, dirnames, filenames in os_walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(tuple(SKIP_SUFFIXES)):
                continue
            p = Path(dirpath) / fn
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            low = text.lower()
            for pat, name in PATTERNS:
                for m in re.finditer(pat, text):
                    hits.append({"file": str(p.relative_to(ROOT)), "type": name,
                                 "snippet": text[max(0, m.start()-20):m.end()+20]})
    return hits


def os_walk(root):
    import os
    return os.walk(root)


def main():
    hits = scan()
    print(__import__("json").dumps({"ok": len(hits) == 0, "mode": "secret_scan",
                                    "hits": hits[:20], "note": "辅助扫描，不构成安全认证。"},
                                   ensure_ascii=False, indent=2))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
