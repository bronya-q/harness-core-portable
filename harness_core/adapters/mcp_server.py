# -*- coding: utf-8 -*-
"""MCP server for Harness Core Portable.

Uses the official MCP Python SDK when available; falls back to a minimal
stdio JSON-RPC implementation otherwise. Public surface: memory list,
event list, usage summary. No private persona content, no network upload.

Install:
  pip install harness-core-portable[mcp]
Run:
  python -m harness_core.adapters.mcp_server
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT = Path(__file__).resolve().parent.parent.parent
_SKILL = _ROOT / "harness-core"
sys.path.insert(0, str(_SKILL))

try:
    from mcp.server.fastmcp import FastMCP

    MCP = FastMCP("harness-core-mcp")
    HAS_SDK = True
except Exception:
    MCP = None
    HAS_SDK = False


def _memory_list(scope: str = "character:demo") -> dict:
    from harness_core.adapter_gate import can, get_adapter_id
    _aid = get_adapter_id()
    if _aid and not can(_aid, "memory_read"):
        return {"ok": False, "error": "adapter_permission_denied", "capability": "memory_read"}
    import subprocess, sys as _sys
    p = subprocess.run([_sys.executable, str(_SKILL / "notebook.py"), "list", "--scope", scope],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"ok": False, "raw": p.stdout[-300:], "stderr": p.stderr[-300:]}


def _events_list(limit: int = 10) -> dict:
    from harness_core.adapter_gate import can, get_adapter_id
    _aid = get_adapter_id()
    if _aid and not can(_aid, "event_read"):
        return {"ok": False, "error": "adapter_permission_denied", "capability": "event_read"}
    from event_store import list_events
    return {"ok": True, "events": list_events(limit=limit)}


def _usage_summary() -> dict:
    from harness_core.adapter_gate import can, get_adapter_id
    _aid = get_adapter_id()
    if _aid and not can(_aid, "usage_read"):
        return {"ok": False, "error": "adapter_permission_denied", "capability": "usage_read"}
    from event_store import list_usage
    rows = list_usage(limit=1000)
    actual = sum(r.get("actual_tokens") or 0 for r in rows)
    baseline = sum(r.get("baseline_tokens") or 0 for r in rows)
    avoided = sum(r.get("estimated_avoided_tokens") or 0 for r in rows)
    by_source = {}
    for r in rows:
        src = r.get("usage_source") or "unknown"
        by_source.setdefault(src, {"rows": 0, "actual_tokens": 0})
        by_source[src]["rows"] += 1
        by_source[src]["actual_tokens"] += r.get("actual_tokens") or 0
    by_provider = {}
    for r in rows:
        prov = r.get("provider") or "unreported"
        by_provider.setdefault(prov, {"rows": 0, "prompt_tokens": 0, "completion_tokens": 0})
        by_provider[prov]["rows"] += 1
        by_provider[prov]["prompt_tokens"] += r.get("prompt_tokens") or 0
        by_provider[prov]["completion_tokens"] += r.get("completion_tokens") or 0
    return {"ok": True, "rows": len(rows), "actual_tokens": actual, "baseline_tokens": baseline,
            "avoided_tokens": avoided, "by_source": by_source, "by_provider": by_provider}


def _register_sdk():
    @MCP.tool()
    def memory_list(scope: str = "character:demo") -> str:
        """List scoped memory notes."""
        return json.dumps(_memory_list(scope), ensure_ascii=False)

    @MCP.tool()
    def events_list(limit: int = 10) -> str:
        """List recent event envelope records."""
        return json.dumps(_events_list(limit), ensure_ascii=False)

    @MCP.tool()
    def usage_summary() -> str:
        """Summarize recorded token usage."""
        return json.dumps(_usage_summary(), ensure_ascii=False)


if HAS_SDK:
    _register_sdk()

# ---- Fallback minimal JSON-RPC (used when mcp package is not installed) ----
TOOLS = [
    {"name": "memory_list", "description": "List scoped memory notes.",
     "inputSchema": {"type": "object", "properties": {"scope": {"type": "string"}}}},
    {"name": "events_list", "description": "List recent event envelope records.",
     "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "usage_summary", "description": "Summarize recorded token usage.",
     "inputSchema": {"type": "object", "properties": {}}},
]


def _call(name, args):
    if name == "memory_list":
        return _memory_list(args.get("scope", "character:demo"))
    if name == "events_list":
        return _events_list(int(args.get("limit", 10)))
    if name == "usage_summary":
        return _usage_summary()
    return {"ok": False, "error": "unknown_tool:" + name}


def _fallback_main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        method = req.get("method")
        rid = req.get("id")
        params = req.get("params", {}) or {}
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                      "serverInfo": {"name": "harness-core-mcp", "version": "0.2.0"}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments", {}) or {}
            content = _call(name, args)
            result = {"content": [{"type": "text", "text": json.dumps(content, ensure_ascii=False)}],
                      "isError": content.get("ok") is False}
        elif method == "notifications/initialized":
            result = None
        else:
            resp = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue
        resp = {"jsonrpc": "2.0", "id": rid, "result": result}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def main():
    if HAS_SDK:
        MCP.run()
    else:
        _fallback_main()


if __name__ == "__main__":
    main()
