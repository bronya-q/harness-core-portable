---
title: Harness Core Portable 全项目进展审计
status: verified
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: project-progress-review
source_commit: 9b6c54e
target_version: v0.2-v0.5
public: true
contains_private_data: false
topics: [project-audit, progress, roadmap, release, mcp, testing]
---

# Harness Core Portable 全项目进展审计

## 1. 审计口径

本报告区分：

```text
designed
implemented
locally tested
clean-clone verified
externally tested
deployed/released
```

报告的 `status: verified` 只表示本次盘点已完成，不表示整个项目完成。

最终复测绑定：

```text
功能/发布基线: v0.1.0-alpha.3 → b3ad9fc
报告首次登记: 9b6c54e
审计结束时仓库: main 与 origin/main 持续推进；最终 git 状态见报告提交后的实际命令
```

审计期间仓库持续并发推进。MCP/packaging 在中途曾处于测试失败的未提交状态，随后已由 `d36f471` 完成、由 `b3ad9fc` 冻结 alpha.3，并在 `9b6c54e` 登记本报告。最终结论只采用完成后的重新验证结果；中途红灯不再作为当前状态。

没有读取私人 overlay、私人语料、API key 或私人数据库正文。

## 2. 一页结论

项目已经从“脚本与说明集合”进入“可运行的 alpha 工程原型”阶段。离线演示、scope 隔离、记忆纠错/恢复、静态控制台、角色包基础、安全校验、工作区、A/B、事件/usage、MCP 原型和基本测试都已有真实代码。

当前最准确判断：

```text
产品概念与架构：较完整
公开离线体验：可运行并经 clean clone 验证
本地角色/记忆基础：可用 alpha
HCP 角色资产：安全和事务基础明显增强，仍非完整沙箱/热挂载
Workspace：真实 worktree 基础可运行，仍非完整隔离执行环境
Dashboard：只读投影可用，真实读取耗时实现有计时边界问题
测试：5 文件/8 用例，本机与 clean clone 通过；没有 CI workflow
MCP：官方 FastMCP SDK + fallback + wheel 基础完成，仍是 R1，未做 Inspector/真实宿主
测量：bootstrap CI 与 Cohen’s kappa 工具已实现，心理效度未建立
知识桥：主要仍是配置/展示，实际 mount/delegation 未完成
游戏：未发现可玩的卡牌游戏引擎
n-gram fallback：未发现实现证据
首次用户研究：只有 protocol/template，没有参与者结果
发布：alpha.2 GitHub Pre-release 已发布；alpha.3 tag 已推送但 Release API 尚为 404
生产就绪：否
```

## 3. 进展评分（工程成熟度，不是心理效度）

| 领域 | 成熟度 | 说明 |
|---|---:|---|
| 项目定位/边界设计 | 4/5 | public/synthetic/private 分层清楚，但公开名称残留 |
| README/首次理解 | 4/5 | 首屏和一分钟 Demo 明显改善；仍缺真实截图/GIF与用户数据 |
| 离线 Demo | 4/5 | clean clone 通过、隔离/纠错/恢复/清理可见 |
| 记忆与 scope | 4/5 | 核心路径存在；全入口 resolver/policy 一致性仍不足 |
| 角色资产 HCP | 3.5/5 | validate/install/preview/activation/rollback 与安全检查有进展 |
| Situated character | 2.5/5 | schema/mode/关系事件基础存在，完整关系—处境 UX 尚未闭环 |
| Knowledge Stewardship | 1.5/5 | schema/config/list 基础；真实 mount/health/delegation 未完成 |
| Workspace/Evidence | 3/5 | worktree/run/evidence 基础可运行；非完整沙箱 |
| Dashboard/可观测性 | 3/5 | 静态只读、escape/CSP、事件/usage/读取 timing；部分 timing 有 bug |
| Token telemetry | 2.5/5 | storage/summary/estimate 基础；provider usage 全入口覆盖未证明 |
| 数据 provenance/consent | 2/5 | 字段和部分 identity consent 存在；首次运行分项同意未完成 |
| 测量学 | 2/5 | 工程指标、bootstrap、κ 工具存在；构念字典/效度研究缺失 |
| 测试与 CI | 2.5/5 | 8 个 unittest 在本机/clean clone 通过；无 GitHub Actions、多 OS、Inspector |
| MCP/Agent 生态 | 2/5 | FastMCP、fallback、wheel 和仓库测试存在；未 Inspector/Registry/host-tested |
| Release 工程 | 3/5 | alpha.2 Pre-release 存在；alpha.3 tag/notes/manifest 已备，Release 页面尚未创建 |
| 可玩卡牌游戏 | 0/5 | 未发现 game engine/game loop/规则/CLI |
| n-gram fallback | 0/5 | 未发现实现或测试 |

## 4. 已验证通过

### 4.1 已提交基线

在最终 HEAD 和临时 clean clone 中：

```text
python release_verify.py           PASS, 183 entries
python package_selfcheck.py        PASS
python -m unittest discover        PASS, 8 tests
python harness.py demo --offline   PASS（本次审计前段）
pip wheel . --no-deps              PASS，生成 0.1.0 wheel
```

离线 Demo 验证：

- 创建两个 synthetic 角色；
- 跨会话召回；
- Alice/Bob scope 隔离；
- 共享 Story Core 不泄露私人记忆；
- 用户纠错；
- 版本恢复；
- Autonomous disabled；
- 无网络上传；
- 临时数据清理。

### 4.2 发布冻结点

已验证的外部 alpha.2：

```text
v0.1.0-alpha.2 → d7f7de7e2fdfaecba43921c0e13016ebb7113c8b
Release URL: https://github.com/bronya-q/harness-core-portable/releases/tag/v0.1.0-alpha.2
draft: false
prerelease: true
published_at: 2026-09-04T11:53:58Z
archive release_verify: PASS, 133 entries
archive package_selfcheck: PASS
```

最新 alpha.3：

```text
v0.1.0-alpha.3 → b3ad9fc4991c4282f0bfcc195b72066dd17d308c
local tag: exists and annotated
remote/main: contains the tag commit
GitHub Release API: 404 at audit time
```

因此 alpha.3 的准确状态是“tag 已部署，Release 页面尚未外部可回读”，不能称 GitHub Pre-release 已完成。`/releases/latest` 404 仍属正常，因为没有 stable/latest Release。

### 4.3 测试增长

已有 5 个测试文件、8 个用例：

- activation failure/rollback；
- ecosystem status；
- Memory/Event/Usage Python API；
- MCP initialize/tools list；
- bootstrap CI；
- Cohen’s kappa。

这是相较早期“无常规测试”的显著进步。

### 4.4 HCP 安装安全

当前代码确认 install 会先 validate，ZIP 使用 `_safe_extract_zip`，并检查多类风险。合成恶意 ZIP 实测：

```text
../escape.txt
→ install rc=1
→ package_validation_failed
→ zip_path_traversal
```

已有/声称覆盖：

- traversal；
- symlink；
- ADS；
- nested zip；
- 大小/压缩比；
- public executable；
- JSON/PNG MIME 基础一致性。

仍不能称为完整恶意包沙箱；未做全面 fuzz、资源耗尽和跨平台攻击矩阵。

### 4.5 Activation

已有：

- preflight；
- state history；
- lock file；
- backup/rollback/recover；
- `--simulate-failure`；
- failure injection unittest。

测试验证激活 B 失败后 active 仍为 A，再 recover 回到 active 状态。

仍缺：真实进程崩溃、断电、锁竞争、多进程并发和完整持久化回放。

### 4.6 Workspace

在临时 clean clone 中实测：

```text
workspace create                 rc=0
workspace worktree create       rc=0
workspace run ...               rc=0, WORKTREE_OK
workspace worktree remove       rc=0
```

这已经不再只是元数据。但命令输出明确说明它是基本命令约束，不是完整沙箱。

### 4.7 Schema

`schema list` 现已包含：

- unified-role；
- event-envelope；
- token-usage；
- situated-mode。

validator 增加了顶层 type/enum 检查。但发现 `--mode` 接线遗漏：帮助和 map 支持它，CLI parser 实际只识别 role/event/token，实测 rc=1。

### 4.8 Dashboard

隔离 `DSH_HOME` 构建 rc=0；静态文件、CSP、HTML escaping 和无服务模式存在。

真实读取 timing 已开始实现，但：

- `event_usage_read_ms` 与 `char_read_ms` 在同一时点赋值，Character Assets span 近似 0；
- `total_ms` 在 HTML render 之前记录，所以 HTML render span 不是真正完整渲染耗时；
- 标题仍写“结构示意；真实耗时待采集”，下方又写真实读取耗时，文案冲突。

## 5. MCP 与打包当前状态

审计中途曾出现 SDK migration 红灯；随后已由 `d36f471` 修复并提交。最终复测：

```text
Official FastMCP SDK path: implemented
stdlib fallback path: implemented
valid initialize + initialized notification + tools/list unittest: PASS
pyproject.toml / console entry point: implemented
clean-clone wheel build: PASS
wheel filename: harness_core_portable-0.1.0-py3-none-any.whl
```

仍需准确限制声明：

```text
MCP compatibility: R1 prototype
MCP Inspector: not run
Official Registry: not listed
Claude/Codex/Copilot host test: not run
PyPI publication: not externally verified
```

`docs/mcp/server.json` 是仓库内 integration manifest，不等于 Official MCP Registry 的规范发布证据。wheel project version 仍为 `0.1.0`，而 Git tag 为 `v0.1.0-alpha.3`；正式 PyPI 发布前必须统一 PEP 440 版本策略。

## 6. 外部生态状态

### GitHub

- public repository：是；
-语言：Python；
- stars/watchers：1/1；
- forks：0；
- open issues：0；
- discussions：关闭；
- alpha.1/alpha.2/alpha.3 annotated tags：存在；
- alpha.2 Pre-release：存在；
- alpha.3 GitHub Release：审计时 API 404，尚未外部验证；
- stable latest release：不存在。

### Topics

API 回读到 19 个 Topics，包括：

```text
harness
harness-plugin
ai-evaluation-tools
humanization
llm-agentic-workflow
local-first
local-first-ai
long-term-memory
long-term-memory-benchmark
long-term-memory-llm
memory-system
multi-agent
multi-agent-ai
personal
roleplay-ai
sqlite
agent-memory
coding-agent-memory
context-engineering
```

Topics 已真实部署，但部分词较宽泛。应继续按“实现+UX+验证+文档至少三类证据”维护，尤其 `harness-plugin`、`multi-agent-ai`、`coding-agent-memory`。

### MCP Registry

查询：

```text
io.github.bronya-q/harness-core-portable
```

结果 count=0。尚未收录。

## 7. 与原始目标的对应

| 原始方向 | 当前状态 |
|---|---|
| 隔离人格 | 基础实现并由 Demo 验证 |
| 长期记忆 | 基础实现并有跨会话 Demo |
| 每角色语料 | corpus-to-draft 基础存在 |
| 角色热切换 | activation 状态存在；真正全入口 runtime 热挂载未完成 |
| 场景卡 | Character Card scenario → Story Core 草稿基础存在 |
| 可玩卡牌游戏 | 未实现 |
| n-gram fallback | 未发现实现 |
| 可视化 | 静态 Dashboard 已实现基础 |
| 工程角色 | workspace/evidence/A-B 基础存在 |
| 本地知识角色 | bindings/sources 列表基础；真实 mount/delegation 未完成 |
| 切身化关系角色 | relationship/episode/mode schema 基础；用户可理解的完整闭环仍不足 |
| grounded diary/reflection | 数据表和部分命令存在；完整 candidate→review→apply→rollback 链未验证 |
| Token 节省可视化 | estimate/usage 面板基础；provider reported 覆盖未证明 |
| 用户同意 | 字段与部分 explicit consent 存在；首次运行分项同意未完成 |
| 测量学 | 工程工具开始补齐；构念字典、信效度计划及真实研究未完成 |

## 8. 明确缺口

### P0：保持绿灯并补自动化

1. 当前 `unittest`、`release_verify`、`package_selfcheck` 已恢复 rc=0；
2. 将这些检查加入 CI，防止只在本机发现回归；
3. 给 MCP 增加 malformed JSON、unknown method、shutdown 与 tool error 测试；
4. 补 alpha.3 Download ZIP/外部 clone 证据，而不只依赖本地 clone。

### P0：状态一致性

1. 兼容矩阵 Markdown 已更新为 MCP R1，但 JSON 仍写 R0/no server；
2. `mcpREADME.md` 仍写没有 MCP server；
3. alpha.2 部署记录仍写 Release 页面待创建，与外部 API 不一致；
4. ROADMAP 把 alpha.3 写成 next Pre-release，但外部 Release 尚未创建，应明确 tag-only；
5. ROADMAP 工作区状态必须随实际 commit 更新，避免静态“clean/synced”谎报；
6. ROADMAP 第 303 行仍说 bridge/span 未实现，与 P2 勾选冲突；
7. v0.3 task 仍写 ADS/MIME 未完成，与后续代码冲突；
8. pyproject version `0.1.0` 与 tag `v0.1.0-alpha.3` 需要 PEP 440 对齐。

### P1：公开边界

公开仓库仍出现偏好型私人角色名称，位置包括 README、Knowledge Stewardship 和若干测量脚本。P0“私人案例已抽象化”不能视为完全完成。

### P1：CLI/Schema

- 根 `python harness.py --help` 仍 rc=1；
- `schema validate --mode` 未接线；
- 顶层 launcher 对 passthrough 脚本的实际 rc 传播不统一；
- `package_selfcheck` 的 root help 只测试无参数，不测试 `--help`。

### P1：Runtime policy

当前默认值与既定核心政策不一致：

```text
代码：g1_expression=shadow, dynamic_memory=shadow
既定目标：g1_expression=canary, dynamic_memory=canary
```

更重要的是 resolver/policy 仅被少量入口导入。尚无证据证明所有 memory/persona/MCP/workspace/dashboard 入口都统一执行 resolver 与 runtime policy。

### P1：数据质量

- event schema 没有明确 session provenance `real/demo/smoke/regression/unknown` 字段；
- Dashboard 没有按 real/demo/smoke 分组；
- vector worker 有 retry/stale/error 机制，但没有统一 dashboard telemetry/持续监控证据；
- `skip_unavailable` 把队列项标 done，需要明确是否允许以后重试；
- provider-reported usage 全入口覆盖未证明。

### P2：测量学

已有 bootstrap/κ 函数不等于完成测量学：

- 没有独立构念字典；
- 没有统一 trait/state/behavior/self_report/inference schema；
- 没有真实双标注数据；
- 没有效度研究；
- 没有首次用户研究结果；
- 没有 Krippendorff’s alpha。

### P2：CI/跨平台

没有 `.github/workflows`。当前只证明本机 Windows 和临时本地 clone，未证明 GitHub Actions、Linux/macOS 或 Python version matrix。

### P2：产品体验

- README 没有真实截图/GIF；
- 首次用户 protocol 存在但没有 5 人结果；
- Demo 运行后自动删除，所以 protocol 中紧接着查找 Alice memory 的步骤可能无法执行，需要重设计测试 fixture；
- Dashboard 的数据路径/状态来源对非专家仍可更直观。

### P3：缺失能力

- 可玩卡牌游戏；
- n-gram fallback；
- 实际知识源 mount/health/delegation；
- 全入口 character hot-load；
- migration/dry-run/rollback/compatibility window；
- 完整沙箱；
- Official MCP Registry 与真实 coding-agent host tests。

## 9. 推荐下一轮顺序

```text
1. 修所有状态漂移和 alpha.2/alpha.3 部署记录
2. 修 --help、schema --mode、Dashboard timing
3. 增加 GitHub Actions Windows/Linux CI
4. 完成 public identifier 清理
5. 真正统一 resolver/runtime policy 全入口
6. session/content provenance + vector telemetry
7. 首次运行分项 consent
8. 构念字典与 measurement schema
9. 首次用户测试
10. MCP Inspector → TestPyPI/PyPI → Registry → Host tests
11. alpha.3 Release 页面经授权创建后做 API/ZIP 回读；不移动现有 tags
12. 单独设计并实现 n-gram fallback 和可玩卡牌游戏
```

## 10. 发布建议

alpha.3 tag 已经创建并推送，但不应自动创建外部 Release 页面；该动作仍需明确授权。当前也不适合继续追加新 tag，原因：

- alpha.3 GitHub Release API 尚为 404；
- 文档状态和代码状态仍有漂移；
- v0.3 task 的验收框尚未按证据更新；
- 无 CI；
- root help 与 schema mode 仍失败。

下一次发布动作前应满足：

```text
clean worktree
HEAD == origin/main
all tests green
release_verify green
package_selfcheck green
Windows/Linux CI green
malicious HCP fixture green
activation failure/recovery green
schema --mode green
public boundary scan green
release notes/tag/manifest aligned
GitHub Release deployment record prepared
```

## 11. 后辈接手说明

- 开始前先运行 `git status`；仓库有并发推进，不能依赖旧 HEAD；
- 本报告功能复测基线为 release tag `b3ad9fc`，首次登记 commit 为 `9b6c54e`；
- 不要把 Registry listing 称为认证；
- 不要把 worktree runner 称为沙箱；
- 不要把读取 timing 称为模型推理 span；
- 不要把 bootstrap/κ 工具称为心理效度；
- 不要把 role activation marker 称为全入口热挂载；
- 不要把 tag 后的 main 能力写进 alpha.2；
- 保持 Autonomous 与 L4/L5 actual-impact disabled；
- 所有外部发布、账号登录、付费和设置更改需要用户授权。

## 12. 最终判定

```text
项目阶段：快速发展的 alpha 工程原型
公开可体验性：已建立
基础可靠性：明显提升
当前工作区健康：绿灯（tests/selfcheck/release_verify/clean-clone wheel）；提交态需连同最新 manifest 一起落库
外部发布：alpha.2 Pre-release 已发布；alpha.3 只有 tag，Release API 404
主线发布准备：部分完成，仍缺 CI/ZIP/文档一致性
MCP 仓库内状态：R1，可测试、可构建 wheel
MCP 外部生态：尚未 Inspector/Registry/host-tested
可玩游戏：尚未
生产就绪：否
下一关键目标：状态一致性 + CI + resolver/policy 全入口 + 数据/测量闭环
```

## 13. 后续处理记录（2026-09-04 续）

在报告提交后，按推荐顺序推进了以下项：

1. 状态漂移：`AGENT_COMPATIBILITY.json` MCP 改为 R1；`mcpREADME.md` 改为“已有 R1 server”；alpha.2 部署记录改为 deployed；alpha.3 改为 tag-only（status=implemented）；DEPLOYMENTS_INDEX 加入 alpha.3；ROADMAP 修正 alpha.3 与 Runtime Bridge 状态；v0.3 task 的 ADS/MIME/激活测试更新；pyproject version 对齐 PEP 440 `0.1.0a3`。
2. CLI/Schema：根 `harness.py --help` 返回 0；`schema validate --mode` 接线并支持 modes 集合；`schema list` 增加 measurement。
3. CI：新增 `.github/workflows/ci.yml`（Windows/Linux × py3.11/3.13）。
4. 公开边界：扫描确认私有角色名只保留在 `local_records_export.py` 的 sanitizer 映射中，作为替换规则而非公开内容。
5. Runtime policy：默认 `g1_expression` / `dynamic_memory` 改为 canary（与 example policy 对齐）；autonomous_tasks 仍 disabled。
6. Provenance / telemetry：event 增加 `session_provenance` / `content_provenance`；Dashboard 增加来源分组；`vector_queue.queue_status()` 与 `data status` 暴露队列摘要。
7. Consent：`privacy consent --status/--set` 实现首次运行分项同意记录。
8. 构念字典：新增 `docs/measurement/CONSTRUCT_DICTIONARY.md` 与 `schemas/measurement.schema.json`。
9. n-gram fallback：新增 `harness-core/ngram_fallback.py` 与 `tests/test_ngram_fallback.py`（目前 unittest 9 个用例）。

仍未做：MCP Inspector/Registry/host、用户首测、alpha.3 Release 页面、可玩卡牌游戏、完整 resolver/policy 全入口覆盖。

## 14. 后续处理记录（2026-09-04 续 2）

- **向量队列“以后重试”语义**：`skip_unavailable` 不再把项标为 done，而是标记为 `deferred` 并写入 `next_retry_at` / `retry_count`；worker 默认指数退避，`--retry-failed` 可重新打开 `failed` 项。`queue_status` / `data status` 增加 `deferred` 与 `retryable`。
- **provider usage 全入口覆盖（R1 起步）**：Ollama `/api/generate` 返回的 `prompt_eval_count` / `eval_count` 现在在 roleplay 入口写入 `provider_reported` 记录；`event_store.token_usage` 增加 `provider` / `prompt_tokens` / `completion_tokens`；`usage summary` 输出 `by_source` 与 `by_provider`；`OpenAICompatibleAdapter` 增加 `chat_with_usage`。
- **可玩卡牌游戏**：新增 `harness-core/card_game.py`（Harness Memory Match），支持 `play` / `deal` / `deck`，含公开合成牌组、配对评分、自动冒烟模式，以及 `tests/test_card_game.py`。
- 测试数量增至 14 个用例。

## 15. 后续处理记录（2026-09-04 续 3）

- **alpha.3 Release 页面**：经用户授权，已用 `gh release create` 创建 GitHub Pre-release 页面，状态 `draft=false / prerelease=true`，URL 可从 `https://github.com/bronya-q/harness-core-portable/releases/tag/v0.1.0-alpha.3` 回读。部署记录与 DEPLOYMENTS_INDEX 同步更新为 `deployed`。

## 16. 后续处理记录（2026-09-04 续 4）

- **Knowledge Stewardship R1 最小闭环**：在 `assets_commands.py` 增加 `knowledge health` / `knowledge mount` / `knowledge delegate`。
  - `health`：检查知识源目录存在/可读，并匹配 steward 与角色 binding；
  - `mount`：把角色对知识域登记为“只读挂载状态”（写入 `knowledge-mounts.json`），明确不是完整知识桥；
  - `delegate`：按关键词匹配负责知识域，返回负责角色与是否允许，不传递知识正文。
  - 新增 `tests/test_knowledge_stewardship.py`（3 用例），unittest 总数 17。

## 17. 后续处理记录（2026-09-04 续 5）

- **Dashboard 可视化增强**：新增纯 CSS/CSP-safe 的可视化卡片：
  - 知识域与挂载（source 健康状态横向条形 + 挂载登记）
  - 向量队列（pending / processing / deferred / done / failed 条形）
  - Token 来源 / Provider（按 provider 聚合 token 与记录数）
  - 新增 `tests/test_dashboard_visualization.py`（1 用例），unittest 总数 18。

## 18. 后续处理记录（2026-09-04 续 6）

- **真实 Dashboard 截图 / 滚动 GIF**：用 `demo --offline --keep` + `dashboard build` + 无头 Edge 生成真实合成数据全页截图，替换 README 合成图；`dashboard.py` 页脚改为 `~/.dsh/memory-emotion` 脱敏显示；新增 `tools/generate_real_dashboard_gif.py` 生成滚动 GIF。
- **首次启动同意向导**：`python harness.py start` 首次运行会询问 `memory/story/notebook/telemetry` 分项同意并写入 `consent.json`。
- **写操作预览 → 确认 → 撤销**：`memory write --scope <s> --text <t> [--yes]` 先预览再确认，写入后可用 `memory undo --id <id>` 归档撤销。
- **知识桥真实只读访问最小步**：`knowledge access --role <r> --source <s> [--query <q>]` 校验授权后读取目录清单/有限文本摘要，不修改不上传。
- **MCP Inspector**：CLI 已尝试，本机 Windows 超时（rc=124），记录为待继续，未伪造成功。
- 新增 `tests/test_user_experience_flows.py`（3 用例），unittest 总数 21。

## 19. 后续处理记录（2026-09-04 续 7）

- **知识桥下一步**：新增 `knowledge suggest --question <q> --role <r> [--limit 3]`，把「委派匹配 + 授权 + 只读访问」连成一步，返回有限上下文片段；不改动知识源。
- **Dashboard 写操作预览**：Dashboard 增加「最近写操作（可撤销预览）」卡片，列出最近 manual 笔记，并给出 `memory undo --id` 撤销命令；真实截图/GIF 已重新生成。
- **MCP Inspector**：Windows/WSL 的 CLI 仍未拿到成功输出；后续需排查 npx/stdio 挂起，或换容器 CI 环境。
- `tests/test_knowledge_stewardship.py` 增加 suggest 用例，unittest 总数 22。

## 20. 后续处理记录（2026-09-04 续 8）

- **n-gram fallback 接入 `memory search`**：`harness.py memory search --query <q>` 在精确子串无结果时自动调用 `ngram_fallback.py`，返回 `source=ngram_fallback`。
- **alpha.4 实现推进记录**：新增 `docs/tasks/2026-09-04-alpha4-implementation-progress.md`，记录已完成/尝试/下一步。
- unittest 总数 23。

## 21. 后续处理记录（2026-09-04 续 9）

- **高风险操作二次确认**：为 `memory forget`、`privacy reset-demo`、`workspace worktree remove`、`workspace release` 增加二次确认；支持 `--yes` 跳过；取消返回 `status=cancelled`。
- `tests/test_user_experience_flows.py` 增加确认/取消用例，unittest 总数 24。

## 22. 后续处理记录（2026-09-04 续 10）

- **A/B / Evidence / Workspace 可视化**：Dashboard 新增「工程工作区 / Evidence」卡片，列出 workspace lease 与 evidence bundle 的关键状态；`test_dashboard_visualization` 增加对应断言。unittest 总数 24。

## 23. 后续处理记录（2026-09-04 续 11）

- **导出前预览**：`privacy export` 与 `feedback export --redacted` 增加预览 + 确认；支持 `--yes`；取消不写文件。
- `tests/test_user_experience_flows.py` 增加 privacy export 预览/确认用例，unittest 总数 25。

## 24. 后续处理记录（2026-09-04 续 12）

- **知识桥受控返回预算**：`knowledge access` / `knowledge suggest` 支持 `--max-chars`，默认 200，片段按预算截断并返回 `max_chars`。
- **MCP Inspector 根因线索**：用最小 Node MCP server 手动 stdio 正常，但 Inspector CLI 仍报 `No servers found in config file`，说明该 CLI 版本可能要求 `--server-url` 或 catalog/config 条目，而非直接传 stdio 命令。

## 25. 后续处理记录（2026-09-04 续 13）

- **合规/公共边界快照**：Dashboard 新增「公共边界快照」卡片，扫描 README/CONTRIBUTING/SECURITY/LICENSE 中的私人标识、绝对路径与 overlay 引用；`test_dashboard_visualization` 增加断言。

## 26. 后续处理记录（2026-09-04 续 14）

- **首次使用向导细化**：`start` 在首次同意后显示「首次使用提示」；选择 Demo 前提示临时合成数据、自动清理与 `--keep`。unittest 总数不变（25）。

## 27. 后续处理记录（2026-09-04 续 15）

- **知识桥多源合并去重**：`knowledge suggest` 支持 `--sources`（默认 2），访问多个匹配知识源并合并去重片段，`sources` 字段列出各源。

## 28. 后续处理记录（2026-09-04 续 16）

- **高风险二次确认再扩展**：`character deactivate`、`character remove`、`backup restore` 增加二次确认；`--yes` 可跳过；取消返回 `status=cancelled`。unittest 总数 26。

## 29. 后续处理记录（2026-09-04 续 17）

- **A/B 结果可视化**：`ab role` / `ab retriever` 支持 `--save <name>` 写入 `docs/evidence/ab-*.json`；Dashboard 新增「A/B 记录」卡片；`test_dashboard_visualization` 增加断言。

## 30. 后续处理记录（2026-09-04 续 18）

- **知识桥 Suggest 历史可视化**：`knowledge suggest` 写入 `~/.dsh/harness/knowledge-suggest-history.json`；Dashboard 新增「知识桥 Suggest 历史」卡片；`test_dashboard_visualization` 增加断言。

## 31. 后续处理记录（2026-09-04 续 19）

- **写操作 GUI 预览**：`memory write --html` 生成 `memory-write-preview.html`，在浏览器查看预览，不写入 notebook；`test_user_experience_flows` 新增用例，unittest 总数 27。

## 32. 后续处理记录（2026-09-04 续 20）

- **知识桥权限矩阵可视化**：Dashboard 知识域关系网格在单元格中显示操作（read/quote/summarize/propose_edit），角色↔知识域↔权限↔操作矩阵可视化进一步完成。

## 33. 后续处理记录（2026-09-04 续 21）

- **本地 SQLite 迁移基础**：新增 `python harness.py migration status|check|dry-run|prepare --backup`，检查关键本地库 schema_version；`dry-run` 只读。
- **情境模式差异对比**：新增 `python harness.py character mode diff --persona <id> --mode-a <a> --mode-b <b>`。
- 新增 `tests/test_migration_and_mode.py`（2 用例），unittest 总数 29。

## 34. 后续处理记录（2026-09-04 续 22）

- **MCP Inspector 外部验证通过**：新增 `harness_core/adapters/mcp_http_server.py`（loopback HTTP），使用 MCP Inspector CLI 完成 `tools/list` + `tools/call` 验证；`docs/mcp/verification.md` 记录通过证据。
- 真实宿主（Claude Code / Codex / Copilot）与 Official Registry 仍未做。

## 35. 后续处理记录（2026-09-04 续 23）

- **首次用户测试辅助**：新增 `python harness.py user-test checklist` / `template [--write]`，生成首次用户测试清单与结果模板；新增 `tests/test_user_test_commands.py`。unittest 总数 30。

## 36. 后续处理记录（2026-09-04 续 24）

- **批量补齐**：consent 分项扩展、GitHub Issue 模板、HCP 包 schema 强制校验、A/B 逐条指标可视化、Adversarial Review 最小冒烟。
- 新增 `tests/test_release_hygiene.py`（2 用例），unittest 总数 32。

## 37. 后续处理记录（2026-09-04 续 25）

- **可视化专项**：模型推理 span（roleplay duration_ms + Dashboard）、A/B 逐条 delta 条形、知识桥 file_count/credibility、卡牌工程牌组与 2 人自动演示。
- unittest 总数仍 32（card_game 测试兼容调整；新增 roleplay duration 未加独立测试）。

## 38. 后续处理记录（2026-09-04 续 26）

- **运行时/沙箱/热加载 R1**：runtime context 状态中枢、activation `--simulate-crash` + recover、HCP public 拒绝 HTML/SVG + 资源上限、knowledge index + health indexed。
- 新增 `tests/test_runtime_and_sandbox_gaps.py`（4 用例），unittest 总数 36。

## 39. 后续处理记录（2026-09-04 续 27）

- **角色/情境/UX R1**：situated 上下文视图、roleplay mode prompt 块、Dashboard 关系-情感状态卡片、Demo 后续引导。
- 新增/更新测试，unittest 总数 37。

## 40. 后续处理记录（2026-09-04 续 28）

- **数据/测量/可观测 R1**：provider usage 记录器、工作流来源分组条、Krippendorff’s alpha、vector queue 历史监控。
- 更新测试；unittest 总数 37（新增 krippendorff 用例与 vector history 断言）。

## 41. 后续处理记录（2026-09-04 续 29）

- **工程/发布工程 R1**：package schema 校验（validate+install）、migration policy 声明、adapter permission schema、secret-scan、断开 adapter 测试、scope 规范化、私人文档迁移设计。
- 更新测试；unittest 总数 40。

## 42. 后续处理记录（2026-09-04 续 30）

- **工程/发布进一步推进**：migration apply 实际写 schema_version、Dashboard adapter 权限矩阵、私人案例文档公共化替换、scope 规范化覆盖 memory 多入口。
- 新增 `tests/test_engineering_release_batch.py`；unittest 总数 45。

## 43. 后续处理记录（2026-09-04 续 31）

- **写操作网页点确认**：新增 `memory-write-confirm` loopback HTTP 服务，浏览器点确认后写入 notebook，返回 undo 命令；测试覆盖。
- unittest 总数 46。

## 44. 后续处理记录（2026-09-04 续 32）

- **角色分工/信件/切身化/用户关联**：letter send/list/reply、Dashboard 角色信件 + owner 标注、situated 增加 role_division / user_relation。
- 新增 `tests/test_role_communication.py`；unittest 总数 49。

## 45. 后续处理记录（2026-09-04 续 33）

- **业务列级迁移**：`migration apply --backup` 补 memory/notebooks/events/vector_queue 业务列。
- **adapter 权限真运行**：`harness_core/adapter_gate.py` 接入 MCP server，`HARNESS_MCP_ADAPTER_ID` 可强制能力校验。
- **文档继续抽象**：HYBRID / ENGINEERING 再替换一批具体示例。
- **scope 全入口**：event / letter 也纳入 normalize_scope。
- 新增/更新测试；unittest 总数 51。

## 46. 后续处理记录（2026-09-04 续 34）

- **可观测/威胁/沙箱补充**：vector queue alert、HCP 拒绝更多可执行脚本、workspace sandbox dry-run。
- unittest 总数 52。

## 47. 后续处理记录（2026-09-04 续 35）

- **测量学 CLI**：`measure construct` / `measure reliability`；**宿主导航** `host-guide`；**knowledge search 别名**。
- 新增 `tests/test_measurement_admin.py`；unittest 总数 55。
