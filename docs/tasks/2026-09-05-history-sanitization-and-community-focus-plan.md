---
title: 历史清理、安全处置与社区聚焦整改方案
status: designed
kind: remediation-plan
date: 2026-09-05
updated_at: 2026-09-05
owner_role: security-audit
source_commit: 2fe4fd6
target_version: post-alpha.4
public: true
contains_private_data: false
topics: [security, git-history, privacy, community, documentation, adoption]
---

# 历史清理、安全处置与社区聚焦整改方案

## 1. 触发原因

外部审阅指出了三个问题：

1. 删除 `secret.txt` 并加入 `.gitignore` 不会删除 Git 历史；
2. 已从当前树移除的私人人格标识仍可能存在于历史提交；
3. 项目提交、文档和 Topics 很多，外部使用与反馈接近空白。

批评的语气很重，但问题问得对：仓库不能用“目前没人看”代替安全处置，也不能用文档和提交数代替真实使用。

## 2. 已核对事实

核对范围：本地全部可达 refs、GitHub Repository API、fork/contributor API、当前文档与提交历史。检查时没有输出历史私人人格名称或正文。

| 项目 | 结果 | 状态 |
|---|---|---|
| 当前公开仓库 star | 1 | 外部 API 可回读；无法证明是谁点的 |
| fork | 0 | 外部 API 可回读 |
| contributor | 1 | `bronya-q`，174 contributions |
| 可达 commit | 174 | 本地 Git |
| GitHub Topics | 19 | 外部 API 可回读，不是“约 20”以外的实质反驳 |
| 顶层 Markdown | 25 个 | 本地 Git |
| 全仓 Markdown / Python | 85 / 129 个 | 本地 Git |
| `docs:` 前缀 commit | 44 / 174，约 25.3% | 不是提交的大多数，但文档入口过多的问题成立 |
| `secret.txt` 历史 blob | 唯一 blob 为 Git 空文件对象 `e69de29...`，大小 0 字节 | 没有密钥内容 |
| `.gitignore` | 当前包含 `secret.txt` | 只能防未来误跟踪，不能清历史 |
| 私人人格历史元信息 | 已确认存在过 scope、名称和本机路径标识 | 当前树移除不等于历史清除 |
| 私人对话/日记正文 | 本轮没有发现进入公开提交的证据 | 不能扩大成“已证明所有历史绝无私人内容” |

### 对 `secret.txt` 的准确判断

审阅者给出的处置原则正确：如果提交过真实 credential，应先撤销或轮换，再考虑清理历史。

本仓库的 `secret.txt` 是 0 字节空文件，当前没有可撤销的 credential。这里不应假装发生了真实密钥轮换，也不应把“文件已删除”写成“历史已清除”。真正需要认真处理的是文件名造成的安全红旗，以及历史中的私人人格元信息。

## 3. 为什么不能直接在当前工作区运行 filter-repo

历史重写会改变相关提交 SHA，并影响：

- `main` 与全部历史 tag；
- alpha.1 至 alpha.4 的冻结 commit；
- annotated tag object；
- Release 与部署记录中保存的旧 SHA；
- 旧 clone、缓存链接和可能存在的外部引用；
- commit/tag 签名（当前 tag 本就未签名）；
- 未知的用户 clone。

GitHub 官方文档还提示：旧 clone 可能把已删除内容重新推回，fork、PR refs 和缓存视图需要单独协调或联系 GitHub Support。历史重写必须在维护窗口中完成，不能作为普通小改动顺手 force-push。

因此本文件只批准调查与演练，不批准远端重写。真正 force-push、重打 tag、编辑 Release 前需要仓库所有者明确授权。

## 4. P0：历史清理方案

### 4.1 决策范围

建议清理两类内容：

1. 从所有 refs 移除 `secret.txt` 路径，消除误导和未来审计噪声；
2. 用私下维护的 replace-text 清单替换历史中的私人人格名称、scope 与绝对路径。

第二类清单不得提交到公开仓库。公开报告只记录类别、命中数量和清理结果。

### 4.2 重写前准备

- 暂停 main、tag 和 Release 写入；
- 确认 open PR 数量并关闭或合并；
- 导出 branches、tags、Release API 元数据和旧 SHA 映射；
- 创建加密、离线、只读的 bare bundle，仅用于事故回滚；
- 获取仓库 traffic/clone 数据；无权限时明确记为 unknown；
- 使用 fresh mirror clone，不在日常工作副本运行；
- 安装 `git-filter-repo >= 2.47`，需要支持 `--sensitive-data-removal`；
- 先在临时 remote 上完成一次演练。

### 4.3 演练命令形状

下面只描述命令形状，不包含私人替换词：

```bash
git clone --mirror <repository-url> cleanup.git
cd cleanup.git

git filter-repo \
  --sensitive-data-removal \
  --invert-paths \
  --path secret.txt \
  --replace-text /private/path/to/replacements.txt
```

实际执行前必须按所用版本核对 `git-filter-repo` 语义。不要把示例直接复制到生产仓库执行。

### 4.4 重写后验证

必须检查所有 branch/tag/ref，而非只看 `main`：

```text
[ ] secret.txt 不再出现在 rev-list/tree 历史
[ ] 私人人格标识 confidential patterns 全部 0 命中
[ ] public boundary patterns 0 命中
[ ] release_verify 通过
[ ] package_selfcheck 通过
[ ] 全量 unittest 通过
[ ] tag archive 可复现
[ ] Release notes 与新 tag target 一致
[ ] old SHA → new SHA 映射已保存
[ ] 新 clone 验证通过
```

历史文本扫描输出只能包含 pattern ID 和计数，不能把私人字符串重新写进日志或 CI artifact。

### 4.5 远端切换

获得明确授权后：

- 在公告过的维护窗口 force-push branches 和 tags；
- 对 alpha Release 逐个核对 tag target；
- 将旧 deployment record 标注为 pre-rewrite historical evidence；
- 新增 history-rewrite Deployment Record，保存新旧 SHA 映射、命令版本与验证结果；
- 通知所有已知 clone 使用者重新 clone，不要普通 pull 后 push；
- 如历史内容满足 GitHub 敏感数据处理条件，向 GitHub Support 请求清理缓存视图和内部 refs；
- 再次检查 forks。当前 API 显示 0，但执行时必须重查。

### 4.6 回滚

重写失败时只允许在缓存清理前恢复旧 remote。恢复旧历史会重新暴露已清理内容，因此不是常规回滚手段。

离线旧 bundle：

- 不上传；
- 不进入日常工作区；
- 不提供给模型或 CI；
- 完成验证与保留期限后安全删除。

## 5. P0：防止再次发生

### 提交前

- 本地 pre-commit/pre-push 运行 secret scan 与 public boundary scan；
- 增加高风险文件名规则：`.env`、`secret*`、credential/token/key 类名称；
- 私人人格名称清单只存本地安全位置，扫描只输出规则 ID；
- fixture 强制使用 synthetic provenance；
- public/private 数据根必须物理分离。

### CI 与 GitHub

- 当前树 secret scan；
- PR diff secret scan；
- 全历史定期扫描；
- GitHub Push Protection/Secret Scanning 可用时启用；
- 扫描失败不得通过新增文档豁免；
- 任何真实 credential 一经确认，先 revoke/rotate，再处理历史。

### Commit 信息

避免再写含混的安全 commit，例如“remove accidental secret”，却不说明它是 0 字节测试产物。安全修复 commit 应写清：

```text
what was exposed
whether it contained a credential
whether rotation was required
whether history was rewritten
what remains unverified
```

## 6. P1：停止用文档和提交数代替用户

### 6.1 收窄对外入口

保留现有文档内容，但降低顶层噪声：

- 顶层只保留 README、QUICKSTART、SECURITY、CONTRIBUTING、ROADMAP、LICENSE、NOTICE；
- 其他文档移入 `docs/concepts`、`docs/reference`、`docs/archive`；
- README 只保留一个新用户路径；
- 旧路径用短迁移说明或稳定链接承接，不静默删除内容；
- 状态数字由脚本生成，减少“docs: 宣布状态变化”的提交。

### 6.2 收窄 Topics

当前 19 个 Topics 太散。建议公开界面只保留 6 至 8 个能由代码和可运行路径支撑的词，例如：

```text
local-first-ai
agent-memory
long-term-memory
context-engineering
sqlite
mcp
humanization
coding-agent-memory
```

具体修改 GitHub Topics 属于外部写操作，需要单独授权。

### 6.3 一个黄金用户路径

暂停继续扩功能，把唯一主路径做实：

```text
clone/install
→ demo --offline
→ 查看 Dashboard
→ 写一条 synthetic memory candidate
→ 人工批准
→ 下一次请求展示实际读取 trace
→ 当前意图覆盖软偏好
→ 发布请求停在 confirmation_required
→ undo/rollback
```

验收不看“命令存在”，只看首次用户能否在无作者帮助下完成。

### 6.4 招募反馈

给审阅者和测试者一个明确请求，不再丢一组 URL：

```text
请完成 10 分钟黄金路径，并回答：
1. 你在哪一步不知道该做什么？
2. 哪个状态看起来像成功，实际没有成功？
3. 你能否看懂本轮给模型提供了哪些记忆？
4. 你是否误以为长期记忆等于操作授权？
```

记录：完成率、放弃点、耗时、错误、未经提示的理解。demo/simulate 不算真人反馈。

## 7. P1：工程优先级调整

在以下事项完成前，不再扩新人格维度或增加新概念文档：

1. 历史清理演练完成；
2. CI matrix 持续全绿；
3. clean clone 的黄金路径通过；
4. 至少 3 名外部测试者留下结构化反馈；
5. rawmem/memdsl synthetic fixture 获得语义核对；
6. 至少一个真实 coding-agent 宿主回填。

文档仍然需要，但文档必须跟着可执行对象走：代码、测试、命令、外部记录至少占其一。纯状态广播应合并进固定进度页。

## 8. 证据和声明边界

当前可以说：

- `secret.txt` 在全部可达 refs 中只有 0 字节 blob；
- 当前没有真实 credential 可轮换的证据；
- 私人人格元信息曾出现在 Git 历史；
- 当前树删除不等于历史删除；
- GitHub API 显示 1 star、0 fork、1 contributor、19 topics；
- 社区采用尚未建立。

当前不能说：

- star 一定是作者自己点的；
- 仓库从未被 clone；
- 私人人格历史已经清理；
- 所有缓存和外部 clone 都可控；
- 有文档、CI 或 Release 就代表有人实际使用。

## 9. 验收标准

### 安全

```text
[ ] confidential 历史扫描清单完成
[ ] fresh mirror 重写演练完成
[ ] 所有 refs 重扫 0 命中
[ ] remote rewrite 获得明确授权
[ ] Release/tag/部署记录迁移完成
[ ] known clone/fork/cache 处置完成或标 unknown
```

### 社区与产品

```text
[ ] Topics 收敛到 6–8 个
[ ] 顶层文档入口显著减少但内容不丢
[ ] 一个黄金路径可在 clean clone 运行
[ ] 至少 3 条真人反馈
[ ] 至少 1 条真实宿主记录
[ ] README 展示结果和限制，不展示提交数量当成成果
```

## 10. 后辈接手

1. 不要读取或公开 confidential replacement list；
2. 不要在当前工作副本直接运行 filter-repo；
3. 不要在未授权时 force-push、重打 tag 或编辑 Release；
4. `secret.txt` 是 0 字节事实，别虚构密钥轮换；
5. 私人人格元信息风险是真实的，不能用空文件结论掩盖；
6. 重写前后都要扫描全部 refs；
7. 旧 clone 可能重新污染远端，必须要求重新 clone；
8. 安全整改完成后写 Deployment Record；
9. 社区工作优先于继续加功能和概念；
10. Autonomous 与 L4/L5 actual-impact 继续 disabled。

## 11. 参考资料

- GitHub Docs, Removing sensitive data from a repository: <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository>
- GitHub Docs, Remediating a leaked secret: <https://docs.github.com/en/code-security/secret-scanning/working-with-secret-scanning-and-push-protection/remediating-a-leaked-secret>
- git-filter-repo: <https://github.com/newren/git-filter-repo>
