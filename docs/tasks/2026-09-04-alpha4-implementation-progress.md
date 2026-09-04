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

> 本记录是 alpha.4 的内部推进日志；状态只表示“已做/未做/尝试过”，不表示生产就绪。

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

## 尝试过 / 未通过

- [ ] **MCP Inspector**
  - Windows `npx @modelcontextprotocol/inspector --cli --method tools/list python -m harness_core.adapters.mcp_server` 超时（rc=124）
  - WSL Debian 尝试同样未取得输出
  - 未伪造成功；下一步排查 npx/stdio target 传递，或用最小 Node MCP server 做平台对比

## 测试与发布

```text
unittest discover   PASS  23 tests
release_verify      PASS  205 entries
package_selfcheck   PASS
```

## 下一步（按清单）

1. MCP Inspector 挂起根因排查
2. 首次同意向导在 `start` 后的引导/空态细化
3. 高风险操作二次确认（workspace / evidence / privacy export）
4. A/B / Evidence / Workspace 可视化
5. 知识桥继续做“受控查询返回有限上下文”（当前 suggest 已经覆盖最小步）
