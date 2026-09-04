# Credits, Attributions, Research Influences, and Dependencies

> 本文件披露本仓库中明确可见的外部研究来源、设计影响、工具/模型依赖及未随仓库分发的素材来源。  
> **重要边界**：`借鉴设计思想`、`参考论文`、`调用外部工具/模型`、`复制或改写第三方代码`是四种不同关系。本仓库目前声明前 3 类；尚未完成逐行代码 provenance/相似性审计，因此不作“所有代码均绝对原创”或“绝无任何第三方文本片段”的无限保证。若发现直接复制或实质性改写，必须补充原作者、源文件、commit、许可证和 NOTICE，并在发布前满足许可证义务。

## 1. 仓库自身许可

仓库根目录 `LICENSE` 当前采用 MIT License，版权标记为：

```text
Copyright (c) 2026 HL
```

MIT 只覆盖发布者有权许可的本仓库原创部分，不会重新许可第三方项目、论文、模型、角色、商标或素材。

---

## 2. 直接影响实现设计的开源项目

### 2.1 Herta / PersonaCLI

- 项目：https://github.com/PersonaCLI/Herta
- 关系：源码与设计研究；仓库文档称未复制其代码、角色卡或素材。
- 影响：
  - 第一人称自传与叙事补全；
  - self/agent 分离；
  - 门控梦境记忆、遗忘与可审计证据；
  - “安全属于 harness”等治理思想。
- 本仓库对应：`p4_experiment.py`、`facts.py`、Perspective Card、自传类文档。
- 许可证：发布前必须以所参考 commit 的 LICENSE 为准；不要仅凭二手描述认定所有素材均受 MIT 覆盖。
- 未分发：Herta 代码、角色素材、角色卡和第三方素材。

### 2.2 Project N.E.K.O. / Xiao8

- 已记录来源：https://github.com/wehos/Xiao8
- 相关项目组织：https://github.com/Project-N-E-K-O
- 关系：本地源码级设计研究；仓库文档称未复制其代码和素材。
- 影响：
  - `FactStore`/原子事实；
  - `subject_forget_cutoff`、tombstone、generation、archive/restore；
  - protected/suppressed persona rendering 与 token 上限；
  - entity ← account 身份/凭据分层；
  - proactive chat/主动陪伴管线。
- 本仓库对应：`facts.py`、`identity_store.py`、`proactive_pipeline.py`、`perspective_card.py`。
- 许可证：相关公开仓库可能采用 Apache-2.0，但发布前必须记录实际参考仓库、commit 和该 commit 的 LICENSE；游戏、角色、Live2D、音频等素材不应推定受代码许可证覆盖。
- 未分发：N.E.K.O. 源码、角色、Live2D、语音、图片及游戏素材。

### 2.3 Mem0

- 项目：https://github.com/mem0ai/mem0
- 许可证：Apache-2.0（仍应绑定参考 commit）。
- 关系：架构和检索设计影响；仓库未声明复制其源文件。
- 影响：
  - memory fact extraction / ADD-only 思路；
  - semantic + lexical/BM25 + entity 的多信号检索；
  - entity linking；
  - temporal retrieval/reasoning。
- 本仓库对应：`multi_signal_retriever.py`、`deep_fusion_retriever.py`、`atomic_facts_build.py`、`atomic_fact_retriever.py`。
- 限制：本仓库的简化 deep fusion 不等于完整 Mem0 实现，也不得借 Mem0 名称暗示兼容或认证。

### 2.4 Letta / MemGPT

- 项目：https://github.com/letta-ai/letta
- 历史项目名：MemGPT。
- 许可证：公开仓库标示 Apache-2.0；仍应绑定实际参考 commit。
- 关系：状态化 agent、分层内存以及“把记忆作为工具”的架构影响；仓库未声明复制其源文件。
- 本仓库对应：`memory_store.py` 及 memory-as-tool 的 CLI 设计。

### 2.5 All-in-RAG

- 项目：https://github.com/datawhalechina/all-in-rag
- 文档：https://datawhalechina.github.io/all-in-rag/
- 关系：教程/研究参考。
- 影响：retrieval → reranking → generation 的 RAG 分层概念。
- 许可证：发布前核对实际参考版本的仓库 LICENSE；当前不在此文件中猜测。
- 仓库未声明复制其教程或代码。

---

## 3. 理论、论文与算法影响

以下主要属于思想、论文或通用算法引用，不表示其作者为本仓库背书，也不自动产生代码兼容性或心理学效度。

### 3.1 ACT-R

- 名称：Adaptive Control of Thought—Rational。
- 来源入口：https://act-r.psy.cmu.edu/
- 影响：声明性记忆与程序性知识的区分。
- 本仓库映射：`kind=fact/preference/event/.../skill/reflection` 等分层。

### 3.2 Soar

- 来源入口：https://soar.eecs.umich.edu/
- 影响：chunking/任务经验沉淀的概念。
- 本仓库映射：任务完成后的 reflection/skill 候选。

### 3.3 OCC 情绪评价模型

- 来源：Ortony, Clore, Collins，*The Cognitive Structure of Emotions*。
- 影响：按目标、标准、偏好对事件进行 appraisal 的思想。
- 边界：本仓库规则是工程代理，不是 OCC 的完整实现或心理测量工具。

### 3.4 Affective Computing / Rosalind Picard

- 来源：Rosalind W. Picard，*Affective Computing*。
- 影响：将情绪识别、内部状态、表达与调节视为可分离模块。
- 边界：引用思想不构成情感真实性或心理效度证明。

### 3.5 Generative Agents

- 论文：Park et al., “Generative Agents: Interactive Simulacra of Human Behavior”。
- 论文入口：https://arxiv.org/abs/2304.03442
- 影响：memory stream、reflection、importance/recency/relevance 检索框架。

### 3.6 MemoryBank

- 论文：“MemoryBank: Enhancing Large Language Models with Long-Term Memory”。
- 论文入口：https://arxiv.org/abs/2305.10250
- 影响：遗忘/衰减与长期对话记忆思路。

### 3.7 Voyager

- 项目：https://github.com/MineDojo/Voyager
- 论文入口：https://arxiv.org/abs/2305.16291
- 影响：可复用技能库和持续积累技能的思路。
- 仓库未声明复制 Voyager 代码。

### 3.8 BM25

- 关系：`deep_fusion_retriever.py` 使用自行编写的简化 BM25 风格 lexical score。
- 来源：Robertson/Sparck Jones 等信息检索工作中的 Okapi BM25。
- 边界：当前实现是简化工程实现，不应被描述为完整搜索引擎或与某特定 BM25 库兼容。

### 3.9 Wasserstein-2 / NT 空间等数学概念

- 出现位置：`nine_dim_revision.py` 与相关研究文档。
- 关系：只读研究概念；代码明确写明完整 Wasserstein-2 协方差、NT 空间等未实现。
- 来源状态：仓库没有给出产生“九维修订版”公式的完整原始文献链；在公开宣称理论来源前必须补具体作者、标题、URL/DOI 和版本。

### 3.10 Neuro-sama / Evil Neuro

- 关系：`SKILL.md` 使用“Neuro × Evil Neuro”“Evil Review”描述 draft → attack → rebuttal → memory 的对抗复核隐喻。
- 影响：以对立 reviewer 攻击候选结论、防止过度自信和人格漂移。
- 边界：这是命名/概念性启发，不是官方项目集成，不表示 Neuro-sama/Evil Neuro 的创作者或权利人背书；仓库不应分发其角色素材、语音或品牌资产。
- 建议：公开版本可将功能名改为中性 `adversarial review`，并在历史说明中保留来源。

---

## 4. 外部模板、角色与非代码参考

### 4.1 w-doctor-perspective.zip / W博士 Perspective Skill

- 来源：本机获得的外部 perspective skill 包；当前没有稳定公开 URL、作者身份、版本、许可证或 hash。
- 影响：Perspective Card 的身份、心智模型、表达 DNA、输出纪律和 Agentic Protocol 等字段组织方式。
- 仓库对应：`perspective_card.py`、`perspective_card_schema.json`、demo card。
- 风险：来源与许可不足以支持复制原模板文本。
- 发布要求：保留的 schema/文案必须确认是独立重写；若存在逐句或结构性复制，应获得许可或删除。补充原 ZIP SHA-256、作者、许可证和取得日期。
- 未分发：原 ZIP、W博士人格内容和原始素材。

### 4.2 哥伦比娅角色 System Prompt

- 已记录页面：https://characters-pawzoisle.gfcmyuyun.com/characters/73
- 关系：角色一致性提示模板研究。
- 影响：关系阶段、防 prompt injection、自我揭示边界、表达 Do/Don't、避免角色标签化。
- 权利边界：角色、设定、原提示词和相关 IP 不受本仓库 MIT 重新许可。
- 发布要求：不得分发原文或高度近似改写；若 demo/schema 中保留了独特表达，必须先做逐句比对或删除。

### 4.3 爱灵（豆包生成素材包）

- 来源：用户本机的 AI 生成角色图/设定包。
- 关系：视觉角色一致性观察。
- 未进入本仓库。
- 边界：AI 生成不自动等于无权利风险；模型服务条款、输入素材和人物/角色权利仍需单独判断。

### 4.4 iterationRP

- 来源：用户本机获取的 Minecraft shader 包。
- 关系：只读研究。
- 未进入本仓库。
- 原因：许可证/分发边界不明确或受限。

### 4.5 用户 DeepSeek 导出语料

- 来源：用户拥有或控制的私有导出数据。
- 关系：系统研究和派生信号来源，不是开源项目依赖。
- 本公开仓库不应包含真实对话原文、PII、账号、token 或可逆重识别数据。
- 注意：仅称“用户自己的数据”仍不自动保证其中所有第三方消息都有公开再分发权。

### 4.6 九维情绪引擎研究资料与本地心智文档

`SKILL.md` 明确要求参考本机资料，包括：

```text
九维情绪引擎（研究记忆必看）/
九维情绪引擎-融合实施报告-20260823.md
心智模型-2026-08-18.md
PERSONA-EMOTION-SYSTEM-BASELINE.md
WESTERN-PSYCHOLOGY-HISTORY-SUMMARY.md
PHENOMENOLOGY-OCR-SUMMARY.md
心智模型-LingChat强化.md
心智模型情感升级路线图.md
扫兴姬-心智模型人类化强化方案-v2-20260830.md
心智情感闭环手册.md
```

- 关系：这些资料影响 `nine_dim.py`、`nine_dim_revision.py`、`emotion_projection.py`、`need_projection.py` 和 humanization 设计。
- 当前缺口：CREDITS 尚无法确认这些文档分别是用户原创、AI 生成、OCR 摘录、外部文章摘要还是第三方作品。
- 发布要求：逐份补 provenance。若含 OCR、书籍、论文或第三方原文，公开包只能保留允许分发的摘要/引用，并标注作者和来源；不得把本地存在误当作拥有公开许可。

### 4.7 Markus / “马克斯”本地人格系统

- 来源性质：用户本机的 `celebrity-markus` 人格系统；不是本仓库随附的外部开源依赖。
- 系统描述：以马克思相关原典/研究材料构造的本地人格镜像，包含分层人格、认知动力、自发候选、精力状态、长短期目标、私人日记与信件等机制。
- 对本仓库的设计影响：

  | 借鉴方向 | 本仓库对应 |
  |---|---|
  | 注意力、好奇心、心情、精力等认知动力 | `cognitive_dynamics.py` |
  | 自发候选、精力约束、长短目标 | `mind_evolution.py`、`proactive_pipeline.py` |
  | 日记、信件与长期沉淀 | `mind_precipitate.py`、humanization diary/letter 功能 |
  | 独立 persona/source/scope 路由 | `runtime_resolver.py` 中的 `markus` 条目 |

- 未随仓库分发：Markus 人格正文、私人记忆、日记、信件、原始语料和本地数据库。
- 权利边界：马克思原著的公版状态不自动覆盖现代译文、注释、整理本和数据库；任何译文或研究材料公开分发前必须按具体版本核验版权。
- 当前结论：可以披露为本地内部设计来源，不能因“内部系统”而推定所有源材料均可按 MIT 发布。

### 4.8 Blanche / 布兰奇本地人格系统

- 来源性质：用户本机由 “Entity 140 - Blanche” 文本与本地 feminism knowledge base 构建的人格系统。
- 对本仓库的设计影响：

  | 借鉴方向 | 本仓库对应 |
  |---|---|
  | “预测式大文本 + 知识块”的人格维持方式 | `p4_experiment.py`、`natural_session.py` 的相关设计 |
  | 知识库/卡片式人格组织 | `perspective_card.py`、`user_model_signals.py` |
  | 独立 persona/source/scope/backend 路由 | `runtime_resolver.py` 的 `blanche` 条目、`mind_evolution.py` 的 predictive/blanche backend 提示 |

- 未随仓库分发：Blanche 原始文本、人格正文、feminism knowledge base、私人记忆与本地启动器。
- 当前缺口：“Entity 140 - Blanche”的作者、取得方式、原始 URL、版本、许可证与允许用途尚未写入仓库。
- 发布要求：在来源未确认前，不得复制或发布原文/高度近似改写；如果本仓库 schema、demo 或文档含独特表达，必须先逐句比对并删除或取得许可。
- 当前结论：属于必须披露的本地派生来源，不是可忽略的“私人内部实现”。

---

## 5. 生态调研对象（不代表代码借鉴或随仓库分发）

`SKILL.md` 还提到以下候选生态：

```text
dsh-hermes-memory
dsh-mnemon
dsh-plugin-long-term-memory
dsh-persona-memory
```

- 关系：只读生态调研/候选比较。
- 当前状态：未提供稳定公开 URL、作者、版本、commit 和许可证。
- 发布要求：若公开文档继续声称从其“分层思路”或“受监督审批思想”获得启发，应补准确来源；若只是名称清单，应明确“未审计、未安装、未复制代码”。

其他在工具清单或插件策略中出现的产品/插件名称，仅表示兼容性、扫描对象或本机生态记录，不自动构成代码来源。

---

## 6. 运行时工具、库与模型

这些不一定属于“借鉴”，但公开可复现仓库必须披露。

### 6.1 Python

- 项目：https://www.python.org/
- 当前声明：Python 3.13。
- 使用：标准库 CLI、SQLite、JSON、HTTP、subprocess 等。
- Python 自身许可证不由本仓库 MIT 取代。

### 6.2 SQLite

- 项目：https://www.sqlite.org/
- 使用：`sqlite3` 标准库接口和本地 sidecar/主库。
- SQLite 上游声明为 public domain；具体 Python 分发仍受 Python 自身条款约束。

### 6.3 jieba

- 项目：https://github.com/fxsjy/jieba
- 使用位置：`user_model.py` 尝试导入。
- 当前代码可能提供无 jieba fallback，但 `PORTABLE_REQUIREMENTS.txt` 的“no external pip deps”应改成“核心可无外部 pip 依赖运行；jieba 为可选增强”，并进行无 jieba 测试。
- 许可证：MIT（发布前仍应核对实际安装版本）。

### 6.4 Ollama

- 项目：https://github.com/ollama/ollama
- 使用：本地 embeddings 和 LLM generate API。
- 边界：Ollama 是可选外部运行时，不随仓库分发；其许可证与模型许可证彼此独立。

### 6.5 Qwen 模型

仓库中出现：

```text
qwen2.5:7b
qwen3-embedding:0.6b
```

- 来源入口：https://huggingface.co/Qwen
- 使用：LLM rerank/query expansion、embedding 实验。
- 未随仓库分发模型权重。
- 许可证：必须按实际 Ollama manifest 对应的模型仓库、版本和权重许可证核验；不能用 Qwen 家族的概括许可替代具体 artifact 许可。

### 6.6 BGE-M3

- 来源入口：https://huggingface.co/BAAI/bge-m3
- 使用：语义检索/向量关联实验。
- 未随仓库分发模型权重。
- 许可证：按实际模型卡与使用版本核验。

### 6.7 DeepSeek

- 来源入口：https://www.deepseek.com/
- 关系：可选外部模型/服务和私有导出数据来源，不随仓库分发模型权重或 API key。
- 许可证/条款：按实际模型或 API 服务版本分别核验。

### 6.8 Live2D、微信、QQ、B站等名称

- 关系：代码/文档中的可选渠道、适配目标或产品名称。
- 边界：这些名称及商标属于各自权利人；本仓库不因此获得其 SDK、素材或平台数据的再分发权。
- 当前公开包不应包含私有聊天记录、账号标识或受限 SDK/素材。

---

## 7. 未使用/未分发声明的适用范围

根据当前仓库记录，以下内容意图上不随仓库发布：

```text
第三方项目源代码
角色原始 prompt/角色卡
角色图片、Live2D、语音、音乐和游戏素材
真实用户对话与数据库
API key、token 和云同步配置
模型权重
下载区 shader/素材包
```

这个声明必须通过发布前扫描验证，而不能仅靠文字保证。建议保存：

```text
secret scan 报告
二进制/媒体文件清单
逐文件 provenance 清单
license scan 报告
相似代码人工复核记录
最终 ZIP/repo commit hash
```

---

## 8. 发布前归属检查清单

- [ ] 为 Herta、N.E.K.O.、Mem0、Letta、All-in-RAG 记录实际参考 commit；
- [ ] 逐个保存所参考 commit 的 LICENSE/NOTICE 状态；
- [ ] 确认是否存在直接复制、翻译、移植或结构性改写；
- [ ] 若存在，列出源文件与本仓库目标文件并履行许可证义务；
- [ ] 对 Perspective Card 与外部 w-doctor 模板做逐句比对；
- [ ] 对哥伦比娅 prompt 做逐句比对，删除独特原文；
- [ ] 为九维研究资料和 OCR/心理学摘要补逐份 provenance；
- [ ] 修正 `PORTABLE_REQUIREMENTS.txt` 对 jieba 的说明；
- [ ] 固定 Ollama/Qwen/BGE 实际模型 artifact 与许可证；
- [ ] 检查 demo 文件没有第三方角色、私有实体或真实对话；
- [ ] 运行 secret/PII/license/binary scan；
- [ ] 更新 manifest，并确保它覆盖 `CREDITS.md`；
- [ ] 不在完成上述核验前声称“所有代码绝对原创”或“零第三方片段”；
- [ ] 若无法确认某项来源或许可，先删除相关内容或保持仓库 Private。

---

## 9. 无背书声明

所有项目名、论文名、模型名、角色名和商标仅用于准确说明研究来源、兼容目标或运行依赖。除非另有书面说明，原作者和权利人均未赞助、认可或背书本仓库。

---

## 10. 如何报告遗漏

若发现遗漏或错误归属，请提交 issue，并提供：

```text
本仓库文件与行号
疑似来源 URL
上游文件路径与 commit
相似片段
上游许可证/NOTICE
建议修复方式
```

确认后应在下一提交中补充 attribution、保留必要 notice，或删除不具备分发权的内容。
