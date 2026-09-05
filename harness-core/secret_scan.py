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


def scan_history():
    """扫描所有 git 历史中的密钥形态（只读，不修改任何对象）。

    Fail-closed：只有全部 refs 都成功扫描且无命中才返回 ok=True。
    输出不包含匹配原文，只记录 ref/file/line/rule。
    """
    import subprocess
    pats = "|".join("(%s)" % p for p, _ in PATTERNS)
    try:
        revs = subprocess.run(["git", "-C", str(ROOT), "rev-list", "--all"],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
        if revs.returncode != 0:
            return {"error": "git_rev_list_failed", "stderr": revs.stderr[-200:]}
        rev_list = [r for r in revs.stdout.splitlines() if r.strip()]
    except Exception as e:
        return {"error": "git_rev_list_failed", "detail": repr(e)}
    hits = []
    scanned = 0
    failed = 0
    for rev in rev_list:
        try:
            p = subprocess.run(["git", "-C", str(ROOT), "grep", "-I", "-n", "-E", pats, rev, "--"],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=30)
        except Exception:
            failed += 1
            continue
        if p.returncode == 0 or p.returncode == 1:
            scanned += 1
        else:
            failed += 1
        if p.returncode == 0:
            for line in p.stdout.splitlines():
                if not line.strip() or "binary" in line:
                    continue
                # 格式: rev:file:line:content
                # 只保留前三个字段，丢弃匹配原文
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    hits.append({"history": True, "ref": rev[:12],
                                 "file": parts[1], "line": parts[2]})
    return {"hits": hits, "scanned": scanned, "failed": failed, "total_refs": len(rev_list)}


def main():
    if "--history" in sys.argv:
        result = scan_history()
        if isinstance(result, dict) and ("error" in result):
            print(__import__("json").dumps({"ok": False, "mode": "secret_scan_history",
                                            "error": result.get("error"),
                                            "detail": result.get("detail", ""),
                                            "note": "扫描失败，不能报告为通过。"},
                                           ensure_ascii=False, indent=2))
            return 1
        hits = result.get("hits", [])
        scanned = result.get("scanned", 0)
        failed = result.get("failed", 0)
        total = result.get("total_refs", 0)
        ok = len(hits) == 0 and failed == 0 and total > 0
        print(__import__("json").dumps({"ok": ok, "mode": "secret_scan_history",
                                        "history": True,
                                        "total_refs": total, "scanned": scanned, "failed": failed,
                                        "hits": hits[:30],
                                        "note": "在指定 refs 与规则覆盖范围内未发现命中；扫描失败另行记录。此结果不构成不存在真实凭据的证明。"},
                                       ensure_ascii=False, indent=2))
        return 0 if ok else 1
    hits = scan()
    print(__import__("json").dumps({"ok": len(hits) == 0, "mode": "secret_scan",
                                    "history": False,
                                    "hits": hits[:30], "note": "辅助扫描，不构成安全认证。"},
                                   ensure_ascii=False, indent=2))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
