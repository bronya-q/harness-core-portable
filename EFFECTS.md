# 项目效果：它到底在什么场景下提升什么

> 这不是“让 AI 变成人”的承诺；而是“在什么工程/产品场景下，这套系统能带来什么可观察提升”。

---

## 1. 长对话 / 跨对话语境下的工程提升

| 场景 | 效果 |
|---|---|
| 长对话 | 连续记忆可让同一角色“记得之前说过的事”，减少重复/漂移 |
| 跨对话 | 记忆 + 身份账本 + 叙事自传让“同一个她”跨会话成立 |
| 会话回顾 | `rating_snapshot` / `mind_review` / `daily_report` 可复现状态 |
| 多角色 | Perspective Card / expression DNA / 跨角色一致性检查，防止串人 |

**工程侧可测指标**：
- `recall-pool`（记忆检索）
- `persona_drift`（人格漂移）
- `production_gate` / `mind_review`（治理与自检）
- `flow-split`（自然流 vs 定向）

## 2. 角色扮演语境下的用户需求满足度

| 用户需求 | 系统怎么做 | 预期提升 |
|---|---|---|
| “更像同一个人” | 第一人称自传锚点 + 关系阶段 + 矛盾公式 | 一致性提升 |
| “记得我/记得我的事” | 记忆检索 + 原子事实 + 实体/时间 | 连续性提升 |
| “不要越界/不要突然热情” | no_self_reveal / anti_prompt_injection / output discipline | 边界安全感 |
| “自然聊，而不是模板” | natural_session / 自然流 / 主动候选门控 | 真实感提升 |
| “不要被吓到/冒犯” | 防注入 / 情感克制 / 不主动恋爱化 | 安全体验 |

**注意**：
- 这些是**工程/体验代理**，不是心理学效度；
- 需要用户盲评/问卷才能真正度量“满足度”。

## 3. 能否接入其他用户本地知识库进行个性化？

**可以，但需要约束。**

### 架构上支持
```text
media_sources.json（文本/JSON/目录）
  → user_model / user_model_signals
  → Perspective Card / 人格卡
  → 记忆/语义检索
```

其他用户可以：
- 把自己的本地笔记/聊天/知识库路径加入 `media_sources.json`；
- 用 `perspective_card.py` 建自己的角色卡；
- 用 `natural_session` 积累自己的自然流。

### 边界（必须说）
- **不自动上传/不自动联网**：默认本地；
- **PII/API key 不进知识库**：需脱敏或明确授权；
- **不得把他人私人数据无授权入料**；
- **知识库有各自许可证/版权**：只做本地引用/索引，不随仓库分发；
- 其他用户的“事实”应与其 `user_confirmed` 绑定，不能当作全局事实。

## 4. 怎么证明“有效”

```bash
python production_gate.py          # 门槛
python mind_review.py run           # 内生审查
python measurement.py recall-pool   # 记忆检索
python harness.py audit             # 汇总
```

> 真正证明“满足用户”：需要 **用户盲评 + 纵向对照 + 自然流样本**，这是下一步研究。

---

> 总结：这套系统在**连续性、一致性、边界安全、可审计性**上有明确工程效果；
> 在“用户情感满足度”上目前只有代理，不做心理效度承诺。
> 它可以接其他用户本地知识库进行个性化，但必须**本地优先 + 授权 + 脱敏**。

---

## 5. 特定工程成效：是否满足预期 / 是否偏离目标 / 是否抑制牛角尖

| 工程维度 | 系统如何帮助 | 可观察指标 |
|---|---|---|
| 满足用户预期 | `user_confirmed` + 盲评 + 自然流反馈 | 用户确认率、盲评通过、user_correction_rate |
| 不偏离最初目标 | `mind_evolution` 目标分层 + 长/短目标 + master_tasks | 目标清单偏离检测、`production_gate` 门控 |
| 抑制牛角尖 | 认知动力（注意力/好奇心/精力）+ 主动候选门控 + 自进化候选 | `cognitive_dynamics` 状态、`proactive_pipeline` 决策分布 |
| 聚焦主线 | user_model 技术主线/创作支线候选信号 | user_model_signals 稳定性 |
| 防止过度自我强化 | 内生审查 mind_review + 自进化白名单 | mind_review 违规计数 |

> 说明：这些是**过程指标**，不等于“用户满意”本身；最终仍需要用户逐项确认。

## 6. 成本：token 与本地资源利用率

| 成本项 | 系统关注点 | 工具 |
|---|---|---|
| Token | 每次 roleplay/memory recall/评测的输入输出 | `ui.usage` / `rating_snapshot` / `daily_report` 可用时统计 |
| 本地资源 | 内存/显存（Ollama 模型）、磁盘（DB/vector/模型）、CPU/GPU | `memory_health_report` / `rating_snapshot` / `deepseek-eyes` 类探针 |
| 复用 | 向量复用、缓存、避免重复重嵌 | `vector_worker` / `fill_vec` 断点续跑 |
| 可控 | `max_recall_items=3 / max_recall_chars=1200` 限制注入上下文 | 运行时 policy |

> 可量化的成本报告建议：
> ```text
> python rating_snapshot.py        # 输出快照含 db hashes / 命令
> python daily_report.py           # 日报含 health/quarterly
> 若接入 usage_daily：可看 token 预算
> ```

## 7. 一个“实验工程”的完整效果闭环

```text
原始目标
  → user_confirmed 目标确认
  → mind_evolution 分目标
  → 执行（roleplay/natural_session）
  → 自审（mind_review / production_gate）
  → 成本（token / 资源 / 时间）
  → 用户反馈（盲评 / 修正）
  → 是否继续 / 回滚
```

> 这套闭环让“是否偏离初始目标”变成**可检查、可回滚**，而不是黑盒。
