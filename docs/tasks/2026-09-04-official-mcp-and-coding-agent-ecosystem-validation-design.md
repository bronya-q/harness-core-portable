---
title: Official MCP and Coding-Agent Ecosystem Validation Design
status: designed
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: ecosystem-integration-review
source_commit: 686470b
target_version: v0.5+
public: true
contains_private_data: false
topics: [mcp, coding-agent, registry, claude-code, codex, github-copilot, interoperability]
---

# 官方 MCP / Coding-Agent 生态验证执行设计

## 1. 目标

为 Harness Core Portable 建立可审计的外部生态证据链，而不是自行制造“官方认证”措辞。

目标链：

```text
仓库内协议测试
→ 官方 MCP Inspector 测试
→ 可重复安装的软件包
→ Official MCP Registry 收录
→ Claude Code / Codex / GitHub Copilot IDE 真实宿主验证
→ GitHub Copilot cloud agent 远程 MCP 验证（后续）
→ 平台目录或 Marketplace 收录（仅在平台提供入口时）
```

## 2. 术语边界

### 可以声明

- `Tested with MCP Inspector <version>`；
- `Listed in the Official MCP Registry`；
- `Tested with Claude Code <version>`；
- `Tested with Codex CLI <version>`；
- `Tested with GitHub Copilot in VS Code <version>`；
- `Published on PyPI`；
- `Submitted to <marketplace>`；
- `Accepted by <marketplace>`。

### 不可以自行声明

- `Officially certified by MCP`；
- `MCP security certified`；
- `Official Anthropic/OpenAI/GitHub partner`；
- `Approved by Claude/Codex/Copilot`；
- `Production-safe because it is in the Registry`。

Official MCP Registry 是官方集中元数据目录，收录不等于安全认证、质量评级或厂商背书。Registry 官方文档说明下游 aggregator/marketplace 可以另做安全检查、评分和策展。

## 3. 当前基线审计

### 已存在

- `harness_core/adapters/mcp_server.py`；
- `harness-core/mcp_server.py` wrapper；
- `python harness.py mcp serve`；
- `tests/test_mcp_server.py`；
- 三个工具名：`memory_list`、`events_list`、`usage_summary`；
- AGENTS/CLAUDE/Codex/DeepSeek 示例文件。

### 当前阻断项

1. `memory_list` 是始终返回空数组的 placeholder；
2. 手写 JSON-RPC，没有使用官方 MCP SDK；
3. `notifications/initialized` 不应产生普通 response，当前会返回 `id: null`；
4. 未知 method 应使用顶层 JSON-RPC `error`，当前把 error 放在 `result`；
5. `shutdown` 分支不可达，因为先进入 unknown method；
6. protocol version 硬编码为 `2024-11-05`；
7. 没有 initialize capability/version negotiation 测试；
8. 没有 malformed request、notification、cancellation、timeout、large input 测试；
9. 没有官方 Inspector 证据；
10. 没有 `pyproject.toml`、PyPI 包或其他 Registry 支持的发布载体；
11. 没有 `server.json`；
12. 没有 MCP Registry 条目；
13. `examples/agent-integrations/mcpREADME.md` 和兼容矩阵仍写 R0/无 server，与当前代码冲突；
14. 默认 event/usage 数据根必须显式约束，避免宿主误读私人本机记录；
15. 没有真实 Claude Code、Codex、Copilot 宿主执行记录。

当前合理状态：

```text
MCP implementation: R1 prototype
MCP protocol validation: R0
Official MCP Registry: not listed
Vendor-host integration: not externally tested
Vendor certification: not available/not claimed
```

## 4. 阶段 A：做成真实 MCP Server

### A1. 使用官方 Python SDK

优先使用 MCP 官方 Python SDK，不继续扩展手写协议循环。固定兼容版本并记录许可证。

建议公开入口：

```bash
python -m harness_core.mcp_server
```

或安装后：

```bash
harness-core-mcp
```

### A2. 初版只读工具

首个 Registry 版本只公开最小、可解释、只读面：

```text
harness_status
memory_list
memory_explain
events_list
usage_summary
```

暂不公开：

```text
memory_correct
memory_forget
character_activate
workspace_run
shell/process
network
Git write/push/release
```

写操作必须等到独立权限 manifest、宿主确认、审计日志和撤销验证完成后再设计。Autonomous 与 L4/L5 actual-impact 继续关闭。

### A3. 数据根必须显式

发布版 MCP server 不得静默读取维护者默认 `~/.dsh`。使用：

```text
HARNESS_MCP_DATA_DIR=<explicit path>
HARNESS_MCP_PROFILE=demo|local
HARNESS_MCP_ALLOW_PRIVATE=false  # default
```

规则：

- 未设置数据目录：只提供 synthetic demo 或返回 `UNAVAILABLE`；
- 未显式允许 private：拒绝读取 private overlay；
- scope 缺失/未知：fail closed；
- 工具结果不返回绝对本机路径；
- 日志不记录完整 prompt、token 或 secret；
- 读取事件前检查 visibility/consent/scope；
- `events_list` 默认只显示 synthetic/test provenance。

### A4. Tool schema

每个工具必须有：

- 稳定名称；
- 清晰 description；
- `inputSchema`；
- 有界 limit；
- 明确 scope；
- 结构化输出；
- 错误码；
- 数据来源与 provenance；
- 是否估算；
- 不支持状态返回 `UNAVAILABLE`，而不是伪造空成功。

例如 `memory_list` 不应继续返回 placeholder：

```json
{
  "ok": false,
  "status": "UNAVAILABLE",
  "reason": "no_explicit_data_dir"
}
```

### A5. 协议测试

至少覆盖：

- initialize；
- initialized notification 无 response；
- tools/list；
- 每个 tools/call 正常路径；
- invalid args；
- unknown tool；
- unknown JSON-RPC method；
- malformed JSON；
- request ID 保持；
- server stderr 不污染 stdout；
- shutdown/EOF；
- timeout；
- scope isolation；
- private data deny；
- secret redaction；
- Windows 中文路径/UTF-8；
- clean environment install。

## 5. 阶段 B：官方 MCP Inspector 验证

MCP Inspector 是官方 reference developer tool，可用于 Web、CLI 和 TUI。官方文档当前要求 Node 22.19.0 或更新版本。

### B1. 本地手工检查

示例：

```bash
npx @modelcontextprotocol/inspector python -m harness_core.mcp_server
```

检查：

- initialize negotiation；
- tools 可见；
- input schema 正确；
- tool call 输出可解析；
- notification 没有错误响应；
- stdout 无普通日志；
- private-deny 路径可见且可解释。

### B2. CLI/CI 检查

按执行时 Inspector 版本的官方参数运行，例如：

```bash
npx @modelcontextprotocol/inspector --cli \
  python -m harness_core.mcp_server \
  --method tools/list
```

不要永久假定参数格式；CI 固定 Inspector 版本，并把实际 `--help` 和执行命令记录进 evidence。

### B3. 保存证据

新增：

```text
docs/evidence/mcp/<version>/environment.json
docs/evidence/mcp/<version>/inspector-tools-list.json
docs/evidence/mcp/<version>/inspector-calls.json
docs/evidence/mcp/<version>/negative-tests.json
docs/evidence/mcp/<version>/README.md
```

不得保存认证 token、私人路径、私人 memory/event 正文。

完成标准：

```text
Inspector CLI rc=0
所有公开工具至少 1 个成功 fixture
所有 deny fixture 按预期拒绝
Windows + Linux CI 通过
```

## 6. 阶段 C：可安装 Python 包

Official MCP Registry 只保存元数据，不托管程序本身。Python 路线应先发布到官方 PyPI。

### C1. 新增打包文件

```text
pyproject.toml
src/ 或可明确打包的 harness_core/
README package section
LICENSE
```

console script：

```toml
[project.scripts]
harness-core-mcp = "harness_core.adapters.mcp_server:main"
```

建议 distribution name：

```text
harness-core-mcp
```

Registry server name：

```text
io.github.bronya-q/harness-core-portable
```

最终名称必须在发布前用 `mcp-publisher` 当前 schema 验证。

### C2. Registry 所有权标记

MCP Registry 官方 PyPI 所有权验证要求项目 README 包含与 `server.json` 相同的 MCP name 注释。按当前官方格式加入：

```html
<!-- mcp-name: io.github.bronya-q/harness-core-portable -->
```

### C3. PyPI 发布方式

优先使用 GitHub Actions + PyPI Trusted Publishing（OIDC），不要创建长期 PyPI token。

流程：

1. TestPyPI build/install；
2. 全新 venv 安装；
3. 启动 `harness-core-mcp`；
4. Inspector 测试；
5. 人工审批 environment；
6. 正式 PyPI 发布；
7. 从 PyPI 全新安装回读。

### C4. 供应链材料

每个版本保存：

- wheel/sdist SHA-256；
- SBOM；
- dependency licenses；
- provenance/attestation（若工作流支持）；
- Python 支持版本；
- OS matrix；
- vulnerability scan 结果；
- clean install transcript。

## 7. 阶段 D：Official MCP Registry 收录

Official Registry 当前仍是 preview，可能有 breaking changes 或数据重置。

### D1. 安装官方 publisher

从 MCP Registry 官方 release 获取 `mcp-publisher`，验证 release 来源和 checksum；不要从随机镜像复制二进制。

```bash
mcp-publisher --help
```

### D2. 创建 `server.json`

```bash
mcp-publisher init
```

预期核心内容（仅示意，以执行时 schema 为准）：

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/<version>/server.schema.json",
  "name": "io.github.bronya-q/harness-core-portable",
  "title": "Harness Core Portable",
  "description": "Local-first, scoped memory visibility tools for coding agents.",
  "version": "<semver>",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "harness-core-mcp",
      "version": "<same-version>",
      "transport": {"type": "stdio"}
    }
  ]
}
```

版本必须与 PyPI 包和 Git tag 对齐。不能拿现有 alpha.2 tag 指向后来才实现的 MCP server；应发布新的 SemVer pre-release。

### D3. 登录和发布

GitHub auth 命名空间要求与账号匹配：

```bash
mcp-publisher login github
mcp-publisher publish
```

不要把登录 token 放入命令历史、仓库、CI log 或聊天。

### D4. 回读验证

通过 Registry API 搜索完整名称并保存：

- Registry URL；
- name/version；
- package identifier；
- transport；
- published timestamp；
- API response 的脱敏副本。

只有此时可以写：

```text
Listed in the Official MCP Registry
```

仍不可以写“官方安全认证”。

## 8. 阶段 E：Claude Code 真实宿主验证

Claude Code 官方支持 local stdio 和 remote HTTP MCP。

项目级 stdio 示例：

```bash
claude mcp add --scope project harness-core -- \
  python -m harness_core.mcp_server
```

也可以使用 `.mcp.json`，但不能写入 secret。项目 scope 配置进入仓库前必须使用可移植命令，不能包含维护者绝对路径。

验证脚本：

1. 全新 clone；
2. 全新 venv 从 PyPI 安装；
3. `claude mcp list`/等价官方命令确认连接；
4. Claude Code 显示全部只读 tools；
5. 调用 synthetic `harness_status`；
6. 调用 synthetic `memory_list`；
7. 尝试 private scope，必须拒绝；
8. 确认未出现写工具；
9. 断开 server，宿主应显示失败而不是伪造结果；
10. 保存版本与脱敏 transcript。

证据措辞：

```text
Tested with Claude Code <exact version> on <OS>, <date>
```

这不是 Anthropic 认证。若未来提交 Claude plugin marketplace，应建立独立任务并引用平台当时的审核规则。

## 9. 阶段 F：OpenAI Codex 真实宿主验证

Codex 官方文档支持 CLI 和 `config.toml` 配置 MCP。优先使用 CLI 添加，避免手写过时配置：

```bash
codex mcp add harness-core -- python -m harness_core.mcp_server
```

执行时先运行：

```bash
codex mcp --help
codex mcp add --help
```

以安装版本实际帮助为准。

验证：

- MCP server 能启动；
- tools/list 可见；
- synthetic tool call 成功；
- private scope 被拒绝；
- 工作目录变化不导致绝对路径依赖；
- server 退出后 Codex 明确报错；
- 无 secret 泄漏；
- AGENTS.md 指令与 MCP 权限互不扩大；
- 不自动执行 Git push/Release。

证据措辞：

```text
Tested with Codex CLI <exact version> on <OS>, <date>
```

这不是 OpenAI partner/certification 声明。

## 10. 阶段 G：GitHub Copilot

### G1. 先做 IDE 本地测试

在 VS Code/Copilot Chat 使用官方 MCP 配置入口添加 stdio server。不要先碰 cloud agent，因为本地 stdio 更适合 local-first 数据边界。

验证同 Claude/Codex，并额外检查：

- VS Code Workspace Trust；
- 工具审批 UI；
- `.vscode/mcp.json` 是否可移植；
- 配置不包含 secret/绝对路径；
- Copilot Agent mode 是否明确显示实际调用工具。

### G2. Cloud agent 需要 remote MCP

GitHub Copilot cloud agent 在 GitHub.com 运行，不能访问用户电脑上的本地 SQLite。要验证它必须另建远程 MCP 服务或仅提供 synthetic/public 数据服务。

安全架构：

```text
Cloud Copilot
→ authenticated HTTPS MCP
→ public/synthetic dataset only
→ no private local overlay
→ no filesystem/process/Git write tools
```

GitHub 官方说明 repository MCP configuration 同时供 Copilot cloud agent 和 Copilot code review 使用，并且 agent 可以自主使用可用工具、不会在每次调用前询问。因此云端配置必须只暴露低风险工具。

不得把本机私人记忆上传到远程服务来换取“认证”。

### G3. Repository 配置

由仓库管理员在 GitHub Settings → Copilot → MCP servers 配置。secret 放 GitHub secrets/对应官方 secret 管理，不进入仓库 JSON。

验证：

- assign synthetic issue 给 Copilot；
- agent 成功调用 `harness_status`；
- 日志能证明 tool call；
- private scope 永远不可达；
- malicious issue prompt 不能扩大工具权限；
- 无写工具；
- disconnect/timeout 明确失败；
- 删除配置后工具不可见。

证据措辞：

```text
Tested with GitHub Copilot cloud agent on <date>
```

不能写“GitHub certified”，除非 GitHub 提供并正式授予相应资格。

## 11. Coding-agent 指令文件验证

### AGENTS.md

要从示例升级到真实 R2：

1. 在仓库根提供真正的 `AGENTS.md` 或明确复制步骤；
2. 修复示例中的错误路径 `docs/ROADMAP.md`（实际是根 `ROADMAP.md`）；
3. 至少用 Codex 在 clean clone 中执行一次受控任务；
4. 验证指令被读取；
5. 验证不能借指令扩大 MCP 权限；
6. 保存脱敏 transcript。

### CLAUDE.md

要从示例升级到真实 R2：

1. 在 clean clone 放置项目级 `CLAUDE.md`；
2. 用 Claude Code 读取并执行只读任务；
3. 检查“不自动 push、不读取 private overlay”约束；
4. 加 hooks 时单独验证 hook 输入、secret redaction 和 failure behavior。

### GitHub Copilot instructions

应新增并测试官方支持的：

```text
.github/copilot-instructions.md
```

需要时再增加 path-specific instructions 或 custom agent 文件。仅有 AGENTS/CLAUDE 示例不能证明 Copilot 兼容。

## 12. 外部账号与成本

可能需要：

| 外部条件 | 用途 | 是否必须付费 |
|---|---|---|
| GitHub 账号 | Registry GitHub auth、仓库与 CI | 基础可免费 |
| PyPI 账号/Trusted Publisher | 发布 Python 包 | 免费 |
| Node 22.19+ | MCP Inspector | 免费 |
| Claude Code 可用账号 | 真实 Claude host 测试 | 取决于账号/计划 |
| OpenAI Codex 可用账号 | 真实 Codex 测试 | 取决于账号/计划 |
| GitHub Copilot entitlement | IDE/cloud agent 测试 | 取决于计划 |
| HTTPS hosting/domain | remote MCP/cloud-agent | 可能产生费用 |

不得为了外部验证绕过用户授权、购买服务或上传私人数据。

## 13. 统一证据矩阵

每个平台保存：

| 字段 | 要求 |
|---|---|
| host | Claude Code/Codex/Copilot/Inspector |
| host_version | 精确版本 |
| server_version | 精确 SemVer |
| commit | 完整 SHA |
| package | PyPI name + SHA-256 |
| OS/Python/Node | 精确版本 |
| install_mode | clean clone/PyPI/wheel |
| transport | stdio/HTTP |
| tools_list | 实际工具名 |
| success_cases | 每工具至少一个 synthetic case |
| deny_cases | private/scope/write/secret |
| disconnect_case | 明确失败 |
| result | pass/fail/unavailable |
| transcript | 脱敏路径 |
| reviewer | 人工复核者 |
| verified_at | ISO 时间 |

## 14. 发布门槛

### MCP R2 门槛

- 官方 SDK；
- Inspector 通过；
- unit + integration + negative tests；
- Windows/Linux clean install；
- 明确数据根；
- private deny；
- 只读工具；
- security review；
- 文档与代码一致。

### Registry Listed 门槛

- PyPI 正式包可安装；
- `server.json` 当前 schema 通过；
- version 对齐；
- Registry API 可回读；
- 没有使用“认证”误导措辞。

### Host Tested 门槛

- 真实付费/授权宿主；
- 精确版本；
- clean environment；
- success + deny + disconnect；
- 脱敏证据；
- 第二人复核或公开可重复步骤。

## 15. 推荐实施顺序

```text
P0 修复协议和文档漂移
P1 官方 SDK + 只读工具 + 数据根 fail-closed
P2 Inspector + CI + 安全负向测试
P3 PyPI/TestPyPI + supply-chain evidence
P4 Official MCP Registry
P5 Claude Code + Codex 本地 stdio
P6 GitHub Copilot IDE
P7 synthetic-only remote MCP + Copilot cloud agent
P8 可选 Marketplace/Plugin 提交
```

不要先做 P7。local-first 项目的价值不应为了 cloud badge 被破坏。

## 16. 第一批具体任务

1. 将 MCP 原型从手写 JSON-RPC 迁移到官方 SDK；
2. 删除 `memory_list` placeholder；
3. 增加 `harness_status` 并默认 synthetic-only；
4. 实现 `HARNESS_MCP_DATA_DIR` 和 private deny；
5. 补 protocol/negative/security tests；
6. 添加 Inspector CI；
7. 修正 `mcpREADME.md` 与 `AGENT_COMPATIBILITY.*`；
8. 修复 AGENTS 示例中的 ROADMAP 路径；
9. 新增 `pyproject.toml` 与 console script；
10. TestPyPI clean-install；
11. 建 `server.json`；
12. 新版本打 tag，不移动 alpha.2；
13. 发布 PyPI；
14. 发布 Registry；
15. 分别执行 Claude/Codex/Copilot 真实宿主验证。

## 17. 官方参考资料

- MCP Registry Quickstart: <https://modelcontextprotocol.io/registry/quickstart>
- MCP Registry About: <https://modelcontextprotocol.io/registry/about>
- MCP Registry Package Types: <https://modelcontextprotocol.io/registry/package-types>
- MCP Registry Authentication: <https://modelcontextprotocol.io/registry/authentication>
- MCP Inspector: <https://modelcontextprotocol.io/docs/tools/inspector>
- Claude Code MCP: <https://docs.anthropic.com/en/docs/claude-code/mcp>
- OpenAI Codex MCP: <https://developers.openai.com/codex/mcp/>
- GitHub Copilot repository MCP: <https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers>
- GitHub Copilot MCP concept: <https://docs.github.com/en/copilot/concepts/agents/cloud-agent/mcp-and-cloud-agent>

执行时必须重新核对官方文档，因为 Registry 当前是 preview，CLI/schema/宿主配置可能变化。

## 18. 后辈接手说明

- 不要把 Registry listing 改写为 certification；
- 不要把单元测试改写为真实 host test；
- 不要发布 placeholder 工具；
- 不要让 MCP server 默认读取维护者 `~/.dsh`；
- 不要通过云服务暴露 private overlay；
- 不要把 secret 写入 `.mcp.json`、`server.json`、CI log 或文档；
- 不要移动已有 alpha.2 tag 来装入后来实现的 MCP；
- 每个平台必须有精确版本和负向测试；
- 外部发布、账号登录、付费和 GitHub 设置更改均需用户明确授权；
- 保持 Autonomous 与 L4/L5 actual-impact disabled。
