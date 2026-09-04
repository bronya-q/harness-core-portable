#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_verify.py — 发布物一致性校验（无需 Ollama / 私有卡）。

用法：
  python release_verify.py            # 校验 release-manifest.json 与当前工作区
  python release_verify.py --generate # 依据 git ls-files 重新生成 release-manifest.json

只做离线/静态检查：文件清单、SHA-256、Python 语法编译、绝对路径残留。
不启动 SQLite/模型/服务。
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "release-manifest.json"
ALGO = "sha256"
EXCLUDED_PARTS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc"}
SKIP_FROM_MANIFEST = {"release-manifest.json"}


def git_ls_files():
    p = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if p.returncode != 0:
        raise RuntimeError("git ls-files failed: " + p.stderr[-300:])
    return [x for x in p.stdout.split("\0") if x]


def is_excluded(rel: str) -> bool:
    parts = Path(rel).parts
    if any(part in EXCLUDED_PARTS for part in parts):
        return True
    if rel.endswith(tuple(EXCLUDED_SUFFIXES)):
        return True
    return False


def sha256_of(rel: str) -> str:
    # 统一按 LF 规范化后计算哈希，避免 Windows/Unix 行尾差异导致 clone 后校验失败。
    data = (ROOT / rel).read_bytes().replace((chr(13) + chr(10)).encode(), chr(10).encode())
    return hashlib.sha256(data).hexdigest()


def build_manifest() -> None:
    files = [f for f in git_ls_files() if f and not is_excluded(f) and f not in SKIP_FROM_MANIFEST]
    files.sort()
    entries = {f: sha256_of(f) for f in files}
    manifest = {
        "schema_version": 1,
        "algorithm": ALGO,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "release_verify.py --generate",
        "count": len(files),
        "files": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "manifest": str(MANIFEST), "count": len(files)},
                     ensure_ascii=False, indent=2))


def verify() -> int:
    issues = []
    if not MANIFEST.exists():
        issues.append("missing release-manifest.json; run `python release_verify.py --generate`")
        print(json.dumps({"ok": False, "issues": issues}, ensure_ascii=False, indent=2))
        return 1

    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as e:
        issues.append("invalid manifest json: %s" % e)
        print(json.dumps({"ok": False, "issues": issues}, ensure_ascii=False, indent=2))
        return 1

    if m.get("algorithm") != ALGO:
        issues.append("algorithm mismatch: %s != %s" % (m.get("algorithm"), ALGO))
    if m.get("schema_version") != 1:
        issues.append("schema_version mismatch")

    files_manifest = m.get("files", {})
    if not isinstance(files_manifest, dict):
        issues.append("files field is not an object")
        files_manifest = {}

    # Every manifest entry must exist and hash-match
    for rel in sorted(files_manifest):
        p = ROOT / rel
        if not p.exists():
            issues.append("missing:%s" % rel)
            continue
        if is_excluded(rel):
            issues.append("excluded_but_listed:%s" % rel)
            continue
        try:
            actual = sha256_of(rel)
        except Exception as e:
            issues.append("hash_error:%s:%s" % (rel, e))
            continue
        if actual != files_manifest[rel]:
            issues.append("hash_mismatch:%s" % rel)

    # Every tracked file (except excluded/manifest itself) must appear
    tracked = git_ls_files()
    for rel in tracked:
        if rel in SKIP_FROM_MANIFEST or rel == "":
            continue
        if is_excluded(rel):
            issues.append("tracked_excluded:%s" % rel)
            continue
        if rel not in files_manifest:
            issues.append("tracked_not_in_manifest:%s" % rel)

    # Python syntax compile (in-memory, no .pyc side effects)
    for rel in sorted(files_manifest):
        if not rel.endswith(".py"):
            continue
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except Exception as e:
            issues.append("py_compile_fail:%s:%s" % (rel, e))

    # No absolute Windows user paths in tracked text files
    bs = chr(92)
    abs_pats = [("C:" + bs + "Users").encode(), ("C:" + bs * 2 + "Users").encode(),  b"C:/" + b"Users/"]
    for rel in tracked:
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if any(pat in data for pat in abs_pats):
            issues.append("absolute_user_path:%s" % rel)

    # Required public files must exist
    for req in ["README.md", "LICENSE", "NOTICE.md", "SECURITY.md", "harness.py", "harness-core/harness.py"]:
        if not (ROOT / req).exists():
            issues.append("missing_required:%s" % req)

    ok = not issues
    print(json.dumps({
        "ok": ok,
        "mode": "release_verify",
        "count": m.get("count"),
        "file_entries": len(files_manifest),
        "issues": issues,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        build_manifest()
        return verify()
    return verify()


if __name__ == "__main__":
    sys.exit(main())
