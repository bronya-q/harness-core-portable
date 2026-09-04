# 公共内容边界与隐私策略（Public Content Boundary）

> 本文档记录公开 Harness 与本机私人系统之间应如何拆分的边界。
> 状态：**方向 / 部分已落地**，属于 v0.2+ 必须遵守的发布规则。

---

## 1. 一句话原则

```text
公共项目发布“能力和插槽”，本机环境保留“人格和偏好”；
人格可以调用公共能力，但公共能力不能依赖某个私人角色才能成立。
```

## 2. 公共核心 vs 本机覆盖层

```text
Harness Public Core
├── Persona Slot
├── Knowledge Steward Slot
├── Engineering Role Slot
├── Review Profile Slot
├── Tool Bridge Slot
└── Permission Host

Local Overlay
├── 私人角色 A
├── 私人角色 B
├── 私人审查别名
├── 私人知识库
├── 本机启动器
└── 私人日记与记忆
```

## 3. 公开示例角色

公开项目只提供中性、合成、功能等价的示例，不预装私人角色。

### 合成角色

- `demo-archivist`：整理虚构城镇档案、事件时间线、来源/版本
- `demo-risk-reviewer`：检查虚构活动计划的时间、预算、依赖风险
- `demo-builder`：维护合成 Python 示例项目，演示 worktree / patch / test evidence / handoff
- `demo-storykeeper`：维护完全原创的“雾港”世界设定，演示私人记忆与共享世界知识区别

这些角色必须明确标记：

```text
synthetic
fictional
public_demo
not_based_on_a_real_person
```

不要复刻本机综合人格 A、本机知识管理员 A、本机知识管理员 B 的独特表达、名字、口癖、背景或美术。

## 4. 四分离

```text
Persona      谁在表达
Capability   能进行哪种处理
Knowledge    可以读取哪些资料
Permission   宿主实际允许什么
```

示例：

```text
公共项目只发布 Capability：
  source-review
  argument-mapping
  risk-review

不发布：
  具体人格名称
  立场
  私人语料
  私人关系表达
  本机路径
  私人使用统计
```

## 5. 公共内容清单

### 可以被公共核心抽象

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

### 不进入公共默认包

```text
本机综合人格 A完整人格
本机知识管理员 A 完整人格
本机知识管理员 B 完整人格
本机 Adversarial Review 人格化命名与表达
私人日记、信件和关系
本机路径与启动器
私人知识库
未核验图片、语音和语料
私人使用统计（按名字）
```

## 6. 本机私有 Overlay

```text
~/.dsh/harness-local/
├── personas.local.json
├── knowledge-sources.local.json
├── integrations.local.json
├── review-profiles.local.json
└── character-packages/
```

示例：

```json
{
  "schema_version": 1,
  "personas": {
    "local-persona-001": {
      "display_name": "本机角色名称",
      "scope": "character:local-persona-001",
      "persona_source": "~/private-personas/persona.md",
      "knowledge_bindings": ["local:knowledge-source-001"],
      "visibility": "private_local"
    }
  }
}
```

公共仓库只提供示例文件，如 `personas.local.example.json`，且不得包含真实角色名、路径或真实内容。

## 7. 框架中立 ≠ 内容中立

公开声明：

```text
Harness Core 不内置特定政治、社会或个人立场角色。
用户可以在本地创建具有明确视角的角色；
系统负责标明其来源、权限、知识范围和解释身份。
```

系统应做到：

- 不预装个人偏好
- 不隐瞒来源
- 不把视角冒充事实
- 允许多个观点并列
- 允许用户禁用或删除

## 8. 方法型专家模板

不推荐：某政治理论专家、某意识形态代言角色、某现实人物人格。
推荐：

```text
literature-reviewer
source-verifier
argument-mapper
timeline-curator
citation-checker
data-quality-reviewer
```

这些角色只负责方法：

```text
找来源
区分事实与推断
比较观点
显示争议
检查引用
提出反例
```

## 9. 工程角色去人格化

公开工程角色是“职责配置 + 权限配置 + 验收配置 + 输出模板”，可以有轻微风格（简洁、谨慎、解释充分），但不能有：

```text
私人关系
思想立场
角色 IP
独特口癖
感情依赖
主人称呼
现实人物模仿
```

## 10. Adversarial Review 去品牌化

公共核心改用功能名：

```text
Adversarial Review
Counterexample Review
Red-Team Review
Claim Audit
Evidence Challenge
```

本机可保留本地别名：

```json
{
  "public_profile": "review:adversarial",
  "local_display_name": "Adversarial Review"
}
```

## 11. 角色包资格检查

### 公开包最低条件

```json
{
  "distribution": "public",
  "content_origin": "synthetic | user_authored | imported | mixed",
  "contains_private_memory": false,
  "contains_real_person_data": false,
  "contains_political_profile": false,
  "license_status": "verified"
}
```

```text
distribution=public
contains_private_memory=false
contains_real_person_data=false
license_status=verified
所有语料来源可说明
没有本机绝对路径
没有秘密字段
没有私人知识绑定
```

### 本机角色

```text
distribution=private_local
默认不能进入 release manifest、公开 snapshot、GitHub、public demo、默认角色列表或公共 telemetry。
```

## 12. 发布前扫描

```bash
python harness.py release scan-private-identifiers
```

检查：

```text
本机角色名
私有知识库名
本机绝对路径
本机用户名
私人 scope
本机启动器名称
私有语料目录
人物图片/音频
private_local manifest
```

本地 denylist 放 `~/.dsh/harness/private-identifiers.txt`，公开仓库只提供 `private-identifiers.example.txt`。

```bash
python harness.py character validate --package examples/demo-archivist --target public
```

## 13. Dashboard 公共演示模式 vs 本机个人模式

```text
Public Demo Mode
  只显示合成角色
  只使用 demo 数据
  隐藏本机集成

Local Personal Mode
  显示用户自己的角色和知识域
  页面只存在本机
  不进入 release artifact
```

顶部显示：

```text
LOCAL PERSONAL VIEW
Contains private local integrations
Do not publish screenshots without review
```

## 14. 日志 / 快照防止角色名外泄

本机 telemetry 记录逻辑 ID：

```text
persona_id=local_persona_01
```

公共 snapshot 只保留：

```text
persona_count
role_type
session_count
scope_isolation_result
```

不输出 `本机知识管理员 A sessions=...`、`本机知识管理员 B diary count=...` 之类的按名字聚合。

## 15. CREDITS 处理

- 只有一般性启发 → 概括性表述，不公开具体角色名和思想领域
- 有独特表达/schema/实现直接派生 → 不能靠重命名隐藏来源，需核验许可、署名或重写
- 原则：保护隐私 ≠ 掩盖需要披露的代码来源

## 16. Git 历史

- 一般产品定位/个人偏好问题：从当前版本移除，明确新架构不包含这些角色，不主动重写历史
- 严格隐私/法律风险：需重写历史、force-push、删除旧 tag/release、通知 clone 用户；必须单独决策，不能由工程角色自动执行

## 17. 公开角色分类命名

```text
role_type:
  companion
  storyteller
  knowledge_method
  engineering
  reviewer
  coordinator
```

推荐公开名字：

```text
demo-archivist / demo-storykeeper / demo-guide
source-verifier / citation-curator / argument-mapper / timeline-curator
runtime-engineer / memory-data-engineer / integration-engineer / ux-observability-engineer / release-auditor
risk-reviewer / security-reviewer / measurement-reviewer / adversarial-reviewer
```

## 18. 建议立即整改

| 优先级 | 内容 |
|---|---|
| P0 | 公共代码去私有角色路由：`runtime_resolver.py` / `manifest.json` / `generate_manifest.py` / README / SKILL / CREDITS / RESARCH / PRE_MODEL_BASELINE；`git grep -i -E "local-persona|local-persona|local-persona|..."` 在不需 attribution 的公共运行代码中应为零 |
| P1 | 建立本机 overlay：`personas.local.json` / `knowledge-sources.local.json` / `integrations.local.json` / `private-identifiers.txt`，全部加入 `.gitignore` |
| P2 | 加入公共发布扫描：private identifier / absolute path / private-local manifest / asset/license / tracked file / ZIP |
| P3 | 替换公开示例为全新合成角色 |
| P4 | 本机适配器保留在桌面，调用本机 overlay，不让公共 core 反向硬编码认识它们 |

## 19. 最终原则

每个准备进入公共仓库的角色、语料、知识源和示例，都问六个问题：

```text
1. 是否基于真实人物或私人关系？
2. 是否代表用户明确的思想或价值偏好？
3. 原始语料是否允许公开？
4. 是否包含本机路径、私人记忆或使用统计？
5. 是否可以被完全合成、功能等价的示例替代？
6. 删除角色名称后，是否仍有独特内容需要署名或获得许可？
```

前四项任意一项为“是”，默认：

```text
private_local
不能进入公共默认包。
```

---

> 结论：本机知识管理员 A、本机知识管理员 B、本机综合人格 A以及本机 Adversarial Review 命名可以继续作为私人系统存在。
> 公共 Harness 只吸收它们验证过的通用能力：角色专属知识域、方法型专家能力、风险审查、来源验证、工程职责、角色热插拔、跨角色委派、日志/日记/内省、权限与回滚。
> 不能吸收具体人格名称、思想立场、私人语料、独特口癖、关系表达、本机目录、私人使用统计、未核验资产。
