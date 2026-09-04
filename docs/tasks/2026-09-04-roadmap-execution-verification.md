---
title: ROADMAP.md 执行情况验证报告
status: verified
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: independent-roadmap-review
source_commit: 8a61230
target_version: v0.2-v0.5
public: true
contains_private_data: false
topics: [roadmap, audit, verification, evidence, release]
---

# ROADMAP.md 执行情况验证报告

## 1. 验证目标

本报告不依据 `ROADMAP.md` 的勾选数量计算完成度，而是核对每项声明是否具有下列证据：

```text
L0 文档声明
L1 工件存在（代码/schema/命令/模板）
L2 代表性路径可运行
L3 正常、失败、隔离、回滚路径经过可复现测试
L4 clean clone / Download ZIP / CI 或独立环境验证
L5 GitHub Release 或其他外部部署可回读
```

`✅ 已实现`最多只说明实现状态，不能自动推导为 L3–L5。静态 smoke check 也不等于生产就绪。

## 2. 验证对象和环境

- ROADMAP：`ROADMAP.md`
- 审计时 ROADMAP 行数：683（`wc -l` 在 Git Bash 中显示 682，文件查看器显示末行 683，源于结尾换行计数差异）
- ROADMAP SHA-256：`f24148d84fa3a111a82b2302b32bfded8cefe7e86a2c9a2ca77b7e44a7b52e06`
- 报告开始时基线：`aa8de72`
- 写报告前最新 HEAD：`8a61230`
- 远端：`origin/main`
- Python：本机 Python 3.13 环境
- 动态写入测试：临时 `DSH_HOME`，测试后删除
- clean clone：使用 `git clone --no-local` 到临时目录，测试后删除
- 外部状态：GitHub 公共 API，只读回读

没有读取私人语料、私人知识库正文、API key 或本机私人角色数据。

## 3. 总体结论

### 3.1 结论摘要

ROADMAP 已从想法目录进步为有大量真实工件的路线图；P1–P4 的许多基础 CLI 和 schema 确实存在并可运行。但是当前状态标记仍存在明显的**重复章节漂移、实现与验证混写、工具存在与治理闭环混写、Tag 与 GitHub Release 混写**。

本次不能给出一个可信的单一“完成百分比”，原因是：

- 46 个 `✅` 分布在相互重复的 DoD 和 Current Next 中；
- 一些顶层章节没有逐项状态；
- 同一功能在一处写未实现，另一处写已实现；
- 某些 `✅` 只证明命令存在，不证明默认路径、安全路径或失败路径完整；
- 不同版本工作提前落地，但版本 DoD 尚未完成。

因此本报告按能力域给出判定，而不使用误导性的总百分比。

### 3.2 能力域判定

| 能力域 | 判定 | 证据等级 | 摘要 |
|---|---|---:|---|
| 公共/本机分层 | 部分实现，存在公开残留 | L2 | resolver 已通用化，但公开文档/示例仍出现偏好型私人角色名称 |
| 离线体验与 clean clone | 已验证基础路径 | L4 | selfcheck 和离线 Demo 在临时 clone 中 rc=0 |
| 统一 role/event/token schema | 基础已实现 | L2 | 三类 schema 可由 CLI 列出并做 required-field 检查 |
| situated mode schema | 工件存在但未接入统一 schema CLI | L1/L2 | 文件与 mode CLI 存在，`schema list` 不显示它 |
| event / token usage 存储 | 已验证基础读写 | L2 | 临时 SQLite 写入、列表、汇总成功 |
| Dashboard | 已验证静态生成，部分数据为示意 | L2 | 静态 HTML/CSP/escape 存在；span 耗时是硬编码结构示意 |
| 用户控制 | 命令存在，完整同意 UX 未完成 | L1/L2 | memory/privacy/backup/feedback 入口存在；分项同意与预览流程未闭环 |
| HCP validate/preview | 基础可运行 | L2 | 正常目录通过，`../` ZIP 在 validate 阶段被拒绝 |
| HCP 安全安装 | 未闭环 | L1 | install 可绕过 validate，ZIP 使用 `extractall()`；威胁模型大部未覆盖 |
| 角色 activation/rollback | 部分实现 | L2 | 激活状态备份机制存在；首次激活无备份；失败注入和并发语义未验证 |
| Character Card / corpus draft | 原型可运行 | L2 | 预览和 corpus evidence/needs_review 可运行，格式语义仍需更严格验证 |
| Knowledge Stewardship | 多为 schema/展示基础 | L1 | 知识源实际挂载、健康检查、委派与受控角色查询未实现 |
| Workspace Lease | 元数据原型，不是 worktree 隔离 | L2 | create/check 可运行，但命令明确声明不执行真实文件系统隔离 |
| Evidence Bundle / handoff | 基础已实现 | L1/L2 | 生成代码存在；独立任务全链路和失败样本仍需测试 |
| Retriever A/B | 条件性实现 | L1/L2 | 代码支持 paired rows/failures/meta；公开 clean clone 无 gold 时不可完成评测 |
| Agent ecosystem bridge | 兼容矩阵原型 | L2 | `ecosystem status` 可运行；无 AGENTS/CLAUDE 模板、无 MCP、无品牌适配测试 |
| 数据迁移与恢复 | 大部未实现 | L0/L1 | schema version 字段存在，但强制校验、migration、compatibility window 未建立 |
| 测量学与首次用户研究 | 未验证 | L0/L1 | 路线与部分 recall 工程指标存在；首次用户数据、bootstrap CI、标注者信度未发现实现证据 |
| GitHub Release | 未部署 | L5 未满足 | 远端 tag 有 alpha.2，但 Releases API 返回空数组 |

## 4. 已通过的代表性验证

### 4.1 当前仓库静态发布检查

| 命令 | rc | 结果 |
|---|---:|---|
| `python package_selfcheck.py` | 0 | `ok: true`；release_verify/local_records/runtime_preflight 通过 |
| `python release_verify.py` | 0 | Git source，154 个清单条目，无 issues |
| `python harness.py demo --offline` | 0 | 6 步合成 Demo 成功，临时数据自动清理 |

注意：`package_selfcheck` 的模式名是 `package_static_smoke_check`；它不是生产安全或心理效度证明。

### 4.2 clean clone

临时 clean clone 中：

| 检查 | rc | 结果 |
|---|---:|---|
| `git status --short` | 0 | 干净 |
| `python package_selfcheck.py` | 0 | 通过 |
| `python harness.py demo --offline` | 0 | 通过 |

本轮未重新下载 GitHub Download ZIP，因此不能把此次验证扩大为“当前远端 ZIP 已重新验证”。

### 4.3 schema

| 命令 | rc | 结果 |
|---|---:|---|
| `schema list` | 0 | 列出 unified-role/event-envelope/token-usage |
| `schema validate --role unified-object-model.example.json` | 0 | required 字段无缺失 |

限制：`schema_commands.py` 只检查顶层 required 字段，不是完整 JSON Schema validator；`situated-mode.schema.json` 未注册到 `schema list`。

### 4.4 event 和 token usage

在隔离 `DSH_HOME` 中：

| 命令 | rc | 结果 |
|---|---:|---|
| `event add` | 0 | 写入合成 `user_correction` |
| `event list` | 0 | 回读成功，含 scope/content/provenance 基础字段 |
| `usage record` | 0 | 写入 actual/baseline/avoided |
| `usage summary` | 0 | 聚合为 10/20/10 |

限制：这是显式 CLI 记录，不证明所有真实 runtime/model 入口已自动采集 provider usage。

### 4.5 Dashboard

在隔离 `DSH_HOME` 中：

```text
python harness.py dashboard build
rc=0
has_private_data=false
```

代码证据：

- 使用 `html.escape`；
- CSP 设置 `script-src 'none'`；
- 不启动 HTTP 服务；
- 生成本地 HTML。

限制：

- `spans` 是硬编码名称与数值；
- 页面已标注“结构示意；真实耗时待采集”；
- 因此只能说“span 结构视图已实现”，不能说“真实 span 时间线 telemetry 已实现”。

### 4.6 合成 HCP 和角色工作台

| 检查 | rc | 结果 |
|---|---:|---|
| public 合成目录 validate | 0 | 无 issues |
| 含 `../escape.txt` 的 ZIP validate | 1 | 正确报告 `zip_path_traversal` |
| character preview | 0 | 只读显示 manifest |
| character install（目录） | 0 | 安装到隔离 DSH_HOME |
| character activate | 0 | 首次激活成功 |
| character rollback（首次激活后） | 1 | `no_backup`，符合当前实现语义 |
| Character Card preview | 0 | 产生 mapping preview |
| corpus build preview | 0 | 产生 evidence/confidence/needs_review 草稿 |
| invalid mode switch | 1 | `mode_not_found` |

限制：

- 本轮没有运行恶意 ZIP 的 install，因为 install 使用 `extractall()`，不能将不可信 ZIP 交给该路径；
- validate 不是 install 的强制前置；
- rollback 尚未做“已有 active → 切换 → 故障注入 → 恢复”的完整验证；
- Character Card 测试输入是通用 JSON，不是标准完整 V2 fixture；
- corpus draft 主要提取身份句和表达样本，尚不能证明生成“完整切身化角色”。

## 5. 需要下调或改写的 ROADMAP 声明

### 5.1 Current main release 状态过时

ROADMAP 第 35 行写：

```text
v0.1.0-alpha.2（next Pre-release）
```

实际：

- 远端存在 `v0.1.0-alpha.2` tag；
- GitHub Releases API 返回 `[]`；
- alpha.2 不是“下一个 tag”，也不是已发布 GitHub Release。

建议改为：

```text
Latest tagged baseline: v0.1.0-alpha.2
GitHub Release: not published
Current main: ahead of tagged baseline
```

### 5.2 工作区同步声明是快照，容易立刻失效

第 37 行写“当前工作区干净，与 origin/main 同步”。审计过程中仓库被并发提交，状态多次变化。这种陈述不应硬编码在长期 ROADMAP。

建议替换为可复现命令：

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
```

并在部署记录中保存一次性结果。

### 5.3 Runtime Bridge 自相矛盾

第 303 行写：

```text
未实现：交互式桥图、点击下钻、span 时间线
```

第 568–570 行却全部 `✅`。

实际判定：

- `<details>` 点击下钻：已实现基础；
- 运行桥静态结构：已实现；
- span 结构示意：已实现；
- 真实耗时采集：未实现。

应按粒度拆开，不要一个“span 时间线”在两处相反标记。

### 5.4 GitHub Issue 模板状态错误

第 389 行把 GitHub Issue 模板列为未完成。仓库实际存在：

```text
.github/ISSUE_TEMPLATE/bug-report.yaml
.github/ISSUE_TEMPLATE/memory-error.yaml
.github/ISSUE_TEMPLATE/privacy.yaml
```

应改为已实现基础模板；若缺 config、feature request 或 support 模板，应逐项列缺口。

### 5.5 “工程角色仅在 worktree 中实施”过度声明

第 492 行标 ✅。实际 `workspace check` 输出明确写：

```text
仅检查租约元数据；真正的文件系统隔离需宿主执行
```

代码创建的是 `~/.dsh/harness/workspaces/<name>/workspace.json`，不是 Git worktree，也没有强制命令运行目录。

建议改为：

```text
🚧 Workspace Lease 元数据和检查已实现；真实 Git worktree 创建、命令约束和隔离执行未实现
```

### 5.6 HCP “事务化 activation”需要降级为基础

第 577 行标 ✅，但第 149–160 行仍将完整事务状态机列为未完成。实际只有：

- 写 active 前备份旧 active；
- 写失败时复制备份；
- 手动 rollback 读取单一 `.bak`。

没有：

- 完整状态机持久化；
- preflight/activating/deactivating 状态；
- 锁与并发语义；
- crash recovery；
- failpoint 测试；
- 安装原子 rename。

建议写：

```text
🚧 activation backup/rollback 基础已实现；完整事务状态机和并发恢复未实现
```

### 5.7 HCP 安全验证不能等同安全安装

第 575 行可以保留“validate 命令基础已实现”，但不得推导出 v0.3 DoD 已满足。

高风险代码路径：

```python
with zipfile.ZipFile(src) as zf:
    zf.extractall(tmp)
```

`character install` 没有强制调用 `_validate_package`。此外威胁模型中的 symlink、ADS、压缩炸弹、文件数/大小、嵌套压缩、MIME、HTML/SVG、可执行脚本没有完整阻断证据。

### 5.8 “统一 schema”需明确覆盖范围

P1 三类 schema 确实存在，但：

- situated mode schema 未注册 CLI；
- validator 只查 required；
- `minimum_core_version` 未发现；
- package schema version 未强制校验；
- migration 未实现。

建议状态为“基础 schema 工件已实现，强校验与迁移未完成”。

### 5.9 Agent compatibility R1 证据不足

兼容矩阵和 `ecosystem status` 存在，但仓库中未找到：

```text
AGENTS.md
CLAUDE.md
MCP server/config
Codex/Claude/DeepSeek/Trae/ZCode 专用 fixture 或集成测试
```

建议：

- AGENTS.md-based：若仅项目理念，降 R0；若补真实模板和手工复现，可为 R1；
- CLAUDE hooks：当前应为 R0，直到存在 hook 模板/事件导入；
- OpenAI-compatible adapter：可保持 R1 原型，但“DeepSeek”应等待真实配置与测试；
- MCP/Trae/ZCode：R0 合理。

### 5.10 公共/私人边界仍未完全达到 P0 声明

P0 第 544 行写“将私人角色案例从公共文档抽象化”已完成，但定向扫描仍发现公开材料包含偏好型角色名称，例如：

- `README.md` 的本地案例与命令；
- `KNOWLEDGE_STEWARDSHIP.md` 的 alias；
- `RESEARCH.md` 的 scope 示例；
- 测量/审计脚本的私人名称 query。

这不一定表示发布了私人正文，但与“公共项目不出现私人角色名”的硬边界和 v0.2 DoD 不一致。

建议 P0 改为 🚧，逐项完成匿名化和通用 synthetic fixture 迁移。

## 6. 各版本 DoD 判定

### 6.1 v0.2：部分满足，不能判定完成

| DoD | 判定 | 说明 |
|---|---|---|
| 新用户 10 分钟内完成离线演示 | 工程路径通过，用户研究未做 | Demo rc=0，不等于首次用户验证 |
| 静态 HTML 不运行服务 | 通过 | 本地文件生成 |
| 动态正文 HTML escape | 代码基础通过 | 仍建议恶意 fixture 测试 |
| 角色/记忆/Story/Notebook 只读查看 | 部分 | 页面有投影，但角色数据路径与真实内容覆盖需测试 |
| Token 标 actual/estimated | 部分 | 估算区有说明，usage 面板仍需更完整来源展示 |
| public demo 无私人角色 | Demo 通过，仓库边界未通过 | 合成 Alice/Bob；公共材料仍有名称残留 |
| 公开 ZIP 隐私扫描 | 历史证据存在，本轮未重跑远端 ZIP | 不能扩大到当前 main |
| Autonomous/L4/L5 关闭 | 通过本轮观察 | 继续保持，不自动启用 |

### 6.2 v0.3：原型较多，DoD 未完成

已存在 validate、preview、activate、rollback、card mapping、corpus draft；但缺少完整包 schema 强校验、安全 install、完整事务状态机、并发语义和失败注入，因此不得宣布 v0.3 完成。

### 6.3 v0.4：功能骨架基本存在，证据强度不均

角色 A/B、检索器 A/B、baseline、evidence、handoff 代码存在。需要下调：

- “仅在 worktree 中实施”并未实现；
- demo/directed/real UI 分组未完成；
- 公开环境无 gold 的 UNAVAILABLE 是诚实边界，但应有完全合成的小型 A/B fixture；
- bootstrap CI、双人标注信度不在 v0.4 DoD 中完成。

### 6.4 v0.5：只有基础，不是完整生态桥

稳定 Python API 文件、OpenAI-compatible adapter 和兼容矩阵存在；权限 manifest、scope portability、secret redaction test、adapter disconnect test、迁移/弃用策略均未完成。当前只可称 v0.5 foundations/prototype。

## 7. 未发现充分实现证据的领域

下列 ROADMAP 方向没有找到足够代码或测试证据，应保持未实现/研究中：

- 首次运行分项同意；
- 关系追踪开关的完整数据流；
- derived diary stale → reflection recompute → injection block 的执行链；
- package `minimum_core_version` 强制；
- migration command / dry-run / rollback / compatibility window；
- 知识目录真实 mount 和健康检查；
- 知识桥委派和角色间受控查询；
- 真实 span timing；
- provider-reported token 自动采集覆盖所有入口；
- bootstrap CI；
- 双人标注 Cohen’s κ / Krippendorff’s α；
- 3–5 名首次用户可用性研究结果；
- MCP server；
- Codex/Claude Code/Trae/ZCode 的真实集成测试；
- GitHub Release 页面发布。

## 8. CLI UX 仍有明确缺口

```text
python harness.py --help
rc=1
unknown command: --help
```

虽然打印了 docstring，但这是公开入口 UX 缺陷。另有部分 group command 对未知子命令返回 0 或只打印帮助，需统一：

- `-h/--help` 返回 0；
- 未知命令返回非 0；
- 错误信息给出有效下一步；
- help 文档列出所有实际顶层命令。

## 9. 建议修复顺序

### P0：立即修正文档状态，不改代码冒充完成

1. 修正 alpha.2 tag / GitHub Release 的区分；
2. 删除 ROADMAP 的易腐“当前工作区同步”静态声明，改成命令；
3. 合并 Runtime Bridge 重复状态；
4. 把 Issue 模板标为已实现基础；
5. 将 worktree、transactional activation、public boundary 降为 🚧；
6. 所有 `AGENT_COMPATIBILITY.md` 路径改为 `docs/AGENT_COMPATIBILITY.md`。

### P1：安全优先

1. `character install` 强制 validate；
2. 禁止直接 `extractall()`，逐项验证后解压；
3. 增加文件数、展开大小、压缩比、symlink/ADS/嵌套压缩/脚本/MIME 检查；
4. 临时目录随机化，原子 rename；
5. malicious fixture regression tests；
6. activation failpoint/并发/crash recovery 测试。

### P2：真实状态一致性

1. situated mode 注册到 schema CLI；
2. 使用完整 JSON Schema validator 或明确“required-only”；
3. mode 切换实际接入 runtime policy 和所有入口；
4. workspace 创建真实 Git worktree，或把名称改成 metadata workspace；
5. provider/event/usage 自动链路测试；
6. span 用实际时间替换硬编码示意。

### P3：公共边界和 UX

1. 将公开私人角色名改为 generic synthetic examples；
2. 修复根/group `--help`；
3. 完成分项 consent、预览、撤销；
4. README/Dashboard 显示数据位置、清理和状态来源；
5. 执行 3–5 名首次用户测试。

### P4：测量和生态

1. synthetic paired A/B fixture；
2. bootstrap CI 和失败样本；
3. 标注者信度试验；
4. AGENTS.md / CLAUDE hook R1 模板；
5. adapter secret-redaction/disconnect/scope tests；
6. MCP 仍按 R0，直到真正实现。

### P5：外部部署

1. 决定是否发布 GitHub Pre-release；
2. tag、commit、manifest、Release asset 对齐；
3. GitHub API 回读 Release；
4. Download ZIP / source archive 复测；
5. 写 deployment record。

外部发布需要用户明确授权，不由审计任务自动执行。

## 10. ROADMAP 状态维护规则

后续每个条目建议使用：

```text
status: planned | implemented | verified | deployed
proof:
  artifact:
  command:
  expected_rc:
  fixture:
  verified_commit:
  verified_at:
limitations:
```

最低规则：

- 只有文件存在：`implemented`；
- 跑通正常路径：仍不一定是 `verified`；
- 正常+失败+隔离+回滚可复现：`verified`；
- GitHub/外部系统可回读：`deployed`；
- 示例 UI 必须写 `illustrative`；
- 本地自报数据不得升级为第三方验证；
- 同一能力只保留一个权威状态，其他章节引用它。

## 11. 未验证项

- 当前 GitHub Download ZIP；
- Windows 双击入口的全新机器体验；
- 所有 memory/privacy/backup 子命令；
- 实际 Ollama/provider 模型链路；
- 私人 overlay 的完整兼容性；
- 大型/恶意压缩包的安全资源限制；
- SQLite 中断恢复和 migration；
- 多进程/并发 session；
- 所有 Markdown 链接和 README 全命令逐条执行；
- 心理学信效度和用户人性化感知。

这些未验证项不能从本报告中的代表性通过项推导为已完成。

## 12. 后辈接手说明

1. 先读取本报告，再修改 `ROADMAP.md`；
2. 先修正状态措辞，不要为了让勾选好看而补假测试；
3. 安全优先处理 `character install` 的 ZIP 路径；
4. 不要把 `workspace.json` 称为真实 worktree 隔离；
5. 不要把固定 span 示意称为 telemetry；
6. 不要把远端 tag 称为 GitHub Release；
7. 任何公开私人角色匿名化都要保留通用能力，不删除产品意义；
8. 每个修复新增/更新 Task Design MD，部署后再写 Deployment Record；
9. 保持 `autonomous_tasks = disabled`，L4/L5 actual-impact 持续关闭；
10. 并发进程频繁提交，编辑前后都检查 HEAD/status。

## 13. 相关文件

- `ROADMAP.md`
- `README.md`
- `PUBLIC_CONTENT_BOUNDARY.md`
- `docs/AGENT_COMPATIBILITY.md`
- `docs/AGENT_COMPATIBILITY.json`
- `harness-core/harness.py`
- `harness-core/assets_commands.py`
- `harness-core/character_workbench.py`
- `harness-core/dashboard.py`
- `harness-core/schema_commands.py`
- `harness-core/event_commands.py`
- `harness-core/comparison_commands.py`
- `harness-core/runtime_resolver.py`
- `schemas/*.json`

## 14. 最终判定

```text
ROADMAP 方向：基本合理
基础工件：大量已存在
代表性正常路径：多项通过
失败/并发/安全闭环：明显不足
状态一致性：未通过
版本 DoD：v0.2-v0.5 均不能整体宣布完成
GitHub Release：未部署
生产就绪：否
心理效度：未建立
```

本报告的 `status: verified` 表示“本次审计过程已完成”，不表示 ROADMAP 中所有项目已验证完成。
