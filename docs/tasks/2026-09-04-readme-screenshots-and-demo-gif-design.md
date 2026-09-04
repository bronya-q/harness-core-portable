---
title: README screenshots and offline demo GIF
status: designed
kind: task-design
date: 2026-09-04
updated_at: 2026-09-04
owner_role: documentation-and-ux
target_version: v0.2+
public: true
contains_private_data: false
topics: [readme, screenshot, gif, demo, onboarding]
---

# README screenshots and offline demo GIF

## 1. 一句话目标

为 README 增加真实、脱敏、可复现的合成数据 Dashboard 截图，以及一段 20–30 秒离线 Demo GIF，让首次访问者不运行命令也能看到“记住 / 隔离 / 纠错 / 恢复 / 清理”。

## 2. 用户场景

- 用户打开 GitHub 页面，只有文字描述，无法快速确认项目是否值得下载；
- 用户想看到“跨会话记忆、角色隔离、版本恢复”的实际画面。

## 3. 设计范围

### 包含

- 生成合成 Dashboard 截图（使用 `demo --offline` 数据，不包含本机私人数据）
- 录制/生成 20–30 秒离线 Demo GIF
- 截图/GIF 放入 `docs/media/`
- README 插入对应媒体

### 不包含

- 任何本机私人角色、私有人格、真实对话
- 云服务、自动上传

## 4. 公共与本机边界

- 截图/GIF 全部来自合成 demo
- 不含本机路径、角色名、私人知识库
- 可安全进入公共包

## 5. 验收标准

- [ ] 截图使用真实 `dashboard build` 输出
- [ ] GIF 展示 `demo --offline` 完整关键步骤
- [ ] 无本机绝对路径
- [ ] 无私人角色名
- [ ] release_verify 通过

## 6. 后辈接手说明

1. 先检查 `docs/media/` 是否存在
2. 截图和 GIF 应从合成 demo 重新生成，不复制本机内容
3. 如果无法生成 GIF，先用静态截图，并标记 TODO

## 7. 相关文件

- `README.md`
- `docs/media/`
