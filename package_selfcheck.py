#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""package_selfcheck.py — 发布包静态冒烟自检（clean clone / Download ZIP 均应通过）。

注意：这是“静态冒烟检查”，不是完整端到端 selfcheck；它不要求 Ollama/真实数据，
也不验证完整生产运行面。完整运行面由 harness_selfcheck.py + production_gate.py 负责。

与 harness_selfcheck.py 的区别：
  - harness_selfcheck.py 面向“完整运行面”，依赖真实会话/模型/门控数据；
  - package_selfcheck.py 只校验仓库内容本身，不启动 SQLite/模型/服务，
    不读取用户私有配置，因此可用于 GitHub 发布前的清洁 clone 校验。

用法：
  python package_selfcheck.py
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent


def run(script, *args, timeout=120):
    p = subprocess.run([sys.executable, str(ROOT / script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    try:
        data = json.loads(p.stdout)
    except Exception:
        data = {"raw": p.stdout[-500:], "stderr": p.stderr[-500:]}
    return data, p.returncode


def main():
    issues = []
    checks = {}

    # 1) 发布物清单一致性
    data, rc = run("release_verify.py")
    checks["release_verify"] = {"rc": rc, "ok": data.get("ok")}
    if rc != 0 or data.get("ok") is not True:
        issues.append("release_verify failed")
        issues.extend(data.get("issues", []))

    # 2) 根 launcher 可导入/可打印帮助
    p = subprocess.run([sys.executable, str(ROOT / "harness.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    checks["root_harness_help"] = {"rc": p.returncode}
    if p.returncode != 0:
        issues.append("root harness help failed: %s" % p.stderr[-300:])

    # 3) 静态 JSON 配置可解析
    for rel in [
        "harness-core/runtime-policy.example.json",
        "harness-core/perspective_card_schema.json",
        "harness-core/tools_inventory.json",
        "harness-core/tools_legacy.json",
        "demo-perspective-card.json",
        "demo_gold.json",
    ]:
        path = ROOT / rel
        if not path.exists():
            issues.append("missing_json:%s" % rel)
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append("invalid_json:%s:%s" % (rel, e))
    checks["json_configs"] = "ok"

    # 4) runtime_preflight（只读无 --live，不要求 Ollama/私有目录存在）
    data, rc = run("harness-core/runtime_preflight.py")
    checks["runtime_preflight"] = {"rc": rc, "ok": isinstance(data, dict)}
    if rc != 0 or not isinstance(data, dict):
        issues.append("runtime_preflight failed")

    # 5) 关键生产门控脚本只读自检可通过（fail-closed 存在性）
    if not (ROOT / "harness-core/production_gate.py").exists():
        issues.append("missing production_gate.py")

    ok = not issues
    print(json.dumps({
        "ok": ok,
        "mode": "package_static_smoke_check",
        "checks": checks,
        "issues": issues,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
