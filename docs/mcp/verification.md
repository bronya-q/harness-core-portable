# MCP Verification Status

## Current

- Official MCP Python SDK v1 (`mcp>=1,<2`) wired via `harness_core.adapters.mcp_server`.
- Public entrypoint: `python -m harness_core.adapters.mcp_server`
- Installable package with extra: `pip install harness-core-portable[mcp]`
- CLI entrypoint: `harness-core-mcp`
- `python harness.py mcp serve` fallback when SDK unavailable.

## Protocol smoke test

```bash
python -m unittest tests.test_mcp_server -v
```

Passes initialize + tools/list.

## Inspector / Registry / Hosts

| Item | Status |
|---|---|
| MCP Inspector | ⚠️ 已尝试 CLI（`npx @modelcontextprotocol/inspector --cli --method tools/list -- python -m harness_core.adapters.mcp_server`），本机 Windows 超时（rc=124），未取得成功输出；需后续排查或在 Linux/容器环境重试 |
| Official MCP Registry | ⬜ 未提交 |
| Claude Code | ⬜ 未验证 |
| Codex CLI | ⬜ 未验证 |
| GitHub Copilot IDE | ⬜ 未验证 |

See `docs/tasks/2026-09-04-official-mcp-and-coding-agent-ecosystem-validation-design.md` for the full plan.
