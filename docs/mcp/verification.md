# MCP Verification Status

## Current

- Official MCP Python SDK v1 (`mcp>=1,<2`) wired via `harness_core.adapters.mcp_server`.
- Public entrypoint: `python -m harness_core.adapters.mcp_server`
- Installable package with extra: `pip install harness-core-portable[mcp]`
- CLI entrypoint: `harness-core-mcp`
- `python harness.py mcp serve` fallback when SDK unavailable.
- Local HTTP loopback MCP server for Inspector / host testing:
  `python -m harness_core.adapters.mcp_http_server --port 8931`

## Protocol smoke test

```bash
python -m unittest tests.test_mcp_server -v
```

Passes initialize + tools/list.

## Inspector evidence

### tools/list via HTTP loopback

```bash
python -m harness_core.adapters.mcp_http_server --port 8932 &
npx -y @modelcontextprotocol/inspector \
  --cli --format json \
  --method tools/list \
  --server-url http://127.0.0.1:8932/mcp
```

Output:

```json
{"result":{"tools":["memory_list","events_list","usage_summary"]}}
```

### tools/call via HTTP loopback

```bash
npx -y @modelcontextprotocol/inspector \
  --cli --format json \
  --method tools/call \
  --tool-name memory_list \
  --tool-arg scope=character:demo \
  --server-url http://127.0.0.1:8933/mcp
```

Output:

```json
{"result":{"content":[{"type":"text","text":"{\"ok\": true, \"scope\": \"character:demo\", \"notes\": []}"}],"isError":false}}
```

> 通过。这是本地 loopback HTTP transport，不代表官方 Registry 收录或真实宿主认证。

## Inspector / Registry / Hosts

| Item | Status |
|---|---|
| MCP Inspector | ✅ 已通过（HTTP loopback，`tools/list` + `tools/call`） |
| Official MCP Registry | ⬜ 未提交 |
| Claude Code | ⬜ 未验证 |
| Codex CLI | ⬜ 未验证 |
| GitHub Copilot IDE | ⬜ 未验证 |

See `docs/tasks/2026-09-04-official-mcp-and-coding-agent-ecosystem-validation-design.md` for the full plan.
