#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comparison_commands.py — P4 可组合与对照（角色 A/B、检索器 A/B、Evidence Bundle）。"""
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
ROOT = SKILL.parent
EVIDENCE_DIR = ROOT / "docs" / "evidence"


def _load_json(path):
    p = Path(path).expanduser()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _est_tokens(obj):
    return max(0, len(json.dumps(obj, ensure_ascii=False)) // 4)


def cmd_role_ab(a, b):
    fa, fb = _load_json(a), _load_json(b)
    if not fa or not fb:
        print(json.dumps({"ok": False, "error": "file_not_found|invalid_json", "a": a, "b": b}, ensure_ascii=False))
        return 1
    out = {
        "a": {"file": a, "persona_id": fa.get("persona_id"), "display_name": fa.get("display_name"),
              "scope": fa.get("scope"), "role_types": fa.get("role_types", []),
              "knowledge_bindings": len(fa.get("knowledge_bindings", [])),
              "permissions_requested": fa.get("permissions_requested", {}),
              "est_tokens": _est_tokens(fa)},
        "b": {"file": b, "persona_id": fb.get("persona_id"), "display_name": fb.get("display_name"),
              "scope": fb.get("scope"), "role_types": fb.get("role_types", []),
              "knowledge_bindings": len(fb.get("knowledge_bindings", [])),
              "permissions_requested": fb.get("permissions_requested", {}),
              "est_tokens": _est_tokens(fb)},
        "differences": {
            "persona_id_same": fa.get("persona_id") == fb.get("persona_id"),
            "display_name_same": fa.get("display_name") == fb.get("display_name"),
            "scope_same": fa.get("scope") == fb.get("scope"),
            "role_types_same": fa.get("role_types") == fb.get("role_types"),
            "knowledge_bindings_same": fa.get("knowledge_bindings") == fb.get("knowledge_bindings"),
        },
        "note": "用途：角色版本/配置对照；不自动选择“更好”。",
    }
    print(json.dumps({"ok": True, "mode": "role_ab", **out}, ensure_ascii=False, indent=2))
    return 0


def cmd_retriever_ab(a, b, top_k, per_query=False):
    def run_one(retriever):
        p = subprocess.run([sys.executable, str(SKILL / "measurement.py"), "recall-pool",
                            "--retriever", retriever, "--top-k", str(top_k)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        try:
            return json.loads(p.stdout)
        except Exception:
            return None
    ra = run_one(a)
    rb = run_one(b)
    if not ra or not rb:
        print(json.dumps({"ok": False, "error": "recall_pool_unavailable",
                          "note": "需要私有 gold 数据；公开 clean clone 通常不可用"}, ensure_ascii=False, indent=2))
        return 1
    rows_a = ra.get("rows") or []
    rows_b = rb.get("rows") or []
    per_query_rows = []
    if per_query:
        for i in range(max(len(rows_a), len(rows_b))):
            xa = rows_a[i] if i < len(rows_a) else {}
            xb = rows_b[i] if i < len(rows_b) else {}
            pd = None
            rd = None
            if xa.get("precision_at_k") is not None and xb.get("precision_at_k") is not None:
                pd = round(xb.get("precision_at_k") - xa.get("precision_at_k"), 4)
            if xa.get("recall") is not None and xb.get("recall") is not None:
                rd = round(xb.get("recall") - xa.get("recall"), 4)
            per_query_rows.append({
                "query": xa.get("query") or xb.get("query"),
                "precision_a": xa.get("precision_at_k"), "precision_b": xb.get("precision_at_k"),
                "precision_delta": pd,
                "recall_a": xa.get("recall"), "recall_b": xb.get("recall"),
                "recall_delta": rd,
                "relevant_pool": xa.get("relevant_pool") or xb.get("relevant_pool"),
            })
        per_query_rows.sort(key=lambda r: (r["precision_delta"] if r["precision_delta"] is not None else 0))
    out = {
        "retriever_a": {"name": a, "p_at_5": ra.get("avg_precision_at_k"), "recall": ra.get("avg_recall"),
                        "hit_rate": ra.get("hit_rate")},
        "retriever_b": {"name": b, "p_at_5": rb.get("avg_precision_at_k"), "recall": rb.get("avg_recall"),
                        "hit_rate": rb.get("hit_rate")},
        "per_query": per_query_rows,
        "note": "基于同一独立 relevance 池；结果仅用于本地对照，不视为第三方认证。",
    }
    print(json.dumps({"ok": True, "mode": "retriever_ab", **out}, ensure_ascii=False, indent=2))
    return 0


def cmd_evidence_create(task, workspace):
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    base_commit = "unknown"
    changed = []
    try:
        p = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
        if p.returncode == 0:
            base_commit = p.stdout.strip()
        p2 = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
        changed = [l.strip() for l in p2.stdout.splitlines() if l.strip()][:80]
    except Exception:
        pass
    lease = None
    if workspace:
        lease_path = Path.home() / ".dsh" / "harness" / "workspaces" / workspace / "workspace.json"
        if lease_path.exists():
            lease = _load_json(lease_path)
    bundle = {
        "task_id": task or "task_" + time.strftime("%Y%m%d-%H%M%S"),
        "role_id": (lease or {}).get("role"),
        "base_commit": base_commit,
        "working_tree": "dirty" if changed else "clean",
        "workspace": workspace,
        "changed_files": changed,
        "checks": [],
        "unverified": ["actual test run not recorded"],
        "external_effects": [],
        "approval_required": True,
        "rollback": "git checkout / revert; see docs/deployments if deployed",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    out = EVIDENCE_DIR / (bundle["task_id"] + ".json")
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "mode": "evidence_bundle", "output": str(out), "bundle": bundle},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_handoff_create(task):
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ev_file = EVIDENCE_DIR / (task + ".json")
    if not ev_file.exists():
        print(json.dumps({"ok": False, "error": "evidence_not_found", "task": task}, ensure_ascii=False))
        return 1
    ev = _load_json(ev_file)
    md = [
        "# Handoff: " + task,
        "",
        "## 后辈最需要知道的五件事",
        "",
        "1. 为什么这样做：" + str(ev.get("role_id") or "未知"),
        "2. 实际改了什么：" + "; ".join(ev.get("changed_files", [])[:5]),
        "3. 哪些证据说明有效：" + str(len(ev.get("checks", []))) + " 条 checks",
        "4. 哪些事情还没有验证：" + "; ".join(ev.get("unverified", [])),
        "5. 出问题怎么撤销：" + str(ev.get("rollback", "见部署文档")),
        "",
        "## 基础信息",
        "",
        "- task_id: " + str(ev.get("task_id")),
        "- base_commit: " + str(ev.get("base_commit")),
        "- working_tree: " + str(ev.get("working_tree")),
        "- approval_required: " + str(ev.get("approval_required")),
        "- created_at: " + str(ev.get("created_at")),
        "",
        "## 尚未验证",
        "",
    ]
    for u in ev.get("unverified", []):
        md.append("- " + u)
    out = SKILL.parent / "docs" / "tasks" / ("handoff-" + task + ".md")
    out.write_text(chr(10).join(md) + chr(10), encoding="utf-8")
    print(json.dumps({"ok": True, "mode": "handoff", "output": str(out)}, ensure_ascii=False, indent=2))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if args[0] == "ab" and len(args) >= 2 and args[1] == "role":
        a = b = ""
        i = 2
        while i < len(args):
            if args[i] == "--a" and i + 1 < len(args):
                a = args[i + 1]; i += 2
            elif args[i] == "--b" and i + 1 < len(args):
                b = args[i + 1]; i += 2
            else:
                i += 1
        return cmd_role_ab(a, b)
    if args[0] == "ab" and len(args) >= 2 and args[1] == "retriever":
        a = b = "keyword"
        top_k = 5
        per_query = False
        i = 2
        while i < len(args):
            if args[i] == "--retriever-a" and i + 1 < len(args):
                a = args[i + 1]; i += 2
            elif args[i] == "--retriever-b" and i + 1 < len(args):
                b = args[i + 1]; i += 2
            elif args[i] == "--top-k" and i + 1 < len(args):
                top_k = int(args[i + 1]); i += 2
            elif args[i] == "--per-query":
                per_query = True; i += 1
            else:
                i += 1
        return cmd_retriever_ab(a, b, top_k, per_query)
    if args[0] == "evidence" and len(args) >= 2 and args[1] == "create":
        task = workspace = ""
        i = 2
        while i < len(args):
            if args[i] == "--task" and i + 1 < len(args):
                task = args[i + 1]; i += 2
            elif args[i] == "--workspace" and i + 1 < len(args):
                workspace = args[i + 1]; i += 2
            else:
                i += 1
        return cmd_evidence_create(task, workspace)
    if args[0] == "evidence" and len(args) >= 2 and args[1] == "handoff":
        task = ""
        i = 2
        while i < len(args):
            if args[i] == "--task" and i + 1 < len(args):
                task = args[i + 1]; i += 2
            else:
                i += 1
        return cmd_handoff_create(task)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
