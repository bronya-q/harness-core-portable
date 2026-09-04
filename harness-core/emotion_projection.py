#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""emotion_projection.py - read-only sixdim -> expression/pet projection.

This is an additive G1 adapter. It does not write memory, emotion_state, or
persona files. Values follow the existing sixdim -100..100 convention and the
LingChat mapping documented in the research reports.
"""
import argparse
import json
import sys

EMOTIONS = ("joy", "anger", "sadness", "fear", "surprise", "disgust")
LABELS = {
    "joy": "高兴",
    "anger": "生气",
    "sadness": "无奈",
    "fear": "警惕",
    "surprise": "惊讶",
    "disgust": "无语",
}
# Conservative display mapping. A quiet baseline should not acquire a prefix.
PET_LEVELS = ("low", "neutral", "positive", "energetic")


def normalize(values):
    out = {}
    for name in EMOTIONS:
        raw = values.get(name)
        if raw is None and name == "sadness":
            raw = values.get("sad")
        try:
            out[name] = max(-100.0, min(100.0, float(raw if raw is not None else 0.0)))
        except (TypeError, ValueError):
            out[name] = 0.0
    return out


def project(sixdim, baseline=None, scope=None, source="input"):
    values = normalize(sixdim)
    has_baseline = bool(baseline)
    base = normalize(baseline or {}) if has_baseline else None
    deltas = {name: round(values[name] - base[name], 1) for name in EMOTIONS} if base is not None else None
    dominant = max(EMOTIONS, key=lambda name: values[name])
    dominant_delta = deltas[dominant] if deltas is not None else None
    negative_peak = max(values["anger"], values["sadness"], values["fear"], values["disgust"])
    positive = values["joy"]
    if deltas is None:
        prefix = None
        prefix_reason = "baseline_not_provided"
    elif max(abs(v) for v in deltas.values()) <= 10:
        prefix = None
        prefix_reason = "within_baseline_band"
    else:
        prefix = LABELS[dominant]
        prefix_reason = "dominant_emotion_deviation"
    if values["fear"] >= 75 or values["anger"] >= 85:
        pet_level = "low"
        pet_reason = "boundary_alert"
    elif negative_peak >= 55 and negative_peak > positive:
        pet_level = "low"
        pet_reason = "negative_peak"
    elif positive >= 85 and values["surprise"] >= 60:
        pet_level = "energetic"
        pet_reason = "joy_and_arousal_high"
    elif positive >= 75:
        pet_level = "positive"
        pet_reason = "joy_high"
    elif positive >= 50:
        pet_level = "positive"
        pet_reason = "joy_moderate"
    else:
        pet_level = "neutral"
        pet_reason = "no_strong_signal"
    return {
        "ok": True,
        "scope": scope,
        "source": source,
        "sixdim": values,
        "baseline": base,
        "baseline_delta": deltas,
        "dominant_emotion": dominant,
        "expression": {"prefix": prefix, "label": LABELS[dominant], "reason": prefix_reason, "max_segments": 2},
        "pet": {"level": pet_level, "reason": pet_reason},
        "deep_needs": {"status": "not_projected", "note": "九维三项需求需沿用既有公式，当前适配器不猜测或写回"},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="JSON 文件；省略则从 stdin 读取")
    ap.add_argument("--scope")
    ap.add_argument("--baseline", help="可选基线 JSON 文件")
    args = ap.parse_args()
    try:
        raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
        data = json.loads(raw)
        baseline = {}
        if args.baseline:
            baseline = json.loads(open(args.baseline, encoding="utf-8").read())
        sixdim = data.get("sixdim", data)
        result = project(sixdim, baseline.get("sixdim", baseline), args.scope or data.get("scope"), "json")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:300]}, ensure_ascii=False))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
