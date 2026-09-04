# Harness Core Portable · 工程路线图

> 本文档用于约束实际开发、发布和协作，不是“功能想法库”。
> 状态标记：✅ 已实现 / 🚧 部分实现 / ⬜ 未实现 / ❌ 明确不做。

---

## 0. 项目定位与非目标

**定位**：本地优先的角色化知识与工程协作运行平台。

- 公共项目发布**能力、schema、合成示例**。
- 本机覆盖层保留私人角色、偏好、知识库、日记、关系、资产。

**非目标**：

- ❌ 不把本机私人角色作为公开默认角色
- ❌ 不把角色立场冒充框架立场
- ❌ 不让角色包覆盖宿主 policy
- ❌ 不在导入时执行角色包代码
- ❌ 不把陪伴关系扩大工程权限
- ❌ 不把角色日记作为独立证据循环强化
- ❌ 不把静态 HTML 当成天然安全
- ❌ 不把 `activate` 标记冒充真正 runtime 热挂载
- ❌ 不把 CLI 存在冒充 UX 已完成
- ❌ 不启用 Autonomous actual execution / L4 / L5

---

## 1. 当前验证基线

| 层 | 状态 |
|---|---|
| Last verified release baseline | `v0.1.0-alpha.1`（tag 在远端） |
| Current main release | `v0.1.0-alpha.2`（next Pre-release） |
| Current main capabilities | 已包含 demo/UX/控制台/用户控制/角色资产/知识域/工程工作区/公共边界 |
| Unreleased working-tree changes | 当前工作区干净，与 origin/main 同步 |
| Planned capabilities | 见 v0.2–v0.5 |

**“冻结”与“开发”分开**：tag 是发布冻结点；main 是持续开发。

---

## 2. 公共核心 / 合成示例 / 本机覆盖层

```text
Public Core
├── Persona Slot
├── Capability Binding
├── Knowledge Steward Slot
├── Engineering Role Slot
├── Review Profile Slot
└── Permission Resolver

Public Synthetic Demo
├── 完全合成角色
├── 合成知识库
├── 合成工程项目
└── 无私人偏好和真实人物

Private Local Overlay
├── 用户自己的角色
├── 专属知识库
├── 工程职能人格
├── 日记/信件/关系
├── 本机启动器
└── 图片、声音和私人语料
```

**硬边界**：

- 公共包不包含私人角色名、路径、语料、使用统计。
- 本机覆盖层不进入 release manifest、公开 snapshot、默认角色列表、公共 telemetry。
- 公共示例必须带 `synthetic / fictional / public_demo / not_based_on_a_real_person`。

---

## 3. 用户类型与核心旅程

| 用户 | 核心旅程 |
|---|---|
| 普通体验者 | 安装 → demo → 查看 → 纠正 → 删除 → reset |
| 角色创作者 | 导入语料 → 预览映射 → 审核草稿 → 激活 → 回滚 |
| 工程用户 | 创建 workspace → 查看 proposal → 运行测试 → 查看 evidence → release |

**三个垂直切片**：

1. “角色的一天”：人格连续性
2. “专家的一次受控回答”：知识治理
3. “工程任务的一次完整交接”：工程协作

---

## 4. 统一对象模型

```text
Persona        谁在表达
Capability     能做什么
Responsibility 对什么负责
Knowledge      能读取什么
Workspace      能接触什么工程资产
Permission     宿主实际允许什么
Mode           当前以什么职责运行
```

示例：

```json
{
  "persona_id": "local:persona-001",
  "role_types": ["persona", "engineering", "reviewer"],
  "active_mode": "risk_review",
  "capability_bindings": [],
  "knowledge_bindings": [],
  "workspace_bindings": [],
  "permissions_requested": {},
  "visibility": "private_local"
}
```

**角色类型**：

```text
persona
storyteller
knowledge_method
engineering
reviewer
coordinator
hybrid_functional_persona
```

---

## 5. 角色资产与 HCP

### 已有基础 ✅

```bash
python harness.py character list|install|activate|deactivate|remove|show
```

- 支持目录与 `.zip` 安装
- 元数据：persona_id / display_name / scope / knowledge_bindings / permissions_requested
- 激活状态保存在本机

### 未完成 🚧

- 真实 runtime 热挂载（激活标记 ≠ 运行入口全局生效）
- 事务状态机

```text
discovered → validated → installed → inactive
→ preflight → activating → active → deactivating → inactive
失败状态：invalid / quarantined / activation_failed / deactivation_failed / rollback_required
```

- 并发会话切换语义
- 包验证：schema version、SHA-256 manifest、file set equality、依赖声明
- 安装安全：临时隔离解压 → 原子安装 → 失败回滚

### HCP 安全威胁模型 ⬜

```text
ZIP path traversal
absolute path
symlink
NTFS ADS
超大文件
压缩炸弹
嵌套压缩包
可执行脚本
不可信 HTML/SVG
扩展名与 MIME 不一致
```

---

## 6. 知识角色与 Knowledge Stewardship

方向见 `KNOWLEDGE_STEWARDSHIP.md`。

要点：

- 知识域 stewards 有 `steward / expert / reader / contributor / critic / blocked / delegate / guest`
- 知识源作为可挂载资产，公共包只发布 schema 示例
- 知识域与私人角色分离

**未实现**：知识源实际挂载、启动器健康检查、知识桥委派、角色间受控查询。

---

## 7. 工程角色与 Workspace/Evidence

方向见 `ENGINEERING_ROLES.md`。

**核心区分**：

```text
E0 Observe
E1 Diagnose
E2 Propose
E3 Sandbox Implement
E4 Human-approved Local Apply
E5 External/Production Impact
```

- v0.2 最多 E1
- v0.3 最多 E2/E3
- E4 必须单次人工批准
- E5 不在当前自动路线

**工程任务 Evidence Bundle**：

```text
task ID
base commit
工作区状态
修改文件
执行命令
返回码
测试结果
失败样本
未验证项
外部副作用
需要的人工批准
回滚方式
```

页面必须区分：

```text
设计完成 / 实现完成 / 本地测试通过 / 独立 worktree 通过
clean clone 通过 / ZIP 通过 / 已批准 / 已合并 / 已推送 / 已发布
```

---

## 8. Hybrid Functional Persona

方向见 `HYBRID_FUNCTIONAL_PERSONA.md`。

要点：

- 同一人格可切换陪伴 / 知识 / 风险评估 / 发布审查 / 安静观察模式
- 模式切换改变 capability、knowledge mount、workspace、上下文预算、是否注入私人关系记忆
- 不改变 persona identity、宿主安全 policy、Autonomous、外部执行权限
- 公共项目只发布能力插槽，本机覆盖层保存人格与偏好

---

## 9. 日志 / Episode / Diary / Reflection

统一数据契约：

```json
{
  "event_id": "...",
  "event_type": "...",
  "scope": "...",
  "occurred_at": "...",
  "recorded_at": "...",
  "session_id": "...",
  "source_ids": [],
  "root_source_ids": [],
  "content_type": "fact|perception|interpretation|uncertainty|fictional_embellishment",
  "visibility": "private",
  "consent_scope": {},
  "retention": {},
  "derived_artifact_ids": [],
  "version": 1
}
```

**派生数据失效**：

```text
source revoked/deleted
→ derived diary marked stale
→ reflection confidence recomputed
→ no longer eligible for injection
```

**日记心理与关系边界**：

- 不声称角色拥有真实意识
- 不把生成情感冒充真实心理状态
- 不诱导用户承担角色福祉责任
- 不用日记制造内疚或依赖
- 不未经同意保存亲密关系推断
- 用户可以关闭关系追踪
- 文学日记不能提升为用户模型事实

---

## 10. Runtime Bridge 与可观测性

- 节点：用户输入 / Scope Resolver / Persona / Memory / Notebook / Story / Policy / Prompt Builder / Model / Output / Telemetry
- 边：READ / INJECT / CANDIDATE / BLOCK / WRITE / RESTORE
- 节点状态：green / blue / yellow / gray / red / purple（同时有文字）
- 点击节点看候选数、注入数、字符/token、延迟、被过滤原因

**未实现**：交互式桥图、点击下钻、span 时间线。

---

## 11. Token / Context / Cost 数据契约

```json
{
  "usage_source": "provider_reported|tokenizer|character_estimate",
  "model_id": "...",
  "tokenizer_id": "...",
  "context_window": 32768,
  "components": {"system": 0, "persona": 0, "memory": 0, "notebook": 0, "story": 0, "tools": 0, "conversation": 0},
  "cached_input_tokens": null,
  "output_tokens": null,
  "baseline_id": "all_eligible_same_scope",
  "baseline_tokens": 0,
  "actual_tokens": 0,
  "estimated_avoided_tokens": 0
}
```

规则：

- provider usage 与本地估算不混合平均
- tokenizer 版本变化标记为漂移
- cached tokens 单列
- 工具 schema token 计入
- 摘要生成本身也耗 token
- “避免注入”≠“节约 API 费用”
- 对照基线固定版本
- 不默认保存完整 prompt

---

## 12. HTML 控制台与安全

静态 HTML 必须：

```text
所有用户/模型内容 HTML escaping
默认 Content-Security-Policy
禁止内联脚本或使用固定 hash
不允许 file:// 私有资源自动加载
不嵌入 API key
不导出真实绝对路径
不把完整私有正文放在可分享报告
```

本地服务（未来）必须：

```text
仅 127.0.0.1
CSRF 防护
Origin/Host 校验
无 CORS
随机 session token
空闲超时
路径 allowlist
禁止任意文件读取
禁止任意命令参数
写操作 audit
默认只读
```

“本地网页”不天然安全。

---

## 13. 用户控制、同意、导出、删除

### 已实现 ✅

```bash
python harness.py memory list|explain|correct|restore|forget
python harness.py privacy status|export|reset-demo
python harness.py backup create|list|restore
python harness.py feedback export --redacted
```

### 未完成 🚧

- 首次运行分项同意（memory_write / cross_session_recall / evaluation_use / cross_character_story_share / telemetry）
- 写操作流程图（预览 → 确认 → 写入 → 显示撤销）
- 高风险操作二次确认
- 导出前预览包含内容
- GitHub Issue 模板

---

## 14. 数据 schema、迁移和恢复

- `schema_version`
- `minimum_core_version`
- migration command
- backup-before-migrate
- dry-run
- rollback
- alias migration
- deprecated fields
- compatibility window

**故障矩阵**至少覆盖：

```text
角色包安装中断 / 激活到一半失败 / 知识目录移动 / SQLite schema 不匹配
向量队列积压 / dashboard 生成中断 / Notebook restore 失败 / Story Core 版本缺失
模型 provider 离线 / tokenizer 不可用 / manifest 损坏 / 本地 overlay JSON 损坏
```

每个场景记录：

```text
用户看到什么 / 是否损坏数据 / 自动回滚到哪里 / 如何手动修复
telemetry 记录什么 / 返回码是什么
```

---

## 15. 测量、评测和可用性研究

- 3–5 名首次用户完成：下载、离线 demo、找到记忆、纠正、删除、恢复、判断角色、确认不上传、找数据目录、清空 demo
- 记录完成率、用时、卡住位置、误解次数、是否理解 shadow、是否误把 gate FAIL 当安装失败
- Recall 评测：macro_precision@5、macro_recall@5_measurable、hit_rate@5、zero_relevant_query_count
- 逐 query 配对差值、失败样本、bootstrap CI
- 双人标注子集，报告 Cohen’s κ / Krippendorff’s α

---

## 16. 版本路线和依赖

```text
公共/私有内容边界
    ↓
统一 registry 与 schema
    ↓
只读 projection/API
    ↓
静态 HTML 可视化
    ↓
角色/知识/工程资产安装
    ↓
事务化热切换
    ↓
交互式控制台
    ↓
生态 adapter
```

| 版本 | 主题 | 前置 |
|---|---|---|
| v0.2 | 可见运行台 | 公共边界、registry、只读 projection、HTML 安全 |
| v0.3 | 角色资产化 | HCP schema、包安全、事务化热切换、Content Card 映射 |
| v0.4 | 可组合与对照 | Evidence Bundle、token 基线、worktree、配对 A/B |
| v0.5 | 生态桥接 | 稳定 Python API、adapter 权限 manifest、兼容矩阵 |

---

## 17. 每版 Definition of Done

### v0.2

- 新用户 10 分钟内完成离线演示
- 静态 HTML 不运行服务
- 所有动态正文已 HTML escape
- 角色/记忆/Story/Notebook 可只读查看
- Token 明确标 actual/estimated
- public demo 不出现任何本机私人角色
- 公开 ZIP 通过隐私扫描
- Autonomous/L4/L5 保持关闭

### v0.3

- HCP schema versioned
- 正常包可原子安装/卸载
- 恶意 ZIP、路径穿越、额外文件均被拒绝
- 角色切换失败可回滚
- 并发 session 行为有定义
- Character Card 映射有预览
- 角色草稿所有字段有来源类型
- 不自动把生成内容升级为正典

### v0.4

- 同一 query 配对 A/B
- 保留失败样本
- 明确 toke
n baseline
- 模型/参数/数据集固定
- demo/directed/real 分离
- 工程角色仅在 worktree 中实施
- 结构化 Evidence Bundle

### v0.5

- 稳定 API 版本
- adapter 权限 manifest
- 跨前端 scope 保持一致
- 无密钥进入 trace
- 断开 adapter 后核心仍可运行
- 兼容性矩阵
- 迁移与弃用政策

---

## 18. 风险登记

| 风险 | 缓解 |
|---|---|
| 本机角色意外泄漏 | public/local overlay + private scan + .gitignore |
| `activate` 被误解为真正热挂载 | 事务状态机 + 明确激活级别 |
| 角色包恶意内容 | HCP 安全校验 + 隔离解压 + 不执行脚本 |
| 静态 HTML XSS | HTML escape + CSP + 无内联脚本 |
| Token 数据不准 | 固定 usage_source + 版本 + CI |
| schema 漂移 | schema_version + migration + rollback |
| 情感依赖 | 关系边界 + 可关闭关系追踪 |

---

## 19. 明确不做（补充）

```text
不把本机私人角色作为公开默认角色
不把角色立场冒充框架立场
不把本机知识库打进 public package
不让角色包覆盖宿主 policy
不在导入时执行角色包代码
不让陪伴关系扩大工程权限
不把角色日记作为独立证据循环强化
不把静态 HTML 当成天然安全
不把 activate 标记冒充真正 runtime 热挂载
不把 CLI 存在冒充 UX 已完成
```

---

## 20. Current Next

### P0：状态和公共边界

- ✅ 修复 Roadmap 状态冲突（已完成/未完成按功能粒度拆分）
- ✅ 将私人角色案例从公共文档抽象化
- ✅ 完成 resolver 去私人硬编码
- ✅ 运行隐私扫描与 clean clone/ZIP 验证
- ⬜ 将私人案例文档移入本机 overlay（若保留）并加入 `.gitignore`

### P1：统一 schema

- ✅ Persona/Capability/Knowledge/Workspace/Permission/Mode schema 文件 + 示例 + `schema validate`
- ✅ 统一 event envelope schema 文件
- ✅ usage/token telemetry schema 文件
- ✅ local overlay loading order（runtime_resolver 读取 `~/.dsh/harness/personas.local.json`）
- ⬜ package schema version 强制校验
- ✅ event envelope 实际写入底层（`event add/list`，events.db）
- ✅ token usage 实际采集（`usage record/list`，events.db token_usage 表）

### P2：v0.2 可视运行台

- ✅ Dashboard 只读 projection（已含角色/经历/日记/Story/Token/桥图/隐私/事件时间线）
- ✅ 角色和职责卡（dashboard 读取本机 character 资产）
- ✅ 运行桥（文本版）
- ✅ 事件时间线（events.db）
- ✅ Token 面板（token_usage）
- ✅ 隐私数据流（文本版）
- ✅ HTML 安全：CSP + HTML escaping + 无内联脚本
- ✅ 交互式桥图（用 HTML <details> 实现点击下钻，无 JS，符合 CSP）
- ✅ 点击节点下钻（details 展开详情）
- ⬜ span 时间线
- ⬜ 角色画廊完整页

### P3：v0.3 角色资产化

- ✅ HCP 安全验证（`character validate --target public`：distribution / private memory / real person / license / absolute path / zip traversal）
- ✅ sandbox preview（`character preview`：只读预览，不写入）
- ✅ 事务化 activation（切换前备份，失败可回滚）
- ✅ rollback（`character rollback`）
- ✅ Character Card 映射（`character card-import`，支持 JSON/PNG chara tEXt，输出 HCP 预览/写入）
- ✅ corpus-to-draft 审批（`character build --from <corpus> [--approve]`，带证据/覆盖率/待审字段）
