#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets_commands.py — 角色资产 / 知识域 / 工程工作区资产管理。

子命令：
  character list|install|activate|deactivate|remove|show
  knowledge list|sources|health|mount|delegate
  workspace create|list|status|release
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SKILL = Path(__file__).resolve().parent
HARNESS_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness"
CHARACTERS_DIR = HARNESS_DIR / "characters"
ACTIVE_FILE = HARNESS_DIR / "active-character.json"
ACTIVE_BACKUP = HARNESS_DIR / "active-character.json.bak"
WORKSPACE_DIR = HARNESS_DIR / "workspaces"
ACTIVE_MODE_FILE = HARNESS_DIR / "active-mode.json"
STATE_FILE = HARNESS_DIR / "character-state.json"
LOCK_FILE = HARNESS_DIR / "activate.lock"
KNOWLEDGE_SOURCES_FILE = HARNESS_DIR / "knowledge-sources.json"
EXAMPLE_SOURCES = ROOT / "knowledge-sources.example.json"
KNOWLEDGE_MOUNTS_FILE = HARNESS_DIR / "knowledge-mounts.json"


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


def _validate_manifest_core(manifest):
    issues = []
    if "schema_version" not in manifest:
        issues.append("missing_schema_version")
    elif not isinstance(manifest.get("schema_version"), int) or manifest["schema_version"] < 1:
        issues.append("invalid_schema_version")
    if "minimum_core_version" in manifest:
        v = manifest.get("minimum_core_version")
        if not isinstance(v, (str, int)):
            issues.append("invalid_minimum_core_version")
    if "persona_id" not in manifest:
        issues.append("missing_persona_id")
    return issues


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
    if sub == "status":
        return _cmd_character_status()
    if sub == "preflight":
        pid = rest[0] if rest else ""
        if not pid:
            print("用法：harness.py character preflight <persona_id>")
            return 1
        return _cmd_character_preflight(pid)
    if sub == "recover":
        LOCK_FILE.unlink(missing_ok=True)
        if not ACTIVE_BACKUP.exists():
            ACTIVE_FILE.unlink(missing_ok=True)
            _write_state("recovered", None, "no backup; cleared active and lock")
            print(json.dumps({"ok": True, "active": None, "recovered": True,
                              "note": "无备份；已清除锁与激活标记。"}, ensure_ascii=False))
            return 0
        prev = read_json(ACTIVE_BACKUP)
        write_json(ACTIVE_FILE, prev)
        ACTIVE_BACKUP.unlink(missing_ok=True)
        _write_state("active", prev.get("persona_id"), "recovered from backup")
        try:
            from runtime_hotload import write_context
            write_context(prev.get("persona_id"), None, {"recovered": True})
        except Exception:
            pass
        print(json.dumps({"ok": True, "active": prev.get("persona_id"), "recovered": True}, ensure_ascii=False))
        return 0
    if sub == "mode":
        return _cmd_character_mode(rest)
    if sub == "card-import":
        path = output = ""
        yes = False
        i = 0
        while i < len(rest):
            if rest[i] in ("--output", "-o") and i + 1 < len(rest):
                output = rest[i + 1]; i += 2
            elif rest[i] == "--yes":
                yes = True; i += 1
            elif rest[i] == "--package":
                path = rest[i + 1]; i += 2
            elif i < len(rest):
                path = rest[i]; i += 1
            else:
                i += 1
        try:
            from character_workbench import read_card, map_card, write_import
            card = read_card(path)
            m = map_card(card)
            return write_import(m, output or "hcp-import", yes)
        except Exception as e:
            print(json.dumps({"ok": False, "error": type(e).__name__, "detail": str(e)}, ensure_ascii=False))
            return 1
    if sub == "build":
        corpus = output = ""
        approve = False
        i = 0
        while i < len(rest):
            if rest[i] == "--from" and i + 1 < len(rest):
                corpus = rest[i + 1]; i += 2
            elif rest[i] == "--output" and i + 1 < len(rest):
                output = rest[i + 1]; i += 2
            elif rest[i] == "--approve":
                approve = True; i += 1
            else:
                i += 1
        try:
            from character_workbench import build_draft
            return build_draft(corpus, output or "draft-output", approve)
        except Exception as e:
            print(json.dumps({"ok": False, "error": type(e).__name__, "detail": str(e)}, ensure_ascii=False))
            return 1
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
            issues = _validate_package(src, "any")
            if issues:
                print(json.dumps({"ok": False, "error": "package_validation_failed", "issues": issues}, ensure_ascii=False))
                return 1
            with zipfile.ZipFile(src) as zf:
                tmp = HARNESS_DIR / "tmp-install"
                if tmp.exists():
                    shutil.rmtree(tmp)
                tmp.mkdir(parents=True, exist_ok=True)
                _safe_extract_zip(zf, tmp)
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
                core_issues = _validate_manifest_core(manifest)
                if core_issues:
                    print(json.dumps({"ok": False, "error": "package_schema_required", "issues": core_issues}, ensure_ascii=False))
                    return 1
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
        core_issues = _validate_manifest_core(manifest)
        if core_issues:
            print(json.dumps({"ok": False, "error": "package_schema_required", "issues": core_issues}, ensure_ascii=False))
            return 1
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
            print("用法：harness.py character activate <persona_id> [--simulate-failure] [--simulate-crash]")
            return 1
        pid = rest[0]
        simulate_failure = "--simulate-failure" in rest
        simulate_crash = "--simulate-crash" in rest
        manifest_path = CHARACTERS_DIR / pid / "package-manifest.json"
        if not manifest_path.exists():
            print(json.dumps({"ok": False, "error": "not_installed", "persona_id": pid}, ensure_ascii=False))
            return 1
        manifest = read_json(manifest_path)
        # 简单并发锁
        crash_simulated = False
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except Exception:
            print(json.dumps({"ok": False, "error": "lock_held"}, ensure_ascii=False))
            return 1
        try:
            _write_state("preflight", pid, "validating package")
            _write_state("activating", pid, "backing up current active")
            if ACTIVE_FILE.exists():
                shutil.copy2(ACTIVE_FILE, ACTIVE_BACKUP)
            if simulate_failure:
                raise RuntimeError("simulated_activation_failure")
            write_json(ACTIVE_FILE, {"persona_id": pid, "scope": manifest.get("scope", "character:" + pid),
                                     "display_name": manifest.get("display_name", pid)})
            if simulate_crash:
                crash_simulated = True
                _write_state("crash_simulated", pid, "simulated crash; lock intentionally left")
                print(json.dumps({"ok": False, "status": "crash_simulated",
                                  "note": "模拟崩溃：已写入 active 但保留锁，请运行 `character recover` 恢复。"}, ensure_ascii=False))
                return 1
            _write_state("active", pid, "activation complete")
        except Exception as e:
            if ACTIVE_BACKUP.exists():
                shutil.copy2(ACTIVE_BACKUP, ACTIVE_FILE)
            _write_state("activation_failed", pid, str(e))
            print(json.dumps({"ok": False, "error": "activation_failed", "detail": str(e)}, ensure_ascii=False))
            return 1
        finally:
            if not crash_simulated:
                try:
                    LOCK_FILE.unlink()
                except Exception:
                    pass
        try:
            from runtime_hotload import write_context
            write_context(pid, None, {"scope": manifest.get("scope")})
        except Exception:
            pass
        print(json.dumps({"ok": True, "active": pid, "scope": manifest.get("scope"),
                          "rollback_available": ACTIVE_BACKUP.exists()}, ensure_ascii=False))
        return 0
    if sub == "deactivate":
        if not _confirm_risk("character deactivate", "清除当前激活角色标记。", yes="--yes" in rest):
            print(json.dumps({"ok": False, "status": "cancelled"}, ensure_ascii=False))
            return 1
        if ACTIVE_FILE.exists():
            ACTIVE_FILE.unlink()
        print(json.dumps({"ok": True, "active": None}, ensure_ascii=False))
        return 0
    if sub == "remove":
        if not rest:
            print("用法：harness.py character remove <persona_id> [--yes]")
            return 1
        pid = rest[0]
        dest = CHARACTERS_DIR / pid
        if not dest.exists():
            print(json.dumps({"ok": False, "error": "not_installed", "persona_id": pid}, ensure_ascii=False))
            return 1
        if not _confirm_risk("character remove", "删除角色资产目录：%s" % pid, yes="--yes" in rest):
            print(json.dumps({"ok": False, "status": "cancelled", "persona_id": pid}, ensure_ascii=False))
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


def _safe_extract_zip(zf, dest):
    """安全解压：拒绝路径穿越、绝对路径和符号链接。"""
    dest = Path(dest).resolve()
    for info in zf.infolist():
        name = info.filename.replace(chr(92), "/")
        target = (dest / name).resolve()
        if not str(target).startswith(str(dest)):
            raise ValueError("zip_path_traversal:" + name)
        if name.startswith("/") or ".." in name.split("/"):
            raise ValueError("zip_path_traversal:" + name)
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError("zip_symlink:" + name)
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src_f, open(target, "wb") as dst_f:
                shutil.copyfileobj(src_f, dst_f)


def _validate_package(src, target):
    issues = []
    if not src.exists():
        return ["source_not_found"]
    manifest_path = None
    if src.is_file() and src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as zf:
            names = zf.namelist()
            if len(names) > 5000:
                issues.append("zip_too_many_files:" + str(len(names)))
            total_size = 0
            for info in zf.infolist():
                n = info.filename.replace(chr(92), "/")
                if n.startswith("../") or "\\" in n or n.startswith("/") or ".." in n.split("/"):
                    issues.append("zip_path_traversal:" + n)
                if ":" in n:
                    issues.append("zip_ads:" + n)
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    issues.append("zip_symlink:" + n)
                if n.lower().endswith(".zip"):
                    issues.append("nested_zip:" + n)
                ext = n.rsplit(".", 1)[-1].lower() if "." in n else ""
                if target == "public" and ext in ("html", "htm", "svg"):
                    issues.append("untrusted_html_svg:" + n)
                total_size += info.file_size
                if n.lower().endswith((".json", ".jsonl")):
                    raw = zf.read(info)
                    try:
                        json.loads(raw.decode("utf-8"))
                    except Exception:
                        issues.append("mime_mismatch_json:" + n)
                elif n.lower().endswith(".png"):
                    sig = zf.read(info)[:8]
                    if sig != bytes([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]):
                        issues.append("mime_mismatch_png:" + n)
                if target == "public" and n.rsplit(".", 1)[-1].lower() in ("exe", "bat", "cmd", "sh", "ps1", "com", "py", "js", "mjs", "ts", "rb", "pl"):
                    issues.append("executable_script:" + n)
            if total_size > 200 * 1024 * 1024:
                issues.append("zip_too_large:" + str(total_size))
            with zipfile.ZipFile(src) as zf2:
                try:
                    compressed = sum(i.compress_size for i in zf2.infolist())
                    if compressed > 0 and total_size / compressed > 100:
                        issues.append("zip_compression_ratio_too_high:" + str(round(total_size / compressed, 2)))
                except Exception:
                    pass
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
    if "schema_version" not in manifest or not isinstance(manifest.get("schema_version"), int) or manifest["schema_version"] < 1:
        issues.append("missing_schema_version")
    if "minimum_core_version" in manifest and not isinstance(manifest.get("minimum_core_version"), (str, int)):
        issues.append("invalid_minimum_core_version")
    # absolute path scan in all text files
    root = src if src.is_dir() else Path(manifest_path)
    if src.is_dir():
        _dir_files = [f for f in src.rglob("*") if f.is_file()]
        if len(_dir_files) > 5000:
            issues.append("dir_too_many_files:" + str(len(_dir_files)))
        _dir_size = sum(f.stat().st_size for f in _dir_files)
        if _dir_size > 200 * 1024 * 1024:
            issues.append("dir_too_large:" + str(_dir_size))
        for f in _dir_files:
            if f.is_file():
                ext = f.suffix.lower().lstrip(".")
                if target == "public" and ext in ("html", "htm", "svg"):
                    issues.append("untrusted_html_svg:" + str(f.relative_to(src)))
                if target == "public" and ext in ("exe", "bat", "cmd", "sh", "ps1", "com", "py", "js", "mjs", "ts", "rb", "pl"):
                    issues.append("executable_script:" + str(f.relative_to(src)))
                import json as _json
                if f.suffix.lower() in (".json", ".jsonl"):
                    try:
                        _json.loads(f.read_text(encoding="utf-8"))
                    except Exception:
                        issues.append("mime_mismatch_json:" + str(f.relative_to(src)))
                if f.suffix.lower() == ".png" and f.read_bytes()[:8] != bytes([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]):
                    issues.append("mime_mismatch_png:" + str(f.relative_to(src)))
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


def _write_state(state, persona_id=None, note=None):
    data = read_json(STATE_FILE) if STATE_FILE.exists() else {}
    history = data.get("history", [])
    history.append({"state": state, "persona_id": persona_id, "note": note,
                    "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")})
    write_json(STATE_FILE, {"state": state, "persona_id": persona_id, "note": note, "history": history[-20:]})
    return data


def _cmd_character_status():
    data = read_json(STATE_FILE) if STATE_FILE.exists() else {}
    cur = read_json(ACTIVE_FILE) if ACTIVE_FILE.exists() else {}
    print(json.dumps({"ok": True, "state": data.get("state"), "note": data.get("note"),
                      "active": cur}, ensure_ascii=False, indent=2))
    return 0


def _cmd_character_preflight(pid):
    manifest_path = CHARACTERS_DIR / pid / "package-manifest.json"
    if not manifest_path.exists():
        print(json.dumps({"ok": False, "error": "not_installed", "persona_id": pid}, ensure_ascii=False))
        return 1
    manifest = read_json(manifest_path)
    issues = []
    if not manifest.get("persona_id"):
        issues.append("missing_persona_id")
    if manifest.get("permissions_requested", {}).get("autonomous"):
        issues.append("autonomous_requested")
    print(json.dumps({"ok": not issues, "preflight": True, "persona_id": pid, "issues": issues}, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def _demo_modes(pid):
    candidates = [pid + "-modes.json", pid.replace("demo-", "") + "-modes.json"]
    for name in candidates:
        p = SKILL / "personas" / "demo-modes" / name
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("modes", [])
            except Exception:
                pass
    return []


def _modes_for(pid):
    p = CHARACTERS_DIR / pid / "modes.json"
    if p.exists():
        return read_json(p).get("modes", [])
    return _demo_modes(pid)


def _cmd_character_mode(args):
    if not args:
        print("用法：harness.py character mode list|switch|current|diff [--persona <id>] [--mode <id>] [--mode-a <id>] [--mode-b <id>]")
        return 1
    sub = args[0]
    pid = ""
    mode_id = ""
    i = 1
    while i < len(args):
        if args[i] == "--persona" and i + 1 < len(args):
            pid = args[i + 1]; i += 2
        elif args[i] == "--mode" and i + 1 < len(args):
            mode_id = args[i + 1]; i += 2
        else:
            i += 1
    if sub == "list":
        if not pid:
            print("用法：harness.py character mode list --persona <id>")
            return 1
        modes = _modes_for(pid)
        print(json.dumps({"ok": True, "persona_id": pid, "modes": modes}, ensure_ascii=False, indent=2))
        return 0
    if sub == "current":
        cur = read_json(ACTIVE_MODE_FILE) if ACTIVE_MODE_FILE.exists() else {}
        print(json.dumps({"ok": True, "active_mode": cur}, ensure_ascii=False, indent=2))
        return 0
    if sub == "switch":
        if not pid or not mode_id:
            print("用法：harness.py character mode switch --persona <id> --mode <id>")
            return 1
        modes = _modes_for(pid)
        match = next((m for m in modes if m.get("mode_id") == mode_id), None)
        if not match:
            print(json.dumps({"ok": False, "error": "mode_not_found", "persona_id": pid, "mode": mode_id}, ensure_ascii=False))
            return 1
        # 事务化保存当前 mode
        if ACTIVE_MODE_FILE.exists():
            shutil.copy2(ACTIVE_MODE_FILE, HARNESS_DIR / "active-mode.json.bak")
        write_json(ACTIVE_MODE_FILE, {"persona_id": pid, "mode_id": mode_id, "display_name": match.get("display_name")})
        try:
            from runtime_hotload import write_context
            write_context(pid, mode_id, {"display_name": match.get("display_name"), "effects": match.get("effect")})
        except Exception:
            pass
        print(json.dumps({"ok": True, "persona_id": pid, "mode_id": mode_id, "effects": match.get("effect")}, ensure_ascii=False))
        return 0
    if sub == "diff":
        mode_a = mode_b = ""
        for i, a in enumerate(args):
            if a == "--mode-a" and i + 1 < len(args):
                mode_a = args[i + 1]
            if a == "--mode-b" and i + 1 < len(args):
                mode_b = args[i + 1]
        if not pid or not mode_a or not mode_b:
            print("用法：harness.py character mode diff --persona <id> --mode-a <a> --mode-b <b>")
            return 1
        modes = _modes_for(pid)
        ma = next((m for m in modes if m.get("mode_id") == mode_a), None)
        mb = next((m for m in modes if m.get("mode_id") == mode_b), None)
        if not ma or not mb:
            print(json.dumps({"ok": False, "error": "mode_not_found", "persona_id": pid,
                              "a": mode_a, "b": mode_b}, ensure_ascii=False))
            return 1
        def _norm(m):
            return {k: v for k, v in m.items() if k in ("display_name", "capabilities", "effect",
                                                        "knowledge_access", "filesystem_write",
                                                        "process_execution", "network", "autonomous")}
        diff = {"a": _norm(ma), "b": _norm(mb)}
        diff["differences"] = {}
        for k in set(diff["a"]) | set(diff["b"]):
            if diff["a"].get(k) != diff["b"].get(k):
                diff["differences"][k] = {"a": diff["a"].get(k), "b": diff["b"].get(k)}
        print(json.dumps({"ok": True, "persona_id": pid, "mode_a": mode_a, "mode_b": mode_b,
                          **diff}, ensure_ascii=False, indent=2))
        return 0
    print("未知 character mode 子命令：" + sub)
    return 1


def _load_sources():
    cfg = read_json(KNOWLEDGE_SOURCES_FILE) if KNOWLEDGE_SOURCES_FILE.exists() else read_json(EXAMPLE_SOURCES)
    sources = cfg.get("sources", []) if isinstance(cfg, dict) else cfg
    return sources or []


def _role_bindings():
    ensure_dirs()
    bindings = []
    for d in sorted(CHARACTERS_DIR.iterdir()):
        if not d.is_dir():
            continue
        manifest = read_json(d / "package-manifest.json") or read_json(d / "character.json")
        pid = manifest.get("persona_id", d.name)
        for kb in manifest.get("knowledge_bindings", []):
            bindings.append({"persona_id": pid, **kb})
    return bindings


def _expand_root(root):
    if not root:
        return None
    try:
        return Path(os.path.expanduser(str(root)))
    except Exception:
        return None


def _load_mounts():
    return read_json(KNOWLEDGE_MOUNTS_FILE) or {"schema_version": 1, "mounts": []}


def _save_mounts(mounts):
    mounts.setdefault("schema_version", 1)
    mounts.setdefault("mounts", [])
    write_json(KNOWLEDGE_MOUNTS_FILE, mounts)


def _knowledge_health(source_id=None):
    sources = _load_sources()
    checks = []
    for src in sources:
        sid = src.get("source_id", "")
        if source_id and sid != source_id:
            continue
        root = _expand_root(src.get("root"))
        exists = bool(root and root.exists())
        is_dir = bool(root and root.is_dir())
        readable = bool(root and is_dir and os.access(str(root), os.R_OK))
        stewards = src.get("stewards", []) or []
        bound_roles = []
        for b in _role_bindings():
            if b.get("domain_id") == sid or b.get("source_ref") == sid:
                if b.get("persona_id") not in bound_roles:
                    bound_roles.append(b.get("persona_id"))
        if not exists:
            status = "missing"
        elif not is_dir:
            status = "not_dir"
        elif not readable:
            status = "unreadable"
        else:
            status = "ok"
        file_count = 0
        if root and root.is_dir():
            try:
                file_count = sum(1 for p in root.iterdir() if p.is_file())
            except Exception:
                pass
        if bool(src.get("private", True)) and src.get("default_access", "deny") == "deny":
            credibility = "private_high_trust"
        elif bool(src.get("private", True)):
            credibility = "private_medium"
        else:
            credibility = "portable_public"
        idx_path = HARNESS_DIR / "knowledge-index.json"
        idx_data = read_json(idx_path) or {}
        idx_src = (idx_data.get("sources", {}) or {}).get(sid) or {}
        checks.append({"source_id": sid, "display_name": src.get("display_name", ""),
                       "file_count": file_count, "credibility": credibility,
                       "indexed": bool(idx_src), "indexed_file_count": idx_src.get("file_count", 0),
                       "root": str(root) if root else None,
                       "exists": exists, "is_dir": is_dir, "readable": readable,
                       "status": status, "private": bool(src.get("private", True)),
                       "portable": bool(src.get("portable", False)),
                       "default_access": src.get("default_access", "deny"),
                       "stewards": stewards, "bound_roles": bound_roles})
    return {"ok": bool(checks) and all(c["status"] == "ok" for c in checks),
            "checks": checks}


def _knowledge_mount(role, domain):
    sources = _load_sources()
    src = next((s for s in sources if s.get("source_id") == domain), None)
    if not src:
        return {"ok": False, "error": "unknown_domain", "domain": domain}
    bindings = _role_bindings()
    role_ok = any(b.get("persona_id") == role for b in bindings)
    if not role_ok:
        return {"ok": False, "error": "unknown_role_binding", "role": role, "domain": domain}
    stewards = src.get("stewards", []) or []
    if role not in stewards and src.get("default_access", "deny") == "deny":
        return {"ok": False, "error": "default_access_deny", "role": role, "domain": domain}
    mounts = _load_mounts()
    recorded = False
    for m in mounts.get("mounts", []):
        if m.get("persona_id") == role and m.get("source_id") == domain:
            m.update({"mount_mode": "read_only", "state": "registered",
                      "mounted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                      "note": "只读挂载状态登记；不是完整知识桥。"})
            recorded = True
            break
    if not recorded:
        mounts.setdefault("mounts", []).append({
            "persona_id": role, "source_id": domain, "mount_mode": "read_only",
            "state": "registered", "mounted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "note": "只读挂载状态登记；不是完整知识桥。",
        })
    _save_mounts(mounts)
    return {"ok": True, "role": role, "domain": domain, "source": src.get("display_name", domain),
            "mount_mode": "read_only", "state": "registered",
            "note": "只读挂载状态登记；不是完整知识桥。"}


def _knowledge_delegate(question, current_role=None):
    q = (question or "").strip().lower()
    if not q:
        return {"ok": False, "error": "missing_question"}
    sources = _load_sources()
    bindings = _role_bindings()
    candidates = []
    for src in sources:
        words = set()
        for v in [src.get("source_id"), src.get("display_name"), src.get("kind")] + (src.get("content_types") or []):
            if not v:
                continue
            for part in str(v).split():
                if part:
                    words.add(part.lower())
        hits = [w for w in words if w and w in q]
        if not hits:
            for ct in (src.get("content_types") or []):
                if str(ct) in q:
                    hits.append(str(ct))
        if hits:
            stewards = src.get("stewards", []) or []
            bound = [b.get("persona_id") for b in bindings
                     if b.get("source_ref") == src.get("source_id") or b.get("domain_id") == src.get("source_id")]
            candidates.append({"source_id": src.get("source_id"), "display_name": src.get("display_name", ""),
                               "hits": sorted(set(hits)), "responsible_roles": sorted(set(stewards + bound))})
    if not candidates:
        return {"ok": True, "matched": False, "responsible_roles": [],
                "allowed": False, "candidates": [], "note": "未匹配到知识域；当前角色可直接回答，不调用知识桥。"}
    best = max(candidates, key=lambda c: len(c.get("hits", [])))
    roles = best.get("responsible_roles", [])
    allowed = not roles or (current_role is not None and current_role in roles)
    return {"ok": True, "matched": True, "source_id": best["source_id"],
            "display_name": best["display_name"], "hits": best.get("hits", []),
            "responsible_roles": roles, "allowed": allowed,
            "candidates": sorted(candidates, key=lambda c: (-len(c.get("hits", [])), c.get("source_id", ""))),
            "current_role": current_role,
            "note": "这是最小委派冒烟，不是真实知识检索；不会把知识正文传给当前角色。"}


def _knowledge_access(role, source_id, query=None, limit=10, max_chars=200):
    sources = _load_sources()
    src = next((s for s in sources if s.get("source_id") == source_id), None)
    if not src:
        return {"ok": False, "error": "unknown_domain", "domain": source_id}
    root = _expand_root(src.get("root"))
    if not root or not root.is_dir():
        return {"ok": False, "error": "source_unreadable", "source_id": source_id,
                "note": "知识源目录不存在或不可读。"}
    stewards = src.get("stewards", []) or []
    bindings = _role_bindings()
    bound = [b.get("persona_id") for b in bindings
             if b.get("source_ref") == source_id or b.get("domain_id") == source_id]
    allowed = role in stewards or role in bound or src.get("default_access", "deny") != "deny"
    if not allowed:
        return {"ok": False, "error": "permission_denied", "role": role, "source_id": source_id,
                "note": "default_access=deny 且该角色不是 steward/bound。"}
    try:
        files = sorted(p.name for p in root.iterdir() if p.is_file())[:limit]
    except Exception as exc:
        return {"ok": False, "error": "read_error", "detail": str(exc)}
    matches = []
    if query and query.strip():
        q = query.strip().lower()
        for p in sorted(root.iterdir()):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".txt", ".md", ".json", ".csv", ".yml", ".yaml"):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            idx = content.lower().find(q)
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(content), idx + len(q) + 40)
                snippet = content[start:end].replace("\n", " ")
                if max_chars and len(snippet) > max_chars:
                    snippet = snippet[:max_chars] + "..."
                matches.append({"file": p.name, "snippet": snippet})
                if len(matches) >= limit:
                    break
    return {"ok": True, "role": role, "source_id": source_id,
            "allowed": allowed, "files": files, "matches": matches,
            "max_chars": max_chars,
            "note": "只读目录清单 + 有限上下文摘要（预算 %s 字符）；不会修改或上传知识源。" % max_chars}


def _record_suggest_history(entry):
    try:
        hist = read_json(HARNESS_DIR / "knowledge-suggest-history.json") or {"schema_version": 1, "entries": []}
        entries = hist.setdefault("entries", [])
        entries.insert(0, entry)
        hist["entries"] = entries[:20]
        write_json(HARNESS_DIR / "knowledge-suggest-history.json", hist)
    except Exception:
        pass


def _knowledge_index(source_id):
    sources = _load_sources()
    src = next((s for s in sources if s.get("source_id") == source_id), None)
    if not src:
        return {"ok": False, "error": "unknown_domain", "domain": source_id}
    root = _expand_root(src.get("root"))
    if not root or not root.is_dir():
        return {"ok": False, "error": "source_unreadable", "source_id": source_id}
    idx_path = HARNESS_DIR / "knowledge-index.json"
    idx = read_json(idx_path) or {"schema_version": 1, "sources": {}}
    entries = []
    total_words = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".txt", ".md", ".json", ".csv", ".yml", ".yaml"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        words = max(1, len(text.split()))
        total_words += words
        entries.append({"file": p.name, "path": str(p), "words": words})
    idx.setdefault("sources", {})[source_id] = {"indexed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                                "file_count": len(entries), "total_words": total_words,
                                                "files": entries[:200]}
    write_json(idx_path, idx)
    return {"ok": True, "source_id": source_id, "indexed": True,
            "file_count": len(entries), "total_words": total_words,
            "index_file": str(idx_path), "note": "只建立文本词频/文件清单索引，不调用模型。"}


def cmd_knowledge(args):
    if not args:
        print("用法：harness.py knowledge list|sources|health|mount|delegate")
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
    if sub == "health":
        source_id = ""
        args1 = args[1:]
        for i, a in enumerate(args1):
            if a == "--source" and i + 1 < len(args1):
                source_id = args1[i + 1]
        result = _knowledge_health(source_id or None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if sub == "mount":
        role = domain = ""
        args1 = args[1:]
        for i, a in enumerate(args1):
            if a == "--role" and i + 1 < len(args1):
                role = args1[i + 1]
            if a == "--domain" and i + 1 < len(args1):
                domain = args1[i + 1]
        if not role or not domain:
            print("用法：python harness.py knowledge mount --role <persona_id> --domain <source_id>")
            return 1
        result = _knowledge_mount(role, domain)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if sub == "delegate":
        question = ""
        role = ""
        args1 = args[1:]
        for i, a in enumerate(args1):
            if a == "--question" and i + 1 < len(args1):
                question = args1[i + 1]
            if a == "--role" and i + 1 < len(args1):
                role = args1[i + 1]
        if not question:
            print("用法：python harness.py knowledge delegate --question <问题> [--role <persona_id>]")
            return 1
        result = _knowledge_delegate(question, role or None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if sub == "index":
        source_id = ""
        args1 = args[1:]
        for i, a in enumerate(args1):
            if a == "--source" and i + 1 < len(args1):
                source_id = args1[i + 1]
        if not source_id:
            print("用法：python harness.py knowledge index --source <source_id>")
            return 1
        result = _knowledge_index(source_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if sub == "access":
        role = source_id = query = ""
        limit = 10
        max_chars = 200
        args1 = args[1:]
        for i, a in enumerate(args1):
            if a == "--role" and i + 1 < len(args1):
                role = args1[i + 1]
            if a == "--source" and i + 1 < len(args1):
                source_id = args1[i + 1]
            if a == "--query" and i + 1 < len(args1):
                query = args1[i + 1]
            if a == "--limit" and i + 1 < len(args1):
                limit = int(args1[i + 1])
            if a == "--max-chars" and i + 1 < len(args1):
                max_chars = int(args1[i + 1])
        if not role or not source_id:
            print("用法：python harness.py knowledge access --role <persona_id> --source <source_id> [--query <text>] [--limit 10] [--max-chars 200]")
            return 1
        result = _knowledge_access(role, source_id, query or None, limit, max_chars)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if sub == "suggest":
        question = ""
        role = ""
        limit = 3
        max_chars = 200
        max_sources = 2
        args1 = args[1:]
        for i, a in enumerate(args1):
            if a == "--question" and i + 1 < len(args1):
                question = args1[i + 1]
            if a == "--role" and i + 1 < len(args1):
                role = args1[i + 1]
            if a == "--limit" and i + 1 < len(args1):
                limit = int(args1[i + 1])
            if a == "--max-chars" and i + 1 < len(args1):
                max_chars = int(args1[i + 1])
            if a == "--sources" and i + 1 < len(args1):
                max_sources = int(args1[i + 1])
        if not question or not role:
            print("用法：python harness.py knowledge suggest --question <问题> --role <persona_id> [--limit 3] [--max-chars 200] [--sources 2]")
            return 1
        d = _knowledge_delegate(question, role)
        if not d.get("matched") or not d.get("allowed"):
            result = dict(d)
            result["note"] = d.get("note", "") + " 未执行只读访问。"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        accs = []
        seen_snippets = set()
        merged_matches = []
        candidates = d.get("candidates") or [{"source_id": d["source_id"], "hits": d.get("hits") or []}]
        for cand in candidates[:max_sources]:
            sid = cand.get("source_id")
            chits = cand.get("hits") or []
            access_query = chits[0] if chits else question
            a = _knowledge_access(role, sid, access_query, limit, max_chars)
            for m in a.get("matches", []):
                key = (m.get("file"), m.get("snippet"))
                if key not in seen_snippets:
                    seen_snippets.add(key)
                    merged_matches.append({**m, "source_id": sid})
            accs.append({"source_id": sid, "ok": a.get("ok"), "allowed": a.get("allowed")})
        acc = {"ok": True, "role": role, "allowed": True, "matches": merged_matches,
               "delegate": d, "sources": accs, "max_chars": max_chars,
               "note": "委派匹配 + 多源只读访问（%d 个 source）返回去重上下文；不会修改/上传知识源。" % len(accs)}
        _record_suggest_history({
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "role": role,
            "question": question, "sources": len(accs), "matches": len(merged_matches),
        })
        print(json.dumps(acc, ensure_ascii=False, indent=2))
        return 0 if acc.get("ok") else 1
    print("未知 knowledge 子命令：" + sub)
    return 1


def _confirm_risk(action, detail, yes=False):
    if yes:
        return True
    print("[高危操作] %s" % action)
    print("  %s" % detail)
    try:
        ans = input("确认继续？[y/N] ").strip().lower()
    except EOFError:
        ans = ""
    return ans in ("y", "yes", "是", "1")


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
    if sub == "run":
        name = ""
        command = []
        i = 0
        while i < len(rest):
            if rest[i] == "--name" and i + 1 < len(rest):
                name = rest[i + 1]; i += 2
            elif rest[i] == "--":
                command = rest[i + 1:]; break
            else:
                i += 1
        if not name or not command:
            print("用法：harness.py workspace run --name <ws> -- <command> [args...]")
            return 1
        lease_path = WORKSPACE_DIR / name / "workspace.json"
        if not lease_path.exists():
            print(json.dumps({"ok": False, "error": "workspace_not_found", "name": name}, ensure_ascii=False))
            return 1
        lease = read_json(lease_path)
        allowed = lease.get("allowed_commands", [])
        if allowed and not any(command[0].startswith(a) for a in allowed):
            print(json.dumps({"ok": False, "error": "command_not_allowed", "allowed_commands": allowed}, ensure_ascii=False))
            return 1
        forbidden = lease.get("forbidden_paths", [])
        for arg in command:
            for pat in forbidden:
                if pat in arg or (pat.endswith("/**") and arg.startswith(pat[:-3])):
                    print(json.dumps({"ok": False, "error": "forbidden_path_in_command", "forbidden": pat, "arg": arg}, ensure_ascii=False))
                    return 1
        if lease.get("actual_execution") is True:
            print(json.dumps({"ok": False, "error": "actual_execution_disabled_for_lease"}, ensure_ascii=False))
            return 1
        cwd = Path(lease.get("worktree_path", WORKSPACE_DIR / name))
        cwd.mkdir(parents=True, exist_ok=True)
        try:
            res = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=120)
        except Exception as e:
            print(json.dumps({"ok": False, "error": "run_failed", "detail": str(e)}, ensure_ascii=False))
            return 1
        lease["last_command"] = command
        lease["last_rc"] = res.returncode
        write_json(lease_path, lease)
        out = {"ok": res.returncode == 0, "workspace": name, "command": command,
               "returncode": res.returncode, "stdout": res.stdout[-1000:], "stderr": res.stderr[-1000:],
               "note": "基本命令约束：仅检查 allowed_commands 与 actual_execution；非完整沙箱"}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if res.returncode == 0 else 1
    if sub == "worktree":
        wsub = rest[0] if rest else ""
    if sub == "worktree":
        wsub = rest[0] if rest else ""
        name = ""
        base = "HEAD"
        i = 1
        while i < len(rest):
            if rest[i] == "--name" and i + 1 < len(rest):
                name = rest[i + 1]; i += 2
            elif rest[i] == "--base" and i + 1 < len(rest):
                base = rest[i + 1]; i += 2
            else:
                i += 1
        if not name:
            print("用法：harness.py workspace worktree create|list|remove --name <ws> [--base <commit>]")
            return 1
        ws_dir = WORKSPACE_DIR / name
        lease_path = ws_dir / "workspace.json"
        wt_root = ROOT / ".worktrees" / name
        if wsub == "create":
            if not (ROOT / ".git").exists():
                print(json.dumps({"ok": False, "error": "not_git_repo"}, ensure_ascii=False))
                return 1
            try:
                subprocess.run(["git", "-C", str(ROOT), "worktree", "add", str(wt_root), base],
                               check=True, capture_output=True, text=True, timeout=60)
            except Exception as e:
                print(json.dumps({"ok": False, "error": "worktree_add_failed", "detail": str(e)}, ensure_ascii=False))
                return 1
            lease = read_json(lease_path) if lease_path.exists() else {}
            lease["worktree_path"] = str(wt_root)
            lease["worktree_base"] = base
            lease["status"] = "active"
            write_json(lease_path, lease)
            print(json.dumps({"ok": True, "workspace": name, "worktree": str(wt_root), "base": base}, ensure_ascii=False))
            return 0
        if wsub == "list":
            out = []
            for d in sorted(WORKSPACE_DIR.iterdir()):
                if d.is_dir() and (d / "workspace.json").exists():
                    l = read_json(d / "workspace.json")
                    out.append({"workspace": d.name, "worktree": l.get("worktree_path"), "base": l.get("worktree_base")})
            print(json.dumps({"ok": True, "worktrees": out}, ensure_ascii=False, indent=2))
            return 0
        if wsub == "remove":
            if not _confirm_risk("workspace worktree remove", "将尝试删除 worktree 目录并清理租约。", yes="--yes" in rest):
                print(json.dumps({"ok": False, "status": "cancelled"}, ensure_ascii=False))
                return 1
            if (ROOT / ".git").exists() and wt_root.exists():
                subprocess.run(["git", "-C", str(ROOT), "worktree", "remove", "--force", str(wt_root)],
                               capture_output=True, text=True, timeout=60)
                import shutil as _sh
                if wt_root.exists():
                    _sh.rmtree(wt_root, ignore_errors=True)
            if lease_path.exists():
                lease = read_json(lease_path)
                lease.pop("worktree_path", None)
                lease.pop("worktree_base", None)
                write_json(lease_path, lease)
            print(json.dumps({"ok": True, "workspace": name, "removed": True}, ensure_ascii=False))
            return 0
        print("未知 worktree 子命令：" + wsub)
        return 1
    if sub == "check":
        name = rest[0] if rest else ""
        if not name:
            print("用法：harness.py workspace check <name>")
            return 1
    if sub == "check":
        name = rest[0] if rest else ""
        if not name:
            print("用法：harness.py workspace check <name>")
            return 1
        lease_path = WORKSPACE_DIR / name / "workspace.json"
        if not lease_path.exists():
            print(json.dumps({"ok": False, "error": "workspace_not_found", "name": name}, ensure_ascii=False))
            return 1
        lease = read_json(lease_path)
        missing = []
        bad = []
        for pth in lease.get("forbidden_paths", []):
            if "*" not in pth and (Path.cwd() / pth).exists():
                bad.append("forbidden_exists:" + pth)
        ok = lease.get("status") == "active" and lease.get("actual_execution") is False and not bad
        print(json.dumps({"ok": ok, "workspace": name, "lease": lease,
                          "issues": bad, "note": "仅检查租约元数据；真正的文件系统隔离需宿主执行"}, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    if sub == "release":
        name = rest[0] if rest else ""
        if not name:
            print("用法：harness.py workspace release <name> [--yes]")
            return 1
        p = WORKSPACE_DIR / name
        if not p.exists():
            print(json.dumps({"ok": False, "error": "workspace_not_found", "name": name}, ensure_ascii=False))
            return 1
        if not _confirm_risk("workspace release", "删除该 workspace 目录及其申请。", yes="--yes" in rest):
            print(json.dumps({"ok": False, "status": "cancelled"}, ensure_ascii=False))
            return 1
        shutil.rmtree(p)
        print(json.dumps({"ok": True, "released": name}, ensure_ascii=False))
        return 0
    if sub == "sandbox":
        name = rest[0] if rest else ""
        command = ""
        for i, a in enumerate(rest[1:]):
            if a == "--command" and i + 1 < len(rest[1:]):
                command = rest[i + 2]
        if not name:
            print("用法：harness.py workspace sandbox <name> --command <cmd> [--dry-run]")
            return 1
        lease_path = WORKSPACE_DIR / name / "workspace.json"
        if not lease_path.exists():
            print(json.dumps({"ok": False, "error": "workspace_not_found", "name": name}, ensure_ascii=False))
            return 1
        lease = read_json(lease_path)
        allowed = lease.get("allowed_commands", []) or []
        forbidden = lease.get("forbidden_paths", []) or []
        bad = []
        if lease.get("status") != "active":
            bad.append("lease_not_active")
        if lease.get("actual_execution") is True:
            bad.append("actual_execution_enabled")
        if command and command not in allowed:
            bad.append("command_not_allowed:" + command)
        for pth in forbidden:
            if "*" not in pth and (Path.cwd() / pth).exists():
                bad.append("forbidden_exists:" + pth)
        ok = not bad
        print(json.dumps({"ok": ok, "mode": "workspace_sandbox_dry_run", "workspace": name,
                          "command": command, "allowed_commands": allowed,
                          "forbidden_exists": bad, "note": "dry-run 只读检查，不是沙箱执行。"},
                         ensure_ascii=False, indent=2))
        return 0 if ok else 1
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
