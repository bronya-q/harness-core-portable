#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""control_commands.py — 用户控制入口（memory / privacy / backup / feedback）。

全部走现有底层：
- memory 使用 notebook.py（list/quote/note/restore/forget）
- privacy 使用本地数据状态与导出
- backup 复制本地 SQLite 文件
- feedback 生成自愿导出的脱敏反馈模板
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"
BACKUP_ROOT = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness-backups"
PRIVACY_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness-dashboard"


def _run(script, *args):
    p = subprocess.run([sys.executable, str(SKILL / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"ok": False, "raw": p.stdout[-300:], "stderr": p.stderr[-300:]}


def cmd_memory(args):
    if not args:
        print("用法：harness.py memory list|explain|correct|restore|forget ...")
        return 1
    sub = args[0]
    rest = args[1:]
    if sub == "list":
        scope = ""
        for i, a in enumerate(rest):
            if a == "--scope" and i + 1 < len(rest):
                scope = rest[i + 1]
        if not scope:
            print("用法：harness.py memory list --scope <scope>")
            return 1
        r = _run("notebook.py", "list", "--scope", scope)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    if sub == "explain":
        nid = ""
        for i, a in enumerate(rest):
            if a == "--id" and i + 1 < len(rest):
                nid = rest[i + 1]
        if not nid:
            print("用法：harness.py memory explain --id <id>")
            return 1
        r = _run("notebook.py", "quote", "--id", nid)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    if sub == "correct":
        scope = txt = nid = ""
        for i, a in enumerate(rest):
            if a == "--scope" and i + 1 < len(rest):
                scope = rest[i + 1]
            if a == "--id" and i + 1 < len(rest):
                nid = rest[i + 1]
            if a == "--text" and i + 1 < len(rest):
                txt = rest[i + 1]
        if not scope or not txt:
            print("用法：harness.py memory correct --scope <scope> --id <id> --text <新内容>")
            return 1
        r = _run("notebook.py", "note", "--scope", scope, "--text", "corrected: " + txt, "--kind", "manual")
        # 自动归档旧记录
        archived = False
        if nid:
            ar = _run("notebook.py", "forget", "--id", nid)
            archived = ar.get("ok") is True
        print(json.dumps({"ok": r.get("ok"), "scope": scope, "new_id": r.get("id"),
                          "old_archived": archived, "old_id": nid,
                          "note": "correction recorded; old id=%s archived=%s" % (nid, archived)}, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    if sub == "restore":
        scope = ver = ""
        for i, a in enumerate(rest):
            if a == "--scope" and i + 1 < len(rest):
                scope = rest[i + 1]
            if a == "--version" and i + 1 < len(rest):
                ver = rest[i + 1]
        if not scope or not ver:
            print("用法：harness.py memory restore --scope <scope> --version <n>")
            return 1
        r = _run("notebook.py", "restore", "--scope", scope, "--version", ver)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    if sub == "forget":
        nid = ""
        for i, a in enumerate(rest):
            if a == "--id" and i + 1 < len(rest):
                nid = rest[i + 1]
        if not nid:
            print("用法：harness.py memory forget --id <id>")
            return 1
        r = _run("notebook.py", "forget", "--id", nid)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    print("未知 memory 子命令：" + sub)
    return 1


def cmd_privacy(args):
    if not args:
        print("用法：harness.py privacy status|export|reset-demo")
        return 1
    sub = args[0]
    if sub == "status":
        total = 0
        names = []
        for name in ["memory.db", "notebooks.db", "story_core.db", "humanization_sidecar.db",
                     "continuity_sidecar.db", "atomic_facts_sidecar.db", "nine_dim_vectors.db"]:
            p = DATA_DIR / name
            if p.exists():
                names.append(name)
                total += p.stat().st_size / (1024 * 1024)
        print(json.dumps({"ok": True, "data_dir": str(DATA_DIR), "files": names,
                          "total_mb": round(total, 2), "auto_upload": False}, ensure_ascii=False, indent=2))
        return 0
    if sub == "export":
        PRIVACY_DIR.mkdir(parents=True, exist_ok=True)
        out = PRIVACY_DIR / "privacy-export.json"
        d = {"version": 1, "platform": sys.platform, "python": sys.version.split()[0],
             "data_dir": str(DATA_DIR), "auto_upload": False, "aggregate_only": True,
             "contains_pii": False, "exported_at": datetime.now().isoformat()}
        out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(out)}, ensure_ascii=False, indent=2))
        return 0
    if sub == "reset-demo":
        return subprocess.call([sys.executable, str(SKILL / "demo_experience.py"), "--reset"])
    print("未知 privacy 子命令：" + sub)
    return 1

def cmd_backup(args):
    if not args:
        print("用法：harness.py backup create|list|restore <name>")
        return 1
    sub = args[0]
    if sub == "create":
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = BACKUP_ROOT / ts
        dest.mkdir(parents=True, exist_ok=True)
        copied = []
        for name in ["memory.db", "notebooks.db", "story_core.db", "humanization_sidecar.db",
                     "continuity_sidecar.db", "atomic_facts_sidecar.db", "nine_dim_vectors.db",
                     "runtime-policy.json"]:
            p = DATA_DIR / name
            if p.exists():
                shutil.copy2(p, dest / name)
                copied.append(name)
        meta = {"backup": ts, "created_at": datetime.now().isoformat(), "files": copied}
        (dest / "backup.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "backup": ts, "dest": str(dest), "files": copied},
                         ensure_ascii=False, indent=2))
        return 0
    if sub == "list":
        if not BACKUP_ROOT.exists():
            print(json.dumps({"ok": True, "backups": []}, ensure_ascii=False))
            return 0
        names = sorted([d.name for d in BACKUP_ROOT.iterdir() if d.is_dir()])
        print(json.dumps({"ok": True, "backups": names}, ensure_ascii=False))
        return 0
    if sub == "restore":
        name = args[1] if len(args) > 1 else ""
        if not name:
            print("用法：harness.py backup restore <name>")
            return 1
        src = BACKUP_ROOT / name
        if not src.exists():
            print(json.dumps({"ok": False, "error": "backup_not_found", "backup": name}, ensure_ascii=False))
            return 1
        restored = []
        for p in src.iterdir():
            if p.is_file() and p.name != "backup.json":
                shutil.copy2(p, DATA_DIR / p.name)
                restored.append(p.name)
        print(json.dumps({"ok": True, "backup": name, "restored": restored}, ensure_ascii=False, indent=2))
        return 0
    print("未知 backup 子命令：" + sub)
    return 1


def cmd_feedback(args):
    if not args or args[0] != "export":
        print("用法：harness.py feedback export --redacted")
        return 1
    if len(args) < 2 or args[1] != "--redacted":
        print("用法：harness.py feedback export --redacted")
        return 1
    PRIVACY_DIR.mkdir(parents=True, exist_ok=True)
    out = PRIVACY_DIR / "feedback-redacted.json"
    d = {"version": 1, "system": {"platform": sys.platform, "python": sys.version.split()[0],
                                  "model": "undisclosed"},
         "results": {"demo_completed": True, "included_content": False},
         "note": "不会自动发送；请检查后再手动附到 issue。"}
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(out)}, ensure_ascii=False, indent=2))
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    rest = sys.argv[2:]
    if cmd == "memory":
        return cmd_memory(rest)
    if cmd == "privacy":
        return cmd_privacy(rest)
    if cmd == "backup":
        return cmd_backup(rest)
    if cmd == "feedback":
        return cmd_feedback(rest)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
