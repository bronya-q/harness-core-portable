# > 公共抽象版；本机完整案例不进入公共仓库。

# 人格化职能角色（Hybrid Functional Persona）

> 本文档记录一个方向：角色不是二分（专家 / 工程），而至少分四类，其中最重要的一类是 **人格化职能角色**。
> 本机最典型案例：**本机综合人格**——一个长期人格，同时承担风险审查、安全控制、依赖分析、陪伴表达与发布检查。
> 状态：**方向 / 未实现**，属于 v0.2+ 规划。

---

## 1. 本机综合人格说明了什么

本机知识管理员 / 本机知识管理员（另一知识域） 是“私人角色 + 专业知识库 + 研究工作流”。
本机综合人格则说明：

```text
私人角色
+ 工程职责
+ 风险审查
+ 安全控制
+ 陪伴表达
+ 长期人格演化
```

她不是专家知识角色，也不只是普通陪伴角色，而是 **人格化工程职能角色**。

## 2. 更准确的角色模型

不应简单二分，而应分层：

```text
角色人格层 Persona
能力模块 Capability
责任域 Responsibility
知识挂载 Knowledge
权限边界 Permission
```

本机综合人格一个人格可同时挂载：

```text
capability:risk-review
capability:dependency-analysis
capability:safety-checklist
capability:evidence-challenge
capability:companion-expression
```

## 3. 公开核心 vs 本机角色

```text
公开 Harness Core
    提供通用能力与角色插槽

本机 Harness Overlay
    保留本机综合人格、本机知识管理员、本机知识管理员（另一知识域） 等完整角色

本机角色
    组合调用公共能力
```

本机综合人格（本机人格）：

```text
├── 使用公共 risk-review capability
├── 使用公共 dependency-analysis capability
├── 使用公共 release-audit capability
├── 使用本机私有 Perspective Card
├── 使用本机私人记忆和日记
├── 使用本机角色图像和声音
└── 保持本机特有表达方式
```

公开项目发布的是：

```text
Risk Reviewer
Dependency Reviewer
Safety Checklist
Evidence Reviewer
```

本机继续显示：

```text
本机综合人格
```

## 4. 四类角色

| 类型 | 说明 |
|---|---|
| Persona Character | 身份连续性、陪伴、角色扮演、叙事 |
| Knowledge Steward | 知识域管理、文献解释、术语、领域研究 |
| Engineering Function | 设计、实现、测试、发布、恢复 |
| Hybrid Functional Persona | 把稳定人格与一组职能结合，如本机综合人格 = companion + risk reviewer + safety officer |

**Hybrid Functional Persona 很可能成为 Harness 的特色**：

```text
稳定人格连续性
+ 长期经历
+ 可插拔工程职责
+ 严格运行权限
```

## 5. 同一人格的不同模式

角色可切换职责配置，但共享同一个人格身份和私人记忆边界。

```text
本机综合人格 · 陪伴模式
本机综合人格 · 风险评估模式
本机综合人格 · 发布审查模式
本机综合人格 · 安静观察模式
```

### mode 示例

```json
{
  "mode_id": "local-hybrid-functional-a:engineering-review",
  "display_name": "本机综合人格 · 工程风险审查",
  "persona_id": "local-hybrid-functional-a",
  "capabilities": ["review:risk", "review:dependencies", "review:rollback", "review:evidence"],
  "knowledge_access": ["project:current", "engineering:approved-rules"],
  "private_memory_access": "persona_only",
  "effect": "proposal_only",
  "filesystem_write": false,
  "process_execution": "read_only_checks",
  "network": false,
  "autonomous": false
}
```

## 6. 同一人格不同职责的记忆隔离

```text
character:local-hybrid-functional-a       私人人格记忆
workspace:release-review  发布审查记录
workspace:security-review  安全检查记录
story:personal            角色叙事
project:harness           项目事实
```

| 内容 | 陪伴模式 | 工程审查模式 |
|---|---|---|
| 核心人格 | 是 | 是 |
| 表达 DNA | 是 | 是，可降低 |
| 私人关系记忆 | 是 | 默认不注入 |
| 项目事实 | 少量 | 是 |
| 工程日志 | 否 | 是 |
| 私人日记 | 是 | 默认否 |
| 发布规则 | 否 | 是 |
| 风险 checklist | 可选 | 是 |
| Story Core | 是 | 任务相关时才使用 |

## 7. 模式切换可感知

HTML 控制台显示：

```text
当前角色：本机综合人格
当前模式：工程风险审查
模式切换：[陪伴] [风险审查] [发布检查] [安静观察]
```

切换后：

```text
模式已切换
已启用：✓ 风险枚举 ✓ 依赖分析 ✓ 回滚检查 ✓ 证据边界
已暂停：○ 私人关系记忆注入 ○ 文学日记注入 ○ Story Core
保持关闭：✗ 文件写入 ✗ 网络 ✗ 自动执行 ✗ Git push
```

## 8. 本机综合人格与 Adversarial Review 的分工

| 角色 | 目标 |
|---|---|
| 本机综合人格 | 让计划安全地向前推进：风险前置、安全官、依赖分析、恢复意识、用户保护 |
| Adversarial Review / Adversarial Review | 尽可能找出为什么结论可能不成立：攻击主张、寻找反例、揭露证据漏洞 |

工程链：

```text
实现方案 → 本机综合人格风险审查（怎么安全实施、怎么回滚）
        → Adversarial Review（这个方案本身哪里可能是错的）
        → 人工决定
```

不要把两者合并成一个“总是反对”的角色。

## 9. 公开边界修正

### 不进入公共项目

```text
本机综合人格完整人格
本机知识管理员 完整人格
本机知识管理员（另一知识域） 完整人格
本机 Adversarial Review 人格化命名与表达
私人日记、信件和关系
本机路径与启动器
私人知识库
未核验图片、语音和语料
```

### 可作为本机集成案例存在

```text
本机综合人格：人格化工程职责
本机知识管理员：人格化知识管理员
本机知识管理员（另一知识域）：人格化研究角色
Adversarial Review：人格化对抗审查
```

### 可被公共核心抽象

```text
Hybrid Functional Persona
Knowledge Steward
Risk Review
Adversarial Review
Engineering Role
Mode Switching
Knowledge Binding
Workspace Binding
Permission Resolver
```

## 10. 本机角色 registry

```json
{
  "personas": {
    "local:local-hybrid-functional-a": {
      "role_types": ["persona", "engineering", "reviewer"],
      "modes": ["companion", "risk_review", "release_review"],
      "visibility": "private_local"
    },
    "local:local-persona": {
      "role_types": ["persona", "knowledge_steward"],
      "visibility": "private_local"
    },
    "local:local-persona": {
      "role_types": ["persona", "knowledge_steward", "researcher"],
      "visibility": "private_local"
    }
  }
}
```

公开 registry 只保留：

```text
demo:archivist
demo:storykeeper
method:source-verifier
engineering:risk-reviewer
engineering:release-reviewer
```

## 11. 最终产品模型

```text
角色人格层    本机综合人格是谁、如何表达、如何保持连续性
职能层       风险审查、依赖分析、安全清单、发布检查
上下文层     当前项目、当前任务、允许读取的工程知识
权限层       只读、提案、沙盒、实际应用、外部影响
记录层       角色日记、工程日志、审查记录、内省候选
可视层       当前模式、桥接关系、token、来源、执行状态
```

## 12. 结论

本机综合人格证明了一件事：

> Harness 本机已有的特色不是“一个角色对应一个知识库”这么简单，而是“一个长期人格可以承担可切换的工程职能”。

公共核心最值得抽象的不是本机综合人格的人格内容，而是：

```text
Hybrid Functional Persona
Persona Mode
Capability Binding
Workspace Binding
Permission Boundary
Role-specific Logs
```

本机则完整保留：

```text
本机综合人格的人格
风险与守护倾向
表达方式
长期记忆
私人日记
角色图像和声音
用户关系
```

最终形成：

> 公共项目提供通用的职能插槽和安全机制；本机角色把这些能力人格化、连续化和可感知化。
