---
title: Topics alignment and situated character design
status: implemented
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: release/docs engineer
target_version: v0.2+
public: true
contains_private_data: false
topics: [topics, character-design, agent-ecosystem, naming]
---

# Topics alignment and situated character design

## 1. 一句话目标

让公开项目通过 GitHub Topics、Release Notes、Agent 兼容矩阵和中性示范角色，与当代 Agent 生态建立真实、可搜索、可核验的连接，同时保持“公共能力与插槽 + 本机人格与偏好”的硬边界。

## 2. 用户场景

- 新用户搜索某个 coding agent + 记忆/上下文时，能找到 Harness Core Portable；
- 用户想看到项目如何做“角色可切换职能”，但不需要先接触本机私人角色；
- 维护者需要一份清晰文档说明哪些是公共能力、哪些是本机私有。

## 3. 当前状态

- 当前 commit：项目 main（见 RELEASE_NOTES / manifesto）
- 当前工作区：正常
- 已有能力：
  - `AGENT_COMPATIBILITY.md`
  - `AGENT_COMPATIBILITY.json`
  - `ecosystem status`
  - 合成 demo 角色 `demo-archivist` / `demo-storykeeper`
  - 后辈交接文档规则
- 尚未实现：
  - 正式 GitHub Topics 设置（需人工在 GitHub About 配置）
  - “情境化角色”模式切换的公开示例
  - 针对不同 coding agent 的 README 分支说明

## 4. 设计范围

### 本次包含

- 整理 Topics / Release Notes / 兼容矩阵的关联方式
- 用中性合成角色展示“情境化角色”与职责模式
- 明确公共能力 vs 本机人格边界

### 本次不包含

- 把任何私人角色、口癖、图片或私人知识库放入公共包
- 接入真实厂商认证

## 5. 公共与本机边界

- 是否涉及私人角色：否
- 是否涉及私人知识库：否
- 是否涉及本机绝对路径：否
- 是否包含真实用户数据：否
- 公共包可以包含：Topics、兼容矩阵、合成角色、schema、通用能力
- 只能保留在 local overlay：本机角色、私人知识库、私人日记、本机启动器

## 6. 对象与数据流

输入：GitHub Topics 配置、Release Notes、`AGENT_COMPATIBILITY.json`、合成角色包

处理：对齐命名与热点、输出兼容矩阵状态、生成情境化角色示例

输出：`AGENT_COMPATIBILITY.md`、`ecosystem status`、合成角色 HCP、README 说明

持久化：`docs/AGENT_COMPATIBILITY.json`、`harness-core/personas/`

外部影响：GitHub 搜索流量与用户认知，无自动外部写入

## 7. 权限与安全

- 文件读取：仓库内文档/JSON
- 文件写入：docs / personas 目录
- 进程执行：无需
- 网络访问：无
- 跨角色访问：无
- 用户批准点：GitHub About/Topics 设置需人工
- Autonomous：disabled
- L4/L5：不启用

## 8. 用户体验

- 用户从哪里进入：README / GitHub 仓库搜索 / `ecosystem status`
- 第一步看到什么：项目定位 + 5 分钟 demo
- 失败时看到什么：兼容矩阵明确标注 R0/R1/R2
- 如何撤销：删除 GitHub Topics / 回退文档
- 如何退出：无需
- 如何清理数据：无需

## 9. 实现计划

1. 在 GitHub About 设置建议 Topics
2. 保持 `AGENT_COMPATIBILITY.md` / `.json` 同步
3. 增加一个“情境化角色”合成示例（如 `demo-archivist` 的模式切换说明）
4. 在 README 增加“Works around modern agent workflows”
5. 后辈交接规则：每次改动留任务/部署文档

## 10. 验收标准

- [x] README 不再出现“建议 GitHub Topics”维护者待办
- [x] `AGENT_COMPATIBILITY.md` 有 R0/R1/R2 等级
- [x] 公共角色均为合成角色
- [x] private persona 名字在公共 core/docs 中为 0
- [x] `release_verify` / `package_selfcheck` 通过

## 11. 风险和反例

| 风险 | 后果 | 缓解 |
|---|---|---|
| Topics 蹭热度被误解为厂商认证 | 用户高估兼容性 | 兼容矩阵用 R0/R1/R2 并注明未认证 |
| 合成角色过于像私人角色 | 边界被破坏 | 使用全新中性命名与原创设定 |

## 12. 未解决问题

- GitHub About/Topics 仍需用户手动配置
- 是否要为不同 coding agent 提供 README 分支入口

## 13. 后辈接手说明

1. 先检查 `AGENT_COMPATIBILITY.md` 是否与 `.json` 一致
2. 不要往公共 core 添加私人角色名
3. 最可信证据：`ecosystem status` 输出
4. 尚未验证：外部实际搜索覆盖

## 14. 相关文件

- `AGENT_COMPATIBILITY.md`
- `docs/AGENT_COMPATIBILITY.json`
- `harness-core/ecosystem_status.py`
- `harness-core/personas/`

## 15. 变更记录

| 日期 | 变化 | 原因 |
|---|---|---|
| 2026-09-04 | 创建任务设计 | 对齐命名与热点策略 |
