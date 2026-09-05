---
title: Situated mode + README onboarding docs deployment
status: deployed
kind: deployment-record
date: 2026-09-04
deployed_at: 2026-09-04
version: main
source_commit: b2f8d02
target: github-main
deployed_by: bronya-q
public: true
contains_private_data: false
topics: [readme, mode, situated-character, onboarding]
---

# Situated mode + README onboarding 部署记录

## 1. 部署摘要

在 main 分支落地情境模式 schema/CLI、合成角色模式示例、README 用户首屏重构、后辈任务设计与索引。

## 2. 用户可感知变化

- `character mode list/switch/current`
- README 首屏“一分钟确认它有没有用”
- 角色不再只是口癖包，而强调处境、关系、共同经历

## 3. 部署目标

- GitHub main
- 非正式发布（未打新 tag）

## 4. 精确版本

- 最新 commit: `b2f8d02`
- release manifest count: 153

## 5. 涉及文件

见 commit `0cbccfe` / `0330351` / `3d58c6e` / `b2f8d02`。

## 6. 执行步骤

```bash
git commit ...
git push origin main
```

## 7. 验证证据

| 检查 | 预期 | 实际 | rc | 结果 |
|---|---|---|---|---|
| release_verify | 0 | 0 | 0 | pass |
| package_selfcheck | 0 | 0 | 0 | pass |

## 8. 未验证项

- 未打新 tag / 未创建 GitHub Pre-release
- 未做真实截图 / GIF
- 未做 5 人首次使用测试

## 9. 回滚方法

回退 main 到上一 commit 即可，无数据迁移。

## 10. 后辈接手说明

- 检查 `character mode` 是否可用
- README 首屏是否仍指向真实 Demo 输出
- 是否按计划补截图 / GIF / 首次用户测试
