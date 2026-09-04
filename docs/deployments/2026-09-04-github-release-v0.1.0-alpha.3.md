---
title: GitHub tag v0.1.0-alpha.3（tag-only；Release 页面待创建）
status: implemented
kind: deployment-record
date: 2026-09-04
deployed_at: 2026-09-04
version: v0.1.0-alpha.3
source_commit: b3ad9fc
target: github
deployed_by: bronya-q
public: true
contains_private_data: false
topics: [release, alpha, github, mcp, character, workspace]
---

# GitHub Tag v0.1.0-alpha.3 部署记录（tag-only）

## 1. 部署摘要

在 main 分支创建 `v0.1.0-alpha.3` annotated tag 并推送。本次只完成 tag 部署；**未创建 GitHub Pre-release/Release 页面**。创建页面需用户授权，本记录不伪造 `deployed` 状态。

## 2. 用户可感知变化

- 角色资产化：install/validate/preview/activate/rollback/card-import/build
- 情境模式：character mode list/switch/current
- A/B 对照、token 基线、Evidence Bundle
- Schema / Event / Usage 统一存储
- MCP 官方 SDK + 可安装包
- 回归测试 `unittest discover`

## 3. 部署目标

- GitHub main
- GitHub tag `v0.1.0-alpha.3`

## 4. 精确版本

- commit: `b3ad9fc`
- tag: `v0.1.0-alpha.3`
- release manifest count: 184（后续工作区随 commit 持续更新）

## 5. 验证证据

| 检查 | 预期 | 实际 | rc | 结果 |
|---|---|---|---|---|
| release_verify | 0 | 0 | 0 | pass |
| package_selfcheck | 0 | 0 | 0 | pass |
| unittest discover | 0 | 0 | 0 | pass |

## 6. 未验证项

- MCP Inspector / Official Registry / Claude Code / Codex / Copilot
- 首次用户真实测试
- GitHub Pre-release 页面创建（需明确授权 + gh/UI）
- 第三方 clone + ZIP 回读

## 7. 回滚方法

删除 tag 或回退 main 到上一提交。

## 8. 后辈接手说明

- 确认 Release 页面是否创建
- 检查 `character mode` / `workspace worktree` / `mcp` 命令
