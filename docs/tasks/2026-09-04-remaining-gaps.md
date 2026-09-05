---
title: 已提出但未完成 / 部分完成的缺口清单（完成度刷新版）
status: archived-paused
kind: gap-list
date: 2026-09-04
updated_at: 2026-09-04
owner_role: project-progress-review
public: true
contains_private_data: false
topics: [gap, remaining, roadmap, archive, review, progress]
---

# 已提出但未完成 / 部分完成的缺口清单（完成度刷新版）

> ⏸️ 本文件原为“待办缺口”，现已大量落地。下面按**当前实际状态**标注。
> ✅ = 可运行/可验证；🟡 = 部分；❌ = 仍未做（通常是外部/真人）。

## 一、外部验证 / 发布

| 事项 | 状态 |
|---|---|
| MCP Inspector | ✅ 通过 HTTP loopback，`mcp-verify` 可复现 |
| Official MCP Registry | ❌ 未做（需账号/审核） |
| Claude Code / Codex / Copilot 真实宿主 | ❌ 未做（需真实环境） |
| PyPI | ❌ 未做 |
| alpha.4 tag / Release | ❌ 未做 |
| 首次用户真人结果 | ❌ 未做 |

## 二、运行时 / 沙箱 / 热加载

| 事项 | 状态 |
|---|---|
| runtime context 状态中枢 | ✅ `runtime status` / activate/mode 写入 |
| activation crash 模拟 + recover | ✅ |
| workspace sandbox dry-run | ✅ |
| workspace sandbox run + `--isolate` | ✅ 临时副本执行 |
| 完整 OS 沙箱 | ❌ 仍非完整操作系统隔离 |
| HCP HTML/SVG/脚本/资源上限 | ✅ |
| knowledge 索引/检索/委派/权限 | ✅ |
| Adversarial Review 最小工作流 | ✅ `adversarial --save` |

## 三、角色 / 情境 / 用户友好 UX

| 事项 | 状态 |
|---|---|
| situated 上下文视图 | ✅ |
| mode 影响 roleplay prompt | ✅ |
| 关系-情感状态可视化 | ✅ |
| 写操作网页点确认 | ✅ |
| 首次同意分项扩展 | ✅ |
| 高风险二次确认 | ✅ |
| GitHub Issue 模板 | ✅ |
| Demo 后续引导 | ✅ |
| 完整“处境→关系→共同经历→…→表达”自动闭环 | 🟡 有视图 + roleplay 注入，但未全入口自动消费 |

## 四、数据 / 测量 / 可观测性

| 事项 | 状态 |
|---|---|
| provider usage 记录器 + adapter autorecord | ✅ |
| usage audit | ✅ |
| 工作流来源分组 | ✅ |
| Krippendorff’s alpha | ✅ |
| vector queue history + alert | ✅ |
| 真实双标注 / 效度研究 | ❌ 需真人/真实数据 |

## 五、工程 / 发布工程

| 事项 | 状态 |
|---|---|
| package schema 强制校验 | ✅ |
| migration policy / apply / apply-script | ✅ |
| adapter permission manifest + gate | ✅ |
| secret-scan | ✅ |
| 断开 adapter 核心可运行测试 | ✅ |
| scope 规范化（memory/event/letter/inspect/notebook/story） | ✅ |
| 私人案例文档抽象 | ✅ 主文档完成，零星参考文件需继续 |

## 六、可视化

| 事项 | 状态 |
|---|---|
| 模型推理 span | ✅ |
| A/B 逐条 delta | ✅ |
| 知识桥健康/可信度/索引 | ✅ |
| 卡牌游戏扩展 + 角色牌衍生 | ✅ |
| 角色分工/信件/关系/运行上下文 | ✅ |

## 七、当前真正瓶颈

```text
真实宿主验证 / Registry / PyPI
首次用户真人结果
真实双标注 / 心理效度
完整 OS 沙箱
```

这些需要外部的人和真实环境，不是继续堆代码能解决。
