---
title: Public release v0.1.0-alpha.2 design
status: deployed
kind: task-design
date: 2026-09-04
source_commit: d7f7de7
target_version: v0.1.0-alpha.2
public: true
contains_private_data: false
topics: [release, alpha, boundary, roadmap]
---

# 发布 v0.1.0-alpha.2 设计

## 1. 一句话目标

发布一个包含公共/本机边界整改、UX 层、统一 schema、event/usage 存储和角色资产化基础的公开 alpha.2 基线。

## 2. 用户场景

新用户可以离线 demo、运行环境检查、查看静态控制台、管理角色资产，并了解公共版与本机私人角色的边界。

## 3. 当前状态

基于 `v0.1.0-alpha.1`，main 新增了 demo/UX/dashboard/user-control/role-assets/knowledge/workspace/schema/event/usage 等。

## 4. 设计范围

### 包含
- 公共边界整改
- README/ROADMAP 重构
- Issue 模板 / Release Notes
- 双模式自检

### 不包含
- P2 完整交互式桥图的所有剩余项
- P3 之后的完整角色资产化

## 5. 公共与本机边界

- 私人角色已从公共 core 移除
- public demo 使用合成角色
- 本机 overlay 在 `~/.dsh/harness/personas.local.json`

## 6. 验收标准

- [x] release_verify rc=0
- [x] package_selfcheck rc=0
- [x] local_records_verify rc=0
- [x] Download ZIP 自检通过

## 7. 回滚方法

回退到 `v0.1.0-alpha.1` tag 即可。
