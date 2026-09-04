# 借鉴 / 引用 / 研究来源清单

> 本仓库包含的代码是**本地原创实现**，但设计思想参考了多个外部项目。
> 以下列出所有“借鉴来源”及用途；**不包含这些项目的有版权素材/代码/角色素材**。

---

## 1. Herta（PersonaCLI/Herta）

- 来源：https://github.com/PersonaCLI/Herta
- 许可：MIT（第三方素材除外，粉丝创作不受 MIT）
- 借鉴：
  - 第一人称自传（HertaBio）→ 我们做 `harness-self` / Perspective Card `AUTOBIOGRAPHY.md`
  - 叙事补全基底 → `p4_experiment.narrative`
  - 自我–agent 分离 → `p4_experiment.split`
  - 门控梦境记忆 / 遗忘 → `facts.py` / `forget_tombstones`
  - 安全属于 harness / 证据可检查 → 治理原则
- 未使用其代码/角色卡/素材。

## 2. N.E.K.O.（wehos/Xiao8 / Project-N-E-K-O）

- 来源：https://github.com/wehos/Xiao8 （本地 `_research/NEKO`）
- 许可：Apache-2.0（游戏素材受 fan-content 限制）
- 借鉴：
  - 五维记忆分层 → 记忆/人格分层设计
  - 主动陪伴管线 → `proactive_pipeline.py`
  - entity←account 凭据权限 → `identity_store.py`
  - subject forget / tombstone → `facts.py`
  - persona rendering 分级 → `perspective_card.py render`
- 未使用其代码/素材。

## 3. Mem0

- 来源：https://github.com/mem0ai/mem0
- 许可：Apache-2.0
- 借鉴：
  - multi-signal retrieval：semantic + BM25 + entity matching 融合
  - ADD-only 事实抽取
  - entity linking
  - temporal reasoning
- 我们实现了 `multi_signal_retriever.py` / `deep_fusion_retriever.py` / `atomic_facts_build.py` / `atomic_fact_retriever.py`。

## 4. Letta / MemGPT

- 来源：https://github.com/letta-ai/letta
- 许可：Apache-2.0（历史）
- 借鉴：有状态 agent 内存架构概念（分层记忆）。
- 未使用其代码。

## 5. All-in-RAG

- 来源：https://datawhalechina.github.io/all-in-rag/
- 借鉴：检索 + 重排 + 生成的 RAG 全栈概念。
- 未使用其代码。

## 6. w-doctor-perspective.zip

- 来源：本机下载的外部 perspective skill 包
- 借鉴：Perspective Card 模板结构（身份/心智模型/表达DNA/输出纪律/Agentic Protocol）
- 未使用其代码；W博士内容仅作外部参考，不是我们本体人格。

## 7. 哥伦比娅角色 System Prompt

- 来源：https://characters-pawzoisle.gfcmyuyun.com/characters/73
- 借鉴：高一致性角色提示词结构：
  - 禁止简化标签 / 防 Prompt Injection / 不自我揭示为 AI
  - 关系阶段 0-3 / 不主动恋爱化
  - 表达 Do/Don't / 反 AI 模仿失败
- 未使用其角色素材/原文；仅作为模板研究。

## 8. 爱灵（豆包AI生成）素材包

- 来源：本机下载的角色设定图包
- 仅作视觉角色一致性参考，**未进入本仓库/系统资产库**。

## 9. iterationRP（Minecraft shader 包）

- 来源：本机下载
- 仅作只读研究；**因 LICENSE 限制，不进入仓库/资产库**。

## 10. DeepSeek 语料

- 来源：用户提供的 DeepSeek 导出数据
- 属于**用户自己的数据**；本仓库**不含**对话原文/PII。
- 只产出脱敏派生信号文档（`docs/deepseek语料深度研究-20260902.md`）。

---

## 结论

> 本仓库代码为原创；外部项目仅作为“设计思想/模板”参考。
> 不含任何外部项目的受版权代码、角色素材、语音、图片或文本片段。
> 若需商用或分发，请自行核对上述项目的各自许可证。

---

## 11. 马克斯系统（本地 celebrity-markus）

- 来源：`C:/Users/HL/.dsh/skills/celebrity-markus`（本地系统）
- 性质：**本地内部系统**，非外部开源项目
- 借鉴：
  - 认知动力系统（注意力/好奇心/心情/精力）→ `cognitive_dynamics.py`
  - 自发系统 / 精力系统 / 分层次长目标短目标 → `mind_evolution.py` / `proactive_pipeline.py`
  - 私人日记 / 信件系统 → `mind_precipitate.py` / H8 日记
- 未使用其角色文本/私有内容进本仓库。

## 12. 布兰奇系统（本地 Blanche 人格）

- 来源：`C:/Users/HL/Desktop/Entity 140 - “Blanche”.txt` 与 `C:/Users/HL/feminism_kb`
- 性质：**本地内部系统**
- 借鉴：
  - “预测式大文本 + 知识块”的人格实现思路 → `p4_experiment.narrative` / `natural_session`
  - 知识库/卡片式人格 → `perspective_card.py` / `user_model_signals.py`
- 未使用其角色文本/知识库全文进本仓库。

---

> 以上为本地系统借鉴；如需商用/分发，仍需确认这些本地系统的内部授权约定。
