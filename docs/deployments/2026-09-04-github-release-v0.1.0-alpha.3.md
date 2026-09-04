---
title: GitHub Pre-release v0.1.0-alpha.3
status: deployed
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

# GitHub Pre-release v0.1.0-alpha.3 部署记录

## 1. 部署摘要

在 main 分支创建 `v0.1.0-alpha.3` annotated tag 并推送；随后经用户授权，使用 `gh release create` 创建 GitHub Pre-release 页面。

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
- release manifest count: 182（以 tag 冻结点为准）

## 5. 验证证据

| 检查 | 预期 | 实际 | rc | 结果 |
|---|---|---|---|---|
| release_verify | 0 | 0 | 0 | pass |
| package_selfcheck | 0 | 0 | 0 | pass |
| unittest discover | 0 | 0 | 0 | pass |

## 6. 未验证项

- MCP Inspector / Official Registry / Claude Code / Codex / Copilot
- 首次用户真实测试
- GitHub Download ZIP 实际下载回读（本地 tag archive 已通过）
- Release body 中 manifest count 与 `schema validate --mode` 勘误已同步；见外部验证记录

## 7. 回滚方法

删除 tag 或回退 main 到上一提交。

## 8. 后辈接手说明

- Release 页面已创建（Pre-release，draft=false）
- GitHub Download ZIP 仍待核验；本地 tag archive 已通过
- 检查 `character mode` / `workspace worktree` / `mcp` 命令
