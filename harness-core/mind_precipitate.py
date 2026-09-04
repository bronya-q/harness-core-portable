#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mind_precipitate.py — P3：Codex 自我进化模式的本地沉淀。

把 approved/applied 的 mind_evolution 候选沉淀为：
  SKILL.md / WORKFLOW.md / experience.json
写入共享目录 C:\\Users\\HL\\Documents\\harness\\_mind-evolution\\
使后续跨会话可通过 index.json 复用。

不自动执行；只写文档资产。
"""
import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from humanization import connect as hum_connect

ROOT = Path.home() / "Documents" / "harness" / "_mind-evolution"
ASSETS = ROOT / "assets"
INDEX = ROOT / "index.json"


def ensure_dir():
    ASSETS.mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        INDEX.write_text(json.dumps({"version": 1, "assets": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_slug(text, maxlen=40):
    text = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text).strip('-')
    return text[:maxlen] or uuid.uuid4().hex[:8]


def load_index():
    ensure_dir()
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "assets": []}


def save_index(idx):
    ensure_dir()
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def candidate_row(c, cid):
    return c.execute("SELECT * FROM self_upgrade_candidates WHERE id=?", (cid,)).fetchone()


def write_assets(cid):
    c = hum_connect()
    row = candidate_row(c, cid)
    if not row:
        c.close()
        return {"ok": False, "error": "candidate not found"}
    if row["status"] not in ("approved", "applied"):
        c.close()
        return {"ok": False, "error": "candidate must be approved or applied"}
    proposal = json.loads(row["proposal_json"])
    review = json.loads(row["review_json"]) if row["review_json"] else {}
    validation = json.loads(row["validation_json"]) if row["validation_json"] else {}
    c.close()
    base = safe_slug(proposal.get("source_type", "self") + "-" + proposal.get("statement", "")[:20])
    idx = load_index()
    existing = next((a for a in idx["assets"] if a["id"] == cid), None)
    if existing and Path(existing["path"]).parent == ASSETS and (Path(existing["path"]) / "SKILL.md").exists():
        asset_dir = Path(existing["path"])
        slug = asset_dir.name
    else:
        slug = base
        asset_dir = ASSETS / slug
        if asset_dir.exists() and not (asset_dir / "SKILL.md").exists():
            slug = f"{base}-{cid[:8]}"
            asset_dir = ASSETS / slug
        asset_dir.mkdir(parents=True, exist_ok=True)
    skill = f"""---
name: mind-{slug}
description: {proposal.get('statement', '')[:200]}
whenToUse: 遇到与该候选相关的复用场景时
---

# {proposal.get('statement', '')}

来源：{proposal.get('source_type', 'unknown')}
目标：{row['target']}

## 建议动作

{proposal.get('suggested_action', '')}

## 证据

{json.dumps(proposal.get('evidence_ids', []), ensure_ascii=False)}

## 审查

{json.dumps(review, ensure_ascii=False)}

## 验证

{json.dumps(validation, ensure_ascii=False)}
"""
    workflow = f"""# Workflow: {proposal.get('statement', '')[:80]}

1. 读取候选：`python mind_evolution.py candidate-status`
2. 审查：`python mind_evolution.py review --id {cid}`
3. 验证：`python mind_evolution.py validate --id {cid}`
4. 审批：`python mind_evolution.py decide --id {cid} --action approve`
5. 沉淀：`python mind_precipitate.py precipitate --id {cid}`
6. 复用：从 `_mind-evolution/` 读取本文档或 SKILL.md
"""
    (asset_dir / "SKILL.md").write_text(skill, encoding="utf-8")
    (asset_dir / "WORKFLOW.md").write_text(workflow, encoding="utf-8")
    exp = {
        "id": cid,
        "source_type": proposal.get("source_type"),
        "statement": proposal.get("statement"),
        "suggested_action": proposal.get("suggested_action"),
        "review": review,
        "validation": validation,
        "created_at": time.time(),
        "status": row["status"],
    }
    (asset_dir / "experience.json").write_text(json.dumps(exp, ensure_ascii=False, indent=2), encoding="utf-8")
    idx = load_index()
    for a in idx["assets"]:
        if a["id"] == cid:
            a.update({"slug": slug, "path": str(asset_dir), "updated_at": time.time()})
            a.pop("kind", None)  # promoted from review_card to formal asset
            break
    else:
        idx["assets"].append({"id": cid, "slug": slug, "path": str(asset_dir),
                              "statement": proposal.get("statement"),
                              "source_type": proposal.get("source_type"),
                              "created_at": time.time()})
    save_index(idx)
    return {"ok": True, "id": cid, "slug": slug, "directory": str(asset_dir),
            "files": ["SKILL.md", "WORKFLOW.md", "experience.json"]}


def precipitate_top(limit=20):
    """P3 扩展：从 Top 候选批量生成可复用「工作流卡」（shadow review，不要求 approve）。"""
    c = hum_connect()
    rows = c.execute(
        "SELECT sc.id, sc.scope, sc.target, sc.proposal_json, "
        "       COALESCE(t.severity, 0.5) AS severity "
        "FROM self_upgrade_candidates sc "
        "LEFT JOIN mind_tensions t ON sc.tension_id=t.id "
        "ORDER BY severity DESC, sc.created_at DESC LIMIT ?",
        (limit,)).fetchall()
    c.close()
    ensure_dir()
    idx = load_index()
    existing_ids = {a["id"] for a in idx["assets"]}
    created = []
    for r in rows:
        if r["id"] in existing_ids:
            continue
        proposal = json.loads(r["proposal_json"])
        base = safe_slug((proposal.get("source_type") or "card") + "-" + (proposal.get("statement") or "")[:20])
        slug = base
        d = ASSETS / "review-cards" / slug
        if d.exists():
            slug = f"{base}-{r['id'][:8]}"
            d = ASSETS / "review-cards" / slug
        d.mkdir(parents=True, exist_ok=True)
        card = f"""# 工作流卡（Shadow Review）

- candidate_id: {r['id']}
- source_type: {proposal.get('source_type')}
- scope: {r['scope']}
- target: {r['target']}
- severity: {r['severity']}
- statement: {proposal.get('statement','')}
- suggested_action: {proposal.get('suggested_action','')}
- evidence_ids: {json.dumps(proposal.get('evidence_ids',[]), ensure_ascii=False)}

> 状态：shadow；未批准，仅用于人工审阅和复用。
"""
        wf = f"""# Workflow（候选）

1. {proposal.get('suggested_action','')}
2. 人工审阅 candidate_id={r['id']}
3. 若通过：python mind_evolution.py decide --id {r['id']} --action approve
4. 沉淀：python mind_precipitate.py precipitate --id {r['id']}
"""
        (d / "CANDIDATE_CARD.md").write_text(card, encoding="utf-8")
        (d / "WORKFLOW.md").write_text(wf, encoding="utf-8")
        idx["assets"].append({"id": r["id"], "slug": slug, "path": str(d),
                              "statement": proposal.get("statement"),
                              "source_type": proposal.get("source_type"),
                              "kind": "review_card", "created_at": time.time()})
        created.append({"id": r["id"], "slug": slug, "path": str(d)})
    save_index(idx)
    return {"ok": True, "created": created}


def list_assets():
    idx = load_index()
    print(json.dumps({"ok": True, "root": str(ROOT), "assets": idx["assets"]}, ensure_ascii=False, indent=2))


def show_asset(cid):
    idx = load_index()
    for a in idx["assets"]:
        if a["id"] == cid:
            p = Path(a["path"])
            for fname in ("SKILL.md", "CANDIDATE_CARD.md", "MASTER_TASK.md"):
                f = p / fname
                if f.exists():
                    print(f.read_text(encoding="utf-8"))
                    return
            print(json.dumps({"ok": False, "error": "no card file"}, ensure_ascii=False))
            return
    print(json.dumps({"ok": False, "error": "id not found"}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="mind_precipitate P3")
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("precipitate"); q.add_argument("--id", required=True); q.set_defaults(fn=lambda a: print(json.dumps(write_assets(a.id), ensure_ascii=False, indent=2)))
    q = sub.add_parser("precipitate-top"); q.add_argument("--limit", type=int, default=20); q.set_defaults(fn=lambda a: print(json.dumps(precipitate_top(a.limit), ensure_ascii=False, indent=2)))
    q = sub.add_parser("list"); q.set_defaults(fn=lambda a: list_assets())
    q = sub.add_parser("show"); q.add_argument("--id", required=True); q.set_defaults(fn=lambda a: show_asset(a.id))
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
