#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evidence-gated projection of sixdim into three candidate needs.

This is a read-only sidecar, not a psychological assessment tool. It wraps the
existing G6 formula while adding provenance, confidence, contradiction checks,
and an explicit state gate. It never writes memory, emotion state, persona, or
relationship values.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

NEEDS = ("security", "possessiveness", "attachment")
EMOTIONS = ("joy", "anger", "sadness", "fear", "surprise", "disgust")

def _num(value, default=0.0):
    try:
        return max(-100.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default

def normalize_sixdim(values):
    values = values or {}
    return {name: _num(values.get(name, values.get("sad") if name == "sadness" else None))
            for name in EMOTIONS}

def clamp_need(value):
    return round(max(0.0, min(100.0, float(value))), 2)

def project(sixdim, *, baseline=None, evidence=None, prior=None, scope=None, source="input"):
    values = normalize_sixdim(sixdim)
    evidence = evidence if isinstance(evidence, list) else []
    prior = prior if isinstance(prior, dict) else None
    baseline = baseline if isinstance(baseline, dict) else None

    # Existing G6 formula from the local handbook; this sidecar adds no new
    # semantic claim about what a human need actually is.
    raw = {
        "security": 100.0 - (values["fear"] + values["disgust"]) / 2.0,
        "possessiveness": (values["anger"] + 0.5 * values["surprise"]) / 1.5,
        "attachment": (values["joy"] + values["sadness"]) / 2.0,
    }
    candidates = {name: clamp_need(raw[name]) for name in NEEDS}
    evidence_ids = [str(x.get("id")) for x in evidence if isinstance(x, dict) and x.get("id") is not None]
    # An id alone is only a pointer. Provenance fields are required before an
    # observation can be treated as verified input.
    verified_evidence = [x for x in evidence if isinstance(x, dict) and x.get("id") is not None
                         and x.get("source_ref") and x.get("event_type") and x.get("observed_at")]
    explicit = isinstance(sixdim, dict) and any(
        key in sixdim for key in ("joy", "anger", "sad", "sadness", "fear", "surprise", "disgust")
    )
    limitations = []
    contradictions = []
    if not explicit:
        limitations.append("sixdim_not_provided")
    if not evidence_ids:
        limitations.append("no_evidence_ids")
    if evidence_ids and not verified_evidence:
        limitations.append("evidence_ids_without_provenance")
    if baseline is None:
        limitations.append("need_baseline_not_provided")
    if prior:
        for name in NEEDS:
            if name in prior and abs(candidates[name] - _num(prior[name])) >= 35:
                contradictions.append(name + "_large_change_without_trajectory")
    # One snapshot is a candidate observation; repeated, sourced observations
    # are needed before a stable candidate can be considered.
    if not explicit:
        status = "insufficient_evidence"
        confidence = 0.0
    elif not evidence_ids or not verified_evidence:
        status = "candidate_unverified"
        confidence = 0.2 if evidence_ids else 0.0
    elif len(verified_evidence) < 2:
        status = "candidate_low_confidence"
        confidence = 0.35
    else:
        status = "candidate_observation"
        confidence = min(0.75, 0.45 + 0.05 * min(len(verified_evidence), 6))
    if contradictions:
        status = "candidate_conflicted"
        confidence = min(confidence, 0.25)
        limitations.append("large_change_requires_review")
    return {
        "ok": True,
        "scope": scope,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_candidate_projection",
        "raw_sixdim": values,
        "candidate_needs": candidates,
        "semantic_guard": {
            "possessiveness": "仅表示关系不确定性/失去线索的候选反应，不授权控制、监视、限制或惩罚他人",
            "attachment": "仅表示持续联结线索的候选反应，不等于依赖、服从或必须维持关系",
            "security": "仅表示当前状态下的稳定/威胁线索，不是现实安全评估",
        },
        "baseline": baseline,
        "prior_candidate": prior,
        "evidence_ids": evidence_ids,
        "evidence_count": len(evidence_ids),
        "status": status,
        "confidence": round(confidence, 2),
        "contradictions": contradictions,
        "limitations": limitations,
        "governance": {
            "writes_performed": False,
            "personality_mutation": False,
            "relationship_mutation": False,
            "llm_inference_used": False,
            "do_not_use_for": ["diagnosis", "consequential decisions", "automatic personality rewrite", "automatic attachment or possessiveness behavior"],
        },
        "formula_id": "local-g6-sixdim-v1",
    }

def main():
    ap = argparse.ArgumentParser(description="Read-only evidence-gated sixdim -> three needs projection")
    ap.add_argument("--input", help="JSON input file; otherwise stdin")
    ap.add_argument("--scope")
    args = ap.parse_args()
    try:
        raw = json.loads(open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read())
        result = project(raw.get("sixdim", raw), baseline=raw.get("need_baseline"),
                         evidence=raw.get("evidence", []), prior=raw.get("prior_candidate"),
                         scope=args.scope or raw.get("scope"), source=raw.get("source", "json"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:300]}, ensure_ascii=False))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
