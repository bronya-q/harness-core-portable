---
title: First-time user usability testing
status: designed
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: documentation-and-ux
target_version: v0.2+
public: true
contains_private_data: false
topics: [usability, user-testing, onboarding, feedback]
---

# First-time user usability testing

## 1. 一句话目标

找 5 个没接触过项目的人，完成首次使用任务，记录困惑点、放弃点、误解点和可操作改进。

## 2. 用户场景

- 项目自认为“低门槛”，但缺少真实用户验证；
- 需要知道用户在哪一行看懂、在哪一步放弃、误解了什么。

## 3. 任务清单

1. 下载/克隆
2. 运行离线 Demo
3. 找到一条记忆
4. 纠正它
5. 删除它
6. 恢复它
7. 判断它属于哪个角色
8. 判断是否上传网络
9. 找到数据目录
10. 清空 demo

## 4. 记录项

- 完成率
- 用时
- 卡住位置
- 错误命令数
- 是否理解 shadow
- 是否误把 gate FAIL 当安装失败
- 是否成功删除数据

## 5. 验收标准

- [ ] 至少 5 人参与
- [ ] 记录逐项结果
- [ ] 输出到 `docs/user-testing/`（脱敏）
- [ ] 形成可行动改进清单

## 6. 后辈接手说明

1. 测试必须使用公开 clean clone / ZIP
2. 不记录真实用户名、路径、私人角色
3. 结果作为下一版 README/UX 改进依据
