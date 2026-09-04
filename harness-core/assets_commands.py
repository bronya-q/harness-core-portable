#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets_commands.py — 角色资产 / 知识域 / 工程工作区资产管理。

子命令：
  character list|install|activate|deactivate|remove|show
  knowledge list|sources
  workspace create|list|status|release
"""
import argparse
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
HARNESS_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness"
CHARACTERS_DIR = HARNESS_DIR / "characters"
ACTIVE_FILE = HARNESS_DIR / "active-character.json"
ACTIVE_BACKUP = HARNESS_DIR / "active-character.json.bak"
WORKSPACE_DIR = HARNESS_DIR / "workspaces"
KNOWLEDGE_SOURCES_FILE = HARNESS_DIR / "knowledge-sources.json"
EXAMPLE_SOURCES = ROOT / "knowledge-sources.example.json"


def ensure_dirs():
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_character(args):
    if not args:
        print("用法：harness.py character list|install|activate|deactivate|remove|show")
        return 1
    sub = args[0]
    rest = args[1:]
    if sub == "validate":
        return _cmd_character_validate(rest)
    if sub == "preview":
        return _cmd_character_preview(rest)
    if sub == "rollback":
        return _cmd_character_rollback()
    if sub == "list":
        ensure_dirs()
        items = []
        for d in sorted(CHARACTERS_DIR.iterdir()):
            if not d.is_dir():
                continue
            manifest = read_json(d / "package-manifest.json") or read_json(d / "character.json")
            items.append({
                "persona_id": manifest.get("persona_id", d.name),
                "display_name": manifest.get("display_name", d.name),
                "scope": manifest.get("scope", "character:" + d.name),
                "path": str(d),
                "installed": True,
            })
        active = read_json(ACTIVE_FILE)
        for it in items:
            it["active"] = (it["persona_id"] == active.get("persona_id"))
        print(json.dumps({"ok": True, "characters": items, "active": active.get("persona_id")},
                         ensure_ascii=False, indent=2))
        return 0
    if sub == "install":
        if not rest:
            print("用法：harness.py character install <path-to-hcp.zip-or-dir>")
            return 1
        src = Path(rest[0]).expanduser().resolve()
        if not src.exists():
            print(json.dumps({"ok": False, "error": "source_not_found", "path": str(src)}, ensure_ascii=False))
            return 1
        ensure_dirs()
        if src.is_file() and src.suffix.lower() == ".zip":
            with zipfile.ZipFile(src) as zf:
                tmp = HARNESS_DIR / "tmp-install"
                if tmp.exists():
                    shutil.rmtree(tmp)
                tmp.mkdir(parents=True, exist_ok=True)
                zf.extractall(tmp)
                # find manifest
                cand = [tmp / "package-manifest.json", tmp / "character.json"]
                manifest_path = next((p for p in cand if p.exists()), None)
                if not manifest_path:
                    # search one level
                    for p in tmp.rglob("package-manifest.json"):
                        manifest_path = p
                        break
                if not manifest_path:
                    print(json.dumps({"ok": False, "error": "manifest_not_found"}, ensure_ascii=False))
                    return 1
                manifest = read_json(manifest_path)
                pid = manifest.get("persona_id")
                if not pid:
                    print(json.dumps({"ok": False, "error": "missing_persona_id"}, ensure_ascii=False))
                    return 1
                dest = CHARACTERS_DIR / pid
                if dest.exists():
                    print(json.dumps({"ok": False, "error": "already_installed", "persona_id": pid}, ensure_ascii=False))
                    return 1
                if manifest_path.parent != tmp:
                    # copy the package directory (parent of manifest)
                    for item in manifest_path.parent.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, dest / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest / item.name)
                else:
                    for item in tmp.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, dest / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest / item.name)
                shutil.rmtree(tmp, ignore_errors=True)
                write_json(dest / "package-manifest.json", manifest)
                print(json.dumps({"ok": True, "persona_id": pid, "installed_at": str(dest)}, ensure_ascii=False))
                return 0
        # directory
        manifest_paths = [src / "package-manifest.json", src / "character.json"]
        manifest_path = next((p for p in manifest_paths if p.exists()), None)
        if not manifest_path:
            print(json.dumps({"ok": False, "error": "manifest_not_found", "path": str(src)}, ensure_ascii=False))
            return 1
        manifest = read_json(manifest_path)
        pid = manifest.get("persona_id")
        if not pid:
            print(json.dumps({"ok": False, "error": "missing_persona_id"}, ensure_ascii=False))
            return 1
        dest = CHARACTERS_DIR / pid
        if dest.exists():
            print(json.dumps({"ok": False, "error": "already_installed", "persona_id": pid}, ensure_ascii=False))
            return 1
        shutil.copytree(src, dest)
        write_json(dest / "package-manifest.json", manifest)
        print(json.dumps({"ok": True, "persona_id": pid, "installed_at": str(dest)}, ensure_ascii=False))
        return 0
    if sub == "activate":
        if not rest:
            print("用法：harness.py character activate <persona_id>")
            return 1
        pid = rest[0]
        manifest_path = CHARACTERS_DIR / pid / "package-manifest.json"
        if not manifest_path.exists():
            print(json.dumps({"ok": False, "error": "not_installed", "persona_id": pid}, ensure_ascii=False))
            return 1
        manifest = read_json(manifest_path)
        # 事务化激活：先备份当前 active，再写入；失败可回滚
        if ACTIVE_FILE.exists():
            shutil.copy2(ACTIVE_FILE, ACTIVE_BACKUP)
        try:
            write_json(ACTIVE_FILE, {"persona_id": pid, "scope": manifest.get("scope", "character:" + pid),
                                     "display_name": manifest.get("display_name", pid)})
        except Exception as e:
            if ACTIVE_BACKUP.exists():
                shutil.copy2(ACTIVE_BACKUP, ACTIVE_FILE)
            print(json.dumps({"ok": False, "error": "activation_failed", "detail": str(e)}, ensure_ascii=False))
            return 1
        print(json.dumps({"ok": True, "active": pid, "scope": manifest.get("scope"),
                          "rollback_available": ACTIVE_BACKUP.exists()}, ensure_ascii=False))
        return 0
    if sub == "deactivate":
        if ACTIVE_FILE.exists():
            ACTIVE_FILE.unlink()
        print(json.dumps({"ok": True, "active": None}, ensure_ascii=False))
        return 0
    if sub == "remove":
        if not rest:
            print("用法：harness.py character remove <persona_id>")
            return 1
        pid = rest[0]
        dest = CHARACTERS_DIR / pid
        if not dest.exists():
            print(json.dumps({"ok": False, "error": "not_installed", "persona_id": pid}, ensure_ascii=False))
            return 1
        shutil.rmtree(dest)
        if read_json(ACTIVE_FILE).get("persona_id") == pid:
            ACTIVE_FILE.unlink(missing_ok=True)
        print(json.dumps({"ok": True, "removed": pid}, ensure_ascii=False))
        return 0
    if sub == "show":
        if not rest:
            print("用法：harness.py character show <persona_id>")
            return 1
        pid = rest[0]
        manifest_path = CHARACTERS_DIR / pid / "package-manifest.json"
        if not manifest_path.exists():
            print(json.dumps({"ok": False, "error": "not_installed", "persona_id": pid}, ensure_ascii=False))
            return 1
        manifest = read_json(manifest_path)
        active = read_json(ACTIVE_FILE).get("persona_id") == pid
        manifest[
"active"] = active
        print(json.dumps({"ok": True, "manifest": manifest}, ensure_ascii=False, indent=2))
        return 0
    print("未知 character 子命令：" + sub)
    return 1


def _has_abs_path(text):
    bs = chr(92)
    return ("C:" + bs + "Users") in text or ("C:" + bs * 2 + "Users") in text or "/Users/" in text


def _validate_package(src, target):
    issues = []
    if not src.exists():
        return ["source_not_found"]
    manifest_path = None
    if src.is_file() and src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as zf:
            names = zf.namelist()
            for n in names:
                if n.startswith("../") or "\\" in n or n.startswith("/"):
                    issues.append("zip_path_traversal:" + n)
            for n in ("package-manifest.json", "character.json"):
                if n in names:
                    manifest_path = "virtual:" + n
                    break
            if not manifest_path:
                issues.append("manifest_not_found")
    else:
        for n in ("package-manifest.json", "character.json"):
            if (src / n).exists():
                manifest_path = src / n
                break
        if not manifest_path:
            issues.append("manifest_not_found")
    if not manifest_path:
        return issues
    manifest = read_json(src / "package-manifest.json") if src.is_dir() else {"_virtual": True}
    if target == "public":
        d = manifest.get("distribution")
        if d != "public":
            issues.append("distribution_not_public:" + str(d))
        if manifest.get("contains_private_memory"):
            issues.append("contains_private_memory")
        if manifest.get("contains_real_person_data"):
            issues.append("contains_real_person_data")
        if manifest.get("license_status") != "verified":
            issues.append("license_not_verified")
        if manifest.get("visibility") == "private_local":
            issues.append("private_local_manifest")
    if not manifest.get("persona_id"):
        issues.append("missing_persona_id")
    # absolute path scan in all text files
    root = src if src.is_dir() else Path(manifest_path)
    if src.is_dir():
        for f in src.rglob("*"):
            if f.is_file():
                try:
                    t = f.read_text(encoding="utf-8", errors="replace")
                    if _has_abs_path(t):
                        issues.append("absolute_path:" + str(f.relative_to(src)))
                except Exception:
                    pass
    elif str(manifest_path).startswith("virtual:"):
        # zip: read manifest content
        try:
            with zipfile.ZipFile(src) as zf:
                import json as _json
                m = _json.loads(zf.read(manifest_path.split(":")[-1]))
                if "persona_id" not in m:
                    issues.append("missing_persona_id")
        except Exception:
            issues.append("invalid_manifest")
    return issues


def _cmd_character_validate(args):
    target = "public"
    package = ""
    i = 0
    while i < len(args):
        if args[i] == "--package" and i + 1 < len(args):
            package = args[i + 1]; i += 2
        elif args[i] == "--target" and i + 1 < len(args):
            target = args[i + 1]; i += 2
        else:
            i += 1
    if not package:
        print("用法：harness.py character validate --package <path> [--target public]")
        return 1
    issues = _validate_package(Path(package).expanduser().resolve(), target)
    ok = not issues
    print(json.dumps({"ok": ok, "target": target, "package": package, "issues": issues},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


def _cmd_character_preview(args):
    package = args[0] if args else ""
    if not package:
        print("用法：harness.py character preview <path>")
        return 1
    src = Path(package).expanduser().resolve()
    if not src.exists():
        print(json.dumps({"ok": False, "error": "source_not_found", "path": str(src)}, ensure_ascii=False))
        return 1
    # dry-run preview: no writes
    manifest_path = src / "package-manifest.json" if src.is_dir() else None
    if src.is_file() and src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as zf:
            names = zf.namelist()
            for n in ("package-manifest.json", "character.json"):
                if n in names:
                    manifest_path = "virtual:" + n
                    break
    if not manifest_path:
        print(json.dumps({"ok": False, "error": "manifest_not_found"}, ensure_ascii=False))
        return 1
    if isinstance(manifest_path, Path):
        manifest = read_json(manifest_path)
    else:
        with zipfile.ZipFile(src) as zf:
            import json as _json
            manifest = _json.loads(zf.read(manifest_path.split(":")[-1]))
    print(json.dumps({"ok": True, "preview": True, "package": str(src), "manifest": manifest},
                     ensure_ascii=False, indent=2))
    return 0


def _cmd_character_rollback():
    if not ACTIVE_BACKUP.exists():
        print(json.dumps({"ok": False, "error": "no_backup"}, ensure_ascii=False))
        return 1
    prev = read_json(ACTIVE_BACKUP)
    write_json(ACTIVE_FILE, prev)
    ACTIVE_BACKUP.unlink(missing_ok=True)
    print(json.dumps({"ok": True, "active": prev.get("persona_id")}, ensure_ascii=False))
    return 0


def cmd_knowledge(args):
    if not args:
        print("用法：harness.py knowledge list|sources")
        return 1
    sub = args[0]
    if sub == "list":
        ensure_dirs()
        bindings = []
        for d in sorted(CHARACTERS_DIR.iterdir()):
            if not d.is_dir():
                continue
            manifest = read_json(d / "package-manifest.json") or read_json(d / "character.json")
            pid = manifest.get("persona_id", d.name)
            for kb in manifest.get("knowledge_bindings", []):
                bindings.append({"persona_id": pid, **kb})
        print(json.dumps({"ok": True, "bindings": bindings}, ensure_ascii=False, indent=2))
        return 0
    if sub == "sources":
        cfg = read_json(KNOWLEDGE_SOURCES_FILE) if KNOWLEDGE_SOURCES_FILE.exists() else read_json(EXAMPLE_SOURCES)
        sources = cfg.get("sources", []) if isinstance(cfg, dict) else cfg
        print(json.dumps({"ok": True, "config": str(KNOWLEDGE_SOURCES_FILE if KNOWLEDGE_SOURCES_FILE.exists() else EXAMPLE_SOURCES),
                          "sources": sources}, ensure_ascii=False, indent=2))
        return 0
    print("未知 knowledge 子命令：" + sub)
    return 1


def cmd_workspace(args):
    if not args:
        print("用法：harness.py workspace create|list|status|release")
        return 1
    sub = args[0]
    rest = args[1:]
    if sub == "create":
        name = role = ""
        allowed = []
        for i, a in enumerate(rest):
            if a == "--name" and i + 1 < len(rest):
                name = rest[i + 1]
            if a == "--role" and i + 1 < len(rest):
                role = rest[i + 1]
            if a == "--allowed" and i + 1 < len(rest):
                allowed = [x.strip() for x in rest[i + 1].split(",") if x.strip()]
        if not name:
            print("用法：harness.py workspace create --name <name> --role <role> [--allowed paths,...]")
            return 1
        ensure_dirs()
        ws = WORKSPACE_DIR / name
        if ws.exists():
            print(json.dumps({"ok": False, "error": "workspace_exists", "name": name}, ensure_ascii=False))
            return 1
        ws.mkdir(parents=True, exist_ok=True)
        lease = {"workspace": name, "role": role, "allowed_paths": allowed,
                 "read_only_paths": [], "forbidden_paths": ["*.db", "production_approval.json", ".env"],
                 "status": "active", "actual_execution": False}
        write_json(ws / "workspace.json", lease)
        print(json.dumps({"ok": True, "workspace": name, "path": str(ws), "lease": lease}, ensure_ascii=False, indent=2))
        return 0
    if sub == "list":
        ensure_dirs()
        items = []
        for d in sorted(WORKSPACE_DIR.iterdir()):
            if d.is_dir():
                items.append(read_json(d / "workspace.json"))
        print(json.dumps({"ok": True, "workspaces": items}, ensure_ascii=False, indent=2))
        return 0
    if sub == "status":
        name = rest[0] if rest else ""
        if not name:
            print("用法：harness.py workspace status <name>")
            return 1
        p = WORKSPACE_DIR / name / "workspace.json"
        if not p.exists():
            print(json.dumps({"ok": False, "error": "workspace_not_found", "name": name}, ensure_ascii=False))
            return 1
        print(json.dumps({"ok": True, "workspace": read_json(p)}, ensure_ascii=False, indent=2))
        return 0
    if sub == "release":
        name = rest[0] if rest else ""
        if not name:
            print("用法：harness.py workspace release <name>")
            return 1
        p = WORKSPACE_DIR / name
        if not p.exists():
            print(json.dumps({"ok": False, "error": "workspace_not_found", "name": name}, ensure_ascii=False))
            return 1
        shutil.rmtree(p)
        print(json.dumps({"ok": True, "released": name}, ensure_ascii=False))
        return 0
    print("未知 workspace 子命令：" + sub)
    return 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    if cmd == "character":
        return cmd_character(sys.argv[2:])
    if cmd == "knowledge":
        return cmd_knowledge(sys.argv[2:])
    if cmd == "workspace":
        return cmd_workspace(sys.argv[2:])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
