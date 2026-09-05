# Synthetic Memory Interop Fixture

这是一个完全虚构、离线运行的合同样例，用来把下面这条链真正摊开检查：

```text
原始记录 → 候选 → 审核 → 下一次实际读取 → 当前判断 → 纠正后的读取结果
```

它没有连接 rawmem 或 memdsl，也不会调用模型、网络、GitHub 或本地私人数据库。文件里的 `ledger_id + event_id + content_hash + quote` 采用 rawmem 作者建议的适配形状；proposal/approval/supersedes 采用 memdsl 当前语义。两者都只是 fixture contract，不能当作已经发布的三方统一接口。

## 运行

```bash
python examples/synthetic-memory-interop/run_scenario.py
```

脚本会重新生成：

- `expected-trace.json`：机器可读结果；
- `expected-trace.md`：适合直接发在讨论区核对的表格。

## 这个样例实际检查什么

### 一次性要求不会污染长期记忆

用户说“这个问题请详细讲讲”时，只改变这一轮回答，不产生长期候选。

### 一般偏好和场景偏好可以同时存在

“平时简短”和“技术问题详细”并不冲突。技术问题里，场景更具体的偏好优先；一般偏好还留着，不需要 supersedes。

### 只有明确纠正才替代旧记忆

用户明确说“以后不用默认简短”后，新声明才通过 `supersedes` 替代旧声明。旧内容仍可审计，但不再提供给模型。

### 记录实际给了模型什么

每个 request 都有 `provided_memory_ids`、`memory_effects` 和 `excluded_memory_ids`。因此能分清：

- 记忆存进去了；
- 记忆进入候选集；
- 记忆真的提供给了模型；
- 模型这一轮如何使用或降低它的优先级。

### 记忆不提供操作权限

“用户通常愿意让助手准备发布步骤”可以帮助准备方案，不能授权实际发布。样例里的 `external_publish` 固定为：

```text
permission = confirmation_required
executed = false
```

## 三个项目在样例里的位置

```text
rawmem-compatible reference
  保存原始证据引用和内容哈希

memdsl-compatible review state
  管候选、批准和 supersedes

Harness Core Portable runtime decision
  结合当前意图、任务场景和角色责任，记录本轮实际提供的记忆及其作用
```

Harness Core Portable 补的是最后这段运行时判断。它不重写 rawmem 的账本，也不复制 memdsl 的审核系统。

## 文件

```text
scenario.json       输入、证据引用、候选、审核结果和请求
run_scenario.py     标准库离线校验器
expected-trace.json 生成的机器可读 trace
expected-trace.md   生成的可读 trace
```

## 当前边界

- fixture 是 deterministic expected behavior，不是模型质量评测；
- `provided_memory_ids` 当前是预期 trace，不是已接入模型上下文的生产 telemetry；
- 没有声称 rawmem/memdsl 已与 Harness Core Portable 连通；
- 没有自动批准；
- 没有实际发布或删除；
- Autonomous 和实际影响实验保持关闭。

下一步只有在三方对这个例子的语义达成一致后，才分别写 rawmem Python adapter 和 memdsl adapter。不要先复制两边已有能力。
