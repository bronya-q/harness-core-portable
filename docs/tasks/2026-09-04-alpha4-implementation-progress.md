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
