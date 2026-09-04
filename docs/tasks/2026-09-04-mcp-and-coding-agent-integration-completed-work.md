---
title: MCP 与 Coding-Agent 集成已完成工作记录
status: verified
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: ecosystem-integration-review
source_commit: b1f49fe
target_version: v0.5+
public: true
contains_private_data: false
topics: [mcp, coding-agent, fastmcp, packaging, interoperability, verification]
---

# MCP 与 Coding-Agent 集成：已经完成的工作

## 1. 文档目的

本文只记录 Harness Core Portable 在 MCP / coding-agent 方向**已经实现并能够在仓库内核验**的部分。

本文不把以下概念混为一谈：

```text
仓库内实现
≠ MCP Inspector 验证
≠ Official MCP Registry 收录
≠ Claude Code / Codex / Copilot 真实宿主验证
≠ 厂商认证或官方背书
```

目前不存在一个适用于所有 MCP server 和 coding agent 的统一“官方认证”。项目当前最准确的状态是：

```text
MCP 仓库内集成：R1 prototype
仓库内协议冒烟测试：通过
Python wheel 构建：通过
Official MCP Registry：未收录
真实 coding-agent 宿主测试：未完成
厂商认证：未获得，也不宣称
```

## 2. 已完成事项总表

| 项目 | 当前状态 | 证据 |
|---|---|---|
| MCP stdio server | ✅ implemented | `harness_core/adapters/mcp_server.py` |
| 官方 MCP Python SDK 接入 | ✅ implemented | `mcp.server.fastmcp.FastMCP` |
| 无 SDK 时的标准库 fallback | ✅ implemented | `_fallback_main()` |
| MCP initialize | ✅ locally tested | `tests/test_mcp_server.py` |
| initialized notification flow | ✅ locally tested | 测试发送 notification 后可继续完成 tools/list；尚未单独断言零响应 |
| tools/list | ✅ locally tested | 至少返回 3 个工具 |
| `memory_list` | ✅ implemented | 调用真实 notebook list，而非固定空数组 |
| `events_list` | ✅ implemented | 读取 event store |
| `usage_summary` | ✅ implemented | 汇总 token usage |
| Python module 启动入口 | ✅ implemented | `python -m harness_core.adapters.mcp_server` |
| 根 CLI MCP 入口 | ✅ implemented | `python harness.py mcp serve` |
| Python console script | ✅ implemented | `harness-core-mcp` |
| `pyproject.toml` | ✅ implemented | setuptools package metadata |
| MCP optional dependency | ✅ implemented | `mcp>=1,<2` |
| wheel 构建 | ✅ locally verified | `pip wheel . --no-deps` rc=0 |
| 仓库内 MCP metadata | ✅ implemented | `docs/mcp/server.json` |
| MCP 验证状态页 | ✅ implemented | `docs/mcp/verification.md` |
| Agent 兼容矩阵 Markdown | ✅ updated | MCP 标记为 R1 |
| AGENTS.md fixture | ✅ implemented | `examples/agent-integrations/AGENTS.md` |
| CLAUDE.md fixture | ✅ implemented | `examples/agent-integrations/CLAUDE.md` |
| Codex fixture | ✅ implemented | `examples/agent-integrations/codex.md` |
| DeepSeek fixture | ✅ implemented | `examples/agent-integrations/deepseek.md` |
| Official MCP Inspector | ⬜ not completed | 无 Inspector 运行证据 |
| Official MCP Registry | ⬜ not completed | Registry 查询 count=0 |
| Claude Code real-host test | ⬜ not completed | 无版本化运行记录 |
| Codex CLI real-host test | ⬜ not completed | 无版本化运行记录 |
| GitHub Copilot real-host test | ⬜ not completed | 无版本化运行记录 |
| PyPI publication | ⬜ not completed | 只验证本地 wheel 构建 |

## 3. MCP Server 实现

### 3.1 官方 SDK 路径

服务优先导入官方 MCP Python SDK：

```python
from mcp.server.fastmcp import FastMCP
MCP = FastMCP("harness-core-mcp")
```

成功导入后，用 `@MCP.tool()` 注册工具，并通过：

```bash
python -m harness_core.adapters.mcp_server
```

启动 stdio server。

这证明官方 SDK 已接入代码路径，但尚不等于通过 MCP Inspector 或某个宿主的完整互操作验证。

### 3.2 标准库 fallback

如果运行环境没有安装 `mcp` 包，代码会进入最小 stdio JSON-RPC fallback。

fallback 已实现：

- `initialize`；
- `tools/list`；
- `tools/call`；
- `notifications/initialized` 分支；
- unknown method 顶层 JSON-RPC error。

它保证最小离线可运行性，但不能代替官方 SDK 和 Inspector 的协议合规证明。

### 3.3 当前只读工具面

已注册三个工具：

```text
memory_list
  → 按 scope 列出 notebook memory

events_list
  → 列出 event envelope 记录

usage_summary
  → 汇总 actual/baseline/estimated avoided tokens
```

当前没有向 MCP 暴露这些高影响操作：

```text
shell/process execution
workspace run
Git write/push
GitHub Release
character activation
memory deletion/correction
network upload
Autonomous tasks
```

因此 MCP 面目前保持小型、读取导向。Autonomous 与 L4/L5 actual-impact 继续禁用。

## 4. 已完成的协议测试

测试文件：

```text
tests/test_mcp_server.py
```

测试执行的消息顺序：

```text
initialize request
→ notifications/initialized notification
→ tools/list request
```

断言包括：

- 进程返回码为 0；
- initialize result 存在；
- server name 为 `harness-core-mcp`；
- initialized notification 后仍可继续处理 tools/list；
- tools/list result 存在；
- 工具数量不少于 3。

当前测试没有显式断言 notification 的 response 数量为零，因此本文不把“零响应”列为已独立验证项。

本次复测：

```text
python -m unittest tests.test_mcp_server -v
Ran 1 test
OK
```

完整仓库回归：

```text
python -m unittest discover -s tests -v
Ran 8 tests
OK
```

测试必须从仓库根目录运行，因为测试 fixture 当前使用 `Path.cwd()` 定位项目。

### 尚未覆盖的协议测试

- malformed JSON；
- malformed JSON-RPC request；
- unknown method 自动化断言；
- unknown tool；
- tool exception；
- cancellation；
- timeout；
- shutdown；
- large input；
- Inspector-generated protocol suite；
- SDK 不存在时 fallback 的独立测试矩阵。

所以当前应称为“仓库内协议冒烟测试通过”，不应称为完整 MCP conformance。

## 5. Python 打包基础

已经增加：

```text
pyproject.toml
project name: harness-core-portable
optional extra: mcp = ["mcp>=1,<2"]
console script: harness-core-mcp
```

本次验证：

```bash
python -m pip wheel . --no-deps
```

结果：

```text
rc=0
harness_core_portable-0.1.0-py3-none-any.whl
```

这证明源代码可以在当前环境中构建 wheel。它不证明：

- 已发布到 TestPyPI/PyPI；
- 从 PyPI 干净安装可用；
- wheel 内所有运行时文件完整；
- Linux/macOS 安装可用；
- console script 已在隔离 venv 中端到端验证。

另外，Python package version 当前为 `0.1.0`，Git tag 为 `v0.1.0-alpha.3`。正式发布前应采用一致的 PEP 440 版本，例如 `0.1.0a3`，并同步 MCP metadata。

## 6. 仓库内 MCP metadata

已提供：

```text
docs/mcp/server.json
```

其中记录：

- server name；
- description；
- stdio transport；
- Python module command；
- 三个工具；
- `local_only` 隐私定位。

这是一份仓库内 integration manifest。目前没有证据证明它已经通过 Official MCP Registry 的当前 schema 校验或成功提交。因此不能把该文件称为 Registry listing。

## 7. Coding-Agent 接入材料

已提供的公开合成 fixture：

```text
examples/agent-integrations/AGENTS.md
examples/agent-integrations/CLAUDE.md
examples/agent-integrations/codex.md
examples/agent-integrations/deepseek.md
examples/agent-integrations/mcpREADME.md
```

已经表达的工作流包括：

- 先运行离线 Demo；
- 运行 doctor/selfcheck；
- 使用 memory/character/workspace；
- 大改前编写 Task Design；
- 部署后编写 Deployment Record；
- 不自动 push；
- 不自动创建 GitHub Release；
- 不读取 private local overlay；
- 不启用 autonomous tasks。

这些 fixture 是 integration guidance，不是 Claude Code、Codex 或 GitHub Copilot 已兼容的运行证据。

### 已知文档漂移

以下内容仍需修正：

- `examples/agent-integrations/AGENTS.md` 写了不存在的 `docs/ROADMAP.md`，实际是根目录 `ROADMAP.md`；
- `examples/agent-integrations/mcpREADME.md` 仍写 `No MCP server in this repo yet (R0)`；
- `docs/AGENT_COMPATIBILITY.json` 仍写 MCP R0/no server；
- `python harness.py ecosystem status` 读取该 JSON，因此运行输出仍错误显示 MCP R0；
- Markdown 兼容矩阵已经更新为 R1，与 JSON/CLI 不一致。

因此“兼容状态展示一致性”尚未完成。

## 8. 隐私与权限边界

已经做到：

- MCP 工具面没有 shell、Git push、Release 或 workspace execution；
- 文档声明 local-first/no network upload；
- 示例不要求 API key；
- 本次验证使用仓库和临时构建目录，没有读取私人 persona corpus；
- Autonomous execution 保持 disabled。

仍未完成设计要求中的显式 MCP 数据根：

```text
HARNESS_MCP_DATA_DIR
HARNESS_MCP_PROFILE=demo|local
HARNESS_MCP_ALLOW_PRIVATE=false
```

当前 `events_list`/`usage_summary` 最终会使用 event store 默认数据目录；`memory_list` 也会走 notebook 默认目录。尚未建立“未显式配置数据根则只返回 synthetic/UNAVAILABLE”的 fail-closed 行为。

因此在接入真实第三方宿主前，显式数据根、scope/visibility/consent 检查仍是 P0。

## 9. 外部状态

截至本记录复核：

| 外部项目 | 状态 | 可声明措辞 |
|---|---|---|
| MCP Inspector | 未运行 | 不可声明 Tested with MCP Inspector |
| Official MCP Registry | 查询 count=0 | Not listed |
| Claude Code | 未运行真实宿主测试 | Not externally tested |
| Codex CLI | 未运行真实宿主测试 | Not externally tested |
| GitHub Copilot | 未运行真实宿主测试 | Not externally tested |
| PyPI | 未验证发布 | Wheel builds locally |
| 厂商安全/质量认证 | 无统一认证且未获得 | Not claimed |

## 10. 当前允许使用的公开表述

可以：

```text
Includes an experimental stdio MCP server built with the official MCP Python SDK.
Repository smoke tests cover initialize, initialized notification, and tools/list.
The Python package builds as a wheel locally.
Experimental integration fixtures are provided for AGENTS.md, CLAUDE.md, and Codex-style workflows.
```

中文：

```text
项目包含一个使用官方 MCP Python SDK 构建的实验性 stdio MCP server。
仓库内冒烟测试覆盖 initialize、initialized notification 和 tools/list。
Python 包已在本地验证可构建 wheel。
项目提供 AGENTS.md、CLAUDE.md 与 Codex 风格的实验性接入模板。
```

不可以：

```text
Officially MCP Certified
MCP Security Certified
Official Anthropic/OpenAI/GitHub integration
Verified with Claude Code/Codex/Copilot
Listed in the Official MCP Registry
Published on PyPI
Production-ready MCP server
```

除非未来取得对应的外部证据。

## 11. 后续外部验证清单

按证据强度依次执行：

1. 修复 integration status JSON/Markdown/CLI 漂移；
2. 实现显式 MCP data root 与 default-deny private policy；
3. 增加 MCP negative/error/fallback tests；
4. 在干净 venv 安装 wheel 并运行 console script；
5. 运行官方 MCP Inspector，保存版本、命令、输出和时间；
6. 对齐 PEP 440 package version；
7. 经授权发布 TestPyPI/PyPI；
8. 准备符合 Registry 当前 schema 的 server metadata；
9. 经授权提交 Official MCP Registry；
10. 回读 Registry API，确认准确条目；
11. 分别在 Claude Code、Codex CLI、GitHub Copilot 中测试；
12. 每个宿主记录版本、OS、安装方式、配置、工具列表、成功调用、断连和清理；
13. 只有取得证据后才升级兼容矩阵和 README 声明。

## 12. 复现命令

从仓库根目录运行：

```bash
python -m unittest tests.test_mcp_server -v
python -m unittest discover -s tests -v
python -m pip wheel . --no-deps
python release_verify.py
python -m harness_core.adapters.mcp_server
```

最后一个命令启动 stdio server，应由 MCP client/Inspector 驱动，不是普通交互式聊天界面。

## 13. 后辈接手说明

- 不要把“使用官方 SDK”写成“官方认证”；
- 不要把仓库内 `server.json` 写成 Registry 已收录；
- 不要把 fixture 存在写成真实宿主已验证；
- 不要把本地 wheel build 写成 PyPI 已发布；
- 首先修 explicit data root 和 compatibility status 漂移；
- 外部账号登录、PyPI 发布、Registry 提交和 Marketplace 操作必须获得用户明确授权；
- 不自动启用 Autonomous 或 L4/L5 actual-impact；
- 所有后续任务和部署继续留下 successor-facing Markdown。

## 14. 最终判定

```text
已完成：MCP R1 实现、官方 SDK 路径、fallback、3 个工具、基础协议测试、Python 打包和 coding-agent fixtures
仓库内测试：通过
外部生态验证：未完成
Official Registry：未收录
真实宿主兼容性：未证明
官方/厂商认证：不宣称
下一步：隐私 fail-closed → Inspector → isolated install → Registry → real-host tests
```
