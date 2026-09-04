---
title: GitHub release v0.1.0-alpha.3
status: deployed
kind: deployment-record
date: 2026-09-04
deployed_at: 2026-09-04
version: v0.1.0-alpha.3
source_commit: d36f471
target: github
deployed_by: bronya-q
public: true
contains_private_data: false
topics: [release, alpha, github, mcp, character, workspace]
---

# GitHub Release v0.1.0-alpha.3 部署记录

## 1. 部署摘要

在 main 分支创建 `v0.1.0-alpha.3` tag 并推送。

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

- commit: `d36f471`
- tag: `v0.1.0-alpha.3`
- release manifest count: 180

## 5. 验证证据

| 检查 | 预期 | 实际 | rc | 结果 |
|---|---|---|---|---|
| release_verify | 0 | 0 | 0 | pass |
| package_selfcheck | 0 | 0 | 0 | pass |
| unittest discover | 0 | 0 | 0 | pass |

## 6. 未验证项

- MCP Inspector / Official Registry / Claude Code / Codex / Copilot
- 首次用户真实测试
- GitHub Pre-release 页面创建（需 gh/UI）

## 7. 回滚方法

删除 tag 或回退 main 到上一提交。

## 8. 后辈接手说明

- 确认 Release 页面是否创建
- 检查 `character mode` / `workspace worktree` / `mcp` 命令
