#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""host_guide.py — 宿主导航（如何把 MCP server 接入各真实宿主）。"""
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if args and args[0] == "host-guide":
        args = args[1:]
    if len(args) > 0:
        print(__doc__)
        return 1
    guide = {
        "mode": "host_guide",
        "hosts": [
            {"name": "Claude Code", "steps": [
                "claude mcp add harness-core -- python -m harness_core.adapters.mcp_server",
                "或使用 HTTP：python -m harness_core.adapters.mcp_http_server --port 8931",
                "然后让 Claude Code 指向 http://127.0.0.1:8931/mcp",
            ]},
            {"name": "Codex CLI", "steps": [
                "codex mcp add harness-core -- python -m harness_core.adapters.mcp_server",
                "或 HTTP：python -m harness_core.adapters.mcp_http_server --port 8931",
            ]},
            {"name": "GitHub Copilot (VS Code / JetBrains)", "steps": [
                "在 MCP 配置中添加本地 stdio 或 HTTP 指向 harness-core",
                "示例配置见 docs/mcp/verification.md",
            ]},
        ],
        "permission": "adapter_gate 默认 fail-closed：未设置 HARNESS_MCP_ADAPTER_ID 时拒绝；显式设置 HARNESS_ALLOW_UNCONFIGURED=1 可放行（仅本地开发）。",
        "note": "这是导航说明，非认证；真实宿主测试需各自环境验证。",
    }
    print(json.dumps({"ok": True, **guide}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
