---
title: GitHub tag v0.1.0-alpha.2（Pre-release 页面已创建）
status: deployed
kind: deployment-record
date: 2026-09-04
deployed_at: 2026-09-04
version: v0.1.0-alpha.2
source_commit: 3ac847f
target: github
deployed_by: bronya-q
public: true
contains_private_data: false
topics: [release, github, alpha]
---

# GitHub Tag v0.1.0-alpha.2 部署记录（Pre-release 页面已创建）

> 外部 GitHub Pre-release 页面已创建，版本可回读。此记录标记为 `deployed`。

## 1. 部署摘要

在主分支创建 annotated tag `v0.1.0-alpha.2` 并推送，随后已创建 GitHub Pre-release 页面。发布正文见 `docs/releases/v0.1.0-alpha.2.md`。

## 2. 用户可感知变化

- `python harness.py demo --offline`
- `start / doctor / inspect / data status`
- HTML 控制台
- memory/privacy/backup/feedback
- character/knowledge/workspace
- schema/event/usage

## 3. 部署目标

- GitHub main
- GitHub tag `v0.1.0-alpha.2`

## 4. 精确版本

- commit: `3ac847f`
- tag: `v0.1.0-alpha.2`
- release manifest count: 133

## 5. 涉及文件

新增/修改见对应 commit。

## 6. 执行步骤

```bash
git commit ...
git push origin main
git tag -a v0.1.0-alpha.2 ...
git push origin v0.1.0-alpha.2
```

## 7. 验证证据

| 检查 | 预期 | 实际 | rc | 结果 |
|---|---|---|---|---|
| release_verify | 0 | 0 | 0 | pass |
| package_selfcheck | 0 | 0 | 0 | pass |

## 8. 未验证项

- 第三方 clone + ZIP 实际下载尚未核验（本地 `git archive` 已模拟）
- alpha.3 Release 页面本次不涉及

## 9. 回滚方法

如果 Release 页面正文有误，优先编辑或删除 GitHub Release 对象；不要移动或删除已经公开的 tag。只有 tag 本身误指向错误 commit 且已评估下游影响时，才另行设计 tag 修复。创建 Release 页面不会改变 main，也不需要回退 main。

## 10. 后辈接手说明

- 确认 Release 页面是否已创建 Pre-release
- 如创建，需同步 README/release notes
