#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plugin_audit.py — 插件级健康/供应链审计看板（只读）。

扫描本地插件候选目录，汇总：
  package.json / README / 脚本 / 目录大小 / 是否在隔离区 / 审计状态默认 unknown。
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOTS = [
    Path.home() / "Documents" / "harness",
    Path.home() / ".dsh" / "profiles" / "node_modules",
]
QUARANTINE = Path.home() / ".dsh" / "profiles" / "node_modules" / ".stale-quarantine-20260821"
LOCAL_REVIEWED = {
    "deepseek-eyes-src", "deepseek灰测-docs", "dsh-agent-tools", "dsh-anchored-standard",
    "dsh-bili-agent", "dsh-crew", "dsh-memory-review", "dsh-neko-galgame",
    "dsh-openbiliclaw", "dsh-worktable-adapters", "dsh-xiao8-bridge", "sensenova-fallback-proxy",
}
KNOWN_AUDITED = {
    "dsh-worktable", "dsh-live2d-pets", "dsh-character-galgame", "dsh-memory-tools",
    "dsh-notify", "dsh-plugin-toggle", "dsh-plugin-toggle-ui", "dsh-project-done",
    "dsh-round-jump", "dsh-undo-savepoint", "dsh-sanitize",
}


def scan_root(root):
    items = []
    if not root.exists():
        return items
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        name = child.name
        if not (name.startswith("dsh-") or name.startswith("deepseek") or name.startswith("sensenova")):
            continue
        pkg = child / "package.json"
        readme = child / "README.md"
        scripts = [f.name for f in child.iterdir() if f.suffix.lower() in (".js", ".ts", ".py", ".ps1", ".mjs")][:5]
        size = 0
        for f in child.rglob("*"):
            try:
                if f.is_file():
                    size += f.stat().st_size
            except OSError:
                continue
        quarantined = False
        if QUARANTINE.exists():
            quarantined = (child.name in [x.name for x in QUARANTINE.iterdir() if x.is_dir()])
        items.append({
            "name": name,
            "path": str(child),
            "package_json": pkg.exists(),
            "readme": readme.exists(),
            "scripts": scripts,
            "size_mb": round(size / 1024 / 1024, 2),
            "quarantined": quarantined,
            "audit_status": ("locally_reviewed" if name in LOCAL_REVIEWED
                              else "known_audited" if name in KNOWN_AUDITED else "unknown"),
        })
    return items


def main():
    all_items = []
    for root in ROOTS:
        all_items.extend(scan_root(root))
    status = {}
    for it in all_items:
        status[it["audit_status"]] = status.get(it["audit_status"], 0) + 1
    print(json.dumps({
        "ok": True,
        "mode": "plugin_health_board",
        "plugin_count": len(all_items),
        "status_counts": status,
        "quarantined_count": sum(1 for x in all_items if x["quarantined"]),
        "plugins": all_items,
        "note": "audit_status=unknown means not yet reviewed; known list is local only",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
