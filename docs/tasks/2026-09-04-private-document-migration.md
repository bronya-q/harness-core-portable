---
title: 私人案例文档迁移设计
status: designed
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: public-boundary-review
public: true
contains_private_data: false
topics: [private-case, migration, public-boundary, gitignore, docs]
---

# 私人案例文档迁移设计

## 1. 问题

公开仓库仍存在少量文档以“本机私人角色”为例，例如：

- `HYBRID_FUNCTIONAL_PERSONA.md`
- `ENGINEERING_ROLES.md`

这些文档本身是方法论，但示例名字/场景仍指向本机私人角色。

## 2. 迁移原则

- 公共仓库只保留**方法 / 职责 / 边界**，不保留“某个特定本机人格”的完整案例。
- 本机完整案例移动到 `~/.dsh/harness-local/docs/`（或本地 overlay）。
- `.gitignore` 已加入：

```text
docs/_private/
harness-local-docs/
HYBRID_FUNCTIONAL_PERSONA.local.md
ENGINEERING_ROLES.local.md
```

## 3. 迁移步骤

1. 把 `HYBRID_FUNCTIONAL_PERSONA.md` / `ENGINEERING_ROLES.md` 中的“具体人名/口癖/私人路径”替换为公共占位：
   - `本机角色 A`
   - `本机知识管理员 A`
   - `本机知识管理员 B`
2. 在文档标题处注明：**公共抽象版；本机完整案例不进入公共仓库**。
3. 本机完整版如有需要，保存到 `~/.dsh/harness-local/docs/`。
4. 运行 `python harness.py secret-scan` 和 `python harness.py dashboard build` 查看公共边界。

## 4. 当前状态

- `.gitignore` 已加入本地 overlay 文档条目。
- 迁移设计已存档；具体替换仍需人工逐段确认（涉及大量示例文本，不作机器批量替换以免误伤方法描述）。
