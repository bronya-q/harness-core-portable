# Herta / N.E.K.O. 源码级设计 → harness 升级方案

> 2026-09-01
> 原则：不新增重复轮子；尽量映射到现有模块；按风险分阶段。
> 参考：Herta PHILOSOPHY/源码、N.E.K.O. 本地源码。

---

## 0. 总览

```text
N.E.K.O. 事实记忆 + subject forget + persona rendering 分级
Herta 第一人称自传 + 叙事补全 + 自我-agent 分离 + 证据可检查
        ↓
harness 升级方向
```

---

## 1. 记忆层升级（最值得先做）

### 1.1 原子事实 + 去重
- **参考**：N.E.K.O. `FactStore`
- **现状**：memory_store 以条目/embedding 为主，无独立事实层。
- **方案**：
  1. 增加 `facts` 层（从对话/反思中抽取原子事实）；
  2. 去重：`SHA-256` + FTS/向量相似度；
  3. 保留 `evidence_id` 关联原条目。
- **映射**：`memory_store.py` / `mind_precipitate.py` 增加 `facts` 表。

### 1.2 subject forget（遗忘 + 墓碑）
- **参考**：N.E.K.O. `subject_forget_cutoff` / tombstone / generation / archive / restore
- **现状**：只有归档/删除，无“可审计遗忘”。
- **方案**：
  - 新增 `forget_tombstones`、`forget_cutoff`；
  - 遗忘前先沉淀到“该主体章节”；
  - 支持 archive/restore。
- **映射**：`memory_store.py` / `mind_precipitate.py`。

### 1.3 Persona 渲染受控
- **参考**：N.E.K.O. `rendering.py` protected/suppressed + token 上限
- **现状**：Perspective Card 是全量/无分级。
- **方案**：
  - card 条目加 `protected / suppressed / priority`；
  - 渲染限制 token；
  - 按 subject 分槽。
- **映射**：`perspective_card.py` / `roleplay_memory_chat.py` 的 card context。

---

## 2. 身份/信任升级（安全）

### 2.1 entity ← account 两层
- **参考**：N.E.K.O. `memory/identity.py`
- **现状**：H6 身份条目主要在 user:real / research:theory，未区分平台凭据。
- **方案**：
  - 增加 `account` 与 `entity` 的映射；
  - 权限授予 **credential**，不授予人；
  - 禁止基于昵称/共现猜测身份。
- **映射**：`user_model.py` / `humanization.py` / trust 治理文档。

---

## 3. 主动陪伴管线升级

### 3.1 candidate → decision → generation → delivery
- **参考**：N.E.K.O. `proactive_chat`
- **现状**：H5 initiative_candidate 已生产，但决策/投递链路不完整。
- **方案**：
  - candidate 记录 trigger/evidence；
  - decision 层（是否打扰、频率）；
  - delivery 层（渠道/去重）。
- **映射**：`humanization.py` initiative 相关 + `autonomous_tasks.py`（禁用态）。

---

## 4. 人格构建升级（深度/实验）

### 4.1 第一人称自传
- **参考**：Herta `HertaBio.txt`
- **方案**：
  - Perspective Card 增加 `autobiography`（第一人称）；
  - 跨会话累积，不重置。
- **映射**：`perspective_card.py` / H6。

### 4.2 叙事补全基底（实验）
- **参考**：Herta 用 completion 而非 chat
- **方案**：为本地 roleplay 增加一个实验性 `narrative-completion` 提示模式（不替换现有）。
- **映射**：`roleplay_memory_chat.py` 可选分支。

### 4.3 自我–agent 分离
- **参考**：Herta 板砖
- **方案**：H5/H9 定义“人格监督 + 无声后端执行”，后端不产生用户可见话语。
- **映射**：`humanization.py` H5 / `autonomous_tasks.py`。

---

## 5. 安全与证据

- **参考**：Herta “安全属于 harness”“证据可检查”
- **现状**：我们已有 governance + plugin_sandbox + policy。
- **方案**：
  - 显式写入“安全边界由 harness 决定，人设不决定”；
  - 所有关键操作保留原始证据（diffs/tool trace/logs）。

---

## 6. 分阶段推进

| 阶段 | 内容 | 风险 |
|---|---|---|
| P0 | 文档/设计落地（本方案） | 低 |
| P1 | memory facts + forget tombstone + persona rendering caps | 中 |
| P2 | entity←account 凭据权限 | 中高 |
| P3 | proactive chat 决策/投递 | 中 |
| P4 | 第一人称自传 / 叙事补全 / 自我-agent 分离 | 高（实验） |
| P5 | 安全/证据显式化 | 低 |

> 建议先做 P0 + P1 的低风险记忆/渲染部分；P4 实验化，不破坏现有 production。

---

## 7. 每阶段验收

- P1：`memory_store` 有 facts 去重指标；遗忘有 tombstone 可回溯；persona 渲染 token 受控。
- P2：身份表区分 account/entity；权限授予 credential。
- P3：proactive candidate 有 decision/delivery 记录。
- P4：实验模式可开关、可回滚，不改变默认角色扮演。
