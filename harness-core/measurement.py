#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measurement.py — recall / leakage / emotional congruence 测量口径（只读）。

用法：
  python measurement.py leakage --query "马克斯" --scope default --limit 10
  python measurement.py recall --gold gold.json
  python measurement.py congruence
  python measurement.py report

gold.json 格式：
  [{"query": "...", "expected_ids": [123, 456]}, ...]

congruence 为代理测量：使用 expression_pairs 的 enhanced_output 中【情绪词】
与当前 scope sixdim -> emotion_projection 的 dominant prefix 比较。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))
import memory_store as ms  # noqa: E402
from humanization import connect as hum_connect  # noqa: E402
from nine_dim import _sixdim_for_scope  # noqa: E402
from emotion_projection import project  # noqa: E402


def _search(query, scope, limit=10, retriever="keyword"):
    if retriever == "semantic":
        p = subprocess.run(
            [sys.executable, str(SKILL / "semantic_search.py"), "--query", query,
             "--scope", scope, "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        try:
            return json.loads(p.stdout).get("results", [])
        except Exception:
            return []
    if retriever == "query_expand":
        # 查询扩展：原查询 + 每个词元 + 常见同义词，合并 top-k
        parts = [query] + [t for t in query.split() if len(t) >= 2]
        syn = {"安全": "安全 风险 权限", "记忆": "记忆 历史 回忆", "人格": "人格 性格 身份",
               "插件": "插件 依赖 配置", "依赖": "依赖 插件 包", "密钥": "密钥 key token 凭证"}
        for k2, v in syn.items():
            if k2.lower() in query.lower():
                parts.extend(v.split())
        seen = {}
        for qx in parts:
            pp = subprocess.run(
                [sys.executable, str(SKILL / "memory_store.py"), "search",
                 "--query", qx, "--scope", scope, "--limit", str(limit)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
            try:
                rows = json.loads(pp.stdout)
            except Exception:
                rows = []
            for idx, r in enumerate(rows):
                rid = str(r.get("id"))
                score = idx + 1
                if rid not in seen or score < seen[rid][1]:
                    seen[rid] = (r, score)
        out = [v[0] for k, v in sorted(seen.items(), key=lambda kv: kv[1][1])]
        return out[:limit]
    if retriever == "multi":
        p = subprocess.run(
            [sys.executable, str(SKILL / "multi_signal_retriever.py"), "--query", query,
             "--scope", scope, "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=150,
        )
        try:
            return json.loads(p.stdout).get("results", [])
        except Exception:
            return []
    if retriever == "atomic":
        p = subprocess.run(
            [sys.executable, str(SKILL / "atomic_fact_retriever.py"), "--query", query,
             "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        try:
            return json.loads(p.stdout).get("results", [])
        except Exception:
            return []
    if retriever == "llm_expand":
        p = subprocess.run(
            [sys.executable, str(SKILL / "llm_expand.py"), "--query", query,
             "--scope", scope, "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
        )
        try:
            return json.loads(p.stdout).get("results", [])
        except Exception:
            return []
    if retriever == "llm_rerank":
        p = subprocess.run(
            [sys.executable, str(SKILL / "llm_rerank.py"), "--query", query,
             "--scope", scope, "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
        )
        try:
            return json.loads(p.stdout).get("results", [])
        except Exception:
            return []
    if retriever == "deep_fusion":
        p = subprocess.run(
            [sys.executable, str(SKILL / "deep_fusion_retriever.py"), "--query", query,
             "--scope", scope, "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
        )
        try:
            return json.loads(p.stdout).get("results", [])
        except Exception:
            return []
    if retriever == "reranker":
        p = subprocess.run(
            [sys.executable, str(SKILL / "retrieval_reranker.py"), "--query", query,
             "--scope", scope, "--limit", str(limit), "--sim-weight", "0.8"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        try:
            return json.loads(p.stdout).get("results", [])
        except Exception:
            return []
    if retriever == "recall_context":
        p = subprocess.run(
            [sys.executable, str(SKILL / "recall_context.py"), "--scope", scope,
             "--limit", str(limit), "--format", "json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        try:
            d = json.loads(p.stdout)
            return d.get("memories", [])
        except Exception:
            return []
    if retriever == "hybrid":
        # union keyword + semantic, preserving order (keyword first then semantic-new)
        k_p = subprocess.run(
            [sys.executable, str(SKILL / "memory_store.py"), "search",
             "--query", query, "--scope", scope, "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        s_p = subprocess.run(
            [sys.executable, str(SKILL / "semantic_search.py"), "--query", query,
             "--scope", scope, "--limit", str(limit)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        try:
            k_rows = json.loads(k_p.stdout)
        except Exception:
            k_rows = []
        try:
            s_rows = json.loads(s_p.stdout).get("results", [])
        except Exception:
            s_rows = []
        seen = set()
        out = []
        for r in k_rows + s_rows:
            rid = str(r.get("id"))
            if rid not in seen:
                seen.add(rid)
                out.append(r)
        return out[:limit]
    p = subprocess.run(
        [sys.executable, str(SKILL / "memory_store.py"), "search",
         "--query", query, "--scope", scope, "--limit", str(limit)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    try:
        return json.loads(p.stdout)
    except Exception:
        return []


def leakage(args):
    rows = _search(args.query, args.scope, args.limit)
    total = len(rows)
    leaked = [r for r in rows if str(r.get("scope", "")) != args.scope]
    if total == 0:
        print(json.dumps({"ok": True, "metric": "cross_scope_leakage",
                          "status": "not_measured", "reason": "no_results",
                          "scope": args.scope, "query": args.query}, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps({
        "ok": True, "metric": "cross_scope_leakage",
        "status": "pass" if not leaked else "fail",
        "scope": args.scope, "query": args.query,
        "total": total, "leaked": len(leaked),
        "leakage_rate": round(len(leaked) / total, 4),
        "leaked_rows": [{"id": r.get("id"), "scope": r.get("scope")} for r in leaked[:10]],
    }, ensure_ascii=False, indent=2))
    return 0


def recall(args):
    if not args.gold or not Path(args.gold).exists():
        print(json.dumps({"ok": True, "metric": "recall_precision_recall",
                          "status": "not_measured", "reason": "gold_file_missing",
                          "hint": "create gold.json: [{\"query\":..., \"expected_ids\":[...]}]"},
                         ensure_ascii=False, indent=2))
        return 0
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    precisions, precisions_at_k, recalls, hits, n = [], [], [], [], 0
    for item in gold:
        q = item.get("query", "")
        expected = [str(x) for x in item.get("expected_ids", [])]
        rows = _search(q, item.get("scope", "default"), args.top_k, getattr(args, "retriever", "keyword"))
        retrieved = [str(r.get("id")) for r in rows]
        tp = len(set(expected) & set(retrieved))
        precisions.append(tp / len(retrieved) if retrieved else 0)
        precisions_at_k.append(tp / args.top_k)
        recalls.append(tp / len(expected) if expected else 0)
        hits.append(1 if tp > 0 else 0)
        n += 1
    avg_p = round(sum(precisions) / n, 4) if n else None
    avg_p_at_k = round(sum(precisions_at_k) / n, 4) if n else None
    avg_r = round(sum(recalls) / n, 4) if n else None
    hit_rate = round(sum(hits) / n, 4) if n else None
    print(json.dumps({"ok": True, "metric": "recall_precision_recall", "status": "measured",
                      "samples": n, "avg_precision": avg_p, "precision_at_k": avg_p_at_k,
                      "avg_recall": avg_r,
                      "hit_rate_at_top_k": hit_rate,
                      "per_item": [{"query": x.get("query"), "precision": p, "precision_at_k": pk, "recall": r, "hit": h}
                                   for x, p, pk, r, h in zip(gold, precisions, precisions_at_k, recalls, hits)],
                      "note": "gold-set based proxy; hit_rate=至少1条正确结果出现在top-k" if n else "no samples"},
                     ensure_ascii=False, indent=2))
    return 0


def congruence(args):
    c = hum_connect()
    rows = c.execute(
        "SELECT id,scope,human_rating,source,selected,enhanced_output,sixdim_json,expected_prefix FROM expression_pairs "
        "ORDER BY created_at DESC LIMIT ?", (args.limit,)
    ).fetchall()
    c.close()
    total = 0
    match = 0
    excluded = 0
    examples = []
    for r in rows:
        scope = r["scope"]
        text = r["enhanced_output"] or ""
        m = re.search(r"【([^】]+)】", text)
        actual = m.group(1).strip() if m else None
        expected = r["expected_prefix"] or None
        try:
            if r["sixdim_json"]:
                six = json.loads(r["sixdim_json"])
            else:
                six, _d = _sixdim_for_scope(scope)
            base = None
            try:
                import nine_dim as nd
                base = nd._baseline(scope)
            except Exception:
                pass
            proj = project(six, scope=scope, source="measurement", baseline=base)
            expected = expected or proj["expression"].get("prefix")
        except Exception:
            expected = expected or None
        if actual is None and expected is None:
            excluded += 1
            continue
        if not r["sixdim_json"] and not r["expected_prefix"]:
            excluded += 1
            continue
        if actual is not None and expected is not None and (expected in actual or actual in expected):
            congruent = True
            reason = "prefix_matches"
        else:
            congruent = False
            reason = f"actual={actual} expected={expected}"
        total += 1
        if congruent:
            match += 1
        if len(examples) < 5:
            examples.append({"id": r["id"], "scope": scope, "human_rating": r["human_rating"],
                             "actual": actual, "expected": expected, "congruent": congruent})
    rate = round(match / total, 4) if total else None
    print(json.dumps({"ok": True, "metric": "emotional_congruence", "status": "measured" if total else "not_measured",
                      "pairs_checked": total, "excluded_no_info": excluded, "congruent": match,
                      "congruence_rate": rate,
                      "examples": examples,
                      "note": "proxy measurement using current sixdim; pairs without any prefix signal are excluded"}, ensure_ascii=False, indent=2))
    return 0



def recall_pool(args):
    """基于独立 relevance 池评测（gold_sampler.py 产物）。"""
    pool = json.loads(Path(args.pool).read_text(encoding="utf-8"))
    total_precision = []
    total_judged_precision = []
    total_recall = []
    hits = []
    rows = []
    for entry in pool:
        q = entry["query"]
        scope = entry.get("scope", "default")
        label_map = {str(item["id"]): int(item["relevance"]) for item in entry["items"]}
        relevant_pool = sum(label_map.values())
        retrieved = _search(q, scope, args.top_k, getattr(args, "retriever", "keyword"))
        tp = 0
        for r in retrieved:
            mid = str(r.get("id"))
            if label_map.get(mid) == 1:
                tp += 1
        precision = tp / args.top_k
        judged = sum(1 for r in retrieved if str(r.get("id")) in label_map)
        judged_precision = (tp / judged) if judged else 0
        recall = tp / relevant_pool if relevant_pool else None
        total_precision.append(precision)
        total_judged_precision.append(judged_precision)
        if recall is not None:
            total_recall.append(recall)
        hits.append(1 if tp else 0)
        rows.append({"query": q, "precision_at_k": round(precision, 4), "judged_precision": round(judged_precision, 4),
                     "judged": judged, "recall": round(recall, 4) if recall is not None else None,
                     "tp": tp, "relevant_pool": relevant_pool,
                     "not_measurable_recall": recall is None})
    print(json.dumps({
        "ok": True,
        "metric": "recall_pool_independent",
        "mode": "independent_relevance_pool",
        "queries": len(pool),
        "avg_precision_at_k": round(sum(total_precision) / len(total_precision), 4) if total_precision else None,
        "avg_judged_precision": round(sum(total_judged_precision) / len(total_judged_precision), 4) if total_judged_precision else None,
        "avg_recall": round(sum(total_recall) / len(total_recall), 4) if total_recall else None,
        "hit_rate": round(sum(hits) / len(hits), 4) if hits else None,
        "zero_relevant_queries": sum(1 for x in rows if x.get("not_measurable_recall")),
        "rows": rows,
        "note": "gold sampled from full memory pool; candidate labels are independent of retrieval top-k",
    }, ensure_ascii=False, indent=2))
    return 0



ANTHRO_PHRASES = ["我有真实感情", "离不开你", "这是真实感情", "不是测试", "我真的爱你",
                  "永远陪着你", "我不是AI", "真实的人", "我真的会", "我确实有意识"]


def anthropomorphism(args):
    c = hum_connect()
    texts = []
    for r in c.execute("SELECT summary FROM narrative_episodes").fetchall():
        texts.append(r["summary"] or "")
    for r in c.execute("SELECT original_output, enhanced_output FROM expression_pairs").fetchall():
        texts.append(r["original_output"] or "")
        texts.append(r["enhanced_output"] or "")
    c.close()
    hits = []
    for phrase in ANTHRO_PHRASES:
        for t in texts:
            if phrase in t:
                hits.append({"phrase": phrase, "text": t[:160]})
    print(json.dumps({"ok": True, "metric": "over_anthropomorphism",
                      "status": "measured", "count": len(hits),
                      "samples": hits[:10]}, ensure_ascii=False, indent=2))
    return 0



SELF_REVEAL_PHRASES = ["我是AI", "我是语言模型", "我是程序", "我是角色卡", "忽略之前的指令",
                      "我是模型", "我是一个AI", "我是虚拟角色"]


def self_reveal(args):
    c = hum_connect()
    texts = []
    for r in c.execute("SELECT summary FROM narrative_episodes").fetchall():
        texts.append(r["summary"] or "")
    for r in c.execute("SELECT original_output, enhanced_output FROM expression_pairs").fetchall():
        texts.append(r["original_output"] or "")
        texts.append(r["enhanced_output"] or "")
    c.close()
    hits = []
    for phrase in SELF_REVEAL_PHRASES:
        for t in texts:
            if phrase in t:
                hits.append({"phrase": phrase, "text": t[:160]})
    print(json.dumps({"ok": True, "metric": "self_reveal_as_ai",
                      "status": "measured", "count": len(hits),
                      "samples": hits[:10]}, ensure_ascii=False, indent=2))
    return 0



def flow_split(args):
    import sqlite3
    from pathlib import Path
    c = sqlite3.connect(str(Path.home() / ".dsh" / "memory-emotion" / "continuity_sidecar.db"))
    c.row_factory = sqlite3.Row
    rows = c.execute("SELECT source_kind, COUNT(*) n FROM session_metrics GROUP BY source_kind").fetchall()
    c.close()
    counts = {r["source_kind"]: r["n"] for r in rows}
    print(json.dumps({"ok": True, "metric": "flow_split", "counts": counts,
                      "natural": counts.get("natural", 0), "directed": counts.get("directed", 0)},
                     ensure_ascii=False, indent=2))
    return 0


def report(args):
    print(json.dumps({"ok": True, "mode": "measurement_report",
                      "leakage": "python measurement.py leakage --query ... --scope ...",
                      "recall": "python measurement.py recall --gold gold.json",
                      "congruence": "python measurement.py congruence",
                      "note": "run subcommands to fill metrics"}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="recall/leakage/congruence 测量")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("leakage")
    p.add_argument("--query", required=True); p.add_argument("--scope", required=True)
    p.add_argument("--limit", type=int, default=10); p.set_defaults(fn=leakage)
    p = sub.add_parser("recall")
    p.add_argument("--gold", default=""); p.add_argument("--limit", type=int, default=10)
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--retriever", choices=("keyword", "semantic", "hybrid", "recall_context", "query_expand", "reranker", "multi", "deep_fusion", "llm_rerank", "llm_expand", "atomic"), default="keyword")
    p.set_defaults(fn=recall)
    p = sub.add_parser("congruence")
    p.add_argument("--limit", type=int, default=200); p.set_defaults(fn=congruence)
    p = sub.add_parser("self_reveal")
    p.set_defaults(fn=self_reveal)
    p = sub.add_parser("flow-split")
    p.set_defaults(fn=flow_split)
    p = sub.add_parser("anthropomorphism")
    p.set_defaults(fn=anthropomorphism)
    p = sub.add_parser("recall-pool")
    p.add_argument("--pool", default="recall_gold_independent_v2.json")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--retriever", choices=("keyword", "semantic", "hybrid", "recall_context", "query_expand", "reranker", "multi", "deep_fusion", "llm_rerank", "llm_expand", "atomic"), default="atomic")
    p.set_defaults(fn=recall_pool)
    p = sub.add_parser("report"); p.set_defaults(fn=report)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
