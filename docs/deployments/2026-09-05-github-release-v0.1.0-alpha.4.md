---
title: GitHub Pre-release v0.1.0-alpha.4
status: deployed
kind: deployment-record
date: 2026-09-05
deployed_at: 2026-09-05
version: v0.1.0-alpha.4
source_commit: b56e2aa
target: github
deployed_by: bronya-q
public: true
contains_private_data: false
topics: [release, alpha, github, deployment, progress]
---

# GitHub Pre-release v0.1.0-alpha.4 部署记录

## 1. 部署摘要

- 创建 annotated tag `v0.1.0-alpha.4` 并推送
- 使用 `gh release create` 创建 GitHub Pre-release 页面
- Release URL: https://github.com/bronya-q/harness-core-portable/releases/tag/v0.1.0-alpha.4

## 2. 用户可感知变化

- 大量 R1 能力落地（详见 `docs/releases/v0.1.0-alpha.4.md`）
- Dashboard 可视化全面升级
- 知识桥索引/检索/委派
- 角色信件/线程/分工
- runtime 热挂载覆盖 7/7 入口
- 一键体检 `project-check` / `mcp-verify` / `boundary-check` / `release-checklist`
- unittest 58 个

## 3. 部署目标

- GitHub main
- GitHub tag + Pre-release

## 4. 精确版本

- commit: `b56e2aa`
- tag: `v0.1.0-alpha.4`
- release manifest count: 242

## 5. 验证证据

| 检查 | 预期 | 实际 | rc | 结果 |
|---|---|---|---|---|
| release_verify | 0 | 0 | 0 | pass |
| package_selfcheck | 0 | 0 | 0 | pass |
| unittest discover | 0 | 0 | 0 | pass |

## 6. 未验证项

- 真实宿主验证（Claude Code / Codex / Copilot）
- Official MCP Registry / PyPI
- 首次用户真人结果
- 真实双标注 / 心理效度
- 完整 OS 级文件系统沙箱

## 7. 回滚方法

- 删除 tag 或回退 main 到上一提交；Release 页面可编辑/删除，不移动公开 tag。

## 8. 后辈接手说明

> ⚠️ **发布后发现（已修复）**：发布时 GitHub Actions 在 Ubuntu 3.13 存在失败；后续重写 MCP stdio 测试后，`cc0e759` / `70d409c` 的 CI 已转绿（4 个 matrix job 全部通过）。详见 `docs/deployments/2026-09-05-github-release-v0.1.0-alpha.4-external-verification.md`。

- 先跑 `python harness.py project-check`
- 检查 `docs/tasks/2026-09-04-alpha.4-r2-plan.md` 的 Definition of Done
- 保持诚实边界：Pre-release ≠ production-ready。
