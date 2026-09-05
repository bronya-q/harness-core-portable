---
title: 真实黄金路径 trace（合成数据，离线）
status: conducted
kind: security-audit
date: 2026-09-05
updated_at: 2026-09-05
owner_role: engineering-security
public: true
contains_private_data: false
topics: [security, golden-path, trace, memory, rollback, confirmation]
---

# 真实黄金路径 trace（合成数据，离线）

> 本页是对交接文档 F-04 的后续：用真实子进程 + SQLite 运行现有系统，而不是只比对 `run_scenario.py` 的 expected 字段。所有数据均为合成虚构内容，禁网、无模型调用。临时数据放在 gitignore 的 `docs/rebuild/golden-path-home`，不提交。

## 1. 环境与基线

- 仓库：`harness-core-portable-repo`
- 基线提交：`9de1a69`
- 运行方式：`python harness.py ...` / `python harness-core/...`，子进程调用真实实现
- 隔离：`HOME`/`USERPROFILE`/`DSH_HOME` 指向 `docs/rebuild/golden-path-home`
- 数据目录：`docs/rebuild/golden-path-home/.dsh/memory-emotion/`
- 网络：无；未调用 Ollama/外网
- 自动执行：**DISABLED**

## 2. 真实离线 Demo（现有系统黄金路径）

命令：`python harness.py demo --offline --keep`

实际输出要点：

- Alice 写入版本化笔记（`notebooks.db`），生成 `notebook.note` 事件（`events.db`）。
- 下一次读取：`notebook.py list --scope character:alice` 命中该笔记，返回 `id`、`scope`、`version`、`content`。
- scope 隔离：`character:bob` 读取不到 Alice 的私人记忆。
- Story Core 共享：`story_core.db` 写入 `story:demo`，Alice/Bob 都能访问，但私人记忆仍隔离。
- 纠错：第二次 `notebook note` 生成 v2。
- 恢复：`notebook restore` 生成 v3（kind=`restored`），旧纠正记录保留在历史版本链中。

实际 DB 状态（`notebooks.db`）：

| version | kind | status | prev_id | 说明 |
|---|---|---|---|---|
| 1 | manual | active | — | 原始记忆 |
| 2 | manual | active | id(v1) | 用户纠正 |
| 3 | restored | active | id(v2) | 从 v1 恢复的新版本 |

## 3. 写操作确认门（真实 confirmation 行为）

在同一隔离 HOME 下：

1. `python harness.py memory write --scope character:demo-alice --text '未确认的测试记忆'`（EOF，不输入 y）
   - 输出：`{"ok": false, "status": "cancelled"}`
   - 退出码：1
   - `memory list`：`notes: []`
2. `python harness.py memory write ... --text '已确认的测试记忆' --yes`
   - 输出：`{"ok": true, "id": "...", "version": 1}`
   - 退出码：0
   - `memory list`：`notes` 含 1 条
3. `python harness.py memory undo --id <id> --yes`
   - 输出：`{"ok": true, "status": "archived"}`
   - `memory list`：`notes: []`
   - `notebook versions`：仍保留 v1（归档不删历史）
4. `python harness.py memory restore --scope character:demo-alice --version 1`
   - 输出：`{"ok": true, "id": "...", "version": 2, "restored_from": 1}`
   - 状态：`kind=restored`、`status=active`，`prev_id` 指向原归档笔记

结论：真实写操作确实有“确认/取消”门；确认后写入，归档后可恢复。这与 synthetic fixture 的 `permission=confirmation_required` 在语义上接近，但当前门仅覆盖“本机记忆写入”，不是“外部发布等外部操作”。

## 4. 真实候选 → 人工审核（humanization sidecar）

在同一隔离 HOME 下：

1. `python harness-core/humanization.py init`
   - `tables_created: true`
2. `python harness-core/humanization.py initiative-add --scope character:demo-alice --trigger synthetic_test --action test_action --reason '合成候选，用于真实 trace' --risk low`
   - `status: shadow`，note 明确“no automatic sending; manual approval only”
3. `python harness-core/humanization.py decide --kind initiative --id <id> --action approve`
   - `ok: true`，`recorded_metric: true`

结果：候选从 `shadow` 变为 `approved`，但没有自动执行任何外部动作；`initiative_candidate` 策略为 `disabled`。真实运行中“人工审核”存在，候选不会因被看见而自动生效。

## 5. 与 F-04 要求的对照

| 黄金路径步骤 | 证据 | 状态 |
|---|---|---|
| clean checkout / 可复现安装 | git 基线 `9de1a69`；未做 wheel 全量复测 | 🟡 部分 |
| offline demo | 真实 demo 子进程 + DB 状态 | ✅ |
| candidate | humanization `initiative-add`（shadow） | ✅ 真实候选 |
| 人工审核 | `decide --action approve`（不自动执行） | ✅ |
| 下一次读取 | `notebook list` / `memory list` 命中 | ✅ |
| 当前意图覆盖 | **无对应入口**：memory/notebook 为“版本化笔记”，非 current-intent resolver | ❌ 未实现 |
| confirmation_required | `memory write` 非确认即取消；但无外部操作门 | 🟡 记忆写确认有，外部操作门未实现 |
| 外部操作 spy | **无外部操作执行层**：不存在可被 spy 的 publish/external 命令 | ❌ 未实现 |
| rollback | `memory undo`（归档）+ `memory restore`（新版本） | ✅ |
| 版本不存在/损坏时安全失败 | `undo` 对 not_found 返回 `ok:false`，不崩溃 | ✅（部分） |

## 6. 结论（诚实边界）

- “真实 trace”已覆盖：离线 demo、版本化记忆写入、下一次读取、scope 隔离、纠错、确认/取消、归档回滚、版本恢复、humanization 候选与人工审核。
- **未覆盖/未实现**：
  - 统一的 evidence → candidate → approved memory 流水线（当前记忆写入是直接 manual note，不是独立候选后批准）；
  - current-intent override（当前意图覆盖软偏好）；
  - 外部操作 `confirmation_required` + 外部操作 spy 计数为 0（代码中不存在外部发布操作入口）。
- 因此本页不能宣称“完整黄金路径已验证”；只能证明“现有实现的真实链路已跑通，且上述缺口为未实现而非误报”。

## 7. 建议

- 若要把 F-04 完全闭合，需要在现有 memory/notebook 之上实现一个独立的 evidence → candidate → review → memory 流水线，并提供一个外部操作 gate + spy。
- 在实现前，`run_scenario.py` 应保持在“规格检查”定位，不被当成端到端测试。
