#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phenomenological_review.py — 内生心智审查（现象学程序化模拟，非心理测量）。

这是“本质直观”的工程上的程序化近似，不是声称 AI 拥有真实现象学体验：
  1. 悬置：强制暂停“直接相信这个判断”。
  2. 意向性：明确这个判断“对什么而言”。
  3. 本质变项：变化 scope/时间/后端，看结论是否仍成立。
  4. 体验/解释分离：区分“我观察到”与“我推断”。

用法：
  python phenomenological_review.py --text "这次证明...最重要..."
  python phenomenological_review.py --scope character:demo-alice --kind belief --text "主人喜欢..."
"""
import argparse
import json
import sys
import re
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


CERTAINTY = ["证明", "一定是", "必然", "本质上", "永远", "总是", "绝对", "毫无疑问", "本质"]
INFERENCE = ["推断", "推测", "可能", "也许", "说明", "意味着", "大概", "似乎", "看起来"]
EXPERIENCE = ["我体验", "我感觉", "我观察到", "我的感受", "我注意到", "当时我", "我记得"]
EXTERNAL = ["用户说", "他说", "她说", "记录显示", "数据显示", "来源", "档案", "引用"]


def classify(text):
    hits = {
        "certainty": [w for w in CERTAINTY if w in text],
        "inference": [w for w in INFERENCE if w in text],
        "experience": [w for w in EXPERIENCE if w in text],
        "external": [w for w in EXTERNAL if w in text],
    }
    if hits["certainty"] and not hits["inference"] and not hits["experience"]:
        source_type = "probably_unchecked_assertion"
    elif hits["experience"] and hits["inference"]:
        source_type = "mixed_experience_and_inference"
    elif hits["experience"]:
        source_type = "observed_or_experiential"
    elif hits["external"]:
        source_type = "external_reference"
    elif hits["inference"]:
        source_type = "inference"
    else:
        source_type = "ambiguous"
    return source_type, hits


def review(text, scope=None, kind=None):
    source_type, hits = classify(text)
    # 现象学式问题清单
    free_variation = [
        "如果换成另一个 backend，这个判断还成立吗？",
        "如果换到另一个 scope，这个判断还成立吗？",
        "如果时间换到一个月后，这个判断还成立吗？",
        "如果只凭这一次事件，是否会被过度固化为规律？",
    ]
    epoché_note = "已悬置自然态度：当前文本不直接等于事实，需要证据和适用边界。"
    verdict = "needs_evidence"
    if source_type in ("observed_or_experiential", "external_reference"):
        verdict = "keep_as_candidate"
    elif source_type == "mixed_experience_and_inference":
        verdict = "downgrade_or_separate"
    return {
        "ok": True,
        "mode": "phenomenological_review_procedure",
        "claim": "not_psychology_measurement",
        "scope": scope,
        "kind": kind,
        "text_preview": text[:160],
        "epoché": epoché_note,
        "intentional_object": "正在判断的文本所指向的对象/事件",
        "source_type": source_type,
        "signal_hits": hits,
        "free_variation": free_variation,
        "experience_explanation_separated": True,
        "verdict": verdict,
        "suggested_action": {
            "needs_evidence": "补充证据、反例、时间/后端/scope 条件后再决定是否落盘",
            "keep_as_candidate": "可作为候选记录，但仍是观察/外部引用，不是人格事实",
            "downgrade_or_separate": "把体验描述与推断结论拆开保存，降低重要性",
        }[verdict],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="", help="待审查文本；留空则从 stdin 读")
    ap.add_argument("--scope", default=None)
    ap.add_argument("--kind", default=None)
    args = ap.parse_args()
    text = args.text
    if not text:
        try:
            text = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        except Exception:
            text = ""
    if not text.strip():
        print(json.dumps({"ok": False, "error": "text required"}, ensure_ascii=False))
        return 1
    print(json.dumps(review(text, args.scope, args.kind), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
