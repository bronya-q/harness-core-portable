# -*- coding: utf-8 -*-
"""Minimal loopback HTTP MCP server for Inspector / host testing.

This is NOT a public network server. It binds to 127.0.0.1 and is intended
for local MCP Inspector validation. The tool implementations reuse the same
stdio server functions (`harness_core.adapters.mcp_server`).

Usage:
  python -m harness_core.adapters.mcp_http_server --port 8931
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from harness_core.adapters.mcp_server import _events_list, _memory_list, _usage_summary

TOOLS = [
    {"name": "memory_list", "description": "List scoped memory notes.",
     "inputSchema": {"type": "object", "properties": {"scope": {"type": "string"}}}},
    {"name": "events_list", "description": "List recent event envelope records.",
     "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "usage_summary", "description": "Summarize recorded token usage.",
     "inputSchema": {"type": "object", "properties": {}}},
]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8")
        try:
            req = json.loads(body)
        except Exception:
            self._json({"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": "parse error"}}, 400)
            return
        method = req.get("method")
        rid = req.get("id")
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05",
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "harness-core-mcp-http", "version": "0.2.0"}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = req.get("params", {}) or {}
            name = params.get("name", "")
            args = params.get("arguments", {}) or {}
            content = _call_json(name, args)
            result = {"content": [{"type": "text", "text": json.dumps(content, ensure_ascii=False)}],
                      "isError": content.get("ok") is False}
        elif method in ("notifications/initialized",):
            self.send_response(202)
            self.end_headers()
            return
        else:
            self._json({"jsonrpc": "2.0", "id": rid,
                        "error": {"code": -32601, "message": "method not found"}})
            return
        self._json({"jsonrpc": "2.0", "id": rid, "result": result})

    def _json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def _call_json(name, args):
    if name == "memory_list":
        return _memory_list(args.get("scope", "character:demo"))
    if name == "events_list":
        return _events_list(int(args.get("limit", 10)))
    if name == "usage_summary":
        return _usage_summary()
    return {"ok": False, "error": "unknown_tool:" + name}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8931)
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("harness-core-mcp-http listening on http://%s:%d/mcp" % (args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
