# PORTABLE_AGENTS.md — 给 agent 的导航

> 这是本地 harness 的“心智/记忆/情感”核心的可迁移包。

## 入口
- `harness.py` 统一 CLI
- `humanization.py` / `memory_store.py` / `nine_dim.py` / `perspective_card.py`
- `production_gate.py` / `mind_review.py`

## 自检
```bash
python harness.py audit
```
> 失败时退出码非 0。

## 原则
- 只读优先，可回滚
- 安全在 harness，不给人设
- 自然流与定向评测分开
- gate fail-closed
- 先看 `docs/` 再改代码
