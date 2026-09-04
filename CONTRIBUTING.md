# Contributing

> 感谢想帮忙的人。先读 `NATURAL_DATA_GAP.md`。

## 你能贡献什么

1. **自然流样本**：脱敏后提供，或使用 `natural_session_*.bat`。
2. **gold 标注**：看 `recall_gold_independent_blind.csv`。
3. **下游任务反馈**：游戏/论文/网页/文书的真实验收结果。
4. **代码/文档**：提交前先跑 `python package_selfcheck.py` + `python -m unittest discover`。
5. **安全/许可证核验**：见 `SECURITY.md` / `NOTICE.md`。
6. **外部协作任务**：见 README「需要大家一起来」，包括：
   - MCP Inspector 实跑
   - Official MCP Registry PR
   - Claude Code / Codex / Copilot 真实宿主验证
   - 首次用户测试
   - 双人标注 Cohen’s κ
   - 真实截图 / GIF
   - GitHub Actions CI / 跨平台矩阵

## 规则

- 不要引入需要联网才能跑的核心依赖；
- 不要往仓库写入 PII / API key / 真实对话；
- 所有新增文件要能回滚；
- 公共包只放合成示例，不放入私人角色/路径/私人知识库；
- 改动后写 `docs/tasks/*.md`，发布后写 `docs/deployments/*.md`。
