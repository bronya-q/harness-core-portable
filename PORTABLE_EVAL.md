# PORTABLE_EVAL.md — 可复现评测

```bash
python measurement.py recall-pool --pool demo_gold.json --top-k 5 --retriever keyword
python mind_review.py run
python production_gate.py
```

> demo_gold.json 为脱敏示例；生产用真实 gold 时请替换。
