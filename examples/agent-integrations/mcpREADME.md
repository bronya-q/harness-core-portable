# MCP integration (R1 prototype)

This repo ships a stdio MCP server using the official FastMCP SDK.

```bash
# from a source checkout with optional MCP extra installed
python -m pip install -e ".[mcp]"
python -m harness_core.adapters.mcp_server
# or via the installed console entry point
harness-core-mcp
```

Provided tools (R1):

- `memory_list` — list local memories for a scope
- `events_list` — list recent unified events
- `usage_summary` — summarize token usage

## Current status

| Item | Status |
|---|---|
| Official FastMCP SDK path | implemented |
| stdlib fallback path | implemented |
| `initialize` + `notifications/initialized` + `tools/list` | tested in repo |
| MCP Inspector | not run |
| Official MCP Registry | not listed |
| Claude Code / Codex / Copilot host test | not run |
| PyPI publication | not externally verified |

## Boundary

- The server is local-first and does not open a network port.
- It is a prototype, not a vendored/anonymous host integration.
- Keep `autonomous_tasks=disabled` and do not store private API keys in this public repo.
