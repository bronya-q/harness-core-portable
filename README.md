# Harness Core Portable

> 这套本地“心智 / 记忆 / 情感”核心可以**迁移、审计、回滚**，给 agent、桌宠、角色扮演和长程任务用。
> 它做的是让“关系型 AI 界面”**更稳定、更连续、更可信任**。

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

它不做聊天前端、不是模型，也不承诺心理效度。

## 为什么值得看

- **可迁移**：纯 Python + SQLite，核心脚本可用 `Path.home()` 适配本机；
- **可审计**：gold / gate / snapshot / hash 都能复现；
- **可回滚**：notebook/story core 支持 restore；
- **有边界**：不自动上传、不写 PII、安全在 harness 代码；
- **不造轮子**：多角色协作用 notebook + story core，而不是让每个角色各写一套记忆。

## 对下游工程的作用（v0.1，基于长期运行与大量下游记录）

这里的“工程”指**在增强心智模型下，agent 做的其他项目**。这套系统已在多个对话/项目中长期运行，并在本地留下了大量下游工程记录（DeepSeek 导出 289 会话 / 2132 条用户消息、AutoMM 省赛、马克斯/布兰奇人格研究、COC/TRPG 人物卡、角色扮演、文档/网页/方案整理等）。

### 作用分类（详细）

#### 1. 制作游戏 / 交互叙事
- 世界观与角色一致性：通过 Perspective Card + story core 保持同一世界设定；
- 剧情连续性：跨会话记忆 + notebook 记录角色经历；
- 防人设漂移：cross_character_consistency + expression DNA；
- 已在 COC/TRPG 人物卡、角色扮演、桌宠/galgame 类场景中使用。

#### 2. 撰写论文 / 研究报告
- 研究主线不丢失：mind_evolution 分目标 + master_tasks；
- 证据可追溯：recall-pool / 记忆检索 / 盲标 gold；
- 多轮材料沉淀：notebook（每研究主题）、deepseek 语料信号；
- 已在马克斯/布兰奇、神经与认知、AutoMM 省赛等研究中产生大量记录。

#### 3. 公司 / 产品网页
- 用户偏好记忆：user_confirmed + user_model signals；
- 多轮需求一致性：story core + notebook 记录需求；
- 成本/资源记录：rating_snapshot / daily_report；
- 可回滚：policy + all-shadow。

#### 4. 文书 / 文档工作
- 长文档注入受控：max_recall_items / max_recall_chars / collab budget；
- 关键信息不丢：事实层（facts）+ 记忆检索；
- 格式稳定：Perspective Card / output discipline。

#### 5. 角色扮演
- 一致性：第一人称自传 + 关系阶段 + 矛盾公式；
- 边界安全：anti_prompt_injection / no_self_reveal / 不主动恋爱化；
- 自然流：natural_session / flow-split；
- 跨角色协作：notebook + story core。

### 前后对比（结合更新后的对话记录）

| 场景 | 使用前（无增强心智模型） | 使用后（增强心智模型） |
|---|---|---|
| 角色扮演 | 容易串人、前后矛盾、没记忆 | 同一角色跨会话稳定，记得之前经历，关系/边界可控 |
| 游戏/叙事 | 世界观容易漂移、剧情断档 | story core + notebook 保持世界观连续，角色防漂移 |
| 论文/研究 | 引用/证据容易丢、主线断裂 | 记忆检索 + 目标分层 + 证据可追溯，研究主线可回看 |
| 公司/产品网页 | 需求多轮后容易偏离 | 用户偏好记忆 + notebook 记录需求，偏离可检测 |
| 文书/文档 | 长文档上下文塞爆、关键信息丢 | 受控注入 + 事实层 + 格式稳定 |
| 多 agent 协作 | 各角色各写一套，容易冲突 | notebook + story core 共享世界核心，一致性提升 |

> 这些对比来自**更新后的对话记录**（DeepSeek 导出、AutoMM、马克斯/布兰奇、COC/TRPG、Obsidian 等）中观察到的工程/体验差异；
> 不代表“AI 真的理解和在乎”，心理效度仍需正式研究。

### 证据来源（本地，不随仓库公开原文）
```text
DeepSeek 导出语料（289 会话 / 2132 用户消息）
AutoMM 省赛工程记录
马克斯 / 布兰奇人格研究
COC / TRPG / 角色卡
Obsidian 学习强化库等
```

> 这些是**工程/体验层面的作用**，基于长期运行与大量下游记录；
> 不代表“AI 真的理解或在乎”；心理效度仍需正式研究。
> 详细边界见 `EFFECTS.md`。

## 快速开始

```bash
# 1. 解压/克隆仓库
cd harness-core-portable

# 2. 发布前离线自检（不依赖 Ollama / 私有卡，干净 clone 应通过）
python package_selfcheck.py

# 3. 根目录统一 launcher（自检，失败返回非 0；生产门控未满足时预期失败）
python harness.py audit

# 4. 看政策
python harness.py status

# 5. 内生审查（走 harness review）
python harness.py review run

# 或直接进入核心目录
cd harness-core
python harness.py status
python roleplay_memory_chat.py --help
```

> 可选：本地 Ollama（用于 embedding / LLM / 角色生成）；最小核心不需要 Ollama。

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
python package_selfcheck.py             # 离线/静态发布自检（干净 clone 应通过）
python release_verify.py                # 发布物 SHA-256 清单校验
python harness.py audit                 # 聚合自检（生产门控 fail-closed）
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
