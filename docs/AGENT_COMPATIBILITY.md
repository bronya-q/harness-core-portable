# Agent Compatibility

说明本项目与当代 AI Agent 生态的集成状态。

> 集成状态会变化。此文件只描述当前状态，不宣称未验证的兼容性。

## 状态等级

| 等级 | 含义 |
|---|---|
| R0 | researched / planned, not currently integrated |
| R1 | prototype / experimental, usage may change |
| R2 | documented and tested in this repo |

## 适配面

| 生态 | 状态 | 说明 |
|---|---|---|
| AGENTS.md-based coding agents | R1 | 项目以 `AGENTS.md` 作为上下文入口，可作为 Codex 等 agent 的项目记忆/上下文基础 |
| CLAUDE.md / hook workflows | R1 | 可提供项目说明、hooks 与 handoff 方向，未做官方 Claude Code 插件 |
| MCP-capable clients | R0 | 当前未提供 MCP server；未来可通过本地事件 API/命令暴露 |
| OpenAI-compatible / DeepSeek backends | R1 | runtime 支持本地 Ollama，理论上可通过兼容端点接入 DeepSeek 等服务，未做完整云端测试 |
| Trae / ZCode | R0 | 当前无专门适配 |

## 真实使用建议

- 把本仓库作为“本地角色/记忆/上下文可见性”层，接入你自己的 agent 工作流。
- 不要把本文件当成厂商认证或官方集成证明。
- 所有集成均保持 local-first，不自动上传。
