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
