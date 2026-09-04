# Harness Core Portable 是什么

这个项目想做的**不只是一个“角色聊天前端”**，而是把几件事做成一个可审计的本地层：

- 分 scope 的跨会话记忆（角色 / 项目 / 任务域）
- 私有记忆隔离 + 共享 Story Core（共享世界 ≠ 共享全部记忆）
- 统一事件信封：日志 / 经历 / 日记 / 内省分层
- 角色资产化：角色包安装、校验、预览、激活、回滚、Character Card 导入、语料生成草稿
- 工程职责角色：角色可以承担风险审查、发布检查、证据审计
- 只读本地 HTML 控制台：运行桥、角色画廊、事件时间线、Token / 上下文面板
- 公共能力与本机私人角色分离：公开包只发布能力和插槽，本机覆盖层保留私人角色、偏好、知识库

另外还逐步加入了：

- `harness_core` 稳定 Python API
- OpenAI-compatible adapter
- 最小 MCP server（stdio JSON-RPC）
- Agent 兼容矩阵（AGENTS.md / CLAUDE.md / MCP / DeepSeek 等）
- 回归测试（标准库 unittest）

---

## 诚实边界

- 这是 Alpha / WIP，不是 production-ready
- `activate` 代表本地激活标记，不等于所有运行入口都已完成全局热挂载
- 完整生产门控依赖本地数据，公开包可能返回 `UNAVAILABLE` 或 `FAIL`
- 不证明 AI 真的有意识、真的理解或真的在乎
- 公共包不包含真实用户数据、私有人格卡、模型权重或 API key

---

## 当前 Pre-release

<https://github.com/bronya-q/harness-core-portable/releases/tag/v0.1.0-alpha.2>

---

## 真的非常需要大家反馈

现在项目就卡这了：)

最欢迎这几类反馈：

1. **首次使用**：哪一步看不明白？哪一步放弃了？
2. **角色 / 记忆场景**：跨会话记忆、角色隔离、纠错 / 恢复是否符合预期？
3. **工程角色**：workspace / evidence / ab 这些命令是否直觉？
4. **MCP / coding-agent 集成**：你希望先接哪个生态？

如果愿意，可以直接在 Issue 里提，或者回帖告诉我。

---

## 如何贡献 / 帮忙

- 自然流样本（`natural_session_*.bat`）
- gold 标注（`recall_gold_independent_blind.csv`）
- 下游任务反馈（游戏 / 论文 / 网页 / 文书）
- 安全 / 许可证核验

详细说明见：

- `CONTRIBUTING.md`
- `SECURITY.md`
- `NATURAL_DATA_GAP.md`

<details>
<summary><strong>需要大家一起来（真的，这些我一个人搞不定）</strong> <em>点击展开</em></summary>

下面这些细项我已经在 README「需要大家一起来」里列好了，这里不重复贴一遍，你直接过去挑一个就行：

- MCP Inspector 实跑
- Official MCP Registry 提交
- 真实宿主验证（Claude Code / Codex / Copilot）
- 首次用户测试
- 双人标注
- 真实截图 / GIF
- CI 与跨平台

→ [README「需要大家一起来」](https://github.com/bronya-q/harness-core-portable#需要大家一起来真的这些我一个人搞不定)

> 哪怕只来 1 个人，也比没人强。
> 不管大家有没有装，都祝看到的朋友们用 AI 许愿工程一次就成，DSH 版本更新兼容性依旧稳定。

</details>

---

## 项目名与定位

- 项目名：**Harness Core Portable**
- 定位：**本地优先的 AI 角色记忆、上下文可见性与角色 / 知识 / 工程职责运行台**

---

最后，不管大家有没有装，都祝看到的朋友们用 AI 许愿工程一次就成，DSH 版本更新兼容性依旧稳定。
