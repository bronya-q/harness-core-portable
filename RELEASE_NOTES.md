# Release Notes

## v0.1.0-alpha.2 (Pre-release)

> Alpha / WIP。不是 production-ready。

### 新增 / 变化

- 离线可感知演示 `python harness.py demo --offline`
- 新手体验层：`start / doctor / inspect / data status`
- 只读本地 HTML 控制台 `dashboard build / open`
- 用户控制：`memory list/explain/correct/restore/forget`
- 隐私 / 备份 / 反馈：`privacy status/export/reset-demo`、`backup create/list/restore`、`feedback export --redacted`
- 角色资产基础：`character list/install/activate/deactivate/remove/show`
- 知识域与工程工作区：`knowledge list/sources`、`workspace create/list/status/release`
- 统一 schema：`schema list`、`schema validate`（role/event/token）
- Event Envelope 与 Token Usage：`event add/list`、`usage record/list`
- 公共/本机边界整改：`runtime_resolver.py` 去除私人角色硬编码；公共合成示例；本机 overlay 支持
- ROADMAP 重构为工程路线图；公共文档去私人角色名

### 验证

- Git clone 与 Download ZIP 双模式自检通过
- `release_verify` / `package_selfcheck` / `local_records_verify` 均通过

### 边界

- 不含真实用户数据 / 私有人格卡 / 模型权重 / API key
- 不开启 Autonomous
- L4/L5 不启用
- 完整生产运行面依赖私有数据，公开包返回 UNAVAILABLE / FAIL
