---
title: v0.1.0-alpha.4 release preparation
status: designed
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: release-engineer
target_version: v0.1.0-alpha.4
public: true
contains_private_data: false
topics: [alpha4, release, mcp, user-testing, runtime-policy, verification]
---

# v0.1.0-alpha.4 release preparation

## 1. 一句话目标

把 alpha.3 从“标签 + Pre-release 页面可回读”推进到 **“外部可复验 + 第一次真实用户反馈闭环 + 全入口运行时一致性”** 的 alpha.4，而不是急着宣称生产就绪。

## 2. 当前基线

- `v0.1.0-alpha.3`：GitHub Pre-release 已创建，`draft=false / prerelease=true`
- 本地基线：`main == origin/main`（如网络恢复需再确认）
- 测试：14 个 unittest，`release_verify` / `package_selfcheck` 通过
- CI：`.github/workflows/ci.yml`（Windows/Linux × py3.11/3.13）已推送
- 已知完成：`--help`、`schema --mode`、Dashboard timing、provenance、vector deferred 重试、provider usage、构念字典、n-gram、卡牌游戏

## 3. alpha.4 主题

**“可复验 + 有人用过 + 全入口一致”**

| 领域 | alpha.4 目标 |
|---|---|
| 外部验证 | MCP Inspector、官方 Registry（或明确不申请）、至少一个真实 coding-agent host 冒烟 |
| 首次用户反馈 | 至少 1 位非角色用户的真实使用记录，不是“自己测自己” |
| Runtime policy | resolver/policy 在所有 memory/persona/MCP/workspace/dashboard 入口统一可观测 |
| 数据可见 | event 的 session/content provenance 在 Dashboard 分组，provider 真实 usage 可区分 |
| 发布工程 | alpha.4 tag + Release notes + Deployment record + 外部下载/克隆回读 |

## 4. 本次包含

- 补 alpha.3 外部证据：`gh release`/API 回读、第三方 clone、ZIP archive 校验
- 建立 alpha.4 发布冻结点，统一 PEP 440 版本策略（`0.1.0a4`）
- 增加 MCP Inspector / host 冒烟记录（不伪造认证）
- 建立 resolver/runtime_policy 全入口一致性检查清单与最小入口测试
- 准备首次用户测试的最小可执行链路：
  - 一个明确的一分钟 Demo 脚本
  - 一个“3 问反馈”模板
  - 一个不依赖私有数据的测试 fixture
- 更新 README / 兼容矩阵 / ROADMAP 状态
- 保持 `autonomous_tasks=disabled`、L4/L5 关闭

## 5. 本次不包含

- 完整沙箱执行环境
- 真实知识源 mount / health / delegation 完整实现
- 心理效度研究（构念字典仍只是“有定义”，不是“已验证”）
- 官方 MCP Registry 正式收录（除非走通并明确授权）
- PyPI 正式发布（除非另开授权）
- 生产就绪 / 商业承诺

## 6. 验收标准

- [ ] `release_verify` / `package_selfcheck` / `unittest` 全绿
- [ ] alpha.3 外部回读记录：Release API、tag、下载 ZIP 至少一种可复验
- [ ] alpha.4 目录文件：release notes、deployment record、compatibility matrix、ROADMAP 一致
- [ ] MCP Inspector 记录至少一次通过（或明确写“未通过/未做”并说明原因）
- [ ] 至少一个真实 coding-agent host（Claude / Codex / Copilot 任一）冒烟记录
- [ ] 首次用户测试：至少 1 条来自非维护者的反馈（哪怕“没看懂某一步”）
- [ ] resolver/runtime policy 覆盖清单更新，并列出未覆盖入口
- [ ] public 边界扫描通过（无私人角色名泄漏在公共文档/代码中）

## 7. 发布步骤

1. 确认 `main == origin/main`
2. 生成 release manifest
3. 建 annotated tag `v0.1.0-alpha.4` 并推送
4. 更新 `pyproject.toml` → `0.1.0a4`
5. `gh release create v0.1.0-alpha.4 --prerelease`
6. 回读 Release API / ZIP / 第三方 clone
7. 写 deployment record 并更新 DEPLOYMENTS_INDEX

## 8. 风险与边界

- 外部验证可能受限于网络/账号，不要为了“完成”而伪造外部记录
- 首次用户反馈可能少，宁可“0 条但如实写”，也不要拿自己测试冒充用户
- alpha.4 仍不是 production-ready；不要把 `R1` / `实验性` 写成 `已验证`
- 发布前需用户授权；本文件只做设计，不自动触发外部操作

## 9. 后辈接手说明

- 先看 `docs/tasks/2026-09-04-whole-project-progress-audit.md` 的缺口清单
- 所有外部发布、账号登录、付费、设置更改要用户授权
- 保持诚实：**能回读才算 deployed；只打 tag 不算 Release 完成**
