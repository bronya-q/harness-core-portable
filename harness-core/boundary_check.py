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
SKIP_DIRS = {".git", "__pycache__", "node_modules", "docs/images", "docs/rebuild", "rebuild", "build", "dist", "tests"}
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
                 "docs/tasks/2026-09-05-security-audit-findings.md",
                 "examples/agent-integrations/AGENTS.md",
                 "harness-core/boundary_check.py",
                 "harness-core/dashboard.py",
                 "harness-core/runtime_resolver.py",
                 "harness-core/mind_evolution.py"}
PATTERNS = [
    (r"local-persona-[ab]\b", "local_persona_ref"),
    (r"[Cc]:\\Users|C:/Users", "windows_abs_path"),
    (r"\.dsh/harness-local", "private_overlay"),
    (r"personas\.local\.json", "private_overlay"),
]
# 只有这些类别才被视为“私人身份标识”泄漏；windows 路径/overlay 引用是边界提示，不单独判失败。
PRIVATE_IDENTITY_NAMES = {"local_persona_ref"}


def _load_extra_patterns():
    """Load extra private identifier rules from env file (not committed)."""
    fp = os.environ.get("HARNESS_PRIVATE_IDENTIFIERS_FILE")
    if not fp or not Path(fp).exists():
        return []
    extras = []
    for line in Path(fp).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "#" not in line:
            extras.append((line, "private_custom:" + line[:8]))
    return extras


def scan():
    hits = []
    all_patterns = PATTERNS + _load_extra_patterns()
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
            for pat, name in all_patterns:
                for m in re.finditer(pat, text):
                    hits.append({"file": str(f.relative_to(ROOT)), "type": name,
                                 "snippet": text[max(0, m.start()-20):m.end()+20]})
    return hits


def scan_history_counts():
    """扫描所有 git 历史中的私人标识，只返回类型计数（提交-文件匹配行数），不输出具体内容。

    Fail-closed：rev-list/grep 异常报告失败，不把失败当零命中。
    指标：每个 (commit, file) 的匹配行数累加，不等同于出现次数/唯一泄漏数。
    """
    import subprocess
    try:
        revs = subprocess.run(["git", "-C", str(ROOT), "rev-list", "--all"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if revs.returncode != 0:
            return {"error": "git_rev_list_failed", "stderr": revs.stderr[-200:]}
        rev_list = [r for r in revs.stdout.splitlines() if r.strip()]
    except Exception as e:
        return {"error": "git_rev_list_failed", "detail": repr(e)}
    all_patterns = PATTERNS + _load_extra_patterns()
    counts = {name: 0 for _, name in all_patterns}
    failed = 0
    for rev in rev_list:
        for pat, name in all_patterns:
            try:
                p = subprocess.run(["git", "-C", str(ROOT), "grep", "-I", "-c", "-E", pat, rev, "--"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            except Exception:
                failed += 1
                continue
            if p.returncode == 0:
                # git grep -c 可能返回多个文件行：commit:file:count
                for line in p.stdout.splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3:
                        try:
                            counts[name] += int(parts[-1])
                        except Exception:
                            pass
            elif p.returncode != 1:
                failed += 1
    private_identity_hits = sum(v for k, v in counts.items()
                                if k in PRIVATE_IDENTITY_NAMES or k.startswith("private_custom:"))
    result = {k: v for k, v in counts.items() if v > 0}
    result["_failed_scans"] = failed
    result["_private_identity_hits"] = private_identity_hits
    return result


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "boundary-check":
        history = "--history" in sys.argv
    else:
        history = "--history" in sys.argv
    if history:
        counts = scan_history_counts()
        if isinstance(counts, dict) and "error" in counts:
            print(json.dumps({"ok": False, "mode": "boundary_check_history",
                              "error": counts["error"], "detail": counts.get("detail", ""),
                              "note": "扫描失败，不能报告为通过。"}, ensure_ascii=False, indent=2))
            return 1
        failed = counts.pop("_failed_scans", 0)
        pri = counts.pop("_private_identity_hits", 0)
        ok = pri == 0 and failed == 0
        print(json.dumps({"ok": ok, "mode": "boundary_check_history",
                          "counts": counts, "failed_scans": failed,
                          "private_identity_hits": pri,
                          "note": "仅统计提交-文件匹配行数，不输出具体内容；失败扫描已记录；"
                                  "private_identity_hits=0 不代表无边界提示（counts 中的 windows/overlay 为提示项）。"},
                         ensure_ascii=False, indent=2))
        return 0 if ok else 1
    hits = scan()
    print(json.dumps({"ok": len(hits) == 0, "mode": "boundary_check",
                      "hits": hits[:30], "note": "辅助扫描；命中需人工确认是否属于边界文档/示例。"},
                     ensure_ascii=False, indent=2))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
