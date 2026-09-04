# 给其他 Agent 的使用指南

> 目标：让另一个 agent（或人）**快速、安全、可回滚地使用这套 harness-core**。

## 0. 先读

```text
README.md
EFFECTS.md
MENTAL_MODEL_EFFECTS.md
NATURAL_DATA_GAP.md
```

## 1. 环境

```text
Python 3.13 + SQLite
可选：Ollama（本地模型 / 嵌入）
不要联网，不要上传数据
```

## 2. 入口

```bash
python harness.py audit          # 聚合自检（失败返回非 0）
python harness.py status         # 看 policy
python harness.py measure congruence --limit 200
python harness.py review run     # 内生心智审查
python harness.py notebook list --scope <scope>
python harness.py story get --namespace <ns>
```

## 3. 核心概念

| 概念 | 说明 |
|---|---|
| Scope | 一个角色/项目/任务域（如 `character:demo-alice`, `game:demo`） |
| Notebook | 每个 scope 的持久笔记本（auto/manual, 带版本） |
| Story Core | 多角色/多任务共享的世界/任务核心 |
| Perspective Card | 角色的高一致性人格卡（`perspective_card.py validate`） |
| Memory | 记忆库（`memory_store.py` / `facts.py`） |
| Gate | `production_gate.py`（fail-closed） |
| Review | `mind_review.py`（内生审查） |

## 4. 推荐工作流（对其他 agent）

```text
1. 先跑 `python harness.py audit`
2. 看 `NATURAL_DATA_GAP.md`，确认数据边界
3. 为每个角色/任务建 `notebook` + `story core`
4. 用 `perspective_card.py` 保证人格一致
5. 用 `natural_session` 积累自然流（不要用定向冒充）
6. 用 `measurement.py recall-pool` 看记忆检索
7. 用 `mind_review run` + `production_gate.py` 做自审
8. 永远可回滚（`all-shadow`）
```

## 5. 安全铁律

```text
- 不自动上传/联网
- 不把 PII / API key 写入笔记或人格
- 不把人设当作安全边界（安全在 harness）
- 自然流与定向评测分开
- gate fail-closed
- 不改静态人格/关系/权限，除非用户确认
```

## 6. 想贡献数据？

见 `NATURAL_DATA_GAP.md`。

---

> 一句话：**把它当成“一个可以被审计、可回滚、可自然生长的角色/记忆/任务系统”，而不是一个“需要你喂世界书的角色扮演前端”。**
