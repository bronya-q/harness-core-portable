---
name: long-term-memory-emotion
description: "长时记忆与情感状态系统：跨会话记忆读写、情感状态跟踪、重要性/时效/情感加权检索、反思与遗忘。| Long-term memory & affective state system: cross-session memory, emotion tracking, weighted retrieval, reflection and forgetting."
whenToUse: 需要跨会话记住用户/任务/关系/偏好，或需要根据情感状态约束回应方式、技能选择、记忆固化优先级时。
---

# 长时记忆与情感系统（long-term-memory-emotion）


## 强化版总复盘

完整的任务链、进度、设计动机、优秀之处、不足、风险、当前开关和未来方向见 [`ENHANCED_SYSTEM_RETROSPECTIVE.md`](ENHANCED_SYSTEM_RETROSPECTIVE.md)。后续维护应先阅读该文档，再修改人格、记忆、情感、测量或自主任务相关代码。

一个**零外部依赖**的通用 Agent 长时记忆 + 情感状态管理 skill。记忆和情感都落在本地 SQLite，
不依赖向量数据库，不调用外部网络，不下载任何第三方代码。

## 理论依据（skill 层约束）

| 来源 | 落地点 |
|---|---|
| ACT-R（声明性/程序性记忆分离） | 记忆表用 `kind` 区分 `fact/preference/event/relationship/skill/reflection/emotion`；技能/经验作为程序性记忆固化 |
| SOAR（chunking） | 每次任务完成后的反思/总结作为 `reflection` 记忆写回，压缩经验 |
| OCC（目标/标准/偏好评估） | 情感状态不是凭空设置，而是对事件做评价后写入 `emotion_state` |
| Picard（情感计算） | 情感识别/表达/调节作为独立模块，不混进基座 prompt |
| Generative Agents（记忆流+反思） | 原始事件进记忆流；定期 `reflection` 汇总；检索按重要性/时效/情感加权 |
| MemGPT（记忆即工具） | 记忆读写通过 `memory_store.py` 工具完成，不把全部历史塞进上下文 |
| MemoryBank（遗忘/衰减） | 低重要度旧记忆 `decay` 降权、`forget` 软归档，不硬删 |
| Voyager（技能库终身学习） | 可复用行为/策略存为 `kind=skill` 的记忆，后续任务直接召回 |
| Neuro × Evil Neuro（双生自进化） | 反思/技能写入前先过 Evil Review：Draft → Attack → Rebuttal → Memory，防止过度自信与人格漂移 |

## 数据位置

- 默认数据目录：`~/.dsh/memory-emotion/`
- 可用环境变量覆盖：`MEMORY_EMOTION_DATA_DIR`
- 数据库：`memory.db`（SQLite WAL）
- 备份/迁移：`export` 出 JSONL，`import` 回灌

## 核心命令
## 研究资料约束（必须遵守）

强化本 skill 时，必须参考本地研究资料，不把情绪系统简化成标签或 prompt 装饰：

- `~/Documents/harness/九维情绪引擎（研究记忆必看）/`：20/40/60/65 轮报告验证了正向记忆联想、负面/创伤触发、反复唤醒、烈度修正和向人格基线回涌。
- `~/Documents/harness/九维情绪引擎-融合实施报告-20260823.md`：事件评价 -> 记忆联想 -> 六维情绪 -> 三维深层需求的传导链；`nine_dim.py` 是现有规则真源，不重复实现。
- `~/Documents/harness/docs/心智模型-2026-08-18.md`：心智变化必须有行为证据，结论要标注置信度、反例和可修正性；不能把一次模型判断直接固化为人格事实。
- `~/Documents/harness/docs/PERSONA-EMOTION-SYSTEM-BASELINE.md`、`WESTERN-PSYCHOLOGY-HISTORY-SUMMARY.md`：精神分析只作为无意识动机/冲突/防御的解释视角，不作诊断或事实断言；人格成长必须区分触发、冲突和可观察行为。
- `~/Documents/harness/docs/PHENOMENOLOGY-OCR-SUMMARY.md`：现象学悬置、意向性和生活世界用于区分事件本身与主体如何经验/赋义；系统应保留体验描述，不把模型解释冒充客观事实。
- `~/Documents/harness/docs/心智模型-LingChat强化.md` 与 `心智模型情感升级路线图.md`：六维状态到情绪词/桌宠档位属于表达层，基线带内保持克制，偏离或极端状态才显式表达。
- `~/Documents/harness/docs/扫兴姬-心智模型人类化强化方案-v2-20260830.md`（v1 指针：`HUMANOID_REINFORCEMENT`/`HUMANIZATION_REINFORCEMENT_20260830.md`）：H0-H7 人类化运行时；配套 `humanization.py`（shadow sidecar + context/narrative/packet/timeline/metrics/set），所有增强走 shadow->canary->measured->production，不扩大前辈 L4/L5 授权。

实现边界：

1. LLM 负责识别事件、提出解释或生成反思候选；规则引擎负责情绪增量；SQLite 负责持久化。
2. 创伤/负面联想只能作为有证据的关联信号，不能直接诊断、操控或覆盖人格核心。
3. 心智成长记录必须保留触发、体验/情绪、意义解释、行动/防御、事后反思和证据记忆 id；不把词频变化等同于人格成长。
4. 静态人格、动态状态和候选信念分层保存；候选信念经过反例审查后才可升级。
5. 新适配器优先只读、旁路、可回滚，不改变默认召回和 roleplay 零注入约定。



脚本路径：`~/.agents/skills/long-term-memory-emotion/memory_store.py`

```bash
# 写入记忆
python memory_store.py add \
  --scope default --entity 用户A \
  --content "用户A偏好简洁回复，讨厌 emoji" \
  --kind preference --importance 0.8 --valence 0.3 --arousal 0.4 \
  --tags "偏好,风格" --source "session-xxx"

# 写入反思/技能前，先跑 Evil Review 检查清单
python memory_store.py review --draft "这次任务证明先给最小工具集再展开更稳定"

# 心智联动审计（词频分析 + 写回记忆/情感）
python mind_audit.py --session <session.jsonl.zstd> --cutoff 2026-08-16T04:17:22+00:00 --dry-run
python mind_audit.py --session <session.jsonl.zstd> --cutoff 2026-08-16T04:17:22+00:00 --write-memory

# 检索（重要性 0.5 + 时效 0.3 + 情感显著性 0.2 加权）
python memory_store.py search --query "偏好" --scope default --limit 10

# 召回某 scope 近期重要记忆
python memory_store.py recall --scope default --limit 10

# 情感状态读写
python memory_store.py emotion get --scope 用户A
python memory_store.py emotion set --scope 用户A \
  --valence -0.6 --arousal 0.7 --dominance 0.3 \
  --label "frustrated" --context "连续两次方案被打回"

# 关系-情感状态机（v2，2026-08-18，吸收自 107 张角色卡的「好感分层+状态回写」范式）
# rel_level 关系档位 0-5：0=初始/陌生 1=冷淡 2=慢热 3=熟络 4=亲近 5=极亲/特殊
# affinity 好感 -2..2 / trust 信任 -2..2（双轴独立追踪）
python memory_store.py rel get --scope 用户A
python memory_store.py rel set --scope 用户A --rel-level 4 --affinity 1.5 --trust 1.0
# 增量回写（等价角色卡 <好感变化:+X>）：affinity 达 +1.8 自动升档、-1.8 自动降档
python memory_store.py rel update --scope 用户A --affinity-delta 0.5 --trust-delta 0.2
python memory_store.py rel update --scope 用户A --rel-adjust 1   # 手动升/降档
python memory_store.py rel update --scope 用户A --affinity-delta -1.0 --no-auto

# 遗忘/衰减
python memory_store.py forget --id 3
python memory_store.py decay --days 30 --factor 0.9

# 导出/导入
python memory_store.py export --file ~/.dsh/memory-emotion/backup.jsonl
python memory_store.py import --file ~/.dsh/memory-emotion/backup.jsonl

# 状态统计
python memory_store.py status
```

Windows 下如遇编码问题可加：`$env:PYTHONUTF8='1'`。

### 人类化影子运行时（humanization.py，H0-H9）

```bash
# H0：状态/指标
python humanization.py status
python humanization.py metrics

# H1：情境在场（只读）
python humanization.py context --scope character:demo-storykeeper --channel dsh

# H2：叙事候选（只读）
python humanization.py narrative --scope character:demo-storykeeper --limit 5

# H3：具身表达包（只读）
python humanization.py packet --scope character:demo-storykeeper --scope-baseline

# H4：关系时间线（只读）
python humanization.py timeline --scope character:demo-storykeeper

# H8：内在认知/日记/信件/张力（shadow）
python humanization.py cognitive --scope character:demo-storykeeper --attention 70 --curiosity 60 --energy 55
python humanization.py diary --scope character:demo-storykeeper --content '私人日记'
python humanization.py letter --scope character:demo-storykeeper --counterpart markus --subject '边界' --body 'shadow only'
python humanization.py tension --scope character:demo-storykeeper --statement '未决问题'
python humanization.py trigger --scope character:demo-storykeeper --record

# H9：人格化变体库（shadow）
python humanization.py variant --scope character:demo-storykeeper --context 项目决策 --outcome 中性 --text '先列依赖，再动手。'

# H3 严格 canary：pair-add / pair-list
python humanization.py pair-add --scope character:demo-storykeeper --original-output '原' --enhanced-output '增强' --selected enhanced --rule-id humanization.expression_packet.v1
python humanization.py pair-list --scope character:demo-storykeeper

# 人工审批：queue / decide / l4-report / export-queue
python humanization.py queue
python humanization.py decide --kind variant --id <id> --action approve
python humanization.py l4-report --scope character:demo-storykeeper
python humanization.py export-queue

# H3 text canary 白名单（当前仅 character:demo-alice 开启）
python humanization.py canary-scope --scope character:demo-alice --on
python humanization.py canary-scope --scope character:demo-alice --off

# 后端分组 / 一键回 shadow / 召回标注
python humanization.py backend-status
python humanization.py all-shadow
python recall_labeling.py --scope character:demo-alice --limit 50

# H7：用户主权调参
python humanization.py set --feature narrative_recall --mode shadow
python humanization.py set --channel text --mode canary

# 其他记录/反馈命令
python humanization.py pair-rate --id <pair_id> --rating enhanced
python humanization.py identity-add --scope character:demo-storykeeper --kind experiential_self --content '职责'
python humanization.py identity-list --scope character:demo-storykeeper
python humanization.py identity-propose --scope character:demo-storykeeper --kind narrative_self --content '待审自我叙事'
python humanization.py identity-decide --id <id> --action approve
python humanization.py policy-log --limit 20
python humanization.py p4-report --limit 10
python humanization.py variant-review --id <id> --approve
python humanization.py rel-add --scope character:demo-storykeeper --event-type milestone --summary '事件'
python humanization.py metric-add --scope character:demo-storykeeper --metric naturalness --value 0.7
python humanization.py initiative-add --scope character:demo-storykeeper --trigger time --action remind --reason '...'
python humanization.py expression-record --scope character:demo-storykeeper --rule-id ... --prefix 警惕
python humanization.py propose --scope character:demo-storykeeper --record

# 冒烟测试
python humanization_smoke_test.py
```

设计边界：默认只写独立 `humanization_sidecar.db`；不写 `memory.db`；
不自动发送主动消息；不修改静态人格；仍受前辈 L4/L5 审批限制。
`recall_context.py --narrative` 和 `roleplay_memory_chat.py --humanization-context` 均为默认关闭的可选影子开关。
当前 H3 text canary 已开启 `character:demo-alice`：该 scope 的 roleplay 会自动跑 original/enhanced 并记录 pair。
桌面入口：`~\Desktop\人类化审批队列.bat`（只读队列展示，审批必须走 CLI）。

> **H6 来源优先级**：用户本人直接提供（`source=user_direct` + `consent=explicit`）是一手来源；
> 真实人类研究语料（精神分析/心理学等）作为 `source=research_theory` 的主动研究来源，是“结构假设”，不是人格事实；
> 历史/模型提炼只作为 `machine_candidate` 候选，必须经用户审批后才可进入自我叙事账本。
> 这符合“人格建构的一手材料来自真实、自愿、愿配合的用户本人”+“主动研究真实人类而非依赖不稳定扮演”的原则。
> **自发心智升级护栏**：用户已授权系统自升级；当前 `autonomous_mind_upgrade=enabled`，
> 但只允许 `research_theory` 内部视角通过 `mind_evolution.py self-upgrade` 自动批准；
> `machine_candidate` / 用户人格 / 关系 / 政策禁止自升级；`all-shadow` 可强制回 `disabled`。
> 主动研究工具只读，不写 memory/humanization persona/policy。

> **主动研究工具**：`~/Documents/harness/_research/persona_research.py`
> 子命令：`index` / `list` / `extract--keyword` / `search--term` / `themes`。
> 语料索引：`_research/persona-corpus-index.json`；抽取文本：`_research/persona-extracts/`。
> 研究综述：`docs/真实人格建构研究-精神分析与心理学-20260830.md`
> `docs/真实人格建构研究-第二轮-20260830.md`
> `docs/真实人格建构研究-第三轮-OCR抽样-20260830.md`（扫描版抽样视觉阅读）
> `docs/真实人格建构研究-第四轮-深读-20260830.md`（千高原/阅读你的症状章节深读）
> 与 `docs/深读×user_model交叉候选-20260830.md`（克里斯蒂娃/德勒兹/弗洛伊德深读 × user_model 信号）。

### 会话启动召回（recall_context.py）

DSH/Agent 会话开始时可用本 skill 自带的 `recall_context.py` 生成一段紧凑记忆上下文，
避免把整个库倒进 prompt：

```bash
# 默认 scope，输出适合注入 system prompt 的文本
python recall_context.py --scope default --limit 5 --min-importance 0.5

# JSON 输出，适合程序/工具解析
python recall_context.py --scope character:demo-alice --format json
```

该脚本不改变记忆内容；默认召回会按 P0-1 回写 `access_count/last_access_at`，不联网。
失败时返回 `{"ok": false, "error": ...}`。可在 DSH 会话首个真实用户消息后由 Agent 调用，把结果压缩成 3~8 条上下文线索。

语义召回是显式 opt-in，不替换原有子串/权重召回：

```bash
# 需要 bge-m3 已在本机 Ollama 中，先完成向量回填
python fill_vec.py --dry-run
python fill_vec.py

# 同义不同词查询
python semantic_search.py --query "偷懒 不干活的工具面板" --limit 5 --sim-weight 0.8
python recall_context.py --semantic-query "偷懒 不干活的工具面板" --limit 5
```

`fill_vec.py` 只写 `nine_dim_vectors.db` sidecar；它通过 import 复用 `nine_dim.py` 的 `_embed/_pack` 格式。
未传 `--semantic-query` 时，`recall_context.py` 的原有路径不变。


### 九维状态到表达层（G1，旁路）

读取 sixdim 并投影为情绪词/桌宠档位，不写库、不修改角色：

```bash
python emotion_projection.py --input state.json
```

`state.json` 可直接使用 `nine_dim.py state` 的 `sixdim` 字段；`sad`/`sadness` 均可。只有同时提供角色基线时，才按基线偏离超过 10 的规则生成情绪前缀；未提供基线时只输出状态投影，不加前缀。警戒状态优先于正向档位。深层三维需求仍由既有九维公式负责，适配器不猜测。


### 常态入库（memory_ingest.py）

后台持续把 DSH 会话记录消化成长期记忆/情感，**只入库、不常态应用**：

#### G1 shadow mode（当前状态）

只读对照脚本：`g1_shadow_test.py`。它并行记录当前生产路径（当前无自动情绪前缀/桌宠切换）与 `emotion_projection.py` 的 G1 结果，不写 `memory.db`、不改 `emotion_state.sixdim`、不注入 Ollama、不驱动 Live2D。报告输出到 `~/.dsh/memory-emotion/g1-shadow-latest.{json,md}`。

当前验收：24 条规范夹具 + 4 个本机 scope derived 快照通过；覆盖基线克制、正向记忆、创伤警戒、恢复回涌、惊讶和 `sad` 别名。由于本机 `emotion_state.sixdim` 当前为空，live 快照明确标记为 derived，不能替代真实 sixdim 事件证据。每条结果保留 `raw_sixdim`、`rule_id`、`evidence_memory_ids` 字段；接入生产前必须提供真实 sixdim、规则 ID 和证据记忆 ID，并继续保留旁路回滚。


```bash
# 试跑：只扫描分析，不写库
python memory_ingest.py --dry-run

# 正式入库：处理新增/变化的会话
python memory_ingest.py
```

- 状态文件：`~/.dsh/memory-emotion/ingest-state.json`

#### 研究资料吸收的证据等级（Evil Review 后修订）

“吸收”不等于“现实规律已验证”，后续引用九维研究目录时必须区分：

- **代码已存在**：规则计算、记忆联想、向量/海马体衰减、关系字段、G1 旁路投影等在本地代码中存在；不代表全部路径已做长期实测。
- **手工/夹具已验证**：已有 20/40/60/65 轮报告、G1 shadow 夹具和本地 smoke test；它们证明给定输入下实现按预期运行，不证明现实心理规律。
- **研究假设**：记忆联想增强、负面触发、恢复回涌、参数量级和关系变化曲线仍需更多真实会话与可重复回归；“创伤后依恋加深”不作为默认机制。

当前 `emotion_state.sixdim` 为空时，derived 快照只能用于旁路观察，必须明确标记，不能替代真实事件证据。生产接入前继续要求 `raw_sixdim`、`rule_id`、`evidence_memory_ids` 和 before/delta/after 情绪事件日志。

#### 2026-08-29 continuity batch

新增本地标准库 sidecar：`continuity_store.py`，数据库为 `~/.dsh/memory-emotion/continuity_sidecar.db`，不迁移或改写 `memory.db`。

- `session_metrics`：scope、provider、召回尝试/成功、召回数量、回答、写回数量、错误和详情。
- `emotion_events`：`before/delta/after`、`rule_id`、source、证据 memory IDs；`nine_dim.py event` 输出单一机器 JSON。
- `profile_layers`：分离静态人格源、memory.db 动态状态和有界 effective projection；动态状态不能回写静态人格。
- `beliefs`：候选 belief、支持证据、反例证据、置信度、状态和来源分开保存；不会自动晋升为人格或事实。
- `report_history`：周报历史、7 日窗口、上一窗口差值和 default scope 软/硬阈值告警。

#### L4/L5 超拟人化研究方向

#### Autonomous 时间治理

> **超长期戳（indefinite-horizon）**：Autonomous 的实际自主执行实验与生产启动不在当前可预想的时间内完成。不设预计完成日期，不进入当前排期，不因其他 canary、belief 审批或记忆系统稳定而自动启动。当前策略固定为 `autonomous_tasks=disabled`，仅保留人工触发的低风险维护与研究登记能力。


详细边界记录见 [`HUMANOID_RESEARCH_L4_L5.md`](HUMANOID_RESEARCH_L4_L5.md)：L4 研究人格/记忆对低风险自主任务调度的候选生成与排序影响；L5 研究对人格本体的长期影响。两者目前均不开放自动生产应用，L5 任何候选变更必须经过 adversarial review、人工批准、版本化和可回滚记录。当前 G1 仅处于表达层 canary，不能推导出 L4/L5 授权。


入口工具：`deepseek_regression.py`、`deepseek_key_rotation_check.py`、`profile_layers.py`、`belief_sidecar.py`、`drift_matrix.py`。DeepSeek key 轮换必须在控制台完成，本地工具只做无秘密值输出的引用扫描和轮换后验证。`drift_matrix.py` 已验证三个人格 Modelfile、roleplay wrapper 和卡牌注册表的模型/scope 引用。

证据等级：本批代码和隔离夹具已验证；DeepSeek 回归 3/3 已验证；Ollama 扫兴姬 Evil Review 因 `127.0.0.1:11434` 未启动而为 BLOCKED；DeepSeek key 状态已由用户人工核验通过，当前标记为 `manual_verified_no_rotation_required`；本地工具仍不读取或输出 key 值。



#### 三项深层需求候选 sidecar（研究调研后）

GitHub 调研未找到可直接复用的 `security / possessiveness / attachment` 成熟计算器；可借鉴的成熟边界是：情绪与回复模型分离、解释与数值分离、显式 provenance、时间衰减、证据消费和宿主保留事实/策略。`need_projection.py` 复用本地 `心智情感闭环手册.md` 的 G6 公式，但定位为只读候选投影，不是心理测量器：

```text
security       = 100 - (fear + disgust) / 2
possessiveness  = (anger + 0.5 * surprise) / 1.5
attachment      = (joy + sadness) / 2
```

输出必须携带 `raw_sixdim`、`formula_id`、`evidence_ids`、`confidence`、`status`、`contradictions` 和语义护栏。只有至少两条带 `id/source_ref/event_type/observed_at` 的结构化证据才可进入 `candidate_observation`；裸 ID 只能是 `candidate_unverified`。sidecar 永不自动修改人格、关系、信念或 G1；`possessiveness` 不得解释为控制/监视/限制/惩罚授权，`attachment` 不得解释为依赖/服从义务。

- 已处理文件不会重复入库
- 提取规则保守：用户偏好/事实、助手反思/技能、整体情感倾向
- 写入统一走 `memory_store.py`，scope=`default`，source=`memory_ingest`
- 复用已有 `mind_audit.py`：每个新会话入库时自动跑一次词频心智分析并写回记忆/情感
- **不会自动注入常规对话**；需要时手动用 `memory_search` / `memory_recall` / `recall_context.py`

定时任务安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "~\.agents\skills\long-term-memory-emotion\install-memory-ingest-task.ps1"
```



## 记忆字段

| 字段 | 含义 |
|---|---|
| `scope` | 隔离域：`default` / `用户A` / `项目X` / `group:YOUR_GROUP_ID` 等 |
| `entity` | 记忆主体：用户/项目/任务/关系对象 |
| `kind` | `fact` 事实 / `preference` 偏好 / `event` 事件 / `relationship` 关系 / `skill` 技能 / `reflection` 反思 / `emotion` 情感 |
| `importance` | 0~1，固化优先级 |
| `valence` | -1~1，情感效价（负=消极，正=积极） |
| `arousal` | 0~1，唤醒度 |
| `tags` | 逗号分隔标签 |
| `archived` | 软删除标记 |

## 检索公式（当前实现）

```
retrieval_score =
    importance * 0.5
  + recency * 0.3          # 1/(天数+1)
  + (|valence| + arousal)/2 * 0.2   # 情感显著性
```

没有外部 embedding，所以目前是**关键词 + 结构加权检索**；后续若需要语义检索，
可把 `search` 替换成本地 embedding 工具，但必须走安全审批。

## Agent 使用协议

### 1. 任务开始前：Recall
- 按 `scope` + 当前实体 `recall` 最近重要记忆；
- `emotion get` 当前情感状态；
- 把召回结果压缩成 3~8 条上下文线索，不要整库倒进 prompt。

### 2. 任务过程中：Observe & Write
- 出现新的稳定事实/偏好/关系/可复用技能 → `add`；
- 用户情绪明显变化 → 用 OCC 式评价更新 `emotion_state`；
- 记忆要**去重**：先 `search` 同 scope+实体，命中则更新/跳过，不无脑追加。

### 3. 任务结束后：Reflect & Consolidate
- 用 LLM 对本次会话做反思，生成 1~3 条 `kind=reflection` 记忆；
- 重要技能/策略存为 `kind=skill`，方便 Voyager 式复用；
- 低价值过程性细节不写，或写后降 importance；
- **写 `reflection` / `skill` / 高权重 `preference` 前，必须执行 `SELF_EVOLUTION.md` 的 Evil Review**：先写草稿 → 暗我攻击 → 主我修订 → 再落盘；
- 通过 Evil Review 的记忆在 `tags` 中加入 `evil_reviewed`，方便后续审计与召回加权。

### 3.5 自进化记忆协议（Evil Review）

完整协议见 `SELF_EVOLUTION.md`。核心步骤：

1. **Draft**：写下反思/技能草稿；
2. **Attack**：以“暗我”视角攻击，检查过度自信、反例缺失、推断当事实、误导风险、敏感信息；
3. **Rebuttal / Integration**：逐条采纳/反驳/降级，补上适用条件和边界；
4. **Memory**：把修订后的内容 `add` 写入，并打 `evil_reviewed` 标签。

这条协议让长期记忆不只是“记住”，而是每次写入都在**自我加固心智模型**。

### 3.6 心智联动审计（Mind Audit）

心智模型 ↔ 长记忆 ↔ 情感系统联动：

1. **工具**：`mind_audit.py`（本 skill 目录内，零外部依赖 + jieba/zstandard）。
2. **输入**：DSH 会话 `.jsonl.zstd`，可用 `--cutoff` 切分前后时段。
3. **输出**：
   - before/after 词频、心智关键词占比、反思占比、正负情感词占比；
   - `mental_ratio_delta` / `reflect_ratio_delta` / `sentiment_delta`；
   - 心智变化水平：显著 / 中等 / 轻微。
4. **联动**：`--write-memory` 会把审计结果写入 `reflection` 记忆，并更新 `emotion_state`。
5. **建议频率**：每个大任务结束、或每次心智模型/记忆系统升级后跑一次。

> 目的：把“我的心智有没有变化”从感觉变成可量化指标，并沉淀进长期记忆。

### 3.7 心智自进化与跨会话沉淀（P0-P3）

长时记忆 skill 不止被动存储，P0-P3 形成一条可复用的自进化工作流：

| 阶段 | 工具 | 作用 |
|---|---|---|
| P0 扫描 | `mind_evolution.py scan` | 从人化 sidecar、记忆、H 层状态中扫描“心智张力” |
| P1 张力 | `mind_evolution.py status` / `top` | 汇总候选及严重度，人工或批量排序 |
| P2 候选 | `mind_evolution.py review` / `validate` / `decide` / `apply` / `rollback` / `batch` | 审查、验证、批准、应用、回滚、批量处理 |
| P3 沉淀 | `mind_precipitate.py precipitate` / `precipitate-top` / `list` / `show` | 把 approved/applied 或 Top 候选沉淀为可复用工作流卡与经验 |

共享沉淀目录：`~/Documents/harness/_mind-evolution/`
- `index.json`：跨 skill 的资产索引；
- `assets/<slug>/SKILL.md`、`WORKFLOW.md`、`experience.json`：正式沉淀；
- `assets/review-cards/<slug>/CANDIDATE_CARD.md`、`WORKFLOW.md`：shadow Top 候选工作流卡。
- `master-tasks/<slug>/MASTER_TASK.md`、`WORKFLOW.md`：合并宽泛项后的主任务卡。

发现入口（已写入 `manifest.json` 的 `mind_evolution` 字段）：任何 skill 或外部脚本可通过
`manifest.json -> mind_evolution -> root/index/assets/scripts` 找到 _mind-evolution 与相关脚本，
无需在各自代码里硬编码路径。

常用命令：

```bash
# 查看候选与工作流卡
python mind_precipitate.py list
python mind_precipitate.py show --id <candidate_id>

# 把 Top 候选批量生成 shadow 工作流卡（不更改状态）
python mind_precipitate.py precipitate-top --limit 20

# 审查/批准后正式沉淀
python mind_evolution.py review --id <id>
python mind_evolution.py validate --id <id>
python mind_evolution.py decide --id <id> --action approve
python mind_precipitate.py precipitate --id <id>
```

> 边界：`precipitate-top` 只生成“shadow review 卡”，不会把候选举为已批准；任何生产改动仍须
> 走 review → validate → decide → apply/rollback 的锁步。

### 3.8 九维修订只读 sidecar（`nine_dim_revision.py`）

对 `九维情绪心智模型_修订版.md` 做 Evil Review + 现象学审查后，只落地低风险部分：

- **`needs --scope S`**：修订版 3.4 的 U→V 独立惯性（`tau_V=8, tau_U=1`），只读候选投影；
- **`conflict --scope S`**：修订版 4.4 冲突指数的轻量代理（记忆六维距离 + 双极性）；
- **`baseline --scope S --baseline JSON`**：候选需求对 need_baseline 的漂移；
- **`status --scope S`**：查看本 sidecar 自己的观测记录。

治理边界与 `need_projection.py` 相同：不写 memory.db 主库、不改人格/关系、
不做心理诊断、不自动驱动表达。自己的观测只写入
`~/.dsh/memory-emotion/nine_dim_revision.db`。

```bash
python nine_dim_revision.py needs --scope character:demo-alice
python nine_dim_revision.py conflict --scope character:demo-alice
python nine_dim_revision.py baseline --scope character:demo-alice \
  --baseline '{"security":60,"possessiveness":40,"attachment":55}'
```

> 完整 NT 空间、Wasserstein-2、可控性、噪声、行为倾向概率等仍为“仅参考”，不实现。

### 3.9 真实用户模型只读 sidecar（`user_model.py`）

在人类研究理论之上，用本机已有真实痕迹构建“真实用户理解候选”：

- `memory.db` 对话/记忆；
- `mind_tensions`（会话存档沉淀的跨会话张力）；
- H8 日记；
- 本地文件收藏/资料命名（Downloads / harness docs 文件名的主题信号）。

`profile` 额外输出第二轮理论增强信号：重复-差异、矛盾/双极性、语言断裂、愿望-压抑代理、他者性/陌生性。

```bash
python user_model.py sources
python user_model.py profile --limit 20 --files-limit 100
python user_model.py files --dir ~/Downloads --limit 50
```

只读、候选、不诊断、不自动写入人格/关系/政策。
> 社交/IM 来源：用户已明确同意并指定 **QQ 与微信**；`media_sources.json` 已登记，QQ 本地报告/消息已可接入（`profile --include-media`），微信数据在 `D:/WeChat`，尚待解析适配。


### 3.10 真实数据回环、健康看板与季度审计

```bash
# 1) 真实会话标记（登记进 real_session_registry）
python session_ingest.py --register-kind real --limit 10
python session_ingest.py --list-real
python user_model.py real-sessions

# 2) 用户确认后 → user_confirmed_archive（进入 H6 approved）
python user_model.py promote --content '用户确认的理解条目' --scope user:real --evidence-ids 'um:xxx'

# 3) 统一健康看板
python health_board.py

# 4) 季度审计 / 测量治理
python quarterly_audit.py
# 阈值在 measurement_governance.json

# 5) 专项测量口径
python measurement.py leakage --query '马克斯' --scope default --limit 10
python measurement.py congruence --limit 200
python measurement.py recall --gold measurement_gold.example.json

# 6) 定时任务注册（健康看板每日 03:00，季度审计每 13 周周一 04:00）
powershell -NoProfile -ExecutionPolicy Bypass -File install-audit-tasks.ps1

# 7) recall gold / 泄漏矩阵
python measurement.py recall --gold recall_gold.json
python leakage_matrix.py

# 8) 人格漂移快照 + 季度盲评导出
python persona_drift.py --save
python persona_drift.py --compare
python blind_review_export.py --limit 100 --out ~/.dsh/memory-emotion/blind-review.csv
python plugin_audit.py
python production_gate.py

# 9) 人工 gold 集标注 + congruence 校准探针
python gold_labeler.py export --gold recall_gold.json --out recall_gold_label.csv
python gold_labeler.py import --file recall_gold_label.csv --out recall_gold_human.json
python congruence_probe.py --dry-run
python congruence_probe.py
```

- `health_board.py`：manifest / drift / smoke / memory / queue / policy / assets / candidates / user_model / real sessions 汇总。
- `quarterly_audit.py`：按阈值输出 pass / fail / not_measured；未测项属于治理缺口不是“已达标”。
- `measurement.py`：cross-scope leakage / emotional congruence / recall precision+recall 的代理测量。
- roleplay H3 canary 现在会把真实输出带 `【情绪】` 前缀，并给 `pair-add` 传 `sixdim_json / expected_prefix`，用于真实 congruence 测量。
- `user_model.py promote` 只应在**用户明确确认**后执行，写入 `source=user_confirmed_archive` + `status=approved`。
- `measurement_gold.example.json` 是示例，不是人工标注 gold；正式 recall 需人工 gold 集。



### 4. 情感约束（OCC/PAD 映射）

| 情感状态 | 建议行为约束 |
|---|---|
| valence<0, arousal 高（愤怒/焦虑） | 降低对抗性，先共情/确认，再给方案；避免长篇大论 |
| valence<0, arousal 低（沮丧/疲惫） | 简化步骤，给明确下一步，少追问 |
| valence>0, arousal 高（兴奋/满意） | 可以顺势推进，但别过度承诺 |
| valence>0, arousal 低（平静/满意） | 保持稳定输出，适合沉淀记忆/复盘 |
| dominance 低 | 多给用户控制权，使用建议式语气 |

情感状态只做**软约束**，不覆盖用户明确指令；遇到心理危机类内容，应建议专业帮助而非扮演心理医生。

## 安全与隐私边界

- ✅ 数据只写本地 `~/.dsh/memory-emotion/`，无网络请求、无遥测、无外传；
- ✅ 不下载/不安装任何第三方插件，除非用户明确批准；
- ✅ 敏感信息（密钥、Cookie、身份信息）默认**不写入记忆**；确需记录必须先问用户；
- ✅ 用户可随时 `export` 备份、`forget` 删除、或直接删除数据目录；
- ⚠️ SQLite 文件是明文，注意本机 ACL；不要放到共享目录。
- ⚠️ 情感标签是推断结果，不是医学/心理诊断。

## 角色记忆 scope 约定（2026-08-16 升级）

角色蒸馏体（dot-skill 产物）可接入本系统，获得**跨会话记忆 + 独立情感状态**。每个角色用独立 scope 隔离，不污染主记忆库：

| 角色 | 记忆/情感 scope | 初始情感 | 协议文档 |
|---|---|---|---|
| 猫娘 neko | `character:neko` | v0.8 a0.6 d0.3「深爱着主人」 | `~/.dsh/profiles/node_modules/dsh-character-galgame/knowledge/memory-protocol.md` |
| 派对姬（Entity-6701） | `character:demo-alice` | v0.4 a0.6 d0.4「开心等马卡龙」 | `~/.dsh/skills/celebrity-demo-alice/knowledge/memory-protocol.md` |
| 掃興姬（Entity-6801） | `character:demo-storykeeper` | v0.2 a0.3 d0.7「谨慎评估中」 | `~/.dsh/skills/celebrity-demo-storykeeper/knowledge/memory-protocol.md` |

**接入方式**（角色会话开始/互动/结束时）：
1. 唤醒：`GET /emotion?scope=character:X` + `GET /recall?scope=character:X&min_importance=0.6`
2. 互动中：`POST /memories {scope:"character:X", entity, content, kind, importance, valence, arousal, tags}`——**记录对方行为而非言语**（掃興姬核心：行为>言语）
3. 沉淀：`POST /emotion {scope:"character:X", valence, arousal, dominance, label, context}` 更新基线

**扩展新角色**：任意 dot-skill 蒸馏体按此模式注册——scope 命名 `character:<slug>`，初始情感按 persona Layer 0.5 基线，协议文档放角色 skill 的 `knowledge/memory-protocol.md`。

**初始情感落库**：文档层初始情感不会自动进 DB，需执行一次：

```bash
python seed_initial_emotions.py            # 只补缺失
python seed_initial_emotions.py --force    # 强制覆盖
python seed_initial_emotions.py --dry-run  # 预览
```

**DeepSeek 自我定位洞察入库**：

```bash
python seed_deepseek_insights.py            # 写入 reflection + skill
python seed_deepseek_insights.py --dry-run  # 预览
```




## 与现有生态的关系（只读调研结论）

已调研但不下载：
- `dsh-hermes-memory`：跨会话记忆 + 自主技能学习（可参考其分层思路）
- `dsh-mnemon`：本地记忆系统 + 受监督记忆体（可参考“受监督”审批思想）
- `dsh-plugin-long-term-memory` / `dsh-persona-memory`：npm 包，未审计不安装
- DeepSeek Harness 官方讨论 #525：bounded cross-session memory（MEMORY.md/USER.md）+ skill lifecycle curation

本 skill 保持零依赖，核心协议可独立使用；未来若想深度集成 Harness 插件，
应把这些候选仓库走完安全审批后再评估移植。
