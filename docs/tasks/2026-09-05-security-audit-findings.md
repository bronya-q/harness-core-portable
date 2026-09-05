---
title: 安全审计发现与处置记录
status: conducted
kind: security-audit
date: 2026-09-05
updated_at: 2026-09-05
owner_role: security-audit
public: true
contains_private_data: false
topics: [security, audit, history, git, mcp, memory, ci]
---

# 安全审计发现与处置记录

> 本记录针对“外部安全审计”提出的红旗项逐条核实。本文件本身应作为公共档案，但**历史 Git 中仍可能存在私人人格标识**。

## 1. `secret.txt` 历史提交

- `git log --all -- secret.txt` 找到 2 个 commit：
  - `f3f78ec`（误加入）
  - `8927c36`（移除）
- 两个 commit 中 `secret.txt` 内容均为 **0 字节**。
- 结论：**没有真实密钥**。不需要轮换/清洗密钥。
- 但删除提交不会清除历史；若未来发生“非空文件误提交”，应使用 `git filter-repo` / BFG 清洗。

## 2. 私人人格内容曾进入公开库

- 早期 commit `16787fd` 的 diff 中可见：
  - `[private-persona-1]`
  - `[private-persona-2]`
  - `~/.dsh/skills/[private-persona]`
  - 相关命令示例
- 这些是**私人人格 scope / 本机路径标识**，属于可识别私人内容的元信息。
- 未在本次检查中发现真实对话正文/日记文本被纳入公开提交（主要是命令示例和 scope 名）。
- 风险：Git 历史可回溯；fork/缓存可能留存。
- 处置：已另建 [历史清理、安全处置与社区聚焦整改方案](2026-09-05-history-sanitization-and-community-focus-plan.md)。当前只完成事实核对，未在日常工作副本执行历史重写；是否 force-push、重打 tag、清理 GitHub 缓存，需维护窗口和明确授权。
- 建议：任何新提交前先跑 `python harness.py boundary-check`，并按整改方案执行 secret / boundary 扫描。

## 3. 记忆系统 + MCP 持久化注入面

- **记忆投毒风险**：长期记忆可被污染并长期召回。当前没有“召回前污染检测”机制。
- 建议后续增加：
  - 记忆来源 `source` 与 `provenance` 强制记录；
  - 召回时对高影响 scope 做来源可信度过滤；
  - MCP `memory_list` 只暴露自己授权 scope，不跨 scope 返回。
- **runtime context 进入 memory_list**：当前 `load_context()` 只返回 persona_id / mode_id / details / note，不包含路径/环境变量原始值。暴露面有限，但仍应审查 `details` 内容，避免后续塞入敏感路径。

## 4. CI 与发布脚本审查

- `.github/workflows/ci.yml`：
  - 使用 `pull_request`（不是 `pull_request_target`）
  - 没有 `GITHUB_TOKEN` 注入、没有 secrets
  - 只跑本地检查
  - 结论：安全
- `scripts/create-github-release.sh`：
  - 只要求 `gh auth status`
  - 不接受/不打印 token
  - 结论：安全

## 5. 工程信号

- 单人贡献、1 star、0 fork：按“不可信基线”处理，持续需要外部 review。
- `harness-core/` 与 `harness_core/` 双目录并存是结构混乱信号。短期用文档说明，长期应统一命名。

## 处置状态

| 项 | 状态 |
|---|---|
| secret.txt | ✅ 无真实密钥 |
| 私人人格历史标识 | ⚠️ 存在，已登记历史清理方案；暂未授权重写 |
| MCP memory_list 暴露面 | 🟡 当前暴露有限；需加 provenance 过滤 |
| 记忆投毒防护 | ❌ 未实现，需后续 |
| CI workflow | ✅ 无风险 |
| release script | ✅ 无风险 |
| 双目录结构 | 🟡 需长期整理 |
