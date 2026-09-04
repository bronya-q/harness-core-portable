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
| MCP Inspector | ⚠️ 已尝试 CLI；Windows 直接传 stdio 命令时出现两种现象：无输出超时/`No servers found in config file`。最小 Node MCP server 手动 stdio 正常，但 Inspector CLI 仍报“No servers found in config file”，说明该 CLI 版本可能要求 `--server-url` 或 catalog/config 条目，而不是原生 stdio 命令；需改用 `--config`/`--catalog` 或 HTTP transport |
| Official MCP Registry | ⬜ 未提交 |
| Claude Code | ⬜ 未验证 |
| Codex CLI | ⬜ 未验证 |
| GitHub Copilot IDE | ⬜ 未验证 |

See `docs/tasks/2026-09-04-official-mcp-and-coding-agent-ecosystem-validation-design.md` for the full plan.
