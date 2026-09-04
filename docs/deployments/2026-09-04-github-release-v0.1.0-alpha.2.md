---
title: GitHub release v0.1.0-alpha.2
status: deployed
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

# GitHub Release v0.1.0-alpha.2 部署记录

## 1. 部署摘要

在主分支创建 `v0.1.0-alpha.2` tag 并推送。

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

删除 tag 或回退 main 到上一提交。

## 10. 后辈接手说明

- 确认 Release 页面是否已创建 Pre-release
- 如创建，需同步 README/release notes
