# Harness Core Portable · 产品路线与未实现方向

> 本文档记录我们讨论过、有方向但**尚未实现**的功能，以及部分已完成的基础。
> 目标不是“再加功能”，而是把现有底层能力串成普通用户能看、能懂、能控制的产品闭环。
> 状态标记：✅ 已实现 / 🚧 部分实现 / ⬜ 未实现。

---

## 0. 一句话定位

本地优先的 AI 角色与长期心智工作台：管理角色资产、经历、日记、内省、共享世界、上下文成本与运行权限。

> 关于“角色化知识治理 / Knowledge Stewardship”的完整方向见 `KNOWLEDGE_STEWARDSHIP.md`。
> 关于“工程角色体系 / Engineering Roles”的完整方向见 `ENGINEERING_ROLES.md`。

---

## 0.1 v0.1.0-alpha.1 冻结状态

> 这是当前发布基线：**alpha / WIP**，不是 production-ready。

### 已满足

- ✅ 统一入口：`python harness.py start / demo / doctor / inspect / data / dashboard`
- ✅ 离线可感知演示：`python harness.py demo --offline`
- ✅ Git clone 与 Download ZIP 双模式自检通过
- ✅ 机器可读本地记录快照 + 口径校验
- ✅ production gate fail-closed（clean clone 预期 rc=1）
- ✅ 文档：README / QUICKSTART / LOCAL_RECORDS / RESEARCH / PRE_MODEL_BASELINE / ROADMAP / KNOWLEDGE_STEWARDSHIP
- ✅ 远端与本地同步
- ✅ 用户控制入口：`memory list/explain/correct/restore/forget`、`privacy status/export/reset-demo`、`backup create/list/restore`、`feedback export --redacted`
- ✅ Notebook 支持 `forget`（归档）与 `list --all`，默认只显示 active
- ✅ 角色资产基础：`character list/install/activate/deactivate/remove/show`
- ✅ 知识域基础：`knowledge list`（读取角色包 knowledge-bindings）+ `knowledge sources`（读取知识源清单/示例）
- ✅ 工程工作区基础：`workspace create/list/status/release`（Workspace Lease / worktree 抽象）

### 发布时仍要保留的边界

- 不含真实用户数据 / 私有人格卡 / 模型权重 / API key
- 不开启 Autonomous
- 不启用 L4/L5 实际影响
- 第三方 provenance 仍逐项核验中
- 完整生产运行面依赖私有数据，公开包返回 UNAVAILABLE / FAIL

### 尚未进入 v0.1 的范围

以下全部留到 v0.2+，详见本文档后续章节：

- 完整角色资产化：HCP 压缩包 / Character Card 兼容 / 角色运行时真正热挂载（安装/激活基础已上线）
- 运行桥交互图 / 模块热插拔
- 完整上下文成本可视化
- 日志-日记-内省-整理系统
- 完整知识域治理与知识桥（启动器/健康检查/权限卡已抽象成示例）
- 更完整的记忆/会话级 `memory explain` 与 `restore` 高级视图（基础版已上线）
- `privacy / backup / feedback` 的 GUI 化与策略化（CLI 基础版已上线）

---

## 1. 两条主线

| 主线 | 目标 |
|---|---|
| A. 证据与治理可信度 | 机器可读快照、口径校验、provenance、gate、回归测试 |
| B. 用户可感知体验闭环 | 新用户几分钟内看到效果，能查看、纠正、删除、恢复 |

不能为了可感知度牺牲 fail-closed；也不能只做治理而让用户面对一堆脚本。

## 2. 用户可感知度十问

1. 系统记住了什么？
2. 为什么这次想起了它？
3. 有没有把别的角色或项目串进来？
4. 人格前后是否一致？
5. 世界设定有没有延续？
6. 记错后能不能纠正或忘掉？
7. 当前哪些能力真的在影响回答？
8. 哪些能力只是 shadow 观察？
9. 我能不能关闭、撤回和重置？
10. 相比不用系统，到底有什么可观察差异？

## 3. 已实现基础（现状）

- ✅ `python harness.py demo --offline`：离线合成数据演示
- ✅ `python harness.py start`：交互式新手向导
- ✅ `python harness.py doctor`：人类可读环境检查（`--json`）
- ✅ `python harness.py inspect --scope <s>`：查看角色/项目
- ✅ `python harness.py data status`：本地数据目录与占用
- ✅ `python harness.py dashboard build`：只读静态 HTML 控制台
- ✅ `python harness.py dashboard open`：打开控制台
- ✅ `开始体验.bat`：Windows 双击入口
- ✅ `QUICKSTART.md` / `QUICKSTART.zh-CN.md`
- ✅ `local_records_export.py` / `local_records_verify.py`：机器可读证据快照
- ✅ `release_verify.py`：Git / ZIP 双模式发布校验

---

## 4. 角色资产化（⬜ 最重要方向）

### 4.1 Harness Character Package

```text
my-character.hcp/
├── character.json
├── perspective-card.json
├── corpus/
│   ├── dialogue.jsonl
│   ├── letters.jsonl
│   └── notes.jsonl
├── memory/
│   └── seed-memories.jsonl
├── story/
│   └── default-story-core.json
├── expressions/
│   └── expression-dna.json
├── assets/
│   └── avatar.webp
├── provenance.json
├── permissions.json
└── package-manifest.json
```

### 4.2 热插拔命令

```bash
python harness.py character install my-character.hcp.zip
python harness.py character list
python harness.py character activate my-character
python harness.py character deactivate
python harness.py character remove my-character
```

### 4.3 切换时区分什么

| 资产 | 是否随角色切换 |
|---|---|
| Perspective Card | 是 |
| 私人长期记忆 | 是 |
| Notebook | 通常是 |
| 情感/关系状态 | 是 |
| 表达 DNA | 是 |
| 用户确认事实 | 按权限 |
| Story Core | 可共享 |
| 项目事实 | 可共享 |
| Runtime Policy | 角色包不能覆盖 |
| Autonomous 权限 | 绝不能随角色包开启 |

**铁律**：角色包能声明自己需要什么，但不能自行授予权限。

### 4.4 Character Card 兼容

- 导入 Character Card V2/V3
- 导入前展示映射预览
- 导出时不泄露私人记忆/关系状态/用户模型/telemetry

### 4.5 语料 → 角色草稿编译器

```text
原始语料 → 去重/分段/来源标记 → 说话者识别 → 原子事实抽取
→ 表达模式抽取 → 关系/边界候选 → 矛盾检测 → Perspective Card 草稿
→ 用户逐项确认 → 角色包
```

- 每个生成字段必须带证据、反证、置信度、状态
- 显示角色完整度（身份、表达、决策、关系、冲突、价值观）
- 输入区分 canon / author_note / roleplay / user_correction / synthetic / unknown
- 默认权重：用户明确设定 > 用户纠正 > 原始语料 > roleplay 历史 > 自动生成 > 未知

### 4.6 编译差异可视化

```text
角色草稿 v3 → v4
新增 / 修改 / 冲突 / 未应用
按钮：接受 / 拒绝 / 编辑 / 保持候选 / 查看证据
```

### 4.7 角色沙盒与“试穿”

```bash
python harness.py character preview unknown-card.png
```

只读、不写长期记忆、不读取其他角色、不允许网络/工具执行、会话结束自动清理。

### 4.8 角色体检

```bash
python harness.py character doctor alice
```

显示字段覆盖、证据、冲突、无来源语料、smoke 记忆、Story Core 同名冲突。

### 4.9 角色版本 A/B

同题并排输出，比较 token、边界违反、证据引用；测试结果标注 demo/directed/calibration。

### 4.10 人格来源地图

- 用户明确设定 / 原始语料 / 信件日记 / roleplay / 自动推断 占比
- 每个字段可点开来源、类型、置信度、反证、是否用户确认

---

## 5. 运行桥可视化（⬜）

### 5.1 Runtime Bridge Graph

```text
用户输入 → Scope Resolver → BLOCK 其他角色记忆
   → Perspective Card / Memory Recall / Notebook / Story Core / Runtime Policy
   → Prompt Builder → 模型 → 输出 → Telemetry → Auto-note
```

- 节点状态：green=已参与 / blue=只读 / yellow=shadow / gray=disabled / red=失败 / purple=等待批准
- 颜色与文字同时表达（色觉友好）
- 点击节点看详情：候选数、注入数、字符/token、延迟、被过滤原因
- 边标记：READ / INJECT / CANDIDATE / BLOCK / WRITE / RESTORE

### 5.2 模块热插拔

可插拔槽位：

```text
Persona Provider / Memory Store / Retriever / Reranker / Embedding Provider
Story Provider / Expression Projector / Model Provider / Telemetry Sink / Policy Provider
```

### 5.3 插件权限卡

安装插件时显示需要的权限，默认拒绝高权限；不自动开启网络/跨角色读取/工具执行。

---

## 6. 上下文成本可视化（⬜）

- Context Budget 面板
- 无选择基线 vs Harness 实际注入的对比
- Token 计算层级：provider 真实 usage > 对应 tokenizer > 通用 tokenizer > 字符估算
- 本地模型不虚构费用，只显示 token / 延迟 / 吞吐
- “节约”必须标基线和估算，不包装成精确数字
- 信息价值密度：injected_relevant_items / injected_tokens × 100
- 上下文瀑布图（trace/span 时间线）
- 质量—成本拨杆：精简 / 平衡 / 连续性优先

---

## 7. 控制台产品化（🚧）

### 7.1 已完成

- `dashboard build` / `open`：只读静态 HTML 控制台

### 7.2 未完成

- 角色画廊（卡片列表、激活、详情、导出）
- 角色状态卡（证据/冲突/版本/token，避免神秘总分）
- 角色首页五个标签：概览 / 经历 / 日记 / 内省 / 来源
- 记忆时间线、记忆管理（list/explain/correct/forget/restore）
- Story / Notebook 版本时间线与 diff
- 上下文组成页面（Persona/Memory/Story/Notebook/Tools 分区）
- 隐私数据流页面
- 局部交互服务（第二阶段，仅 loopback + 随机 token + 写操作确认）

---

## 8. 日志 / 日记 / 内省 / 整理（⬜ 重点方向）

### 8.1 四种内容严格分开

| 类型 | 回答 | 示例 |
|---|---|---|
| 系统日志 Log | 系统实际执行了什么？ | 16:20:31 检索 12 条候选，注入 3 条 |
| 经历记录 Episode | 这一轮对角色/项目发生了什么？ | 用户把银色钥匙放在钟楼下 |
| 角色日记 Diary | 角色如何理解这段经历？ | 今天她告诉了我钥匙的位置…… |
| 内省 Reflection | 这段经历可能意味着什么？ | 我可能过度用“保护”解释分享 |

### 8.2 真实化的定义

真实化 = 可追溯，而不是更像真人：

- 经历有来源
- 变化有原因
- 表达有连续性
- 不知道时承认不知道
- 冲突时展示冲突
- 修改后保留历史
- 主观内容明确标注

### 8.3 三条并行时间线

1. 系统运行时间线（调试/延迟/token）
2. 角色经历时间线（剧情/事实/纠正）
3. 内省与人格变化线（候选/支持/反证/审批）

### 8.4 日记工作台（Diary Studio）

- 左侧：日期/主题/未整理
- 中间：日记正文
- 右侧：来源事件、用户原话、系统推断、反证、类型、状态、影响范围
- 底部：编辑/接受/归档/转经历摘要/提出内省/查看来源/比较版本/删除

### 8.5 日记真实性面板

- fact / perception / emotion_projection / interpretation / uncertainty / fictional_embellishment
- 可确认事实 / 用户明确陈述 / 角色状态 / 叙事连接 / 模型推断
- 文学句保留在日记，不写入 facts 或 user_model

### 8.6 内省收件箱

- candidate → review → accept/reject/edit → optional apply → rollback
- 支持/反证/置信度；不影响核心身份、用户事实、Autonomous 权限

### 8.7 防自引用强化

- 用户确认 > 可验证外部事实 > 原始事件 > 角色语料 > 角色日记 > 模型内省
- 模型对旧内省的重复不增加置信度
- 记录 root_source_ids / derived_from / generation_id / model_version

### 8.8 整理系统

六个维度：Scope / 时间 / 类型 / 来源 / 状态 / 主题实体

- 自动整理只建议，不静默合并高风险信息
- 自然语言整理： “把这周和旧港有关的日记整理成一个专题”
- 日记册与卷：组织层不自动改变事实或人格
- 分层摘要树：原始事件 → 每日 → 每周 → 章节 → 长期回顾
- 导出前预览包含内容

### 8.9 日志/日记与桥图、Token 结合

- 每个节点可点进历史运行统计
- 显示摘要覆盖（关键人物 4/4、明确事实 12/14、原话保留 1/8）

### 8.10 回顾与安静模式

- 每日/每周回顾
- 记忆相册
- 安静模式（沉浸 / 平衡 / 研究）

---

## 9. 用户控制与隐私（🚧）

### 9.1 已完成

- `data status`
- `demo --reset`
- doctor 提示自动执行关闭、网络上传未启用

### 9.2 未完成

- `memory list/explain/correct/forget/restore` 统一入口
- `privacy status / export / forget / reset-demo`
- 首次运行同意（allow_memory_write / allow_cross_session_recall / allow_evaluation_use / allow_cross_character_story_share / allow_telemetry）
- 写操作：预览 → 确认 → 写入 → 显示撤销方式
- 高风险操作二次确认（输入角色名）
- `backup create/list/restore`
- `data export / backup / reset-demo`
- `feedback export --redacted`
- GitHub Issue 模板（bug / 记忆错误 / 隐私问题）

---

## 10. 对标公开项目（只借鉴，不复制）

| 项目 | 可借鉴 | 不复制 |
|---|---|---|
| SillyTavern | 角色画廊、Character Card 导入导出、Lorebook | 完整聊天前端 |
| Langfuse / OpenLIT | trace/span、token、latency、cost | 云端可观测产品 |
| LangGraph Studio | agent graph、节点状态、调试 | 工作流编排器 |
| Dify | 节点式工作流、非开发者表单 | 完整拖拽工作流 |
| Promptfoo | A/B 并排、diff、pass/fail、web viewer | 通用评测平台 |
| Open WebUI / AnythingLLM | 本地模型接入、低门槛安装 | 同类聊天产品 |

---

## 11. 版本路线

| 版本 | 主题 | 交付 |
|---|---|---|
| v0.1 | alpha / 实证基础 | 已提交，冻结中 |
| v0.2 | 可见运行台 | 静态 HTML 控制台、角色画廊、Memory/Story/Notebook 时间线、Token、trace、隐私状态 |
| v0.3 | 角色资产化 | HCP、Character Card 导入、热插拔、角色草稿、证据覆盖/冲突、sandbox |
| v0.4 | 可组合与对照 | 角色/检索器 A/B、质量成本预设、context waterfall、场景快照、会话分支 |
| v0.5 | 生态桥接 | 稳定 Python API、OpenAI-compatible adapter、Open WebUI/SillyTavern 集成、事件 API |

---

## 12. 明确不做

- 继续堆 H10/H11 新心理维度
- 在信度/效度未建立前增加大量不可解释总分
- Autonomous / L4 / L5 实际影响
- 大型 Web 前端 / 云端账号 / 自动上传 telemetry
- 把所有模块做成任意拖拽节点
- 把“节约 token”写成一定省钱
- 把“角色完整度 93%”这种神秘总分当作结论
- 自动把模型生成为正典/真实事实

---

## 13. 与现有底层模块映射

| 用户功能 | 可复用模块 |
|---|---|
| 系统运行时间线 | continuity_store.py |
| 角色经历 | narrative_episodes、Notebook |
| 日记 | humanization.py diary entries |
| 信件 | letter threads |
| 内省候选 | mind_evolution.py |
| 关系时间线 | relationship events |
| 冲突 | tensions、cross-character consistency |
| 世界版本 | story_core.py |
| 角色版本 | Perspective Card |
| 来源地图 | session/content provenance |
| Token 图 | prompt builder + provider usage |
| 桥图 | runtime resolver + telemetry |
| 回滚 | notebook/story/mind evolution 版本机制 |

---

## 14. 建议第一个完整垂直切片：“角色的一天”

用户打开 HTML 控制台，完成：

1. 选择一个角色
2. 查看今天的经历时间线
3. 点开一篇自动生成的日记草稿
4. 查看每句话来自哪个事件
5. 看到其中一条是推断而非事实
6. 编辑或拒绝这条推断
7. 将认可的内容保留为日记，但不升级为人格
8. 查看运行桥图
9. 查看本轮用了多少记忆和 token
10. 切换角色，确认私人经历没有串过去

这条体验能同时体现：角色热插拔、日志可视化、日记真实化、内省审阅、来源追踪、角色隔离、Token 可视化、HTML 控制台。
