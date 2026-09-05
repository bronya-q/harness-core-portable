# -*- coding: utf-8 -*-
"""usage_recorder.py — 将 provider usage 写入本地 token_usage（提供方有真实值时调用）。

用于 OpenAI-compatible adapter 等入口：拿到 provider 真实 prompt/completion tokens 后，
回填到统一 usage 表，避免只靠字符估算。
"""
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SKILL = _ROOT / "harness-core"


def record(provider, model, prompt_tokens=0, completion_tokens=0, total_tokens=None, components=None):
    if total_tokens is None:
        total_tokens = int(prompt_tokens or 0) + int(completion_tokens or 0)
    data = {
        "usage_source": "provider_reported",
        "provider": provider,
        "model_id": model,
        "actual_tokens": int(total_tokens or 0),
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "components": dict(components or {}),
        "baseline_id": "provider_reported",
        "baseline_tokens": 0,
        "estimated_avoided_tokens": 0,
    }
    try:
        if str(_SKILL) not in sys.path:
            sys.path.insert(0, str(_SKILL))
        from event_store import record_usage
        return record_usage(data)
    except Exception:
        return None
