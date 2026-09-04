---
title: GitHub tag v0.1.0-alpha.2（Release 页面待创建）
status: implemented
kind: deployment-record
date: 2026-09-04
deployed_at: 2026-09-04
version: v0.1.0-alpha.2
source_commit: d7f7de7
target: github
deployed_by: bronya-q
public: true
contains_private_data: false
topics: [release, github, alpha]
---

# GitHub Tag v0.1.0-alpha.2 部署记录（Release 页面待创建）

> 本记录早期标题使用了“GitHub Release”，但实际只完成 main 与 annotated tag 推送。GitHub Releases API 仍为空，因此状态修正为 `implemented`；只有 Release 页面可回读后才能标为 `deployed`。

## 1. 部署摘要

在主分支创建 annotated tag `v0.1.0-alpha.2` 并推送。尚未创建 GitHub Pre-release 对象。待发布正文见 `docs/releases/v0.1.0-alpha.2.md`。

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

- commit: `d7f7de7`
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

- GitHub Pre-release 页面尚未在 UI 创建
- 第三方 clone + ZIP 实际下载尚未核验（本地 `git archive` 已模拟）

## 9. 回滚方法

如果 Release 页面正文有误，优先编辑或删除 GitHub Release 对象；不要移动或删除已经公开的 tag。只有 tag 本身误指向错误 commit 且已评估下游影响时，才另行设计 tag 修复。创建 Release 页面不会改变 main，也不需要回退 main。

## 10. 后辈接手说明

- 确认 Release 页面是否已创建 Pre-release
- 如创建，需同步 README/release notes
