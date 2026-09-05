#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adversarial_review.py — 最小 Adversarial Review 冒烟。

流程（R1）：
  草稿 → 主张抽取 → 证据审查 → 反例/越界检查 → 修订建议

不声称真正的对抗推理；只是让“审查链”先可运行、可记录。
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent


def extract_claims(text):
    claims = []
    for seg in re.split(r"[。！？；\n]", text):
        seg = seg.strip()
        if len(seg) >= 8:
            claims.append(seg)
    return claims[:20]


def evidence_check(claim, evidence_dir):
    if not evidence_dir or not Path(evidence_dir).exists():
        return {"claim": claim, "status": "no_evidence_dir", "matches": []}
    hits = []
    for p in sorted(Path(evidence_dir).iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".md", ".txt", ".json"):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for word in re.findall(r"[\u4e00-\u9fa5]{2,}|[A-Za-z]{3,}", claim):
            if len(word) >= 2 and word.lower() in content.lower():
                hits.append(p.name)
                break
    status = "supported" if hits else "unsupported"
    return {"claim": claim, "status": status, "matches": hits[:5]}


def review(text, evidence_dir=None, persona="adversarial-review"):
    claims = extract_claims(text)
    results = [evidence_check(c, evidence_dir) for c in claims]
    supported = sum(1 for r in results if r["status"] == "supported")
    unsupported = sum(1 for r in results if r["status"] == "unsupported")
    issues = []
    for r in results:
        if r["status"] == "unsupported":
            issues.append("缺少独立证据：" + r["claim"][:60])
    if len(claims) == 0:
        issues.append("未抽取到主张")
    return {"reviewer": persona, "draft": text, "claims": claims,
            "checks": results, "supported": supported, "unsupported": unsupported,
            "issues": issues, "revision_suggestions": issues[:5],
            "note": "这是最小对抗审查冒烟，不构成心理效度或真实对抗推理。"}


def main():
    args_all = sys.argv[1:]
    if args_all and args_all[0] == "adversarial":
        args_all = args_all[1:]
    sys.argv = [sys.argv[0]] + args_all
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True)
    ap.add_argument("--evidence-dir", default=None)
    ap.add_argument("--persona", default="adversarial-review")
    ap.add_argument("--save", default=None)
    args = ap.parse_args()
    result = review(args.draft, args.evidence_dir, args.persona)
    try:
        from event_store import record_event
        record_event({"event_type": "adversarial_review.result", "scope": "character:" + args.persona,
                      "content_type": "fact", "content_provenance": "derived",
                      "session_provenance": "smoke", "version": 1})
    except Exception:
        pass
    if args.save:
        out_dir = ROOT / "docs" / "tasks"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / ("adversarial-review-" + args.save + ".json")
        out.write_text(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        result["saved"] = str(out)
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
