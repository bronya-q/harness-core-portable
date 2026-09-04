# Contributing

> 感谢想帮忙的人。先读 `NATURAL_DATA_GAP.md`。

## 你能贡献什么

想帮哪个都行，不用全做，能来一个就很好：

1. **自然流样本**：脱敏后给我，或者用 `natural_session_*.bat`。
2. **gold 标注**：看 `recall_gold_independent_blind.csv`。
3. **下游任务反馈**：游戏/论文/网页/文书，跑完说一句“行不行”都算数。
4. **代码/文档**：提交前跑 `python package_selfcheck.py` + `python -m unittest discover`。
5. **安全/许可证核验**：见 `SECURITY.md` / `NOTICE.md`。
6. **外部协作任务**：见 README「需要大家一起来」，包括 MCP Inspector、Registry PR、真实宿主验证、首次用户测试、双人标注、截图/GIF、CI。

> 特别说一句：项目目前最缺的是“真人在真实环境里跑一遍”，不是缺新功能。你愿意花十分钟跑个 demo 或者帮测一个环境，就已经是很大的帮助。

## 规则

- 不要引入需要联网才能跑的核心依赖；
- 不要往仓库写入 PII / API key / 真实对话；
- 所有新增文件要能回滚；
- 公共包只放合成示例，不放入私人角色/路径/私人知识库；
- 改动后写 `docs/tasks/*.md`，发布后写 `docs/deployments/*.md`。
