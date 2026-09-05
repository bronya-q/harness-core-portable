---
title: 已提出但未完成 / 部分完成的缺口清单
status: archived-paused
kind: gap-list
date: 2026-09-04
updated_at: 2026-09-04
owner_role: project-progress-review
public: true
contains_private_data: false
topics: [gap, remaining, roadmap, archive, review]
---

# 已提出但未完成 / 部分完成的缺口清单

> 🔄 **2026-09-04 后续更新**：本清单原为暂存，后续已大量推进。当前 alpha.4 progress 已补完多项 R1；真正仍缺的主要是外部环境/真人/心理效度。本文件保留为历史存档。

> 本文件是补充存档，配合 `partial-implementation-inventory.md` 使用。
> 凡已完成的项不再列入；标 🟡 表示部分完成，标 ❌ 表示未做。

## 一、外部验证 / 发布

| 事项 | 状态 |
|---|---|
| Official MCP Registry 提交 | ❌ 未做（需账号/审核） |
| Claude Code / Codex / Copilot 真实宿主测试 | ❌ 未做 |
| PyPI 正式发布 | ❌ 未做 |
| alpha.4 tag / Release 页面 | ❌ 未做 |
| 首次用户真实测试结果 | ❌ 0 条真人结果 |
| GitHub Download ZIP 实际下载回读 | 🟡 本地 tag archive 已过，外部 ZIP 未回读 |
| GitHub Topics / About 手动配置核查 | 🟡 部分 |

## 二、运行时 / 沙箱 / 热加载

- ❌ **全入口 runtime 热挂载**：`activate` 仍是状态标记，不是所有入口全局生效。
- ❌ **完整事务化 activation 状态机**：缺真实崩溃/断电/多进程并发/持久化回放。
- ❌ **完整文件系统沙箱**：`workspace run` 只是命令约束。
- ❌ **HCP 完整威胁模型**：已有基础，缺不可信 HTML/SVG、资源耗尽、全面 fuzz、跨平台攻击矩阵。
- ❌ **知识源真实 mount / health / delegation**：只有 R1，没有真实正文检索、索引健康、角色间受控委派。
- ❌ **Adversarial Review 工作流**：仍是文档。

## 三、角色 / 情境 / 用户友好 UX

- ❌ **完整“处境 → 关系 → 共同经历 → 当前状态 → 责任 → 表达”闭环**。
- ❌ **mode 切换对各入口的实际策略影响**：只有 list/switch/current/diff。
- ❌ **关系-情感状态机的用户可理解界面**。
- ❌ **写操作交互式 GUI 确认**：有 CLI 确认 + HTML 预览，但没有网页点击确认。
- ❌ **首次同意分项更细**：缺 cross_session_recall / evaluation_use / cross_character_story_share。
- ❌ **高风险操作二次确认覆盖全部**。
- ❌ **GitHub Issue 模板**。
- 🟡 **1 分钟 Demo 后的新手引导**。

## 四、数据 / 测量 / 可观测性

- ❌ **provider usage 全入口覆盖**。
- 🟡 **demo / directed / real 在 UI 的完整分组**。
- ❌ **心理效度 / 信度**：无真实双标注、Krippendorff’s alpha、效度研究。
- 🟡 **vector queue 持续监控**：无历史趋势、告警、端到端重试面板。

## 五、工程 / 发布工程

- ❌ **package schema version 强制校验**。
- 🟡 **迁移/弃用政策**：有基础命令，但完整迁移/兼容窗口/弃用政策未闭环。
- ❌ **私人案例文档移动**到本机 overlay 并加入 `.gitignore`。
- ❌ **adapter 权限 manifest 完整版**。
- ❌ **无密钥进入 trace 验证**。
- ❌ **断开 adapter 后核心仍可运行测试**。
- ❌ **跨前端 scope 保持一致**。

## 六、可视化

- ❌ **模型推理 span / 真实 provider span**。
- 🟡 **A/B 结果可视化**（有卡片，缺逐条指标对比图）。
- 🟡 **知识桥可视化**（缺索引健康、来源可信度）。
- 🟡 **卡牌游戏**（可玩最小版，无扩展/多人/角色牌衍生）。

## 七、当前真正瓶颈

```text
外部真实环境验证（Registry / 真实宿主 / PyPI）
真实用户反馈（首次用户测试）
完整 runtime 热挂载 / 沙箱 / 知识桥真实访问
测量学信效度
```

这些需要外部的人和真实环境，而不是继续堆功能。
