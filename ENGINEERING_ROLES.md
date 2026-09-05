# > 公共抽象版；本机完整案例不进入公共仓库。

# 工程角色体系（Engineering Roles）

> 本文档记录另一个方向：Harness 的角色体系不仅覆盖“谁懂什么”（知识型角色），还要覆盖 **谁负责规划、实现、测试、审查、发布、维护和恢复**（工程型角色）。
> 状态：**方向 / 未实现**，属于 v0.2+ 规划。

---

## 1. 知识型 vs 工程型

| 类型 | 主要产出 | 核心问题 |
|---|---|---|
| 知识型角色 | 解释、判断、知识候选 | 这个角色凭什么知道？ |
| 工程型角色 | 代码/文件/命令/测试/运行状态/artifact | 这个角色凭什么改？改了什么？怎么验证？如何回滚？ |

工程角色不能只是“会写代码的人格”。它应包含：

```text
工程职责
+ 项目知识
+ 工具能力
+ 工作目录
+ 可修改范围
+ 禁止范围
+ 验收命令
+ 证据要求
+ 交接协议
```

## 2. 两大主族 + 审查

| 主族 | 例子 |
|---|---|
| 知识型 | 本机知识管理员 A、本机知识管理员 B、法律/医学/历史专家、文献校勘者、世界观管理员 |
| 工程型 | 架构师、Python 工程师、数据工程师、测试工程师、发布工程师、安全工程师、可观测性工程师、UX 工程师、迁移工程师、Incident Responder |
| 审查型 | Adversarial Review profiles（Code / Data / Security / Release / Measurement / UX） |

两者不隔离。例如：

```text
本机知识管理员 B：负责经济理论
研究工程师：把资料索引进知识库
Adversarial Review：检查结论是否夸大
发布工程师：决定哪些聚合结果进入公共包
```

## 3. 工程角色按“职责”设计

```text
role_type = engineering
engineering_function = release
```

### 推荐第一批工程角色

| 工程角色 | 核心职责 | 默认权限 |
|---|---|---|
| Architect | 模块边界、接口、依赖、迁移设计 | 只读 + 提案 |
| Implementer | 按批准方案修改代码 | 沙盒写入 |
| Test Engineer | 编写/运行测试和复现失败 | 沙盒执行 |
| Data Engineer | schema、迁移、队列、数据质量 | 私有数据受限 |
| Release Engineer | manifest、clone/ZIP、版本 | 无自动 push |
| Security Engineer | 权限、输入、路径、泄漏审查 | 只读审查 |
| Observability Engineer | trace、token、日志、健康指标 | 只读 telemetry |
| UX Engineer | 新用户流程、HTML 控制台、可访问性 | UI 范围写入 |
| Incident Responder | 故障诊断、备份与恢复 | 紧急但需审批 |
| Documentation Engineer | 文档、示例、命令一致性 | 文档范围写入 |
| Integration Engineer | 本机知识管理员 A/本机知识管理员 B/Ollama 等桥接 | 适配器范围写入 |
| Measurement Engineer | 指标定义、评测、CI、失败样本 | 评测范围写入 |

## 4. Engineering Steward

对应 Knowledge Steward，工程角色是**工程资产管理员**：

```text
Engineering Steward / Artifact Steward / Runtime Steward
```

管理对象：repository、package、database schema、test suite、release artifact、runtime route、integration、dashboard、telemetry、backup、deployment profile。

示例：

```text
Release Engineer
 ├── steward: release-manifest.json
 ├── steward: release_verify.py
 ├── steward: package_selfcheck.py
 ├── steward: Git clone/ZIP acceptance
 └── contributor: README release instructions
```

## 5. 工程域

```text
engineering:architecture
engineering:runtime
engineering:memory
engineering:data-quality
engineering:measurement
engineering:release
engineering:security
engineering:observability
engineering:frontend
engineering:integration
engineering:documentation
engineering:incident-response
```

角色可绑定多个域，但要有优先级和范围。

## 6. 影响级别

```text
E0 Observe
E1 Diagnose
E2 Propose
E3 Sandbox Implement
E4 Approved Local Apply
E5 External/Production Impact
```

| 级别 | 允许 | 禁止 |
|---|---|---|
| E0 | 读公开代码、看脱敏状态、看测试结果 | 改文件、执行命令、读私有数据 |
| E1 | 只读检查、读日志、定位错误 | 改文件 |
| E2 | 生成 patch 预览、写设计文档、迁移计划 | 实际修改目标工作区 |
| E3 | 临时目录/独立 worktree 修改、运行测试、生成变更包 | 合并到主工作区 |
| E4 | 用户确认后应用 patch、创建备份、执行迁移 | 自动 push/发布/开 production |
| E5 | push / release / 生产 / 网络 / Autonomous | 当前保持禁用 |

> runtime policy 管“功能是否影响模型输出”；engineering impact 管“工程角色能否影响文件和环境”。两者分开记录。

## 7. 工程角色热插拔

切换工程角色时，切换的是整个工程工作上下文，不是 prompt。

```text
正在停用 UX Engineer
 ✓ 当前 UI 草稿已保存
 ✓ 未提交修改保持原样
 ✓ 没有后台命令仍在运行

正在激活 Release Engineer
 ✓ 工作目录：harness-core-portable-repo
 ✓ 责任域：release
 ✓ 已加载 manifest 和发布约束
 ✓ 当前工作区：dirty
 ✓ 本地分支领先 origin/main 8 commits
 ✓ 自动 push：禁止
 ✓ Production activation：禁止
```

铁律：工程角色切换不能隐式清理、覆盖或提交另一个角色留下的修改。

## 8. 工作区租约与 Worktree 隔离

### Workspace Lease

```json
{
  "lease_id": "lease_...",
  "role_id": "ux-engineer",
  "workspace": "worktree:dashboard-prototype",
  "allowed_paths": ["harness-core/dashboard/**", "docs/UX/**"],
  "read_only_paths": ["harness-core/runtime_policy.py"],
  "forbidden_paths": ["*.db", "production_approval.json", ".env"],
  "expires_at": "...",
  "actual_execution": false
}
```

### Worktree

```text
main working tree
├── worktree/ux-dashboard
├── worktree/release-alpha
├── worktree/vector-repair
└── worktree/integration-local-persona
```

每个任务记录：task_id、role_id、base_commit、worktree、allowed_paths、changed_files、tests、approval、merge_status。

## 9. 工程角色自己的日志 / 工作日志 / 日记 / 内省

| 类型 | 语义 |
|---|---|
| 工程日志 | 读取了哪些文件、运行了哪些命令、修改了哪些文件、测试返回码、artifact、是否访问网络 |
| 工程工作日志 | 目标 / 发现 / 变更 / 证据 |
| 工程日记 | 允许角色化表达，但应与证据分开 |
| 工程内省 | 结构化候选经验，需人工批准后转成规则/测试/checklist |

示例候选规则：

```text
候选规则：所有检查脚本在 FAIL 时必须返回非零。
来源：production_gate.py 旧行为、root audit 旧行为
反例：信息型报告命令可能允许 rc=0
批准后写入：docs/ENGINEERING_RULES.md + tests/test_fail_closed.py
```

## 10. Engineering Evidence Bundle

工程角色要说“完成”，必须提供证据包：

```json
{
  "task_id": "task_release_verify_zip",
  "role_id": "release-engineer",
  "base_commit": "...",
  "working_tree": "dirty",
  "changed_files": ["release_verify.py", "tests/test_release_verify.py"],
  "checks": [
    { "command": "python release_verify.py", "return_code": 0 },
    { "scenario": "tampered_file", "expected": "hash_mismatch", "observed": "hash_mismatch" }
  ],
  "unverified": ["GitHub Download ZIP was not fetched from remote"],
  "external_effects": [],
  "approval_required": true
}
```

控制台把“声称完成”和“已经验证”分开。

## 11. 角色间交接包

```text
Architect → Implementer：设计目标、接口约束、不变量、受影响文件、迁移计划、验收标准、禁止事项
Implementer → Test Engineer：base commit、patch、变更说明、已知风险、重点攻击路径
Test Engineer → Security/Adversarial Review：测试矩阵、未覆盖路径、失败样本、异常行为、权限变化
Security/Adversarial Review → Implementer：严重级别、复现步骤、证据、修复建议、是否阻断合并
Release Engineer → 用户：候选版本、manifest、clean clone、ZIP、已知限制、发布边界
```

## 12. Adversarial Review 工程专业化

```text
Adversarial Review-Code：异常是否被吞、返回码、portable path、部分写入、timeout fail-closed、并发一致性
Adversarial Review-Data：real/demo/smoke 混淆、derived 循环强化、schema 迁移可回滚、orphan/duplicate、删除是否生效
Adversarial Review-Security：API key、路径穿越、shell injection、dashboard bind、CORS、插件权限、私有导出
Adversarial Review-Release：manifest、Git/ZIP、tracked file equality、许可证、文档命令、公共包是否引用私有文件
Adversarial Review-Measurement：指标标签与实际 k、分母/排除项、A/B 口径、demo 冒充 real、内部 PASS 冒充认证
```

## 13. 典型工程角色方案摘要

| 角色 | 负责 | 注意 |
|---|---|---|
| Runtime Engineer | resolver、policy、scope、collaboration、provider routing、fail-closed | 检查路径展开、alias 统一 |
| Memory/Data Engineer | SQLite schema、memory lifecycle、vector queue、dedup、provenance、migration、backup | 诊断 9 条缺向量需先副本测试 |
| Persona Integration Engineer | Character Card 导入、HCP、本机知识管理员 A/本机知识管理员 B adapter、热插拔、legacy alias | 不判断内容正确性，只负责格式/边界/兼容 |
| Dashboard/UX Engineer | HTML 控制台、时间线、角色画廊、桥图、token 图、可访问性 | 不直接查询全部私有正文 |
| Observability Engineer | trace/span、token、latency、fallback、errors、report | 不默认保存完整 prompt、不记录密钥 |
| Release Engineer | manifest、selfcheck、clone/ZIP、版本、Release Notes | 不能仅凭角色权限自动 push |
| Recovery Engineer | 备份、恢复演练、SQLite integrity、rollback | 恢复前显示会覆盖什么 |

## 14. 工程角色知识分层

| 信息类型 | 例子 | 用途 |
|---|---|---|
| 项目事实 | 当前文件、commit、测试结果 | 直接判断当前状态 |
| 工程规范 | fail-closed、manifest 规则 | 约束实现 |
| 历史经验 | 曾发生 rc=0 on FAIL | 风险提示 |
| 角色日记 | “我认为此处最危险” | 低权重提示 |
| 外部知识 | Python/SQLite 文档 | 设计参考 |
| 推断 | “可能有竞态” | 待验证假设 |

工程角色尤其不能把旧工作日志当作当前仓库事实。每次执行前重新检查当前状态和 commit。

## 15. 资源隔离

工程角色除 scope isolation 外，还需要：

- filesystem isolation
- process isolation
- network isolation
- environment isolation
- credential isolation
- database copy isolation

默认：

```text
未知脚本 → 沙盒
真实数据库迁移 → 先复制
写入目标目录 → allowlist
网络 → deny
密钥 → 不进入角色上下文
外部进程 → 明确批准
```

> 角色 prompt 中说“我是安全工程师”不构成安全边界，真正边界必须由宿主执行。

## 16. 角色包增加工程能力声明

```json
{
  "persona_id": "memory-data-engineer",
  "role_type": "engineering",
  "responsibilities": ["memory_schema", "vector_queue", "data_quality"],
  "knowledge_bindings": [
    { "domain_id": "engineering:memory", "role": "steward" }
  ],
  "resource_requests": {
    "filesystem_read": ["harness-core/**"],
    "filesystem_write": ["worktrees/vector-repair/**"],
    "database_read": ["copy:memory.db"],
    "database_write": [],
    "process_execution": "sandbox_only",
    "network": false
  },
  "forbidden_actions": ["modify_live_database", "enable_autonomous_tasks", "push_remote"]
}
```

这只是请求能力，最终有效权限由宿主 policy 决定。

## 17. 用户友好表达

普通用户不需要看到 `E3 sandbox implement`，可以显示：

```text
这个角色现在可以：
 ✓ 查看项目文件
 ✓ 在临时副本中尝试修复
 ✓ 运行本地测试

这个角色现在不能：
 ✗ 修改你的正式数据
 ✗ 上传代码
 ✗ 连接外部网络
 ✗ 自动发布
```

## 18. 推荐第一批本机工程角色

1. **Core Runtime Engineer**：resolver / policy / scope / 入口一致性
2. **Memory & Data Engineer**：SQLite / vector queue / provenance / 迁移清理
3. **Persona Integration Engineer**：本机知识管理员 A / 本机知识管理员 B / HCP / 热插拔 / 知识域挂载
4. **UX & Observability Engineer**：HTML 控制台 / 时间线 / 桥图 / token 图 / 用户友好度
5. **Release & Audit Engineer**：公开包 / manifest / clone/ZIP / 文档一致性 / Adversarial Review

Security 和 Measurement 可以先作为 Release & Audit Engineer 的审查 profile。

## 19. 完整工程任务体验

```text
用户：把 本机知识管理员 A 终端接入统一角色启动器

1. Persona Integration Engineer：创建 integration manifest，不修改原知识库
2. Runtime Engineer：检查路径展开和 scope，设计 alias / healthcheck
3. UX Engineer：创建 本机知识管理员 A 状态卡
4. Test Engineer：临时配置测试存在/缺失路径、启动失败提示、不泄漏本机路径
5. Adversarial Review/Security Review：命令注入、私有文件暴露、权限扩大
6. Human Approval：决定是否替换桌面 .bat

最终状态卡：
实现状态：候选完成
 ✓ 原终端未被修改
 ✓ 新 integration manifest 已生成
 ✓ 路径已转为本地配置
 ✓ 私有知识未进入公开包
 ✓ Autonomous 保持关闭
未执行：
 - 替换桌面快捷方式
 - 提交仓库
 - 推送远端
```

## 20. 工程角色与“真实化”

工程角色的真实感不来自“像程序员一样抱怨 bug”，而来自：

```text
知道自己负责什么
承认自己没验证什么
保留失败记录
发现仓库变化后重新判断
能把经验转成测试
不把计划说成完成
能正确交接
遇到权限不足时停止
```

示例：

```text
我已经在临时副本中验证了正常和篡改路径，
但还没有从 GitHub 实际下载 ZIP，因此不能声称公开分发链已经验证完成。
```

## 21. 产品定位升级

加入工程角色后：

```text
本地优先的角色化知识与工程协作运行平台。
专业角色管理知识，工程角色管理代码、数据、测试和发布，
审查角色负责证据与边界；
所有角色通过统一权限、日志、版本和可视化桥进行协作。
```

核心结构：

```text
知识型角色     本机知识管理员 A / 本机知识管理员 B
工程型角色     Runtime / Memory / Integration / UX / Release
审查型角色     Adversarial Review Profiles
宿主治理层     Policy / Scope / Workspace Lease / Human Approval / Audit Log / Rollback
```

## 22. 建议路线

| 版本 | 主题 |
|---|---|
| v0.2 | 统一可视化：角色类型、职责卡、知识域地图、工程资产地图、Runtime Bridge、日志/日记/工程日志、Token |
| v0.3 | 角色化工程工作台：工程任务 manifest、worktree 隔离、路径 allowlist、diff、测试证据包、结构化 handoff、人工审批 |
| v0.4 | 跨角色协作：知识专家→工程需求→架构→实现→测试→Adversarial Review/Security→Release→用户批准 |

仍不启用：

```text
无人批准自动改正式环境
自动 push
自动发布
自动访问任意网络
自动读取密钥
Autonomous actual execution
L4/L5 actual impact
```

## 23. 最关键设计原则

> 知识角色的核心问题是：**这个角色凭什么知道？**
> 工程角色的核心问题是：**这个角色凭什么改？改了什么？怎么验证？如何回滚？**

两类角色都需要来源，但来源形式不同：

```text
知识角色：文献、语料、事件、证据、反证
工程角色：commit、文件、diff、命令、返回码、测试、artifact、审批
```

Harness 如果把这两种证据链统一展示，就会成为真正有特色的：

**角色化知识与工程责任系统。**
