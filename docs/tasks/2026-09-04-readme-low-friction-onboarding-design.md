---
title: README 低认知负担入口重构设计
status: implemented
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: documentation-and-ux
source_commit: b450db2
target_version: v0.2+
public: true
contains_private_data: false
topics: [readme, onboarding, usability, local-first, humanization]
---

# README 低认知负担入口重构设计

## 1. 一句话目标

不删除现有技术、证据和边界内容，在 README 顶部增加一条几乎无需学习的体验路径，让第一次访问者快速知道项目能解决什么、如何运行、会看到什么、数据是否上传以及下一步点哪里。

## 2. 用户问题

原 README 信息丰富，但首次访问者需要先理解“心智模型、Humanization、Gate、Notebook、Story Core”等术语，才能判断项目是否与自己有关。在注意力短、项目选择多的环境中，这会造成：

- 首屏不能立刻对应用户痛点；
- 安装、体验、审计和深入使用混在一起；
- 命令很多，用户不知道第一条该运行什么；
- 项目已有的记忆隔离、纠错、恢复和清理效果不够醒目；
- 角色方向容易被误解为口癖或提示词包装；
- 安全边界写在后文，用户在首屏仍不确定是否上传数据或自动执行。

## 3. 设计原则

### 3.1 把用户当成没有时间，而不是没有能力

“低认知负担”不是贬低用户，而是：

- 不要求用户先学术语；
- 每一步只给一个主动作；
- 先展示结果，再解释架构；
- 重要风险和数据去向在行动前说明；
- 高级用户仍可访问完整技术与证据内容。

### 3.2 不删除已有内容

本次采用“新增入口层、原内容下沉”的重构方式：

```text
用户收益句
→ 一条命令
→ 实际输出预览
→ 痛点与能力对应
→ 按用户目标分流
→ 人性化核心主张
→ 原有 Agent、Demo、技术、证据、命令和文档内容
```

原有内容允许移动、折叠、加索引或改标题，但不能在没有迁移表和人工复核时删除。

### 3.3 首屏声明必须可运行验证

首屏只展示实际离线 Demo 已产生的结果：

- 跨会话召回；
- scope 隔离；
- Story Core 共享但私人记忆不共享；
- 纠错与版本恢复；
- Autonomous disabled；
- network upload none；
- 临时数据自动清理。

不使用虚构截图，不声称正式心理效度，不把 planned adapter 写成已兼容。

## 4. 已实施的信息架构

README 顶部新增：

1. 用户收益句：“记得该记得的，隔离不该串的”；
2. 一分钟离线入口；
3. 实际 Demo 流程预览；
4. 自动执行、网络上传和数据清理结果；
5. ZIP、Windows 双击和命令行三种入口；
6. “你是不是正在烦这些事”痛点表；
7. “我现在该点哪里”用户分流表；
8. “角色不应该只是口癖包”的切身化主张；
9. 正确的 `docs/AGENT_COMPATIBILITY.md` 链接和兼容性免责声明。

## 5. 面向不同用户的单一路径

| 用户 | 首个动作 | 成功信号 |
|---|---|---|
| 只想看看 | `python harness.py demo --offline` | 看见 6 步演示和自动清理 |
| Windows 非技术用户 | 双击 `开始体验.bat` | 获得可理解入口和结果 |
| 可视化用户 | `python harness.py dashboard build` | 生成本地只读 HTML |
| 记忆用户 | `memory list` | 看见 scoped records |
| 角色用户 | 先跑 Demo | 理解隔离、共享和纠错后再装角色 |
| Coding Agent 用户 | `ecosystem status` | 看到 R0/R1/R2，而非模糊“支持” |
| 审计者 | `package_selfcheck.py` | 获得明确返回码 |
| 贡献者 | `CONTRIBUTING.md` | 找到测试、UX、安全和评测入口 |

## 6. 角色与人性化首屏表达

README 必须明确：

```text
处境 → 关系 → 共同经历 → 当前状态 → 责任与张力 → 可解释选择 → 表达
```

口癖只属于最后一层。首屏不宣称 AI 具有人类意识，而强调：

- 用户看得见角色使用了什么经历；
- 能理解角色为什么改变；
- 能质疑和纠正关系推断；
- 能撤销记忆和派生变化；
- 角色表达不能扩大系统权限。

## 7. 后续优化，不在本次冒充完成

### P1：真实截图或 GIF

- 录制离线 Demo；
- 展示 Dashboard 的上下文、事件和角色处境；
- 图片只使用合成数据；
- 添加替代文本；
- 检查图片元数据和隐私。

### P2：README 内容导航

- 将目录更新为包含新手入口；
- 增加“快速体验 / 深入使用 / 审计 / 贡献”四组导航；
- 对长命令清单提供按任务折叠视图，同时保留完整命令；
- 生成原段落到新位置的迁移表，证明无信息丢失。

### P3：用户可用性测试

请至少 5 名未接触项目的用户完成：

1. 说出项目解决的一个问题；
2. 找到第一条运行命令；
3. 判断是否需要 API key；
4. 判断 Demo 是否上传数据；
5. 找到纠正或删除记忆的命令；
6. 找到 Agent 兼容等级；
7. 找到数据与隐私说明。

记录：完成率、耗时、误解点、放弃位置和主观负担。样本小，只用于 UX 改进，不包装成普遍有效性结论。

### P4：语言与无障碍

- 中英文首屏保持同样低门槛；
- 命令可复制；
- 避免只依靠颜色传达状态；
- 表格在移动端仍有对应纯文本说明；
- 错误信息附下一步动作；
- 后续补 Social Preview 和短演示视频。

## 8. 内容保留验收

重构完成前应保存基线并检查：

- 原有所有二级标题均存在或出现在迁移表；
- 原有命令逐条保留，除非确认已失效并留下替代说明；
- 效果边界、本地证据限制、隐私、License 和致谢不被折叠到不可发现；
- README 链接指向真实存在的文件；
- 私人角色名称和本地记录若已有公开边界问题，单独整改并留文档，不能在本次重构中静默删除；
- README 中 planned、implemented、verified、deployed 使用准确。

## 9. 验证计划

### 自动检查

```bash
python harness.py demo --offline
python package_selfcheck.py
python release_verify.py
```

同时运行：

- Markdown 相对链接存在性检查；
- fenced code block 配对检查；
- README 中命令存在性与帮助输出检查；
- Git diff whitespace check；
- 私人绝对路径和秘密模式扫描。

### 人工检查

- GitHub 桌面和移动端渲染；
- Windows Download ZIP 路径；
- 首次用户是否在 10 秒内找到主动作；
- 首屏是否对 alpha 和数据边界诚实；
- 深度内容是否仍然可达。

## 10. 风险和缓解

| 风险 | 后果 | 缓解 |
|---|---|---|
| 首屏变长 | 用户仍需滚动 | 前 30 行集中主命令和结果；后续用截图压缩文字 |
| 新入口与旧 Demo 重复 | 维护成本增加 | 后续将旧段改为逐项检查，不删除检查信息 |
| 为吸引用户而夸大 | 损害 evidence-first 定位 | 所有首屏声明来自实际 Demo 或明确标 planned |
| 隐私保证措辞过强 | 用户误以为全项目绝不联网 | 限定到离线 Demo和默认行为，外部 provider 单独说明 |
| 非技术表达掩盖技术边界 | 高级用户找不到证据 | 保留原有详细章节和审计入口 |
| 并发修改覆盖 | 丢失其他 Agent 工作 | 每次编辑前重读 status 和目标段，避免整文件覆盖 |

## 11. 权限和安全

本次只修改 Markdown，不改变运行策略。继续保持：

```text
autonomous_tasks = disabled
L4/L5 actual-impact experiments = disabled
unknown/missing mode = fail closed
```

不读取或记录 API key，不加入私人语料、私人角色资产或本机绝对路径。

## 12. 后辈接手说明

1. 先查看 `git status` 和 README 最新首屏，项目存在并发修改；
2. 不要为了缩短 README 直接删除原章节；先建立段落迁移表；
3. 优先修复新入口与原“5 分钟”段落的重复；
4. 下一项高价值工作是真实合成数据截图/GIF，不是增加更多口号；
5. 所有命令必须实际运行，失败必须写返回码；
6. 改完更新本任务状态并新增部署记录；
7. 不得把用户研究结果夸大为心理效度；
8. 不得启用 Autonomous 或 L4/L5 actual-impact。

## 13. 相关文件

- `README.md`
- `QUICKSTART.md`
- `QUICKSTART.zh-CN.md`
- `CONTRIBUTING.md`
- `docs/AGENT_COMPATIBILITY.md`
- `docs/tasks/2026-09-04-topics-alignment-and-situated-character-design.md`
- `docs/TASKS_INDEX.md`

## 14. 变更记录

| 日期 | 变化 | 原因 |
|---|---|---|
| 2026-09-04 | 初版并实施首屏入口 | 降低首次理解和运行成本，同时保留全部已有深层内容 |
