#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_verify.py — 发布物一致性校验（无需 Ollama / 私有卡 / Git）。

用法：
  python release_verify.py            # 校验 release-manifest.json 与当前工作区
  python release_verify.py --generate # 需要 Git；依据 git ls-files 重新生成清单

支持三种来源：
  - Git clone：用 git ls-files 作为“应有文件”基准；
  - GitHub Download ZIP / 普通复制目录（无 .git）：扫描实际文件，
    并强制“实际文件集合 == release-manifest.json 集合”。
只做离线/静态检查：文件清单、SHA-256、Python 语法编译、绝对路径残留。
不启动 SQLite/模型/服务。
"""
import hashlib
import json
import os
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
    return [x for x in p.stdout.split(chr(0)) if x]


def try_git_ls_files():
    try:
        return git_ls_files()
    except Exception:
        return None


def scan_files():
    """递归扫描实际文件，排除 .git/__pycache__/pyc/release-manifest.json。"""
    out = set()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        rel = Path(dirpath).relative_to(ROOT)
        for fn in filenames:
            relpath = ((rel / fn).as_posix() if str(rel) != "." else fn)
            if relpath in SKIP_FROM_MANIFEST:
                continue
            if relpath.endswith(tuple(EXCLUDED_SUFFIXES)):
                continue
            out.add(relpath)
    return sorted(out)


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


def build_manifest() -> int:
    if not Path(ROOT / ".git").exists():
        print(json.dumps({"ok": False, "mode": "release_verify.generic",
                          "issues": ["--generate requires a git clone (.git present)"]},
                         ensure_ascii=False, indent=2))
        return 1
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
    return 0


def verify() -> int:
    issues = []
    if not MANIFEST.exists():
        issues.append("missing release-manifest.json; run `python release_verify.py --generate` in a git clone")
        print(json.dumps({"ok": False, "mode": "release_verify", "issues": issues},
                         ensure_ascii=False, indent=2))
        return 1

    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as e:
        issues.append("invalid manifest json: %s" % e)
        print(json.dumps({"ok": False, "mode": "release_verify", "issues": issues},
                         ensure_ascii=False, indent=2))
        return 1

    if m.get("algorithm") != ALGO:
        issues.append("algorithm mismatch: %s != %s" % (m.get("algorithm"), ALGO))
    if m.get("schema_version") != 1:
        issues.append("schema_version mismatch")

    files_manifest = m.get("files", {})
    if not isinstance(files_manifest, dict):
        issues.append("files field is not an object")
        files_manifest = {}

    # 1) manifest 里的每个文件都必须存在且哈希一致
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

    # 2) 判断来源：Git clone 用 git ls-files；无 .git ZIP/复制目录用目录扫描
    git_list = try_git_ls_files()
    if git_list is not None:
        source = "git"
        for rel in git_list:
            rel = rel.strip()
            if not rel or rel == "":
                continue
            if rel in SKIP_FROM_MANIFEST:
                continue
            if is_excluded(rel):
                issues.append("tracked_excluded:%s" % rel)
                continue
            if rel not in files_manifest:
                issues.append("tracked_not_in_manifest:%s" % rel)
        file_list = git_list
    else:
        source = "zip_scan"
        file_list = scan_files()
        actual_set = set(file_list)
        expected_set = set(files_manifest.keys())
        for rel in sorted(actual_set - expected_set):
            issues.append("unlisted_file:%s" % rel)
        for rel in sorted(expected_set - actual_set):
            if not (ROOT / rel).exists():
                issues.append("missing:%s" % rel)

    # 3) Python 语法编译（内存中，不写 .pyc）
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

    # 4) 绝对 Windows 用户路径残留
    bs = chr(92)
    abs_pats = [("C:" + bs + "Users").encode(), ("C:" + bs * 2 + "Users").encode(), b"C:/" + b"Users/"]
    for rel in file_list:
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if any(pat in data for pat in abs_pats):
            issues.append("absolute_user_path:%s" % rel)

    # 5) 必备公开文件
    for req in ["README.md", "LICENSE", "NOTICE.md", "SECURITY.md", "harness.py", "harness-core/harness.py"]:
        if not (ROOT / req).exists():
            issues.append("missing_required:%s" % req)

    ok = not issues
    print(json.dumps({
        "ok": ok,
        "mode": "release_verify",
        "source": source,
        "count": m.get("count"),
        "file_entries": len(files_manifest),
        "issues": issues,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        return build_manifest()
    return verify()


if __name__ == "__main__":
    sys.exit(main())
