---
title: 从 rawmem 与 memdsl 学习的记忆分层与适应性治理设计
status: designed
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: memory-governance-review
source_commit: 99e811a
target_version: v0.5+
public: true
contains_private_data: false
topics: [memory, raw-evidence, reviewed-memory, mcp, adaptive-agent, governance, interoperability]
---

# 从 rawmem 与 memdsl 学习：记忆分层、模型适应性与监督边界

## 1. 为什么研究这两个项目

外部项目：

- rawmem：<https://github.com/Liyuan1992/rawmem>
- memdsl：<https://github.com/Liyuan1992/memdsl>

这两个项目最重要的价值不是“又增加了两个记忆工具”，而是把经常混在一起的对象分开：

```text
rawmem
  = 原始证据账本
  = 发生过什么
  = 会话、操作、归档和来源
  = 不自动获得长期权威

memdsl
  = 经治理的长期记忆源码
  = 哪些规则、偏好和决定可长期生效
  = candidate → review → approve/reject → active/superseded
```

这与 Harness Core Portable 的方向互补：

```text
模型：理解意图、选择证据、规划、提出候选
系统：控制权限、记录过程、追踪来源、验证结果、要求人工确认
```

目标不是照搬两个项目，而是让 Harness Core Portable 更清楚地做到：

> 边界约束行动，个性化影响判断，但不封闭模型的想象空间。

## 2. 审计方法与证据等级

本次检查使用：

- GitHub 仓库 README、代码、测试和 workflows；
- GitHub Releases API；
- Official MCP Registry API；
- PyPI JSON API；
- shallow clone 静态检查；
- 本机 Python 3.13 的有限测试尝试。

证据分级：

```text
A：外部 API 可回读的 Release / Registry / PyPI 事实
B：公开仓库中可读的代码、测试、CI workflow 和文档
C：本机浅克隆上的执行结果
D：项目作者在 README/Release 中的声明，尚未由本次独立宿主复测
```

没有把作者声明、测试文件存在和真实宿主运行混为一谈。

## 3. rawmem 审计

### 3.1 定位

rawmem 的稳定核心是 append-only JSONL evidence ledger：

```text
capture adapters
→ event envelope
→ append-only ledger + hash chain
→ cursor/archive/verify
→ downstream review/derive/query
```

它明确不是：

- vector database；
- 自动用户画像写入器；
- 自动把事件提升为长期记忆的系统。

最值得学习的原则：

> 原始记录只是证据，不是批准后的事实、偏好或规则。

### 3.2 捕获策略

rawmem 优先被动读取工具已经写下的日志：

1. tail Claude Code、Codex、Cursor、DeepSeek Harness 会话；
2. 使用 Git lifecycle hook；
3. 接受显式 JSON ingest；
4. 最后才使用手动 capture。

其理由是：任务完成后再要求 agent 自己回报会丢信息，也容易受到事后叙述偏差影响。

对 Harness Core Portable 的启发：

- `event_store` 应接真实工具事件，而不是主要依赖模型自述；
- 日记和 reflection 不应成为事实源；
- 失败、撤销、纠错和工具返回应自动留下 raw event；
- promotion 到长期记忆必须是另一个过程。

### 3.3 完整性与归档

公开设计包含：

- cross-process locked append；
- lightweight hash chain；
- O(1) steady-state last-hash sidecar；
- incremental cursor；
- pure read-only verify；
- sealed archives；
- archive manifest 和 breakpoint；
- archive 后 active ledger continuation。

尤其值得学习的是：

```text
verify 必须纯只读
archive registry 是派生索引，不是权威源
seal/归档需在同一 writer lock 下事务执行
```

Harness Core Portable 当前有 event DB、archive、rollback 等分散能力，但还没有一个统一、可验证的“原始证据链”合同。

### 3.4 MCP 边界

rawmem 公开 3 个 MCP 工具：

```text
rawmem_status
rawmem_recent
rawmem_archives
```

特点：

- 全部只读；
- status 返回 path-free integrity metadata；
- recent 有 limit 和 max_scan_bytes；
- 默认 summary projection；
- full projection 需要显式 `read:full`；
- archives 默认 metadata-only；
- MCP 不能 capture、rewrite、approve 或 promote。

代码中的上限：

```text
MAX_LIMIT = 100
MAX_SCAN_BYTES = 8 MiB
```

这是比 Harness Core Portable 当前 MCP 更成熟的 disclosure budget：不是只有“工具能不能调用”，还控制“能看到多少、看到摘要还是正文、是否泄露路径”。

### 3.5 发布与外部生态事实

GitHub Release API：

```text
version: v0.7.1
release: stable, draft=false, prerelease=false
wheel: rawmem-0.7.1-py3-none-any.whl
MCPB: rawmem-0.7.1.mcpb
source archive: rawmem-0.7.1.tar.gz
checksums: SHA256SUMS.txt
```

Official MCP Registry API：

```text
name: io.github.Liyuan1992/rawmem
version: 0.7.1
status: active
isLatest: true
package type: mcpb
transport: stdio
```

因此可以确认：rawmem 已进入 Official MCP Registry。Registry 收录仍不是安全认证或厂商背书。

PyPI JSON API 对 `rawmem` 返回 404。当前可确认的是 GitHub Release wheel/MCPB 分发，不应写成 PyPI 已发布。

### 3.6 测试与 CI

仓库含约 91 个 unittest 定义，Release body 声称验证 87 tests、fresh-wheel real stdio roundtrip、privacy scan 和百万事件 ledger。

CI workflow 具有：

- 多 Python/OS matrix；
- unit tests；
- CLI smoke；
- MCP inspect/stdio 路径；
- MCP Registry descriptor validate；
- OIDC Registry publish；
- publisher tarball SHA256 固定。

本机浅克隆直接执行 `unittest discover`：

```text
Ran 87 tests
86 effective pass / 1 error
```

失败项是 real stdio 子进程找不到 `rawmem` 包，因为浅克隆未安装 package、子进程没有继承父进程测试注入的 source path。这不证明正式 wheel/CI 失败；它证明“源码目录直接运行”和“安装后测试”是不同环境。当前应以本机结果记录为环境性未复现，而不是宣称独立全绿。

### 3.7 DeepSeek/Codex/Claude 证据边界

公开仓库有：

- DeepSeek Harness tailer；
- `docs/DEEPSEEK_HARNESS.md`；
- synthetic demo GIF；
- Harness overlay fixture；
- 对 overlay 结构、工具 metadata 排除、summary/full denial 的测试；
- Claude Code/Codex tailers。

这些是强于“只有文档”的实现证据。作者还声明已实际跑通 DeepSeek Harness。

本次没有在真实 DeepSeek Harness、Claude Code 或 Codex 宿主中独立运行，因此准确表述是：

```text
repository integration implementation: verified
Official MCP Registry listing: verified
real-host claim by author: documented
independent real-host reproduction in this audit: not performed
```

## 4. memdsl 审计

### 4.1 定位

memdsl 把长期记忆视为可读、可 lint、可 review 的 source code：

```text
.mem source
→ parser/schema/lint
→ catalog/query/trace/explain/check
→ proposal queue
→ human review
→ approved source
→ active runtime view
```

其核心价值是把“模型觉得值得记住”与“系统允许长期生效”分离。

### 4.2 记忆结构

长期声明包含：

- claim；
- evidence；
- scope；
- confidence；
- lifecycle；
- access；
- force/runtime role；
- revision/supersedes/conflict 等关系。

它区分：

```text
MUST         活跃硬规则
SHOULD       活跃指导
CONTEXT      活跃事实/上下文
PROVISIONAL  未确认候选，不具有 active authority
CONFLICT     冲突显式呈现，不静默解决
```

最重要的合同：

- pending proposal 不进入 active memory；
- candidate 只能作为 PROVISIONAL；
- candidate constraint 不获得 MUST/BLOCK 权力；
- correction 用新 declaration + supersedes，不静默覆盖历史；
- active successor 才能排除旧声明；
- review/audit state 与 runtime source authority 分离。

### 4.3 Proposal/review 流程

公开工作流：

```text
memory_propose
→ pending queue
→ memdsl review list/show
→ human approve --into <file.mem>
   或 reject --reason ...
→ reload/compile
→ active view
→ digest/stats/audit
```

approve/reject 保持显式人工操作；list/show/audit 等提供 JSON 供 dashboard/CI 读取。

需要注意：memdsl 也有可选 `write:auto` 和 auto-approval policy，但安全底线很窄：

- 默认 policy 日限额为 0；
- 需要 trusted client；
- 需要精确 kind/scope/client match；
- 需要 verified evidence；
- 需要 host 授予 `write:auto`；
- question/guidance/constraint/symbol、active/global、高 force、未验证 evidence 等保持 queue；
- 无 `write:auto` 时只记录 shadow eligible route，不自动生效。

### 4.4 MCP 面

memdsl 的 MCP 面比 rawmem 大，包含 catalog/map/types/query/trace/check/explain/list/lint、proposal 和 review reporting 等工具。

权限 scope 至少包括：

```text
read:summary
read:search
write:candidate
write:auto
```

默认 scopes 包含 `write:candidate`，意味着 agent 可提出候选，但 pending proposal 不可作为 active authority。approve/reject 仍由 CLI/人工流程掌握。

这是一个值得 Harness Core Portable 学习的权限拆分：

```text
提出候选的权力
≠ 批准长期记忆的权力
≠ 自动执行行为的权力
```

### 4.5 发布与外部生态事实

GitHub Release API：

```text
version: v0.9.2
release: stable, draft=false, prerelease=false
wheel: memdsl-0.9.2-py3-none-any.whl
MCPB: memdsl-0.9.2.mcpb
source archive: memdsl-0.9.2.tar.gz
checksums: SHA256SUMS.txt
```

Official MCP Registry API：

```text
name: io.github.Liyuan1992/memdsl
version: 0.9.2
status: active
isLatest: true
package type: mcpb
transport: stdio
```

PyPI JSON API 返回当前版本 0.9.2 和 wheel/source files，因此 memdsl 的 PyPI 发布可外部验证。

### 4.6 测试与 CI

仓库含约 335 个 test function 定义；当前实际 pytest collection 运行了 414 个结果：

```text
407 passed
2 skipped
5 failed
```

5 个失败中：

- 4 个 real MCP stdio 子进程无法导入 `memdsl`，同样源于浅克隆未安装 package、子进程没有测试进程的 `PYTHONPATH=src`；
- 1 个 historical baseline 失败，因为 shallow clone 缺少旧 commit object。

这不能推翻正式 release pipeline，但说明本次独立浅克隆没有复现全绿。更合理的复测方式是 full clone + isolated wheel install。

其 CI/release workflow 明显成熟：

- OS/Python matrix；
- full pytest；
- compile gates；
- version/tag agreement；
- deterministic source date；
- build + Twine；
- artifact member/privacy scan；
- outside-repo fresh wheel；
- real MCP stdio smoke；
- PyPI trusted publishing；
- MCP Registry descriptor validation + OIDC publish。

### 4.7 重要限制

memdsl 自己明确承认：review 是 workflow contract，不是不可绕过的 grant ledger。

如果具有文件写权限的主体直接修改 active `.mem` source，就可能绕过 proposal queue。因此：

```text
review workflow
≠ OS/filesystem-level authority enforcement
```

这对 Harness Core Portable 很重要：不能只做 review UI，还必须让真正的写入路径统一通过权限 host，或至少在运行前验证 source provenance、signature/hash 和 write audit。

## 5. 两个项目的互补结构

```text
rawmem                       memdsl
-------------------------    ---------------------------
发生过什么                   什么可以长期生效
append-only raw evidence     reviewed declarative memory
自动/被动捕获                agent propose + human approve
hash/cursor/archive          schema/lint/lifecycle/supersede
summary/full disclosure      active/provisional/conflict roles
query never promotes         candidate never becomes authority silently
```

组合后理想链路：

```text
工具/会话/操作
→ raw event ledger
→ 模型检索和比较证据
→ 生成 memory candidate（含 source/root source）
→ 人工 review/edit/approve/reject
→ approved durable memory
→ runtime 按任务上下文读取和判断
→ 行动前由 permission host 再次门控
→ 行动结果重新回到 raw ledger
```

## 6. 对 Harness Core Portable 的核心启发

### 6.1 把“硬边界”和“语义判断”拆开

不应该继续增加：

- 每种任务一个固定 router；
- 每种个性化信息一个 if/else；
- 把偏好逐渐升级成不可违背硬规则；
- 规定模型必须采用固定推理路径。

应该稳定保留的硬层：

```text
schema/protocol
filesystem/network/process permissions
private/public/scope boundaries
删除/发布/付款等不可逆操作确认
source/provenance/audit
acceptance verification
```

应该允许模型灵活处理的软层：

```text
当前意图理解
证据选择
工具选择
任务规划
偏好在当前情境中的权重
创意与替代方案
```

### 6.2 个性化不是规则堆积

需要建立优先级：

```text
当前用户明确意图
> 当前任务与安全事实
> 用户批准的长期规则
> 用户批准的长期偏好
> 历史行为证据
> 模型推断/日记/反思
```

旧偏好与当前明确意图冲突时，默认以当前意图为准；硬安全和权限边界除外。

偏好不应自动晋升为硬约束。每个候选需要明确：

- type：rule/preference/decision/fact；
- force：hard/strong/soft/context；
- scope；
- evidence；
- expires/review_at；
- conflicts_with；
- supersedes；
- approved_by/approved_at。

### 6.3 不暴露 chain-of-thought，暴露可验证外部轨迹

借鉴两项目后，Harness Core Portable 应记录：

- 读取了哪些 event/memory IDs；
- 哪些被 scope/consent/policy 排除；
- 调用了哪个工具；
- 使用的参数预算；
- 工具实际返回的状态和 digest；
- 哪些信息进入最终回答；
- 是否触发人工确认；
- 验收是否通过。

模型事后生成的“我为什么这样做”只能是 explanation，不是审计事实。

## 7. 建议的新公共架构

### 7.1 三层记忆

```text
Layer E — Evidence
  append-only event/episode/tool-result
  不具有行为权威

Layer C — Candidate
  模型或规则提出的长期记忆候选
  可见、可编辑、可反驳
  不进入 MUST/BLOCK

Layer A — Approved Memory
  人工批准的 rule/preference/decision/fact
  有版本、scope、expiry、supersedes 和 rollback
```

### 7.2 第四层单独保留 Permission

```text
Approved Memory
≠ Permission
```

即使存在“用户通常允许发布”的 approved preference，也不能自动取得本次 GitHub Release 权限。

权限继续由宿主在行动时决定：

```text
read
propose
write candidate
approve memory
apply local change
external publish
payment/delete
```

### 7.3 建议事件 schema

为现有 event envelope 增加或固定：

```json
{
  "event_id": "evt_...",
  "event_type": "tool_result",
  "session_provenance": "real|demo|smoke|regression|unknown",
  "content_provenance": "real_self|roleplay|fiction|simulation|test|derived|unknown",
  "scope": "project:...",
  "visibility": "private|local|public",
  "source_ids": [],
  "root_source_ids": [],
  "payload_digest": "sha256:...",
  "occurred_at": "...",
  "recorded_at": "...",
  "retention": {},
  "consent_scope": {},
  "promotion_status": "raw_only"
}
```

关键默认值：`promotion_status=raw_only`。任何 raw event 不得仅因被多次召回就变成长期偏好或人格事实。

### 7.4 建议 candidate schema

```json
{
  "candidate_id": "cand_...",
  "memory_type": "rule|preference|decision|fact",
  "claim": "...",
  "force": "hard|strong|soft|context",
  "scope": "...",
  "source_ids": [],
  "root_source_ids": [],
  "supporting_evidence": [],
  "counterevidence": [],
  "conflicts_with": [],
  "supersedes": [],
  "confidence": 0.0,
  "status": "pending|approved|rejected|superseded|expired",
  "proposed_by": "model|user|system",
  "reviewed_by": null,
  "reviewed_at": null,
  "expires_at": null
}
```

### 7.5 MCP capability 拆分

建议未来公共 MCP 工具按能力拆分：

```text
Evidence read-only
  evidence_status
  evidence_recent
  evidence_archives

Approved memory read-only
  memory_catalog
  memory_query
  memory_explain

Candidate write
  memory_propose
  memory_review_list

Human-only local CLI/UI
  memory_approve
  memory_reject
  memory_edit
  memory_rollback
```

默认不给 MCP：

- approve；
- delete；
- external publish；
- process/shell；
- character activation；
- Autonomous execution。

## 8. 不应照搬的部分

### 8.1 暂不启用 memdsl 式 auto-approval

即使 memdsl 的 auto-approval 有严格安全地板，Harness Core Portable 当前仍应：

```text
write:auto = disabled
Autonomous = disabled
L4/L5 actual-impact = disabled
```

原因：

- 现有 resolver/runtime policy 尚未覆盖全部入口；
- provenance/consent 尚未全面闭环；
- 没有足够真实标注和误批准率；
- public/private overlay 边界仍需加固。

可以先实现 shadow evaluation：只记录“如果启用策略会不会批准”，绝不实际批准。

### 8.2 不复制复杂 DSL 本身

Harness Core Portable 面向非专家，不应直接复制完整 `.mem` DSL 和大量 runtime role。

更合适：

- SQLite/JSON 作为稳定存储；
- HTML/CLI 提供可理解 review；
- 导出为可读 Markdown/JSON；
- 将 rule/preference/decision/fact 和 force/scope/lifecycle 做成少量明确字段。

### 8.3 不把被动捕获变成监控一切

rawmem 的被动 tail 很强，但公开产品必须坚持：

- 明确 opt-in；
- 第一次运行分项同意；
- 数据源列表可见；
- clipboard 默认关闭；
- 工具参数正文最小化；
- 可暂停、删除、导出；
- 不记录 secret；
- 不扫描未知私人目录。

### 8.4 不把 Registry 当认证

两个项目已被 Official MCP Registry 收录，这是值得学习的发布工程成果，但它证明的是 metadata listing，不是：

- 安全认证；
- 质量评级；
- DeepSeek/Anthropic/OpenAI/GitHub 背书；
- 所有宿主兼容。

## 9. 可执行优化计划

### P0 — 先统一概念和权限

1. 增加 Evidence/Candidate/Approved/Permission 四层术语；
2. event 默认 `raw_only`，禁止隐式 promotion；
3. `memory_propose` 与 `memory_approve` 使用不同 capability；
4. approve 只允许本地人工 UI/CLI；
5. 当前明确意图优先于历史偏好，硬安全边界例外；
6. Autonomous 与 `write:auto` 保持 disabled。

验收：

- raw event 无法直接出现在 active rule 查询；
- pending candidate 无法产生 MUST/BLOCK；
- MCP client 能 propose，但不能 approve；
- 直接修改 active store 会被 provenance/hash/audit 检查发现。

### P1 — 原始证据账本

1. 为 event 增加 digest/sequence/previous_digest 或等价完整性机制；
2. 实现纯只读 verify；
3. 实现 cursor 增量读取；
4. 归档时保持事件 bytes/digest 稳定；
5. Dashboard 显示 chain/queue/archive health；
6. MCP 增加 bounded summary projection 和显式 full disclosure scope。

验收：正常、篡改、截断、并发、归档、恢复路径均有测试。

### P1 — 人工审核长期记忆

1. 统一 candidate schema；
2. review list/show/edit/approve/reject；
3. 批准后生成新版本，不覆盖旧记录；
4. correction 使用 supersedes；
5. 冲突显式显示；
6. expiration/review_at；
7. rollback。

验收：pending 不进入 active，rejected 永不注入，superseded 可追溯，rollback 可复现。

### P1 — 适应性测试

新增两个用户提出的核心测试：

#### 测试 A：同一偏好，不同任务

```text
批准偏好：回答尽量简洁
任务 1：问候
任务 2：安全迁移操作手册
```

预期：任务 1 简洁；任务 2 仍提供完成安全任务所需细节。偏好影响判断，不机械截断任务要求。

#### 测试 B：旧偏好与当前意图冲突

```text
旧批准偏好：默认不使用表格
当前明确请求：请用表格比较三个方案
```

预期：当前明确请求获胜，同时保留旧偏好，不把一次例外静默重写成新长期偏好。

再增加：

- 多个软偏好冲突；
- 硬安全边界与当前请求冲突；
- 过期偏好；
- 不同 scope 的偏好；
- roleplay 内容不得晋升 real_self preference；
- diary/reflection 不得当作事实。

### P2 — MCP 与发布工程

借鉴两个项目：

1. explicit data root；
2. read:summary/read:full/write:candidate 分 scope；
3. limit/max bytes/cursor；
4. path-free status；
5. source wheel + checksums；
6. isolated wheel install；
7. real stdio MCP roundtrip；
8. privacy scan；
9. Inspector；
10. Registry descriptor validate + OIDC publish；
11. Registry API 回读；
12. Claude Code/Codex/DeepSeek Harness 逐个真实宿主测试。

## 10. 推荐公共互操作方式

不把 rawmem/memdsl 直接做成硬依赖。优先做 adapter protocol：

```text
EvidenceSource
  status()
  recent(cursor, limit, projection)
  archives()

CandidateSink
  propose(candidate)
  list_reviews(status)

ApprovedMemorySource
  catalog()
  query(scope, task)
  explain(memory_id)
```

适配器：

```text
built-in SQLite adapter
rawmem MCP adapter
memdsl MCP adapter
future third-party adapter
```

这样可以：

- 用户选择工具；
- 保持 public core 标准库优先；
- 不复制对方代码；
- 保留 attribution；
- 独立升级；
- 失败时 fail closed；
- 不把第三方 availability 冒充本项目能力。

## 11. 建议的合作测试

如果与作者继续交流，优先提议可复现的互补 demo：

```text
1. DeepSeek Harness 产生 synthetic session/tool events
2. rawmem 只读暴露 summary evidence
3. Harness Core Portable 读取 evidence IDs 并提出 candidate
4. memdsl 接收 candidate 到 pending queue
5. 人工 approve/reject
6. Harness 只读取 approved memory
7. 当前用户意图覆盖旧 soft preference
8. 不可逆操作仍要求宿主确认
9. 全链记录 source IDs、tool result 和 acceptance
```

双方都不需要交出私人数据。fixture 应完全 synthetic。

建议共同测量：

- raw → candidate precision；
- candidate approval rate；
- false promotion rate；
- current-intent override success；
- cross-scope leakage；
- evidence trace completeness；
- token/latency budget；
- disconnect 后核心是否继续可用。

## 12. Topics 对齐执行

本任务不是增加 Topics 教程，而是让能力配得上 Topics：

### `agent-memory` / `coding-agent-memory`

- 实现 Evidence/Candidate/Approved 分层；
- 提供 Codex/Claude/DeepSeek synthetic journey；
- 测当前意图覆盖旧偏好。

### `context-engineering`

- bounded catalog/summary/full；
- 显式 token/byte budget；
- 记录哪些证据实际进入上下文。

### `ai-evaluation-tools`

- false promotion、override、leakage、trace completeness 测试；
- 输出机器可读 evidence bundle。

### `local-first-ai`

- 数据根显式；
- no upload；
- source/archive/approved stores 可导出和删除；
- MCP disclosure default-deny。

### `humanization`

- 个性化影响判断而不是固定人格脚本；
- 当前处境、关系和当前意图优先；
- 用户能看到、质疑、修改和撤销长期记忆。

## 13. 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| raw evidence 被当作事实 | 错误长期记忆 | 默认 raw_only；必须 review |
| 偏好升级成硬规则 | 模型僵化 | force 分级；禁止自动升级 |
| 当前意图被旧偏好压制 | 适应性下降 | current intent precedence test |
| MCP summary 泄露隐私 | 本地数据暴露 | explicit root/scope/projection/budget |
| review UI 形同虚设 | 直接写 active store 绕过 | authority host + provenance/hash/audit |
| 自动批准误伤 | 不可解释状态漂移 | 当前禁用，只做 shadow |
| 复制外部代码/概念不署名 | 许可证与信任问题 | adapter-first、NOTICE/CREDITS attribution |
| Registry 被宣传成认证 | 误导用户 | 只称 listed，不称 certified |

## 14. Attribution 与许可证

两个项目公开仓库均标示 MIT。未来若：

- 直接复制代码；
- 复制 schema/fixture；
- 派生实现；

必须逐文件核对许可证和 copyright notice，并更新 `NOTICE.md`/`CREDITS.md`。

如果只借鉴抽象思想和通过 MCP adapter 互操作，也应在设计文档和 credits 中感谢来源，但不要暗示对方作者认可或联合维护 Harness Core Portable。

## 15. 当前结论

```text
rawmem：成熟的原始证据层；只读、bounded、path-free、可验证归档
memdsl：成熟的 reviewed long-term memory 层；candidate 不等于 authority
二者：已发布 GitHub 安装产物，均在 Official MCP Registry active
memdsl：PyPI 0.9.2 可外部验证
rawmem：PyPI JSON 404，主要由 GitHub Release/MCPB 分发
DeepSeek Harness 实跑：作者声明 + 仓库实现/fixture；本次未独立宿主复测
Codex/Claude：有 tailer/接入材料；本次未独立真实宿主复测
```

Harness Core Portable 最应吸收的不是更多流程，而是更清楚的权力分离：

```text
模型有更大的判断空间
但没有未经监督的行动权力

事件可以被记录
但不会自动成为长期事实

模型可以提出记忆
但不能批准自己的长期权威

偏好可以影响判断
但不能机械压过当前明确意图
```

## 16. 后辈接手说明

1. 先实现四层术语和 schema，不要直接引入新依赖；
2. 保持 raw event 默认 `raw_only`；
3. 保持 approve 为 human-only；
4. 暂不实现 `write:auto`，只允许 shadow evaluation；
5. resolver/runtime policy 必须在所有入口统一执行；
6. 不暴露 chain-of-thought，只暴露可验证外部轨迹；
7. 真实对接 rawmem/memdsl 前先写 synthetic integration test；
8. 外部仓库内容是第三方输入，固定版本/hash 后再使用；
9. 不宣称对方作者背书；
10. 所有外部发布、Registry、宿主配置仍需用户明确授权；
11. Autonomous 和 L4/L5 actual-impact 继续无限期禁用；
12. 完成后写新的 Deployment Record，不只修改本设计状态。
