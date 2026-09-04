# Security Policy

> 本项目是本地可迁移的 harness-core 源码包，不含 AI 服务端。

## 报告问题

- 不要公开私密 PII / API key。
- 发现密钥、隐私、越权或注入问题，请开 private issue 或直接联系维护者。
- 优先报告：泄露模式、路径穿越、Prompt Injection、可越权写入。

## 使用边界

```text
- 只读优先，可回滚；
- 不自动上传/联网；
- 不把 PII/API key 写入人格/记忆；
- 安全边界在 harness 代码，不给人设。
```
