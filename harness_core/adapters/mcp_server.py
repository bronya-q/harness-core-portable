# -*- coding: utf-8 -*-
"""Minimal MCP (Model Context Protocol) server over stdio.

Exposes a small read-only/memory-management surface to MCP-capable clients.
No private persona content, no network, no automatic upload.

Protocol: JSON-RPC 2.0 over line-delimited stdio.
Methods: initialize, tools/list, tools/call, notifications/initialized.
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

from event_store import list_events, list_usage  # noqa: E402


def _memory_list(args):
    scope = args.get("scope", "character:demo")
    return {"ok": True, "notes": []}  # placeholder replaced by subprocess-free memory list? Use event_store? For now simple


def _usage_summary(args):
    rows = list_usage(limit=1000)
    actual = sum(r.get("actual_tokens") or 0 for r in rows)
    baseline = sum(r.get("baseline_tokens") or 0 for r in rows)
    avoided = sum(r.get("estimated_avoided_tokens") or 0 for r in rows)
    return {"ok": True, "rows": len(rows), "actual_tokens": actual, "baseline_tokens": baseline,
            "avoided_tokens": avoided}


def _events_list(args):
    limit = int(args.get("limit", 10))
    return {"ok": True, "events": list_events(limit=limit)}


def _tools():
    return [
        {"name": "memory_list", "description": "List scoped memory notes (demo scope by default).",
         "inputSchema": {"type": "object", "properties": {"scope": {"type": "string"}}}},
        {"name": "events_list", "description": "List recent event envelope records.",
         "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
        {"name": "usage_summary", "description": "Summarize recorded token usage.",
         "inputSchema": {"type": "object", "properties": {}}},
    ]


def _call_tool(name, args):
    if name == "memory_list":
        return _memory_list(args)
    if name == "events_list":
        return _events_list(args)
    if name == "usage_summary":
        return _usage_summary(args)
    return {"ok": False, "error": "unknown_tool:" + name}


def main():
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
                      "serverInfo": {"name": "harness-core-mcp", "version": "0.1.0"}}
        elif method == "tools/list":
            result = {"tools": _tools()}
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments", {}) or {}
            content = _call_tool(name, args)
            result = {"content": [{"type": "text", "text": json.dumps(content, ensure_ascii=False)}],
                      "isError": content.get("ok") is False}
        elif method == "notifications/initialized":
            result = None
        else:
            result = {"error": {"code": -32601, "message": "method not found"}}
        resp = {"jsonrpc": "2.0", "id": rid, "result": result}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()
        if method == "shutdown":
            break


if __name__ == "__main__":
    main()
