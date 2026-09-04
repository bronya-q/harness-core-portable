---
title: README single-user-path and nav refactor
status: designed
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: documentation-and-ux
target_version: v0.2+
public: true
contains_private_data: false
topics: [readme, navigation, onboarding, command-grouping]
---

# README single-user-path and nav refactor

## 1. 一句话目标

合并重复 Demo 段落，重构目录导航，把长命令清单按“用户目标”折叠，让新手入口和高级内容都易达。

## 2. 用户场景

- 新手只想要“一条路径”，不想读完整命令清单；
- 高级用户仍需要完整命令和技术细节。

## 3. 设计范围

### 包含

- 合并“5 分钟看到什么”与后续重复 Demo 段落
- 更新目录，增加新手入口可导航
- 命令清单按任务折叠（离线演示 / 记忆管理 / 角色资产 / 工程 / 生态 / 审计）
- 保留完整命令内容

### 不包含

- 删除任何技术/证据/边界章节
- 引入 JS 或交互依赖

## 4. 验收标准

- [ ] README 无重复 Demo 段落
- [ ] 目录能导航到新手入口
- [ ] 命令清单分组可读
- [ ] 原技术章节全部保留
- [ ] release_verify / package_selfcheck 通过

## 5. 后辈接手说明

1. 先阅读当前 README 结构
2. 合并时保留链接、命令和边界声明
3. 不要为了“简短”删除安全/隐私/证据说明
