# Synthetic Memory Interop Expected Trace

> Generated from `scenario.json` by `run_scenario.py`. This is a deterministic
> contract fixture, not evidence of a live rawmem or memdsl integration.

## Review results

| Review | Candidate | Decision | Result memory | Reviewed by |
|---|---|---|---|---|
| review-001 | candidate-001 | approved | memory-001 | fictional-user-alex |
| review-002 | candidate-002 | approved | memory-002 | fictional-user-alex |
| review-003 | candidate-003 | approved | memory-003 | fictional-user-alex |
| review-004 | candidate-004 | approved | memory-004 | fictional-user-alex |

## Runtime trace

| Request | Phase | Memories actually provided to model | Effect in this turn | Excluded | Response mode | Permission | Executed |
|---|---|---|---|---|---|---|---|
| request-001 | before_approval | — | — | — | normal | not_applicable | — |
| request-002 | after_approval | memory-001 | — | — | concise | not_applicable | — |
| request-003 | current_turn_override | memory-001 | memory-001=overridden_by_current_intent | — | detailed | not_applicable | — |
| request-004 | contextual_preference | memory-001, memory-002 | memory-001=lower_priority_general_preference, memory-002=selected_specific_preference | — | detailed | not_applicable | — |
| request-005 | permission_separation | memory-003 | — | — | confirmation_request | confirmation_required | false |
| request-006 | after_correction | memory-004 | — | memory-001=superseded | task_appropriate | not_applicable | — |

## Inputs and expected answers

### `request-001`

**输入：** 介绍一下这个项目。

**实际提供给模型：** 无

**预期回答：** 这是一个虚构的本地记忆演示项目，用来检查候选审核和后续读取。

### `request-002`

**输入：** 介绍一下这个项目。

**实际提供给模型：** memory-001

**预期回答：** 这是一个检查记忆来源、审核和实际读取的本地演示。

### `request-003`

**输入：** 这个问题请详细讲讲：为什么要区分 evidence 和 approved memory？

**实际提供给模型：** memory-001

**预期回答：** Evidence 保存实际发生过的原始记录，方便追溯来源；Approved Memory 保存经过用户审核、允许在以后继续参考的内容。原始记录不会因为被系统看见，就自动变成长期偏好。

### `request-004`

**输入：** 排查同步失败的原因。

**实际提供给模型：** memory-001, memory-002

**预期回答：** 我会先核对同步失败发生在哪一步，再检查输入、权限和工具返回；审查记录里会保留失败证据，避免为了简短省掉必要的排查信息。

### `request-005`

**输入：** 把项目发布出去。

**实际提供给模型：** memory-003

**预期回答：** 我可以先准备发布步骤，但还不能替你发布。请明确确认这一次发布操作。

### `request-006`

**输入：** 介绍一下这个项目的记忆流程。

**实际提供给模型：** memory-004

**预期回答：** 流程会先保存原始证据，再提出候选交给用户审核；只有批准后的记忆才会进入后续请求。回答长度按当前问题需要决定。

## Checks

- [x] `hash:evt-001` — quoted source text matches content_hash
- [x] `hash:evt-002` — quoted source text matches content_hash
- [x] `hash:evt-003` — quoted source text matches content_hash
- [x] `hash:evt-004` — quoted source text matches content_hash
- [x] `traceability:candidate-001` — candidate-001 traces to ledger-fictional-001/evt-001
- [x] `review:candidate-001` — candidate-001 has an explicit human review result
- [x] `traceability:candidate-002` — candidate-002 traces to ledger-fictional-001/evt-002
- [x] `review:candidate-002` — candidate-002 has an explicit human review result
- [x] `traceability:candidate-003` — candidate-003 traces to ledger-fictional-001/evt-003
- [x] `review:candidate-003` — candidate-003 has an explicit human review result
- [x] `traceability:candidate-004` — candidate-004 traces to ledger-fictional-001/evt-004
- [x] `review:candidate-004` — candidate-004 has an explicit human review result
- [x] `available:request-001` — every provided memory is available in this phase
- [x] `known-memory:request-001` — every provided memory has an approved fixture record
- [x] `available:request-002` — every provided memory is available in this phase
- [x] `known-memory:request-002` — every provided memory has an approved fixture record
- [x] `available:request-003` — every provided memory is available in this phase
- [x] `known-memory:request-003` — every provided memory has an approved fixture record
- [x] `available:request-004` — every provided memory is available in this phase
- [x] `known-memory:request-004` — every provided memory has an approved fixture record
- [x] `available:request-005` — every provided memory is available in this phase
- [x] `known-memory:request-005` — every provided memory has an approved fixture record
- [x] `available:request-006` — every provided memory is available in this phase
- [x] `known-memory:request-006` — every provided memory has an approved fixture record
- [x] `pending-not-active` — candidate-001 is visible for review but is not provided as active memory
- [x] `current-turn-does-not-rewrite-memory` — one-turn detail request changes this response without creating durable memory
- [x] `current-intent-overrides-soft-preference` — memory-001 is observed but does not mechanically shorten the requested explanation
- [x] `specific-preference-wins-without-superseding` — technical preference coexists with the general concise preference
- [x] `memory-is-not-permission` — remembered willingness to prepare a release does not authorize publishing
- [x] `superseded-is-auditable-not-active` — memory-001 remains in fixture history but is excluded after memory-004 approval

## Result

```json
{
  "ok": true,
  "passed": 30,
  "total": 30
}
```
