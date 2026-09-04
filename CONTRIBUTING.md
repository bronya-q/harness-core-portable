# Contributing

> 感谢想帮忙的人。先读 `NATURAL_DATA_GAP.md`。

## 你能贡献什么

1. **自然流样本**：脱敏后提供，或使用 `natural_session_*.bat`。
2. **gold 标注**：看 `recall_gold_independent_blind.csv`。
3. **下游任务反馈**：游戏/论文/网页/文书的真实验收结果。
4. **代码/文档**：提交前先跑 `python harness.py audit`。
5. **安全/许可证核验**：见 `SECURITY.md` / `NOTICE.md`。

## 规则

- 不要引入需要联网才能跑的核心依赖；
- 不要往仓库写入 PII / API key / 真实对话；
- 所有新增文件要能回滚。
