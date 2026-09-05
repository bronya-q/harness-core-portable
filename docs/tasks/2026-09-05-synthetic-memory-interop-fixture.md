---
title: rawmem / memdsl 合成记忆互操作样例
status: verified
kind: task-record
date: 2026-09-05
updated_at: 2026-09-05
owner_role: memory-governance-review
source_commit: 3c2440c
target_version: post-alpha.4
public: true
contains_private_data: false
topics: [memory, interoperability, rawmem, memdsl, trace, synthetic-fixture]
---

# rawmem / memdsl 合成记忆互操作样例

## 目的

把公开讨论中的建议落成可以查看、执行和校验的 fixture：

```text
原始记录 → 候选 → 审核 → 下一次实际读取 → 当前判断 → 纠正后的读取结果
```

本任务只固定三方合同与预期行为，不声称已经连接 rawmem 或 memdsl。

## 产物

```text
examples/synthetic-memory-interop/README.md
examples/synthetic-memory-interop/scenario.json
examples/synthetic-memory-interop/run_scenario.py
examples/synthetic-memory-interop/expected-trace.json
examples/synthetic-memory-interop/expected-trace.md
tests/test_synthetic_memory_interop.py
```

## 样例涵盖

- 候选通过 `ledger_id + event_id + content_hash + quote` 追溯虚构原始记录；
- pending candidate 不提供给模型；
- review 结果明确指向批准后的 memory；
- 每次请求记录 `provided_memory_ids`、作用、排除原因和预期回答；
- 当前回合的“详细解释”不会写成长期候选；
- 一般简洁偏好与技术场景详细偏好可以并存；
- 只有明确长期纠正才使用 `supersedes`；
- 旧记忆保留供审计，纠正后不再提供给模型；
- 记忆可以影响准备方式，但不能授予发布权限。

## Harness Core Portable 在链中的职责

rawmem-compatible 部分只描述原始证据引用；memdsl-compatible 部分只描述候选、审核与 supersedes。Harness Core Portable 负责固定和检验中间的运行时语义：

- 当前话语是本轮要求还是长期修改；
- 哪些已批准记忆适用于当前任务；
- 一般偏好和更具体的场景偏好如何取舍；
- 哪些记忆实际提供给模型；
- 当前明确意图何时降低软偏好的作用；
- 操作授权为什么不能从记忆推导。

## 验证

执行：

```bash
python examples/synthetic-memory-interop/run_scenario.py
python -m unittest tests.test_synthetic_memory_interop -v
python -m unittest discover -s tests -v
```

2026-09-05 本地结果：

```text
fixture contract checks  30/30 PASS
fixture unit tests        8/8 PASS
full unittest             66 tests PASS
```

这些结果证明 fixture 内部合同一致，不证明真实模型质量、真实 rawmem/memdsl 对接或真实宿主集成。

## 后辈接手

1. 先让 rawmem/memdsl 作者核对 `scenario.json` 与 `expected-trace.md` 的语义；
2. 如果引用语义获得确认，再实现 rawmem Python adapter；当前不要假设 MCP 支持 event-id 正文回读；
3. memdsl adapter 复用现有 proposal/approval/supersedes，不复制 review store；
4. 把 `provided_memory_ids` 接到真实 prompt/context telemetry 后，才能把 expected trace 升级为 runtime evidence；
5. 加失败样例：hash 不符、正文读取无权限、pending 泄漏、superseded 泄漏；
6. 自动批准、Autonomous、实际发布和删除保持 disabled；
7. 真实外部部署另写 Deployment Record。
