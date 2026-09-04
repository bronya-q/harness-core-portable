# 本地记录说明（Local Records）

> 结论先写：这些是**作者自己的本地观察记录**，不是受控实验，不是可公开复现的证据。
> 本文件参照 Hugging Face Model Card / GEM Data Card 的做法，用“可量化字段 + 来源 + 限制”来记录，而不是只列名字。
> 机器可读快照：`local-records-snapshot.public.json`，由 `local_records_export.py` 在本机生成，`local_records_verify.py` 校验口径，避免手抄漂移。

---

## 1. 数据快照时间

以下数据来自本地运行环境，采集时间集中在 **2026-09-04**，之后可能继续变化。

| 项目 | 数值 |
|---|---|
| memory.db 总记忆 | 6086 |
| active 记忆 | 784 |
| archived 记忆 | 5302 |
| 向量行 | 775 |
| active_missing vector | 9 |
| duplicate_groups_active | 0 |
| relation_out_of_range | 0 |
| 原子事实（atomic_facts_sidecar.db） | 2370 |
| 人格/身份条目 | 84 |
| humanization 事件 | 349 |
| 情境观测 | 449 |
| 叙事片段 | 400 |
| 主动候选 | 340 |
| 日记条目 | 365 |
| 信件线程 | 14 |
| persona variants | 26 |
| 自进化候选 | 282 |
| policy 审计 | 31 |
| 真实会话注册 | 17 |
| 会话指标（session_metrics） | 171 |
| mind_review 审查记录 | 85 |
| notebook 记录 | 3 |
| rating 快照文件 | 19 |
| H2 review CSV 行数 | 398 |

## 2. 评测数据

### 2.1 盲标 gold

| 项目 | 数值 |
|---|---|
| 独立盲标 human_relevance | 2160 条 |
| 查询数 | 36 |
| 每查询采样 | 60 |
| 盲标 CSV 行数（含表头） | 2161 |

### 2.2 recall-pool（最新本地快照）

| 指标 | 数值 |
|---|---|
| P@5（avg_precision_at_k） | 0.7944 |
| judged_precision | 0.9167 |
| recall | 0.3422 |
| hit_rate@5 | 0.9444 |
| zero_relevant_queries | 2 |
| queries | 36 |

> 说明：这是“独立 relevance 池”上的本地评测，不是提交到第三方 benchmark 的结果。
> 这里的“independent”指**候选池独立于检索 top-k 抽样**，不是“有独立评价者/独立标注者”。
> bootstrap 95% CI（query 级，1000 次重采样）：P@5 = [0.6889, 0.8944]，recall = [0.2569, 0.4415]。
> 逐 query 明细、失败 query（precision@5 < 1.0）和完整定义见 `local-records-snapshot.public.json`。

## 3. 生产门控（最近一次 PASS 快照）

采集时间：2026-09-04 15:36 左右，`production_gate.commands` 中 `gate_status = PASS`。

| 检查 | 值 | 通过 |
|---|---|---|
| G1 real_sessions>=5 | 17 | true |
| G2 h3_rated>=30 | 57 | true |
| G3 enhanced_win>=0.6 | 0.702 | true |
| G4 congruence>=0.9 | 1.0 | true |
| G5 multi_scope>=3 | 3 | true |
| G6 narrative_unknown==0 | 0 | true |
| G7 no_high_risk_narrative | 0 | true |
| G8 user_correction<=0.2 | 0.0025 | true |
| G9 leakage<=0.05 | 0.0 | true |
| G10 hit_rate@5>=0.9 | 0.9444 | true |
| G13 independent_recall@5>=0.5 | 0.7944 | true |
| G14 over_anthropomorphism==0 | 0 | true |
| G15 no_self_reveal_as_ai==0 | 0 | true |
| G16 service_db_health | db_ok / ollama_ok | true |
| G17 natural_flow_min>=1 | 29 | true |
| G18 duplicate_groups_active==0 | 0 | true |
| G19 relation_out_of_range==0 | 0 | true |
| G11 plugin_unknown==0 | 0 | true |
| G12 explicit_production_approval | true | true |

> 说明：公开仓库 `production_gate.py` 覆盖 G1–G19（G11/G12 顺序在末尾）。本地完整 gate 曾多一个 `G20 notebook_story_boundary`，该检查未包含在公开仓库，因此不在此表列出。

## 4. 本地下游工程记录

这些记录只有脱敏后的数量/类型，原文不随仓库分发。

| 记录 | 可量化部分 |
|---|---|
| DeepSeek 导出语料 | 289 会话 / 2132 条用户消息 |
| AutoMM 省赛 | 题目、多轮方案、主动话题记录 |
| 马克斯 / 布兰奇人格研究 | 本地人格系统、研究材料、信件/日记线索 |
| COC / TRPG / 角色扮演 | 人物卡、多轮叙事、跨会话记忆 |
| Obsidian 学习强化库 | 本地知识/学习记录 |
| 插件审计 | 30 个插件，12 个本地复核，18 个已知审计，0 隔离 |
| 人工/GPT 复核 | 多轮复核意见保留结论性文档 |

## 5. 参照 GitHub 公开做法时采用的结构

- **来源/时间**：数据来自本机，不是可下载数据集；
- **量化字段**：计数、指标、时间、范围；
- **评测说明**：指标含义、样本口径、是否独立；
- **限制**：没有受控 A/B、没有独立评价者、没有公开原始数据；
- **可复现性**：只提供命令和脚本，不提供原始数据。
- **边界**：已有检索组件的离线 A/B（候选池独立）；**尚无**整体系统下游效果的 A/B。

### 5.1 借鉴的公开模板/惯例

- Hugging Face Model Cards（记录模型/数据集来源、用途、限制、量化指标）：
  https://raw.githubusercontent.com/huggingface/blog/fix_more_llm_3/model-cards.md
- GEM Data Card（数据集的构成、动机、语言、拆分、许可、伦理）：
  https://arxiv.org/abs/2108.07374
- Hugging Face modelcard 模板本身：
  https://github.com/huggingface/hub-docs/blob/main/modelcard.md

> 本文件不是完整数据集卡，只在“能公开什么 / 量化到什么程度 / 不能声称什么”上采用它们的字段思路。

## 6. 这些数据能说明什么

- 本地系统确实积累了跨会话记忆、人格条目、叙事片段、主动候选、评测记录；
- 在本地独立 relevance 池上，recall-pool 有具体数值（P@5=0.7944，hit_rate@5=0.9444）；
- 生产门控在特定本地快照上通过，且大部分边界检查值为 0；
- 下游工程确实产生了可观察的连续性/一致性/目标管理记录。

## 7. 这些数据不能说明什么

- 不是受控 A/B；没有随机分组、基线对照、盲审。
- 没有公开抽样方案、样本量计算、评价者间信度。
- 没有独立评价者复核；记录里包含作者/维护者自己的主观判断。
- 没有可复现实验：原始数据、prompt、模型版本、评分标准都没随仓库公开。
- 不证明“AI 真的理解/在乎/有感情”；心理效度需独立研究。
- 不证明在别的机器、别的用户、别的角色上也能得到同样效果。
- 生产门控 PASS 是本地配置下的一次快照，不代表长期稳定或通用达标。

## 8. 为什么不能公开原文

- 真实对话涉及用户隐私、第三方消息、账号/平台条款；
- 角色卡、人格正文可能涉及角色/作品/人物的 IP；
- 本地知识库可能有版权或来源不明的材料；
- gold 标注如果公开，会污染后续评测；
- API key / token / 本地路径不能进公开仓库。

## 9. 想把“本地观察”变成可检验证据，需要什么

1. 公开抽样方案：记录来源、纳入/排除标准、时间范围；
2. 设计受控 A/B：同样任务，有/无增强心智模型各跑一轮；
3. 独立评价者：不看系统内部标签，盲评结果；
4. 任务成功指标：如“目标偏离次数”“用户确认率”“重复率”；
5. 失败样本：记录翻车、回滚、纠偏案例；
6. 可复现打包：脱敏后的输入、prompt、模型版本、配置、评分标准。

## 10. 现状

当前仓库是 **v0.1 / alpha / WIP**。
本地记录支撑了设计方向和工程观察；但它们还没有达到“可公开验证效果”的程度。
README / EFFECTS 里凡是出现“使用后 / 本地观察 / 预期改善”的地方，都应读作：

> **作者观察 + 本地案例记录，未经受控 A/B 验证。**
