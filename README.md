# Harness Core Portable

> 一套**可迁移、可审计、可回滚**的本地“心智 / 记忆 / 情感”核心，供其他 agent、桌宠、角色扮演与长程任务系统使用。
> 不是“让 AI 变成人”，而是让“关系型 AI 界面”**更稳定、更连续、更可信任**。

```text
版本：v0.1（粗糙草稿，未完成端到端公开验证）
状态：alpha / WIP
License：MIT
Python：3.13+
```

---

## 目录

- [这是什么](#这是什么)
- [为什么值得看](#为什么值得看)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [常用命令](#常用命令)
- [效果与边界](#效果与边界)
- [数据与隐私](#数据与隐私)
- [如何贡献/帮忙](#如何贡献帮忙)
- [文档](#文档)
- [License](#license)
- [致谢](#致谢)

---

## 这是什么

一个把“人格一致性、跨会话记忆、关系/情感状态、自进化、门控治理”做成**可复现模块**的工程。

```text
角色扮演 / 长程任务 / 多 agent 协作
        ↓
Humanization H1-H9 / 记忆 / 情感 / 自进化
        ↓
production_gate / mind_review / rating_snapshot
```

它不是聊天前端，不是模型，也不是“心理效度声明”。

## 为什么值得看

- **可迁移**：纯 Python + SQLite，核心脚本可用 `Path.home()` 适配本机；
- **可审计**：gold / gate / snapshot / hash 都能复现；
- **可回滚**：notebook/story core 支持 restore；
- **有边界**：不自动上传、不写 PII、安全在 harness 代码；
- **不造轮子**：多角色协作用 notebook + story core，而不是让每个角色各写一套记忆。

## 对下游工程的作用（0.1 草稿，未验证）

这里的“工程”指**在增强心智模型下，agent 做的其他项目**：

- 制作游戏（世界观/角色一致性/剧情连续性）
- 撰写论文/报告（记忆检索/目标分层/证据可追溯）
- 公司/产品网页（用户偏好记忆/多轮需求一致性）
- 文书工作（长文档受控注入/关键信息不丢）
- 角色扮演（一致性/边界/自然流/关系阶段）

> 本版本为 0.1 粗糙草稿：**这些作用目前只是设计意图和初步工程代理，尚未经过真实下游项目验收。**
> 详细边界见 `EFFECTS.md`。

## 快速开始

```bash
# 1. 解压/克隆仓库
cd harness-core-portable

# 2. 运行自检（失败返回非 0）
python harness.py audit

# 3. 看政策
python harness.py status

# 4. 内生审查
python mind_review.py run
```

> 可选：本地 Ollama（用于 embedding / LLM），不联网即可跑核心指标。

## 核心概念

| 概念 | 说明 |
|---|---|
| Scope | 一个角色 / 项目 / 任务域 |
| Notebook | 每个 scope 的持久笔记本（auto/manual，版本链） |
| Story Core | 多角色/多任务共享的世界核心（可 diff） |
| Perspective Card | 高一致性角色人格卡 |
| Gate | `production_gate.py`（fail-closed） |
| Review | `mind_review.py`（内生审查） |

## 常用命令

```bash
python harness.py audit                 # 聚合自检
python harness.py notebook note --scope game:demo --text '...' --kind manual
python harness.py notebook restore --scope game:demo --version 1
python harness.py story set --namespace story:game-demo --content '...'
python harness.py story diff --namespace story:game-demo
python harness.py measure congruence --limit 200
python harness.py persona render --name demo-storykeeper --max-tokens 120
python harness.py review run
```

角色扮演注入（受控）：

```bash
python roleplay_memory_chat.py \
  --persona demo-alice \
  --prompt '这是什么地方？' \
  --story-namespace 'story:game-demo' \
  --notebook-auto
```

## 效果与边界

- 效果：一致性、连续性、边界安全、可审计性；
- 边界：**不是心理学效度**；工程 proxy ≠ 用户满足度；自然数据仍缺口。

详见：

```text
EFFECTS.md           场景效果与个性化边界
MENTAL_MODEL_EFFECTS.md 心智模型效果说明
NATURAL_DATA_GAP.md  数据缺口与求助
```

## 数据与隐私

- 默认**本地**，不自动上传；
- **不含** PII / API key / 真实对话 / 大模型文件；
- 原用户绝对路径已替换为 `~`；
- 其他用户本地知识库需授权/脱敏。

## 如何贡献/帮忙

- 自然流样本（`natural_session_*.bat`）
- gold 标注（`recall_gold_independent_blind.csv`）
- 下游任务反馈（游戏/论文/网页/文书）
- 安全/许可证核验

见 `CONTRIBUTING.md` / `SECURITY.md` / `NATURAL_DATA_GAP.md`。

## 文档

```text
AGENT_USAGE.md          给其他 agent 的使用指南
EFFECTS.md              效果与个性化边界
MENTAL_MODEL_EFFECTS.md 心智效果说明
NOTICE.md               第三方许可证义务
CREDITS.md              来源归属
SECURITY.md / CONTRIBUTING.md
```

## License

MIT。第三方许可证/来源见 `NOTICE.md` / `CREDITS.md`。

## 致谢

借鉴/参考：Herta、N.E.K.O.、Mem0、Letta、Kimi/Moonshot、DeepSeek Harness、W博士 Perspective Skill、哥伦比娅角色提示词等。详见 `CREDITS.md`。

---

> 如果你在 10 秒内没看出它适合什么，请回去读 [NATURAL_DATA_GAP.md](NATURAL_DATA_GAP.md) —— 它最诚实。
