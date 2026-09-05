# -*- coding: utf-8 -*-
"""adapter_gate.py — 用 adapter 权限 manifest 驱动真实运行（R1）。

如果设置了 HARNESS_MCP_ADAPTER_ID，MCP 工具在执行前会查该 adapter 的 capabilities。
没设置时保持默认放行（兼容现有行为）；设置后未授权能力返回 deny。
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
        return True
    manifest = _load_manifest()
    adapter = manifest.get(adapter_id)
    if not adapter:
        return False
    caps = adapter.get("capabilities", [])
    return capability in caps


def get_adapter_id():
    return os.environ.get("HARNESS_MCP_ADAPTER_ID") or None
