# Kimi / Moonshot AI 研究学习（2026-09-03）

> 目标：把 Kimi / Moonshot AI 在“长上下文 / 记忆 / 个性化 / 智能体”方向的成果全部梳理，提取对我们 harness 的启发。
> 说明：本次抓取受网络限制，部分论文只拿到摘要/官方页片段；不捏造具体数字。

---

## 1. 目前已确认的 Kimi / Moonshot 相关成果

### Kimi K2: Open Agentic Intelligence（arXiv 2507.20534）
- 开放智能体模型；
- 强调 **agentic intelligence**：工具调用、多步任务、自我反思；
- 长上下文评测采用 **128K context**；
- 采用 **YaRN 长上下文扩展**；
- 开放权重/开放模型。

### Kimi K2 Thinking
- 新一代开源 agentic reasoning 模型；
- Moonshot 主打的 **lossless long context**：大段文本仍可精确回忆、不丢信息；
- 目标是 **personalization** 路径：长上下文让模型“记得你”成为可能；
- 支持 INT4 推理，降低 GPU 显存。

### Kimi Agent Swarm（官方帮助页）
- 多智能体协作模式；
- 每个 subagent 有自己 **notebook**，聚焦记录自己的信息；
- 围绕 **同一 story core** 共享语境，避免单一上下文窗口瓶颈。

### Kimi CLI Memory System（GitHub issue #1283，功能请求）
- 需要跨会话持久上下文；
- 自动记忆（AI 管理的 notes）+ 手动 memo；
- 团队 memory 共享；
- memory 版本化。

### Kimi K3（社区解读）
- 传闻支持 ~1M token 上下文；
- 长时自动化/长程任务能力；
- 具体技术细节未正式释放。

---

## 2. 这些成果共同指向的“范式”

```text
1. 长上下文是“形态”，记忆/个性化是“目的”
2. 光靠 context window 不够 → 需要显式 memory（notebook/notes/memo）
3. agentic 模型 + tool use + 反思 → 长程任务
4. 多 agent 用“各自 notebook + 共享 story core”避免上下文爆炸
5. 开放模型 + 本地/INT4 → 降低成本
```

## 3. 对我们 harness 的启发

| Kimi 点 | 我们的对应/可做 |
|---|---|
| lossless long context → personalization | 我们做本地记忆 + user_confirmed + Perspective Card 个性化 |
| notebook / automatic+manual memo | `facts.py` + `mind_precipitate.py` + `user_confirmed_intake` |
| memory versioning | `mind_precipitate` review-cards / 快照 |
| Agent Swarm 每个 subagent 一个 notebook | 每个角色一张 Perspective Card + cross_character_consistency |
| 共享 story core | H1-H9 共享人类化 core + 跨场景同一她 |
| 128K/YaRN 长上下文 | 我们已用 `max_recall_items=3 / max_recall_chars=1200` 控制注入 |
| INT4/本地开源 | 我们本地 Ollama + WSL 沙盒 |

## 4. 具体可落地动作

1. **Kimi-style memory notes**：在我们的 `facts`/`mind_precipitate` 上加“自动笔记 + 手动 memo + 版本”；
2. **Agent Swarm notebook 模式**：把每个角色卡当成“notebook”，跨角色一致性用共享 core；
3. **长上下文成本**：继续用受控注入，不盲目扩 context；
4. **personalization**：用 long-context/记忆做“越聊越懂你”，但必须是用户确认 + 本地。

## 5. 诚实边界

- 2026-09-04 已补抓：Kimi K2 arXiv 原文、官方 K2 仓库/技术页、K2 Thinking 官方模型卡/许可证、kimi-cli 官方仓库/文档及 session persistence 源码；稳定入口见第 6 节。
- Turing Post 等二手文章只作导航，不替代论文、模型卡、许可证或源码。
- Kimi 官方 Agent Swarm 帮助页中的产品描述仍需绑定页面版本并与本地独立复现区分。
- GitHub MoonshotAI/kimi-cli issue #1283 是功能请求/设计提案，不是完整 automatic memory 已发布的证明。
- 当前已找到 `context.jsonl` 会话持久化与恢复源码；尚未确认 #1283 设想的自动 notes、团队共享和 memory versioning 已完整合并。
- Kimi K3 社区传闻不得进入事实结论，除非出现可核验的官方报告、仓库或模型卡。

---

> 结论：Kimi/Moonshot 最启发我们的是“**长上下文不是目的，持久记忆与个性化才是**”，以及“**多 agent 用 notebook 分工而非单一大窗口**”。
> 这与我们正在做的“本地记忆 + 人格卡 + 主动管线 + 受控上下文”高度一致。


## 6. 后继者可直接访问的官方来源索引（2026-09-04 补全）

### 6.1 Kimi K2 原始技术报告

```text
arXiv 摘要页： https://arxiv.org/abs/2507.20534
arXiv PDF：   https://arxiv.org/pdf/2507.20534
官方仓库：    https://github.com/MoonshotAI/Kimi-K2
仓库报告：    https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf
官方技术页：  https://moonshotai.github.io/Kimi-K2/
```

已核验：arXiv PDF 为 32 页《Kimi K2: Open Agentic Intelligence》技术报告；官方仓库 README 同时链接 arXiv Full Report 和官方 Tech Blog。官方 README 标示 K2 context length 为 128K，并将代码与权重许可标为 **Modified MIT**。引用和使用前必须读实际 LICENSE，不能简写成普通 MIT。

### 6.2 Kimi K2 Thinking 官方材料

```text
官方技术页： https://moonshotai.github.io/Kimi-K2/thinking.html
官方模型卡： https://huggingface.co/moonshotai/Kimi-K2-Thinking
模型卡原文： https://huggingface.co/moonshotai/Kimi-K2-Thinking/raw/main/README.md
实际许可证： https://huggingface.co/moonshotai/Kimi-K2-Thinking/blob/main/LICENSE
```

官方模型卡明确声明：

```text
context length = 256K
native INT4 / quantization-aware training
可在 200–300 次连续工具调用范围内维持长程 agentic 行为（官方评测主张）
license_name = modified-mit
```

证据边界：这些是 Moonshot 官方模型卡/评测声明，不是本地独立复现结果。模型卡还说明，当累积输入超过 256K 时，其 agentic-search harness 会隐藏此前 tool outputs；因此不得把 K2 Thinking 写成“无限/绝对无损记忆”。“lossless”在原文里主要对应 INT4 量化带来的性能/延迟权衡表述，不应未经原文支持扩大成“任意长文本都绝不丢信息”。

### 6.3 kimi-cli 官方仓库、文档与许可证

```text
官方仓库：  https://github.com/MoonshotAI/kimi-cli
README：    https://raw.githubusercontent.com/MoonshotAI/kimi-cli/main/README.md
官方文档：  https://moonshotai.github.io/kimi-cli/en/
配置文档：  https://moonshotai.github.io/kimi-cli/en/configuration/config-files.html
Changelog： https://moonshotai.github.io/kimi-cli/en/release-notes/changelog.html
许可证：    https://raw.githubusercontent.com/MoonshotAI/kimi-cli/main/LICENSE
```

已核验：kimi-cli 仓库代码许可证为 **Apache-2.0**。不要与 Kimi K2/K2 Thinking 权重的 Modified MIT 混为一谈。

### 6.4 kimi-cli 当前真正存在的持久化机制

会话持久化源码：

```text
https://github.com/MoonshotAI/kimi-cli/blob/main/src/kimi_cli/session.py
https://raw.githubusercontent.com/MoonshotAI/kimi-cli/main/src/kimi_cli/session.py
```

当前 `session.py` 可直接看到：

```text
每个 session 有独立目录
context.jsonl 保存消息上下文
wire.jsonl 保存 wire 记录
Session.find/list/continue_ 可恢复已有 session
SessionState 单独持久化 approval、plan mode、workspace scope 等状态
```

这证明的是“会话历史持久化与恢复”，不自动等于“跨会话自动抽取长期事实/偏好记忆”。官方 changelog 也可作为 session persistence 的版本证据，但引用时应绑定具体 release/version，不要只引用不断变化的 main 页面。

### 6.5 kimi-cli memory issue #1283 的正确身份

```text
Issue： https://github.com/MoonshotAI/kimi-cli/issues/1283
标题： Feature Request: Memory System - Persistent context across sessions
```

它提出的目标包括：

```text
manual memory via AGENTS.md
user/project/organization 分层指令
AI-managed automatic notes
按需读取 topic memory
memory sharing/versioning
```

但它是 **feature request / 设计提案**，不能作为“自动长期 memory 已全部实现”的证据。Issue 中描述 `AGENTS.md / AGENTS.local.md` 的发现与 `KIMI_AGENTS_MD` 注入机制，但 automatic memory 目录、失效策略、版本化等仍需按当前代码和 release 逐项核对。

后继报告必须拆开写：

```text
已证实：session context.jsonl 持久化/恢复
已描述：AGENTS.md 类项目/用户指令记忆
提案中：AI 自动 notes、team sharing、memory versioning 等完整长期记忆系统
```

### 6.6 AGENTS.md 相关稳定入口

```text
kimi-cli 仓库自身 AGENTS.md：
https://github.com/MoonshotAI/kimi-cli/blob/main/AGENTS.md

raw：
https://raw.githubusercontent.com/MoonshotAI/kimi-cli/main/AGENTS.md

生成项目 AGENTS.md 的初始化 prompt：
https://github.com/MoonshotAI/kimi-cli/blob/main/src/kimi_cli/prompts/init.md
```

仓库根 AGENTS.md 主要是 kimi-cli 项目自身的开发约定；`prompts/init.md` 是引导 agent 为目标代码库生成 AGENTS.md。两者都不能单独证明 issue #1283 所设想的完整自动长期记忆已经落地。

### 6.7 二手来源只能作导航

Turing Post 等文章可以用于快速理解或寻找关键词，但涉及以下事实时应回到官方/原始来源：

```text
模型参数和 context length
评测分数与条件
INT4/QAT
工具调用步数
许可证
memory 是否已经实现
源码行为
```

引用优先级：

```text
实际源码/许可证/模型卡/论文
> 官方技术博客和官方文档
> 官方 issue/discussion（只证明有人提出或讨论）
> 二手媒体/社区解读
```

### 6.8 当前仍未完成的核验

```text
1. 为所有引用绑定 commit/release，而不是只指向 main；
2. 定位 AGENTS.md 发现/注入机制当前版本的确切源码文件；
3. 验证 issue #1283 中哪些子功能已合并、哪些仍是提案；
4. 本地运行 kimi-cli，观察 context.jsonl/session state 的真实生命周期；
5. 对 K2/K2 Thinking 官方 benchmark 做独立复现或明确标记“官方声明”；
6. 不传播 Kimi K3 社区传闻，除非出现官方报告/仓库/模型卡。
```

---

> **2026-09-04 修订结论**：K2 原始论文、K2/K2 Thinking 官方技术材料、kimi-cli 仓库与 session persistence 源码已经找到。尚未找到可证明“完整自动长期 memory 已发布”的官方实现；#1283 仍应视为功能请求。后继者不要再写“找不到原文”，也不要把 session 恢复、AGENTS.md 指令和自动长期事实记忆混成同一能力。