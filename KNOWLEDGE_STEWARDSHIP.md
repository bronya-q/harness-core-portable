# 角色化知识治理（Knowledge Stewardship）

> 本文档记录一个方向：角色不只是“说话的人”，而是某些**知识域、工作流、日志、日记和解释方式的责任主体 / 知识管理员**。
> 状态：**方向 / 未实现**；本机已有 Blanche、Markos、Evil Review 三种原型。

---

## 1. 核心命题

角色 = 人格 + 知识域管理职责 + 工具/工作流 + 权限 + 来源可信度。

**关键区分**：
- 角色对知识域负有**管理职责**，但不等于“拥有真理”。
- 原始资料属于知识域；角色负责整理、解释和维护。
- 角色的解释仍是 interpretation，原始来源仍可核验。
- 其他角色访问时需经过共享策略。

## 2. 本机已有原型

| 角色 | 负责的认知职责 |
|---|---|
| Blanche | 女性主义理论、术语、流派、伦理、舆情、研究方法 |
| Markos | 马克思主义政治经济学、价值理论、经济结构、派别辩论、研究日志、日记信件 |
| Evil Review | 跨角色对抗审查：草稿→攻击→反驳→修订→记忆 |

**Evil 的特殊性**：它不应作为“知识所有者”，而应作为 Review Provider / Critic Role / Adversarial Bridge。

## 3. 五层分离

| 层 | 内容 |
|---|---|
| Persona Layer | 角色是谁、如何表达、价值边界 |
| Knowledge Domain Layer | 角色负责哪些知识域 |
| Source Layer | 具体资料来自哪里（书籍/论文/OCR/网页/日记/生成） |
| Tool/Workflow Layer | 角色能调用什么（搜索/检索/辩论/引文/报告） |
| Permission Layer | read / quote / summarize / annotate / propose_edit / write_note / publish / execute / network / cross_scope_share |

不能把五层揉成一个 `.bat` 或 persona prompt。

## 4. 角色—知识域关系

| 关系 | 含义 |
|---|---|
| owner | 用户指定主管理角色，不代表事实绝对正确 |
| steward | 负责整理、维护、审查 |
| expert | 可优先回答该领域问题 |
| reader | 可读取但不能修改 |
| contributor | 可提交候选笔记或修订 |
| critic | 只能审查、提出反证 |
| observer | 只读和记录 telemetry |
| blocked | 明确禁止访问 |
| delegate | 临时委派 |
| guest | 当前会话有限访问 |

示例：

```text
domain:feminism
  Blanche       steward + expert
  Markos        reader + contributor
  Evil Review   critic
  其他角色       blocked / guest

domain:marxian-economics
  Markos        steward + expert
  Blanche       reader + critic
  Evil Review   critic

domain:user-private
  当前指定角色   reader
  其他角色       blocked
```

> Evil Review 不应因负责审查就默认可读取全部私人数据。

## 5. 角色包扩展

```text
blanche.hcp/
├── character.json
├── perspective-card.json
├── knowledge-bindings.json
├── tool-bindings.json
├── permissions.json
├── corpus/
├── expressions/
├── workflows/
├── provenance.json
└── package-manifest.json
```

`knowledge-bindings.json` 示例：

```json
{
  "schema_version": 1,
  "persona_id": "blanche",
  "scope": "character:blanche",
  "domains": [
    {
      "domain_id": "domain:feminism",
      "role": "steward",
      "priority": 100,
      "mount_mode": "read_only",
      "source_ref": "local:feminism-kb",
      "allowed_operations": ["search", "read", "quote", "summarize", "propose_annotation"],
      "forbidden_operations": ["overwrite_source", "publish_without_review", "cross_scope_export"]
    }
  ]
}
```

## 6. 知识源资产

`knowledge-sources.example.json`：

```json
{
  "source_id": "local:feminism-kb",
  "display_name": "Blanche 女性主义知识库",
  "kind": "directory",
  "root": "~/feminism_kb",
  "portable": false,
  "private": true,
  "default_access": "deny",
  "stewards": ["blanche"]
}
```

公开仓库只发布 schema 和示例，不发布私有知识正文。

## 7. 热插拔应包含两步

```text
角色激活
+ 角色授权的知识域挂载
```

切换示例：

```text
正在激活 Blanche
✓ Perspective Card 已加载
✓ 私人记忆 scope 已切换
✓ 女性主义知识域已挂载（只读）
✓ 访谈伦理规则已启用
✓ Story Core 未改变
✓ 其他角色私人记忆已隔离
✓ 外部网络未授权
✓ Autonomous 保持关闭
```

## 8. 角色间委派

用户不一定要整体切换角色。

```text
当前角色：排队姬
问题：这个概念在女性主义理论中如何理解？

系统提示：
该问题匹配知识域：女性主义
负责角色：Blanche

请选择：
1. 切换到 Blanche
2. 让 Blanche 提供后台知识摘要
3. 当前角色不调用该知识域，自行回答
4. 取消
```

委派只传当前问题和有限摘要，不共享私人日记、关系状态。

## 9. 回答责任链

一条回答可区分三个角色：

- **Speaker**：谁在说话
- **Knowledge Steward**：谁提供专业知识
- **Reviewer**：谁审查

```text
回答角色：排队姬
知识支持：Markos · 政治经济学
审查：Evil Review
来源：3 条
```

用户不会误以为排队姬“拥有”Markos 的全部研究经历。

## 10. Evil Review 作为 Review Bridge

工作流：

```text
原始回答 → 主张抽取 → 证据审查 → 反例搜索 → 越界/夸大检查
→ 反驳 → 修订建议 → 由原角色重新表达
```

Evil 不应：
- 直接覆盖主角色人格
- 自动把攻击意见写入事实库
- 读取所有私人 scope
- 因为风格更苛刻就被当成“更真实”
- 通过审查权限获得 Autonomous 权限

Evil Review 可按知识域加载不同攻击清单：

| 角色 | Evil Review 关注点 |
|---|---|
| Blanche | 来源准确性、理论流派混淆、代表性偏差、访谈伦理、刻板印象 |
| Markos | 概念年代错置、价值/价格混淆、流派立场、引用版本、数据与理论混用 |
| 角色生成 | 单一语料过拟合、生成循环自证、一次 state 固化为 trait、反证缺失 |
| Production | 指标标签错位、门控与公开实现不一致、demo 冒充 real、本地快照冒充第三方验证 |

## 11. 知识控制台：“知识领地地图”

```text
Blanche ── steward ──> Feminism KB
Markos  ── steward ──> Marxian Economics KB
Evil    ── critic  ──> Approved Review Inputs
```

节点显示：关系、权限、可写原始资料、跨角色共享、网络访问。

## 12. 日志 / 日记 / 知识库必须分开

| 内容 | 默认用于知识回答 | 默认用于人格 | 可跨角色共享 |
|---|---|---|---|
| 理论资料 | 是 | 否 | 受控 |
| 参考文献 | 是 | 否 | 受控 |
| 术语表 | 是 | 否 | 受控 |
| 研究笔记 | 可选 | 否 | 需标注 |
| 系统日志 | 否 | 否 | 否 |
| 角色日记 | 否 | 低权重体验来源 | 默认否 |
| 信件 | 否 | 可选 | 默认否 |
| 私人记忆 | 否 | 是 | 否 |
| 模型内省 | 否 | 候选 | 否 |

**核心风险**：角色日记被检索器搜到，并作为理论事实回答。

建议知识分区：

```text
/source  /canon  /research  /notes  /diary  /letters  /logs
/drafts  /generated  /quarantine
```

检索时按任务选择：

```text
知识问答： source + canon + approved research
角色连续性： persona + approved memory + selected diary
内省： episodes + diary + feedback
审计： claims + sources + telemetry
默认排除： logs + generated + quarantine
```

## 13. 统一命名与 Resolver 修正

当前存在 `Markos / Markus / character:markus / celebrity-markus` 混乱。

建议：

```text
display_name = Markos
persona_id = markos
scope = character:markos
legacy_aliases = ["markus"]
```

Resolver 修正：
- 所有 `~` 路径使用 `.expanduser().resolve()`
- 对外显示重新脱敏为 `~/...`
- 公开代码不把本机绝对路径写死；用户配置放 `knowledge-sources.local.json`
- `source` 与 `entrypoint` 混用改为结构化 manifest

## 14. 新角色 manifest 结构

```json
{
  "persona_id": "blanche",
  "display_name": "Blanche",
  "aliases": ["布兰奇"],
  "scope": "character:blanche",
  "persona_source": { "ref": "local:blanche-persona", "private": true },
  "knowledge_bindings": [
    { "source_id": "local:feminism-kb", "domain_id": "domain:feminism", "role": "steward", "mount_mode": "read_only" }
  ],
  "notebook_scope": "character:blanche",
  "story_access": [ { "namespace": "story:shared", "permission": "read" } ],
  "review_profiles": ["evil-review:feminism"],
  "permissions_requested": {
    "network": false,
    "external_commands": false,
    "cross_character_memory": false,
    "knowledge_write": false
  }
}
```

## 15. 本机集成适配器

不重写现有终端，先登记：

```text
local-integrations/
├── blanche.json
├── markos.json
└── evil-review.json
```

命令：

```bash
python harness.py integrations list
python harness.py integrations inspect blanche
python harness.py integrations launch blanche
```

集成 manifest 示例：

```json
{
  "integration_id": "blanche-local",
  "display_name": "Blanche 终端",
  "kind": "persona_knowledge_terminal",
  "persona_id": "blanche",
  "scope": "character:blanche",
  "private": true,
  "portable": false,
  "working_directory": "~/feminism_kb",
  "launcher": { "kind": "python_script", "path": "~/feminism_kb/blanche_persona.py" },
  "knowledge_sources": [ { "path": "~/feminism_kb", "domain": "feminism", "mode": "read_only" } ],
  "requested_permissions": { "network": false, "process_spawn": true, "knowledge_write": false, "cross_scope_memory": false },
  "review_profile": "evil-review:feminism"
}
```

> 路径只保存在本地配置；公开导出时改逻辑 source ID；`process_spawn` 必须宿主批准。

## 16. 角色专属 Token 策略

| 角色 | 优先保留 | 减少 |
|---|---|---|
| Blanche | 术语定义、流派差异、争议状态、伦理约束、精确来源 | 重复舆情、未核验情绪化摘要 |
| Markos | 概念定义、版本、论证链、流派立场、历史语境、反对意见 | 重复派别、低来源草稿 |
| Evil | 待审主张、证据、反证、指标定义、边界 | 完整文学日记、无关关系状态 |

## 17. 完整信息流

```text
用户请求 → 角色选择 → 知识域路由 → 知识来源检索 → 角色解释
→ 可选 Evil Review → 最终输出
→ 系统日志 → 角色经历 → 日记草稿 → 内省候选 → 人工确认
```

每层保留引用：

```text
session_id / persona_id / domain_id / source_ids
review_id / episode_id / diary_id / reflection_id
```

## 18. 第一垂直切片：Persona Knowledge Control Center

只支持本机三个现有对象：Blanche、Markos、Evil Review。

第一版页面：

```text
角色卡片
Blanche
知识域：女性主义
启动器：可用
人格源：可用
私有：本地私有

知识桥
Blanche ── steward ──> Feminism KB
Markos  ── steward ──> Marxian Economics KB
Evil    ── critic  ──> Approved Review Inputs

权限
读取专业知识：允许
修改原始资料：拒绝
读取其他角色私人日记：拒绝
网络：关闭
自动执行：关闭
```

这个版本不需要先把所有知识迁进 Harness，只把已有本机系统安全、可视地登记和调用起来。

## 19. 开发顺序

| 阶段 | 内容 |
|---|---|
| P0 | 本机集成登记；统一 markos/markus；修 resolver expanduser；knowledge-sources.local.json |
| P1 | 只读 HTML 知识控制台：角色列表、知识域地图、权限卡、健康检查 |
| P2 | 统一启动与热插拔：character activate blanche/markos，自动挂载/卸载知识域 |
| P3 | 角色间委派：知识桥、有限摘要、不共享私人日记 |
| P4 | 知识维护与内省：来源核验队列、研究笔记整理、日记与理论分区、审批/回滚 |

## 20. 最终定位与边界

> 本地角色化知识与心智运行平台：每个角色可以管理自己的专业知识、记忆、日记、工具和工作流，并在统一 policy 下被热插拔、委派、审查和可视化。

**特色组合**：

```text
角色热插拔
+ 角色专属知识域
+ 跨角色受控委派
+ 日志/日记/内省分层
+ Evil 对抗审查
+ 运行桥和权限可视化
+ Token 成本可视化
+ 本地隐私
+ 版本与回滚
```

**最后守住的边界**：

角色可以负责组织与解释知识，但不能因“控制”知识域而垄断事实、绕过来源核验或自动获得更高权限。

Blanche、Markos 和 Evil 最
