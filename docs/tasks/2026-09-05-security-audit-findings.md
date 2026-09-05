---
title: 安全审计发现与处置记录
status: conducted
kind: security-audit
date: 2026-09-05
updated_at: 2026-09-05
owner_role: security-audit
public: true
contains_private_data: false
topics: [security, audit, history, git, mcp, memory, ci]
---

# 安全审计发现与处置记录

> 本记录针对“外部安全审计”提出的红旗项逐条核实。本文作为公共档案，**不包含**私人人格标识原文；涉及私人标识的规则与替换清单仅保存在本地 gitignore 目录，不提交公开库。

## 重要结论（先读）

- “审计通过”不是“不存在风险”的证明，只代表 **在被检查的 refs、规则覆盖范围和工具能力内未发现对应命中**。
- 历史重写已于维护窗口内执行；远程 main 已更新到清洗后的提交。此操作已获仓库所有者明确授权，后续不得在无授权情况下再次重写。
- 扫描器为 **fail-closed**：如果 git rev-list / grep 失败，会报告 `failed_scans > 0` 或 `ok=false`，**不会输出一张“零命中合格证”**。

## 1. `secret.txt` 历史提交

- `git log --all -- secret.txt` 找到 2 个 commit：
  - `1e910fe`（误加入）
  - `64a4ba7`（移除）
- 两个 commit 中 `secret.txt` 内容均为 **0 字节**。
- 结论：**没有真实密钥**。不需要轮换/清洗密钥。
- 但删除提交不会清除历史；本次仍按整改方案执行了 `git filter-repo` 历史清洗，以防未来出现“非空文件误提交”时无法恢复。

## 2. 私人人格内容曾进入公开库

- 早期提交中存在私人人格 scope / 本机路径标识（如私人人格名称、`feature:xxx` 角色名、local-persona 的 a/b 变体、本机绝对路径等元信息）。
- 这些是**可识别私人内容的元信息**，不属于真实对话正文/日记文本，但属于敏感边界信息。
- 处置：
  - 执行 `git filter-repo --replace-text`，将私人人格名与相关标识替换为 demo 占位名称。
  - 远程 main 已更新到清洗后的提交；标签同步更新。
  - 清洗后的 **private-identity 类命中为 0**；当前工作树边界扫描通过。
  - 注意：`windows_abs_path`（19 处，历史）与 `private_overlay`（1706 处，历史）属于**边界提示项**，不是私人身份标识；它们仍需要在未来文件规范中逐步收敛，不应被当作“已完全无痕”。

## 3. 记忆系统 + MCP 持久化注入面

- **记忆投毒风险**：长期记忆可被污染并长期召回。当前没有“召回前污染检测”机制。
- 建议后续增加：
  - 记忆来源 `source` 与 `provenance` 强制记录；
  - 召回时对高影响 scope 做来源可信度过滤；
  - MCP `memory_list` 只暴露自己授权 scope，不跨 scope 返回。
- **runtime context 进入 memory_list**：当前 `load_context()` 只返回 persona_id / mode_id / details / note，不包含路径/环境变量原始值。暴露面有限，但仍应审查 `details` 内容，避免后续塞入敏感路径。
- **adapter 权限 fail-closed**：`harness_core/adapter_gate.py` 已改为未配置 `HARNESS_MCP_ADAPTER_ID` 时默认拒绝；仅当显式设置 `HARNESS_ALLOW_UNCONFIGURED=1` 才放行（本地开发/兼容）。

## 4. CI 与发布脚本审查

- `.github/workflows/ci.yml`：
  - 使用 `pull_request`（不是 `pull_request_target`）
  - 没有 `GITHUB_TOKEN` 注入、没有 secrets
  - 只跑本地检查
  - 已增加 history 扫描：`secret-scan --history`、`boundary-check --history`
  - 已为 MCP 自检注入 `HARNESS_MCP_ADAPTER_ID=harness-core-mcp`
  - 结论：安全（但仍需保持“公共 CI 不做内容上传/网络回传”原则）
- `scripts/create-github-release.sh`：
  - 只要求 `gh auth status`
  - 不接受/不打印 token
  - 结论：安全

## 5. 工程信号

- 单人贡献、1 star、0 fork：按“不可信基线”处理，持续需要外部 review。
- `harness-core/` 与 `harness_core/` 双目录并存是结构混乱信号。短期用文档说明，长期应统一命名。

## 5.1 历史扫描量化结果（清洗后）

- `python harness.py secret-scan --history`：
  - `total_refs=178`，`scanned=178`，`failed=0`，`hits=0`
  - 说明：在 178 个 refs 与现有密钥规则覆盖范围内未发现命中；不等于证明不存在真实凭据。
- `python harness.py boundary-check --history`：
  - `private_identity_hits=0`（私人身份标识类：`local_persona_ref` + 本地加载的私人清单）
  - `failed_scans=0`
  - `counts`（边界提示项）：`windows_abs_path=20`、`private_overlay=1723`
  - 说明：`private_identity_hits=0` 只表示私人身份标识在清洗后的历史中未再检出；`windows_abs_path` / `private_overlay` 仍属于边界提示，需逐步收敛。

### 清洗前（历史事实记录）

- 在历史重写前，上述边界扫描曾在清洗后的替代清单上误计（因为 `git filter-repo --replace-text` 把扫描器源码中的私人名也替换成了中文占位符）。
- 已修复：公共扫描器不再包含具体私人名规则，改为通用规则 + 本地私有规则文件（`HARNESS_PRIVATE_IDENTIFIERS_FILE`）加载，私有清单不提交公开库。

## 5.2 已增强工具

- `secret-scan --history`：扫描全历史密钥形态，fail-closed。
- `boundary-check --history`：统计历史指示命中类型（不输出内容），fail-closed；区分“私人身份标识”与“边界提示项”。
- `adapter_gate.can()`：未配置 adapter 默认拒绝。
- `mcp_http_server`：仅允许 loopback 绑定；请求体大小限制（1 MiB）、请求超时（30s）、要求 `application/json`、校验顶层对象类型、非法 UTF-8 统一返回错误。
- CI：MCP extra 安装不再用 `||` 回退掩盖失败；未配置 adapter 时 MCP 工具默认拒绝。

## 6. 外部安全审计交接复核（F-01~F-09）

> 对应桌面交接文档《安全审计交接-本地源码与黄金路径》中的编号。这里只登记当前仓库状态，不复述私人标识。

| 编号 | 问题 | 当前状态 |
|---|---|---|
| F-01 | adapter 身份缺失默认放行 | ✅ 已修复：未配置 `HARNESS_MCP_ADAPTER_ID` 时拒绝；`HARNESS_ALLOW_UNCONFIGURED=1` 才放行 |
| F-02 | HTTP 默认 loopback 但未强制 | ✅ 已修复：非 loopback host 拒绝启动并返回退出码 2 |
| F-03 | HTTP 无请求体上限/超时/顶层类型检查 | ✅ 已修复：1 MiB 上限、30s 超时、`application/json`、顶层对象、非法 UTF-8 校验 |
| F-04 | synthetic trace 只是规格检查，不是真实黄金路径 | 🟡 已跑通现有系统真实链路（offline demo / 版本化记忆 / 确认门 / 归档回滚 / 候选人工审核）；但 evidence→candidate→memory 流水线与外部操作门未实现，见 `docs/tasks/2026-09-05-real-golden-path-trace.md` |
| F-05 | pyproject 把标准库声明为分发依赖 | ✅ 已修复：移除 `test = ["unittest"]` |
| F-06 | CI MCP 安装失败被核心回退掩盖 | ✅ 已修复：去掉 `||` 回退，MCP extra 安装失败会让 CI 失败 |
| F-07 | rev-list/grep 返回码未检查，失败可能输出零命中 | ✅ 已修复：secret-scan 与 boundary-check 均 fail-closed |
| F-08 | git grep 命中原文写入报告 | ✅ 已修复：只输出 ref/file/line/rule，不输出匹配原文 |
| F-09 | boundary-check 只取最后一个文件计数 | ✅ 已修复：逐行解析 `git grep -c` 并累加，且说明是匹配行数 |

### Gitleaks 命中分类

- 外部审计在 `release-manifest.json` 中报了 4 条 `generic-api-key`，文件内容是 SHA-256 文件哈希清单。
- 从字段语义看这些是哈希值，不是可用的 API key/secret；当前远程 `release-manifest.json` 仍保留同类哈希。
- 结论：判定为**哈希误报**，不要求 revoke/rotate；但记录其规则、路径、提交和分类即可。

## 7. 禁网 WSL 沙箱测试结果分类

> 这些是外部审计在禁网 WSL 副本中的执行记录。分类原则：工具未启动、环境拦截、无法复现都按失败/未验证记录，不写成通过，也不归为产品漏洞。

### 7.1 Bandit：`Permission denied`，退出码 126

- 事实：Bandit 未能启动，报 `Permission denied`，退出码 126。
- 分类：**工具未运行 / 环境权限阻塞**。
- 含义：不是“扫描通过”，也不是产品漏洞；不能据此声称“无 Bandit 问题”。
- 处置：未通过更换解释器或绕过沙箱来制造全绿；若后续要在该环境运行 Bandit，需按沙箱允许的授权机制处理，或明确记录为 blocked / unverified。

### 7.2 `memory_write_http_confirm`：`URLError: Operation not permitted`

- 失败点：`tests/test_user_experience_flows.UserExperienceFlowsTest.test_memory_write_http_confirm`
- 报错：`urllib.error.URLError: <urlopen error [Errno 1] Operation not permitted>`
- 原因：该测试在 `127.0.0.1` 起本地 HTTP 服务，然后用 `urllib.request.urlopen` 访问 `http://127.0.0.1:8777`。WSL 执行时处于**禁网沙箱**，网络/套接字 syscall 被拦截，因此连 loopback 的 `urlopen` 也被拒绝。
- 分类：**环境限制（禁网拦截 loopback socket）**，不是记忆写入逻辑错误。
- 佐证：在非禁网本地/CI 上该用例通过；仓库内已新增不依赖 socket 的 `tests/test_real_golden_path.py`（`memory write` 确认/undo/restore）作为替代回归证据。
- 处置：当前**不应解除禁网**来让该测试通过。若要覆盖该 HTTP 确认链路，应改成不依赖网络 syscall 的内部驱动，或让沙箱明确授权 loopback。

### 7.3 MCP stdio 测试（外部审计未完全分类）

- 外部审计曾报 `tests.test_mcp_server.MCPServerTest.test_initialize_notification_tools_list` 失败（只返回 initialize，未返回 tools/list）。
- 这是 stdio 时序/缓冲敏感问题，已重写为逐条写/逐条读；在本地与 CI 均通过（含 4 个矩阵 job）。
- 分类：**已修复的测试稳定性问题**，并非产品功能缺陷。

## 处置状态

| 项 | 状态 |
|---|---|
| secret.txt | ✅ 无真实密钥 |
| 私人人格历史标识 | ✅ 已执行历史重写；private-identity 类命中 0；边界提示项仍在 |
| 历史重写 | ✅ 已获授权并执行；后续重写需再获授权 |
| MCP memory_list 暴露面 | 🟡 当前暴露有限；需加 provenance 过滤 |
| 记忆投毒防护 | ❌ 未实现，需后续 |
| adapter 未配置权限 | ✅ fail-closed |
| mcp_http_server 绑定 | ✅ loopback-only + 限制 |
| CI workflow | ✅ 无风险 |
| release script | ✅ 无风险 |
| 双目录结构 | 🟡 需长期整理 |
