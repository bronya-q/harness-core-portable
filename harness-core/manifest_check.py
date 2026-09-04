#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manifest_check.py — 校验统一 manifest 与真实运行面是否一致。

只读；发现漂移只报告，不自动修改。
"""
import json
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))
import runtime_resolver as rr  # noqa: E402

MANIFEST = SKILL / "manifest.json"


def main():
    if not MANIFEST.exists():
        print(json.dumps({"ok": False, "error": "manifest.json missing; run generate_manifest.py first"},
                         ensure_ascii=False, indent=2))
        return 1
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    issues = []
    # 1) persona 引用面
    for pid, entry in m.get("personas", {}).items():
        if not Path(entry["source"]).exists():
            issues.append("missing_source:%s:%s" % (pid, entry["source"]))
        if not Path(entry["entrypoint"]).exists():
            issues.append("missing_entrypoint:%s:%s" % (pid, entry["entrypoint"]))
    # 2) resolver 与 manifest 一致性
    for pid, e in rr.ENTRIES.items():
        me = m.get("personas", {}).get(pid)
        if not me:
            issues.append("manifest_missing_persona:%s" % pid)
            continue
        for key in ("scope", "model", "source", "entrypoint"):
            mv = str(me.get(key) or "")
            rv = str(e.get(key) or "")
            if rv != mv:
                issues.append("drift:%s:%s:manifest=%s resolver=%s" % (pid, key, mv, rv))
    # 3) profiles
    for prof in m.get("profiles", []):
        pkg = Path.home() / ".dsh" / "profiles" / prof / "package.json"
        if not pkg.exists():
            issues.append("missing_profile:%s" % prof)
    # 4) dsh
    if not shutil.which("dsh"):
        issues.append("dsh_not_in_path")
    # 5) policy files
    for name, path in m.get("policy_files", {}).items():
        if not Path(path).exists():
            issues.append("missing_policy_file:%s" % name)
    # 6) mind_evolution 共享沉淀面
    me = m.get("mind_evolution")
    if not me:
        issues.append("manifest_missing_mind_evolution")
    else:
        for key in ("root", "readme", "index", "assets"):
            p = str(me.get(key) or "")
            if not Path(p).exists():
                issues.append("missing_mind_evolution_%s:%s" % (key, p))
        for name, p in me.get("scripts", {}).items():
            if not Path(str(p)).exists():
                issues.append("missing_mind_evolution_script:%s:%s" % (name, p))
    print(json.dumps({"ok": not issues, "issues": issues,
                      "dsh_version": m.get("dsh_version"),
                      "persona_count": len(m.get("personas", {}))},
                     ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
