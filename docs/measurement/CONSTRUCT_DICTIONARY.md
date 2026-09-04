---
title: Harness Core Portable 构念字典
status: drafted
kind: measurement
date: 2026-09-04
updated_at: 2026-09-04
owner_role: measurement-engineer
public: true
contains_private_data: false
topics: [measurement, construct-dictionary, validity, reliability, evaluation]
---

# Harness Core Portable 构念字典

> 这是“工程可用”的构念清单，不是心理效度声明。
> **构念有定义 ≠ 构念有信效度。** 每个构念需要单独做操作化、双标注、信度（Cohen’s kappa / Krippendorff’s alpha）与效度论证，才能从 `planned` 进入 `demonstrated`。

## 使用方式

- 定义新测量先在这里登记 `construct_id`；
- 所有测量数据尽量套用 `schemas/measurement.schema.json`；
- 工程指标与心理量分开记录，不要混用“roBERTa 分数”和“研究人员判断”。

## 构念类型

| 类型 | 含义 | 示例 |
|---|---|---|
| trait | 较稳定的倾向/特质 | 共情特质、谨慎性 |
| state | 当前情境下的状态 | 当前情绪状态、当前认知负荷 |
| behavior | 可观察行为/事件 | 是否跨 scope 检索、是否引用原记忆 |
| self_report | 用户/角色自陈 | 用户满意度、角色确认 |
| inference | 从数据推出的二阶判断 | 模型推断的意图、情绪归因 |

## 构念清单

### A. 记忆与检索

| construct_id | construct_name | type | operation 摘要 | scale |
|---|---|---|---|---|
| recall.hit | 回忆命中 | behavior | 检索 top-k 中 gold 是否出现 | binary/count |
| recall.mrr | 平均倒数排位 | inference | gold 首次出现位置的倒数 | continuous |
| leakage.cross_scope | 跨 scope 泄漏 | behavior | 返回结果 scope 与查询 scope 不一致 | proportion |
| memory.precision | 回忆精确率 | inference | 命中数 / 返回数 | proportion |
| memory.archived | 归档记忆占比 | behavior | archived / total | proportion |

### B. 对话与人格表现

| construct_id | construct_name | type | operation 摘要 | scale |
|---|---|---|---|---|
| expression.consistency | 表达一致性 | state | 同一情境下主题/词分布差异 | continuous |
| emotion.congruence | 情绪一致性 | state | 情绪词投影 与 角色 sixdim 主导词 | binary/likert |
| persona.identity_hold | 身份保持 | behavior | 跨 session 是否保持角色宣称 | binary |
| role.scope_isolation | 角色 scope 隔离 | behavior | 是否读/写越界 | binary |

### C. 用户控制与信任

| construct_id | construct_name | type | operation 摘要 | scale |
|---|---|---|---|---|
| consent.explicit | 分项同意 | behavior | 是否在首次运行逐项显式同意 | binary |
| privacy.leak_to_public | 公开泄漏 | behavior | 公共包是否出现私人标识/内容 | count |
| user.control_recall | 纠错召回 | behavior | 用户纠错后记忆是否更新 | binary |
| user.satisfaction | 用户满意度 | self_report | 问卷/访谈自陈 | likert_5 |

### D. 工程可观测性

| construct_id | construct_name | type | operation 摘要 | scale |
|---|---|---|---|---|
| usage.actual_tokens | 实际 token | inference | provider/估计算法 | continuous |
| latency.dashboard_read | 控制台读取耗时 | behavior | 数据读取时间 span | duration |
| telemetry.vector_queue | 向量队列状态 | inference | pending/retry/stale/error 计数 | count |
| ci.green | CI 绿灯 | behavior | GitHub Actions matrix 通过 | binary |

## 信效度登记

| construct_id | reliability | validity | 现状 |
|---|---|---|---|
| usage.actual_tokens | not_measured | not_yet_established | 工程口径，未与 provider count 对齐 |
| leakage.cross_scope | demonstrated（单测） | not_yet_established | 已有泄漏检测，未做大样本 |
| ci.green | demonstrated | demonstrated | CI 每次运行可复验 |
| user.satisfaction | not_measured | not_yet_established | 未开始首测 |

## 下一轮要做

- 为每个 construct 定义评分手册（annotation guideline）；
- 准备双标注样本，报告 Cohen’s kappa / Krippendorff’s alpha；
- 在真实用户/角色样本上做小规模试测；
- 禁止把“工具能跑”写进“信效度已建立”。
