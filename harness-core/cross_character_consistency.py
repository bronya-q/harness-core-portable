#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cross_character_consistency.py — #5 跨角色一致性审查。"""
import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CARDS = Path.home() / "Documents" / "harness" / "_perspective-cards"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-overlap", type=float, default=0.3)
    args = ap.parse_args()
    cards = {}
    for d in sorted(CARDS.iterdir()):
        p = d / "card.json"
        if not p.exists():
            continue
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        cards[d.name] = c
    issues = []
    names = list(cards.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a = cards[names[i]]; b = cards[names[j]]
            # overlap in contradiction_formula / decision_heuristics / mental model one-liners
            a_text = set(str(a.get("contradiction_formula") or [])) | set(str(m.get("one_liner")) for m in (a.get("mental_models") or []) if isinstance(m, dict))
            b_text = set(str(b.get("contradiction_formula") or [])) | set(str(m.get("one_liner")) for m in (b.get("mental_models") or []) if isinstance(m, dict))
            overlap = len(a_text & b_text) / max(1, len(a_text | b_text))
            if overlap >= args.min_overlap:
                issues.append({"pair": [names[i], names[j]], "overlap": round(overlap, 3)})
    print(json.dumps({"ok": True, "cards": names, "issues": issues,
                      "note": "跨角色一致性审查；重叠高于阈值需人工确认是否应区分"}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
