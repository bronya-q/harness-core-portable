---
title: alpha.4 实现推进记录
status: in_progress
kind: progress
date: 2026-09-04
updated_at: 2026-09-04
owner_role: release-engineer
target_version: v0.1.0-alpha.4
public: true
contains_private_data: false
topics: [alpha4, progress, knowledge, memory, dashboard, ngram, consent]
---

# alpha.4 实现推进记录

> ⏸️ **施工暂停 / CONSTRUCTION PAUSED**
>
> 当前暂停批量功能推进，本记录转为存档。恢复时先核对本文件与 `docs/tasks/2026-09-04-partial-implementation-inventory.md`。

> 本记录是 alpha.4 的内部推进日志；状态只表示“已做/未做/尝试过”，不表示生产就绪。


> 🌱 **路过 Agent 也欢迎搭把手**：如需恢复推进，优先做可复验的外部记录（MCP Inspector / 真实宿主 / 公共边界扫描 / 首次 Agent 测试）。详细清单见 `docs/tasks/2026-09-04-partial-implementation-inventory.md`。


## 已完成

- [x] **真实 Dashboard 截图 / 滚动 GIF**
  - 用 `demo --offline --keep` + `dashboard build` + 无头 Edge 生成真实合成数据全页截图
  - Dashboard 页脚脱敏为 `~/.dsh/memory-emotion`
  - 新增 `tools/generate_real_dashboard_gif.py`
- [x] **首次启动同意向导**
  - `python harness.py start` 首次运行询问 `memory/story/notebook/telemetry` 分项同意
  - 写入 `~/.dsh/harness/consent.json`
- [x] **写操作预览 → 确认 → 撤销**
  - `memory write --scope <s> --text <t> [--yes]`
  - `memory undo --id <id>`
  - Dashboard 增加「最近写操作（可撤销预览）」卡片
- [x] **知识桥“真实只读访问”最小步**
  - `knowledge access --role <r> --source <s> [--query <q>]`
  - `knowledge suggest --question <q> --role <r> [--limit 3]`（委派匹配 + 授权 + 只读摘要）
- [x] **n-gram fallback 接入 `memory search`**
  - `memory search --query <q> [--scope <s>] [--limit 10]`
  - 精确子串无结果时自动调用 `ngram_fallback.py`
  - 输出 `source=exact_substring / ngram_fallback / none`
- [x] **高风险操作二次确认**
  - `memory forget --id <id>` 默认需要确认，`--yes` 可跳过
  - `privacy reset-demo` 默认需要确认，`--yes` 可跳过
  - `workspace worktree remove` / `workspace release` 默认需要确认，`--yes` 可跳过
  - 取消时返回 `status=cancelled`，不执行破坏性操作
- [x] **A/B / Evidence / Workspace 可视化**
  - Dashboard 新增「工程工作区 / Evidence」卡片
  - 展示 Workspace lease（status / role / worktree / actual_execution）
  - 展示 Evidence Bundle（task_id / working_tree / checks / unverified / approval）
- [x] **导出前预览**
  - `privacy export`：先显示 data_dir / platform / aggregate_only / contains_pii，确认后写入
  - `feedback export --redacted`：先显示 platform / model / included_content，确认后写入
  - 均支持 `--yes` 跳过；取消返回 `status=cancelled`
- [x] **知识桥受控返回预算**
  - `knowledge access` / `knowledge suggest` 支持 `--max-chars`（默认 200）
  - 返回片段按预算截断，并注明 `max_chars`
- [x] **合规/公共边界快照**
  - Dashboard 新增「公共边界快照」卡片
  - 扫描 README / CONTRIBUTING / SECURITY / LICENSE 中的私人标识与绝对路径
  - 命中时高亮提示需人工确认；默认关键公开文件应为干净
- [x] **首次使用向导细化**
  - `start` 首次同意后显示「首次使用提示」
  - 选择 Demo 前提示临时合成数据/自动清理/--keep
- [x] **知识桥多源合并去重**
  - `knowledge suggest` 支持 `--sources`（默认 2）
  - 会访问多个匹配知识源，合并去重片段，并在 `sources` 中列出每个源
- [x] **高风险二次确认再扩展**
  - `character deactivate` / `character remove` 默认需要确认
  - `backup restore` 默认需要确认
  - 均支持 `--yes`；取消返回 `status=cancelled`
- [x] **A/B 结果可视化**
  - `ab role` / `ab retriever` 支持 `--save <name>`，写入 `docs/evidence/ab-*.json`
  - Dashboard 新增「A/B 记录」卡片，列出保存的 A/B 结果
- [x] **知识桥 Suggest 历史可视化**
  - `knowledge suggest` 写入 `~/.dsh/harness/knowledge-suggest-history.json`
  - Dashboard 新增「知识桥 Suggest 历史」卡片
- [x] **写操作 GUI 预览**
  - `memory write --html` 生成 `memory-write-preview.html` 预览页
  - 页面明确标注“未写入任何数据”；不触发 notebook 写入
- [x] **知识桥权限矩阵可视化**
  - Dashboard 知识域关系网格现在在每个单元格显示操作（read/quote/summarize/propose_edit）
  - 角色与知识域之间的权限不再只有身份，还展示可执行操作
- [x] **本地 SQLite 迁移基础**
  - `python harness.py migration status|check|dry-run|prepare --backup`
  - 检查 `memory/notebooks/story/events/vector_queue` 的 schema_version 表
  - `dry-run` 只读；`prepare --backup` 迁移前备份复制
- [x] **情境模式差异对比**
  - `character mode diff --persona <id> --mode-a <a> --mode-b <b>`
  - 输出两个模式的 display_name / capabilities / effect / 权限差异

## MCP Inspector 外部验证（已通过）

- ✅ 通过 **HTTP loopback transport**：
  - `python -m harness_core.adapters.mcp_http_server --port <port>`
  - `npx @modelcontextprotocol/inspector --cli --format json --method tools/list --server-url http://127.0.0.1:<port>/mcp`
  - `tools/call` 也通过（`_memory_list` 返回正常）
- ⬜ 仍未做：Official MCP Registry 提交、Claude Code / Codex / Copilot 真实宿主验证
- 记录见 `docs/mcp/verification.md`

## 首次用户测试辅助

- 新增 `python harness.py user-test checklist`：输出任务清单 + 记录字段 + protocol 路径
- 新增 `python harness.py user-test template [--write]`：生成可填写的 `docs/user-testing/results-YYYYMMDD-HHMMSS.md`
- **仍需真人参与**；工具只是让“找人跑”这一步更容易，不代替真实用户

## 本轮批量补齐

- ✅ **首次同意分项扩展**：`privacy consent` 新增 `cross_session_recall / evaluation_use / cross_character_story_share`
- ✅ **GitHub Issue 模板**：`.github/ISSUE_TEMPLATE/` 增加 bug / feature / user-feedback / security
- ✅ **HCP 包 schema 强制校验**：`character install` 要求 `schema_version`，可选 `minimum_core_version`
- ✅ **A/B 逐条指标可视化**：Dashboard A/B 记录显示 `per_query pos/neg/zero`
- ✅ **Adversarial Review 最小冒烟**：`python harness.py adversarial --draft ... [--evidence-dir ...]`

## 可视化专项

- ✅ **模型推理 span**：roleplay 采集 Ollama `duration_ms`，Dashboard 显示总/平均推理耗时
- ✅ **A/B 逐条 delta 图**：Dashboard 对保存的 A/B 记录渲染 precision_delta 正/负条形
- ✅ **知识桥可视化**：`knowledge health` 增加 `file_count` 与 `credibility`，Dashboard 显示
- ✅ **卡牌游戏扩展**：`card_game.py` 支持 `--deck classic|engineering`，`--players 2` 自动多人演示

## 运行时/沙箱/热加载 R1

- ✅ **runtime context 状态中枢**：新增 `python harness.py runtime status`，`character activate` / `mode switch` 写入 `~/.dsh/harness/runtime-context.json`
- ✅ **activation 崩溃恢复模拟**：`character activate --simulate-crash` 保留锁并进入 crash_simulated，`character recover` 可恢复/清理
- ✅ **HCP 威胁模型补充**：public 包拒绝 `.html/.htm/.svg`，增加目录文件数/大小上限
- ✅ **知识源索引与检索**：新增 `knowledge index --source <id>`，`knowledge health` 报告 indexed / indexed_file_count

## 角色/情境/UX R1

- ✅ **情境化上下文视图**：新增 `python harness.py situated --scope <s>`，展示 处境/关系/共同经历/当前状态/责任/表达
- ✅ **mode 实际策略影响**：roleplay 读取 `runtime-context.json`，把当前 mode 写入 prompt（“当前情境模式”块）
- ✅ **关系-情感状态可视化**：Dashboard 新增「关系-情感状态」卡片
- ✅ **Demo 后续引导**：`demo --offline` 结束后打印下一步命令（dashboard/list/start）

## 数据/测量/可观测 R1

- ✅ **provider usage 记录器**：新增 `harness_core/usage_recorder.py`，OpenAI-compatible adapter 支持 `autorecord=True` 回填 provider_reported
- ✅ **工作流来源分组**：Dashboard「数据来源分组」增加 demo/directed/real 计数条
- ✅ **Krippendorff’s alpha**：`measurement_utils.krippendorff_alpha()` + 测试
- ✅ **vector queue 历史监控**：`queue_status()` 写入 history，`queue_history()` 读取，Dashboard 显示近期 pending 趋势

## 工程/发布工程 R1

- ✅ **package schema 强制校验**：`character validate` 也强制 `schema_version` / `minimum_core_version`
- ✅ **迁移/弃用政策声明**：`python harness.py migration policy` 输出 compatibility window / deprecation / backup / dry-run 策略
- ✅ **adapter 权限 manifest 基础**：`schemas/adapter-permission.schema.json` + `harness-core/adapters.example.json` + `schema validate --adapter-permission`
- ✅ **无密钥 trace 扫描**：`python harness.py secret-scan` + 测试
- ✅ **断开 adapter 核心可运行测试**：`test_core_runs_independent_of_adapter`
- ✅ **跨前端 scope 规范化**：`harness-core/scope_utils.py`，`memory search` 使用
- ✅ **私人文档迁移设计**：`docs/tasks/2026-09-04-private-document-migration.md` + `.gitignore` 条目

## 工程/发布工程进一步推进

- ✅ **实际逐库 migration 动作**：`python harness.py migration apply --backup` 为本地库创建/更新 `schema_version` 表（备份先行）
- ✅ **真实 adapter 权限矩阵**：Dashboard 新增「Adapter 权限矩阵」卡片，读取 `adapters.example.json`
- ✅ **私人案例文档人工替换**：`HYBRID_FUNCTIONAL_PERSONA.md` / `ENGINEERING_ROLES.md` 已把具体本机角色名替换为公共占位，并加“公共抽象版”说明
- ✅ **跨所有入口 scope 一致性**：`memory list/write/correct/restore/search` 均使用 `normalize_scope`

## 写操作网页点确认

- ✅ 新增 `python harness.py memory-write-confirm --scope <s> --text <t> [--port 8766]`
- 在浏览器打开后点「确认写入」才真正写 notebook
- 完成后显示 id / version / undo 命令
- 只监听 `127.0.0.1`，不自动上传

## 角色分工 / 信件 / 切身化 / 用户关联

- ✅ **角色信件系统**：`python harness.py letter send|list|reply`，Dashboard 新增「角色信件」卡片
- ✅ **独立角色掌握知识域**：Dashboard 知识域网格中 steward 标注为 `owner · steward`
- ✅ **角色分工**：`situated` 视图新增 `role_division`（source → stewards）
- ✅ **切身化 / 用户关联处境**：`situated` 视图新增 `user_relation`（关系状态 + 用户关联说明）

## 业务迁移 / adapter 真运行 / 文档抽象 / scope 全入口

- ✅ **业务列级迁移**：`migration apply --backup` 现在为 memory/notebooks/events/vector_queue 补业务列（sixdim / rel_level / status / session_provenance 等）
- ✅ **adapter 权限矩阵驱动真实运行**：新增 `harness_core/adapter_gate.py`；MCP server 可通过 `HARNESS_MCP_ADAPTER_ID` 强制能力校验，未授权返回 deny
- ✅ **HYBRID / ENGINEERING 继续抽象**：`本机综合人格 A`、`本机知识管理员 A/B`、`local-persona/b` 等进一步替换为公共占位
- ✅ **scope 全入口规范化**：`event add/list`、`letter send/list` 也使用 `normalize_scope`

## 可观测 / 威胁 / 沙箱补充

- ✅ **vector queue 告警**：`queue_alert()` 检测 stale/failed 阈值，`data status` 输出 alerts
- ✅ **HCP 可执行脚本扩展**：public 包拒绝 `.py/.js/.mjs/.ts/.rb/.pl` 等可执行脚本
- ✅ **workspace sandbox dry-run**：`workspace sandbox <name> --command <cmd>` 只读检查 allowed_commands / forbidden_paths / actual_execution

## 测量学 CLI / 宿主导航 / 知识搜索

- ✅ **测量学 CLI**：`python harness.py measure construct` 列出构念字典；`measure reliability --file <r.json>` 计算 Cohen’s κ / Krippendorff’s α
- ✅ **宿主导航**：`python harness.py host-guide` 输出 Claude Code / Codex / Copilot 接入步骤
- ✅ **知识源 search 别名**：`python harness.py knowledge search --source <id> --query <q>`

## 继续推进

- ✅ **scope 再补**：`inspect` 也使用 `normalize_scope`
- ✅ **Adversarial Review 保存**：`python harness.py adversarial --save <name>` 把审查结果写入 `docs/tasks/adversarial-review-*.json`
- ✅ **知识源 explain 视图**：`python harness.py knowledge explain --source <id>` 展示健康/可信度/索引状态
- ✅ **notebook / story_core 也做 scope/namespace 规范化**
- ✅ **construct 列表过滤**：`measure construct` 不再把分隔行 `---` 当作构念
- ✅ **卡牌角色牌衍生**：`card_game.py role-card --persona <id>` 从 persona 资产衍生角色卡
- ✅ **workspace sandbox run**：`workspace sandbox <name> run --command <cmd>` 在 lease 目录内受控执行（非完整 OS 沙箱）
- ✅ **角色分工可视化**：Dashboard 新增「角色分工（知识域 → 负责角色）」卡片
- ✅ **公共示例 stewards 去私人化**：`knowledge-sources.example.json` 的 stewards 改为合成 demo 角色
- ✅ **复杂 schema 迁移脚本**：`python harness.py migration apply-script --file migrate.py` 支持执行外部 `upgrade(con)` 脚本（带备份）
- ✅ **文档抽象扩展到更多参考文件**：`KNOWLEDGE_STEWARDSHIP.md` / `harness-core/SKILL.md` 也去掉具体私人示例名
- ✅ **letter/situated/role_division 接入 roleplay 实际决策**：roleplay prompt 现在加入「角色分工 / 用户关联 / 近期信件」
- ✅ **situated 视图增加信件上下文**：`situated` 输出 `letters`
- ✅ **knowledge 全文索引检索**：`knowledge index` 存 token 列表，`knowledge search --use-index` 按词重叠打分检索
- ✅ **knowledge suggest 主动参考 role_division / letters**：返回责任分工与近期信件
- ✅ **MCP memory_list 显示最近信件**：`memory_list` 响应包含 `letters`
- ✅ **Dashboard 可视化 roleplay 注入上下文**：新增「角色运行上下文（roleplay 注入）」卡片
- ✅ **usage 覆盖审计**：`python harness.py usage audit` 列出非 provider_reported 的入口
- ✅ **workspace 隔离运行**：`workspace sandbox <name> run --command <cmd> --isolate` 使用临时副本执行
- ✅ **MCP 自检脚本**：`python harness.py mcp-verify` 一键跑 stdio 单测 + HTTP loopback 冒烟
- ✅ **项目一键体检**：`python harness.py project-check` 聚合 package_selfcheck / mcp-verify / secret-scan / migration_check
- ✅ **信件会话线程**：`python harness.py letter thread --scope <s>` 按 in_reply_to 链展示信件线程
- ✅ **首次用户测试模拟管线**：`python harness.py user-test simulate` 跑 demo + dashboard + memory list，生成 simulated 结果文件
- ✅ **R2 发布勾选清单**：`python harness.py release-checklist` 输出 R2 DoD 自动/人工勾选项

## 测试与发布

```text
unittest discover   PASS  29 tests
release_verify      PASS  208 entries
package_selfcheck   PASS
```

## 下一步（按清单）

1. 首次用户反馈（当前瓶颈）
2. 真实宿主验证（Claude Code / Codex / Copilot）
3. Official MCP Registry 提交（需外部账号/审核）
4. 恢复时继续补齐 `partial-implementation-inventory.md` 中 ❌ / 🟡 项
