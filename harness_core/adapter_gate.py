# -*- coding: utf-8 -*-
"""adapter_gate.py — 用 adapter 权限 manifest 驱动真实运行（R1）。

Fail-closed：未设置 HARNESS_MCP_ADAPTER_ID 时默认拒绝（deny）。
仅当显式设置 HARNESS_ALLOW_UNCONFIGURED=1 时才放行未配置 adapter（本地开发兼容）。
设置 HARNESS_MCP_ADAPTER_ID 后按 manifest capabilities 校验。
"""
import json
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST = _ROOT / "harness-core" / "adapters.example.json"


def _load_manifest():
    try:
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {a.get("adapter_id"): a for a in data}
        if isinstance(data, dict) and data.get("adapter_id"):
            return {data["adapter_id"]: data}
    except Exception:
        pass
    return {}


def can(adapter_id, capability):
    if not adapter_id:
        return os.environ.get("HARNESS_ALLOW_UNCONFIGURED") == "1"
    manifest = _load_manifest()
    adapter = manifest.get(adapter_id)
    if not adapter:
        return False
    caps = adapter.get("capabilities", [])
    return capability in caps


def get_adapter_id():
    return os.environ.get("HARNESS_MCP_ADAPTER_ID") or None
