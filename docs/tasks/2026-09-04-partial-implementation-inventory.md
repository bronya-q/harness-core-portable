---
title: 部分实现清单（诚实盘点）
status: archived-paused
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: project-progress-review
public: true
contains_private_data: false
topics: [inventory, partial, gap, roadmap, review]
---

# 部分实现清单（诚实盘点）

> ⏸️ **施工暂停 / CONSTRUCTION PAUSED**
>
> 本清单作为**存档记录**保留。当前暂停批量功能推进，优先转为等待首次用户反馈、外部环境验证与后续授权。
> 之后如需恢复，应先核对 `docs/tasks/2026-09-04-alpha4-implementation-progress.md` 的最新状态。


---

## 给 Agent 用户与路过 Agent 的提示

本项目同样欢迎 **Agent 用户** 来读、来跑、来搭把手。

### 对 Agent 友好的约定

- 先读 `README.md` / `CONTRIBUTING.md` / `AGENTS.md`，再到 `docs/` 找任务设计。
- 项目保持**诚实边界**：`R1 / 实验性 / 未外部验证` 不会写成 `已验证`。
- 不要把“能跑通”当成“真人验证”或“心理效度已建立”。
- 公共仓库不包含真实用户数据、私有人格卡、模型权重或 API key。
- `Autonomous` 与 `L4/L5` 保持 disabled；看到“可执行”不等于“已授权自动执行”。

### 路过 Agent 可以搭把手的事

- 跑一次 MCP Inspector，记录版本/传输/结论；
- 在 Claude Code / Codex / Copilot 任一宿主里加载 `harness-core-mcp` 并回填结果；
- 做公共边界扫描（私人标识 / 绝对路径 / overlay 引用）；
- 补一条可复验的首次用户/首次 Agent 测试记录；
- 给 `docs/tasks/` 里的设计补“真实环境”一列。

> 哪怕只来一个 Agent 提交一条可复验记录，也比没人强。
> 祝看到这里的朋友们用 AI 许愿工程一次就成，DSH 版本更新兼容性依旧稳定。


> 结论先说：**这个项目几乎每个被提到的能力都只完成了一部分。**
> 下面不是“批评”，而是为了下一轮 alpha.4 能把有限的精力放到真正缺人的地方。

## 1. 角色与环境特色化（Situated Character）

| 功能 | 已完成 | 仍缺 |
|---|---|---|
| `situated-mode` schema / demo modes | ✅ 存在 | 没有完整“处境 → 关系 → 共同经历 → 当前状态 → 责任 → 表达”闭环 UX |
| `character mode list/switch/current` | ✅ CLI 基础 | 模式切换没有可视化/预览差异；没有角色间情境化示例 |
| 关系-情感状态机 | ✅ `emotion_state` + `rel get/set/update` 基础 | 没有用户可理解的“关系变化”界面，也没有共同经历→关系升级的完整流程 |
| 角色环境特色化 | 🟡 部分 | 情境化还是“状态位”，没有真正影响 prompt/输出策略的完整链路 |

## 2. 知识角色 / Knowledge Stewardship

| 功能 | 已完成 | 仍缺 |
|---|---|---|
| 方向文档 / schema / 示例 | ✅ | — |
| `knowledge list` / `sources` | ✅ | 静态列表 |
| `knowledge health` | ✅ R1 | 只查目录 + 权限；没有索引/依赖健康 |
| `knowledge mount` | ✅ R1 | 只是挂载登记，不访问正文 |
| `knowledge delegate` | ✅ R1 | 只做关键词匹配冒烟，不传知识内容 |
| 知识源真实挂载 / 检索 | ❌ | 未实现 |
| 角色间受控查询 / Adversarial Review 工作流 | ❌ | 未实现 |

## 3. 工程角色 / Workspace / Evidence

| 功能 | 已完成 | 仍缺 |
|---|---|---|
| `workspace worktree create/list/remove` | ✅ | — |
| `workspace run` | ✅ 基本命令约束 | 不是文件系统沙箱 |
| 完整沙箱 | ❌ | 未实现 |
| `evidence create/handoff` | ✅ 基础 | 没有可视化 evidence 网络；没有证据生命周期管理 |
| 工程角色体系 | 🟡 文档 + 部分命令 | 实际按不同工程角色做门控/权限的运行时少 |
| A/B / token 基线 | ✅ CLI 基础 | 没有结果可视化 |

## 4. 可视化

| 功能 | 已完成 | 仍缺 |
|---|---|---|
| 静态 Dashboard | ✅ | — |
| 运行桥彩色状态条 | ✅ R1（新加） | 无真实 span / model 推理延迟 |
| 知识域关系网格 | ✅ R1（新加） | 无真实访问/索引状态 |
| 向量队列 / Provider / 来源分组 | ✅ R1（新加） | 无历史趋势 |
| README 截图 / GIF | 🟡 合成绩效 | 不是真实 `dashboard build` 浏览器截图；GIF 非真实录制 |
| 模型推理 span / 成本曲线 | ❌ | 未接入 |
| A/B / Evidence / Workspace 可视化 | ❌ | 未做 |

## 5. 用户友好处理

| 功能 | 已完成 | 仍缺 |
|---|---|---|
| `privacy consent --status/--set` | ✅ R1 | 没有首次启动向导；未与 demo/start 流程整合 |
| 写操作预览 → 确认 → 写入 → 撤销 | ❌ | 未实现 |
| 高风险操作二次确认 | ❌ | 未实现 |
| 导出前预览包含内容 | ❌ | 未实现 |
| 错误提示 / 空态 / 可恢复提示 | 🟡 部分 | 大多是 JSON/文本，不总是面向普通用户 |
| 首次用户测试 | ❌ | 只有 protocol，没有真实用户结果 |
| README 真实截图 / GIF | 🟡 合成 | 不是真实录制 |

## 6. 生态 / MCP / 数据

| 功能 | 已完成 | 仍缺 |
|---|---|---|
| MCP server | ✅ R1 | Inspector（HTTP loopback）已通过；Registry / 真实宿主未做 |
| `harness_core` Python API | ✅ 基础 | 覆盖入口不全 |
| provider usage | ✅ roleplay provider_reported | 未全入口覆盖 |
| vector queue retry 语义 | ✅ R1 | 未做端到端持续监控面板 |
| n-gram fallback | 🟡 独立模块 | 未接入 `memory_store.search` 自动 fallback |
| 卡牌游戏 | ✅ 可玩最小版 | 固定牌组、无扩展/多人 |
| 构念字典 / measurement schema | ✅ 文档 | 无真实双标注 / 信效度研究 |

## 7. 当前测试 / 发布

- unittest：18 用例
- release_verify：201 entries
- package_selfcheck：通过
- alpha.3：Pre-release 已创建，外部 body errata 已同步
- alpha.4：设计文档已建，尚未 tag / Release

## 8. 建议 alpha.4 优先

按“外部证据 + 用户可见 + 可验证”排序：

1. **真实 Dashboard 截图 / 录制 GIF**（把合成图换成真图）
2. **首次启动同意向导**（把 `consent` 接入 `start`）
3. **写操作预览→确认→撤销** 的完整用户流程（哪怕只做 memory write）
4. **MCP Inspector 跑一次**（本地可做，外部证据）
5. **知识桥“真实只读访问”最小步**（打通 source 目录读取 + 授权校验）

> 不要在 alpha.4 试图一次补齐“所有”部分实现；那会把每个都做成半吊子。
> 挑 1–2 个闭环打通，比 10 个只有 R1 的入口更有可信度。
