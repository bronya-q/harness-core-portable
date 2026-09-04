# Harness Core Portable

> 心智模型 / 记忆系统 / 长期情感 的可迁移、可自检特化包。
> 供其他 agent / 其他电脑导入使用。

## 快速开始

```bash
# 解压后
python harness.py audit          # 自检（失败返回非 0）
python mind_review.py run
python production_gate.py
```

## 目录

- `harness-core/`：核心脚本（humanization / memory_store / nine_dim / measurement / production_gate / mind_review / harness ...）
- `harness-core/docs/`：精选工程文档
- `demo_gold.json`：脱敏评测示例
- `demo-perspective-card.json`：脱敏人格卡示例
- `PORTABLE_AGENTS.md` / `PORTABLE_README.md` / `PORTABLE_EVAL.md`
- `PORTABLE_REQUIREMENTS.txt`
- `manifest.json`：文件哈希清单

## 边界

- 不含 PII / API Key / 真实对话 / 大模型文件
- 不含原用户绝对路径
- 本地优先，只读优先，可回滚

## License

MIT
