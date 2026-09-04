#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
user_model.py — 真实用户人格模型（只读候选版，2026-08-30）

定位：
  在既有“人类研究理论”之上，用本机已有的真实痕迹：
    1) 对话/记忆（memory.db + mind_tensions）
    2) 本地文件收藏/资料命名（Downloads / Documents 顶层）
    3) 会话存档（session zips 已沉淀的跨会话张力）
  构建对“真实用户”的理解候选，供心智模型参考。

硬边界：
  - 只读：不写 memory.db / humanization_sidecar / policy / persona。
  - 不诊断、不贴人格标签、不自动改变人格/关系/权限。
  - 输出均为 candidate，必须人工审阅后才能进入 H6 或心智模型。

子命令：
  python user_model.py profile [--limit 30] [--files-limit 200]
  python user_model.py sources
  python user_model.py files --dir <path> [--limit 50]
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_store as ms  # noqa: E402
from humanization import connect as hum_connect  # noqa: E402
from need_projection import project as g6_project  # noqa: E402
from nine_dim import _sixdim_for_scope        # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_FILE_DIRS = [
    Path.home() / "Downloads",
    Path.home() / "Documents" / "harness" / "docs",
]
MEDIA_SOURCES = Path(__file__).resolve().parent / "media_sources.json"
STOPWORDS = set("的了和是在我你他她它与也就都而及或一个这个那个什么怎么如何可以能要会没有不是但如果因为所以然后现在之前之后今天明天".split())
ENGLISH_STOPWORDS = set("""the and to of in or is are was were be been being a an this that these those it its as at by for with on not no but if then so can will would should could may might do does did have has had from up down out over under again further once here there when where why how all any both each few more most other some such only own same than too very just also into about after before between through during above below off member text type data message image img face reply at self user group sender nickname card role time seq real message_id user_id group_id""".split())


def _texts_from_memory(limit=2000):
    con = __import__("sqlite3").connect(str(ms.db_path()))
    con.row_factory = __import__("sqlite3").Row
    rows = con.execute(
        "SELECT content, tags, source, kind, created_at, valence FROM memories WHERE archived=0 "
        "ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        if r["content"]:
            out.append({"text": str(r["content"]), "tags": str(r["tags"] or ""),
                        "source": str(r["source"] or ""), "kind": str(r["kind"] or ""),
                        "ts": r["created_at"], "valence": r["valence"]})
    return out


def _texts_from_tensions(limit=300):
    c = hum_connect()
    try:
        rows = c.execute(
            "SELECT statement, source_type, scope, created_at FROM mind_tensions "
            "WHERE status='open' ORDER BY severity DESC LIMIT ?", (limit,)
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    return [{"text": str(r["statement"] or ""), "tags": str(r["source_type"] or ""),
             "source": "mind_tensions", "kind": "tension", "ts": r["created_at"]} for r in rows]


def _texts_from_diary(limit=200):
    c = hum_connect()
    try:
        rows = c.execute(
            "SELECT content, mood_json, created_at FROM diary_entries ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    return [{"text": str(r["content"] or ""), "tags": "diary",
             "source": "humanization_diary", "kind": "diary", "ts": r["created_at"]} for r in rows]



def _texts_from_session_zips(downloads=None, max_lines=20000, total_cap=5000):
    """从 Downloads 的 dsh-session-*.zip 提取真实用户消息（含 ts）。"""
    downloads = downloads or Path.home() / "Downloads"
    zips = sorted(Path(downloads).glob("dsh-session*.zip"), key=lambda x: x.stat().st_size)
    out = []
    try:
        import session_ingest as si
    except Exception:
        return out
    for zp in zips:
        try:
            msgs = si.user_messages_from_zip(zp, max_lines)
        except Exception:
            continue
        for m in msgs:
            if not m.strip():
                continue
            out.append({"text": str(m), "tags": "session_zip",
                        "source": "session_zip", "kind": "user_message",
                        "ts": zp.stat().st_mtime})
            if len(out) >= total_cap:
                return out
    return out



def _load_media_sources():
    """读取已同意接入的社交/IM 来源文件（QQ 已启用，微信待解析）。"""
    if not MEDIA_SOURCES.exists():
        return [], {"note": "media_sources.json missing"}
    cfg = json.loads(MEDIA_SOURCES.read_text(encoding="utf-8"))
    items = []
    loaded = {}
    for key, src in cfg.get("sources", {}).items():
        if not src.get("enabled"):
            continue
        count = 0
        for fp in src.get("text_files", []):
            try:
                f = Path(fp)
                if not f.exists():
                    continue
                txt = f.read_text(encoding="utf-8", errors="replace")
                items.append({"text": txt, "tags": key, "source": "media:" + key,
                              "kind": "media_text", "ts": f.stat().st_mtime})
                count += 1
            except Exception:
                continue
        for fp in src.get("json_files", []):
            try:
                f = Path(fp)
                if not f.exists():
                    continue
                data = json.loads(f.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, list):
                    for obj in data[:2000]:
                        if isinstance(obj, dict):
                            msg = obj.get("raw_message") or obj.get("message") or obj.get("content") or ""
                            if isinstance(msg, list):
                                texts = []
                                for seg in msg:
                                    if isinstance(seg, dict):
                                        t = seg.get("data", {}).get("text") if isinstance(seg.get("data"), dict) else None
                                        if t:
                                            texts.append(str(t))
                                msg = "".join(texts)
                            if msg:
                                items.append({"text": str(msg), "tags": key,
                                              "source": "media:" + key,
                                              "kind": "media_json", "ts": obj.get("time") or f.stat().st_mtime})
                                count += 1
                elif isinstance(data, dict):
                    texts = []
                    if "messages" in data and isinstance(data["messages"], list):
                        texts = [str(x.get("message") or x.get("raw_message") or "") for x in data["messages"] if isinstance(x, dict)]
                    for t in texts:
                        if t:
                            items.append({"text": t, "tags": key, "source": "media:" + key,
                                          "kind": "media_json", "ts": f.stat().st_mtime})
                            count += 1
            except Exception:
                continue
        loaded[key] = count
    return items, {"loaded": loaded, "consent": cfg.get("consent"), "sources": list(cfg.get("sources", {}).keys())}


def _file_names(file_dirs, limit=300):
    names = []
    for d in file_dirs:
        try:
            if not d.exists():
                continue
            files = [f for f in d.iterdir() if f.is_file()]
            for f in files[:limit]:
                stem = f.stem
                if stem:
                    names.append({"text": stem, "tags": str(d.name),
                                  "source": "file_collection", "kind": "filename",
                                  "ts": f.stat().st_mtime})
        except Exception:
            continue
    return names


def _tokenize(text):
    try:
        import jieba
        words = jieba.lcut(text, cut_all=False)
    except Exception:
        words = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    out = []
    for w in words:
        w = w.strip().lower()
        if len(w) < 2:
            continue
        if w in STOPWORDS or w.isdigit():
            continue
        if re.fullmatch(r"[a-z]+", w) and w in ENGLISH_STOPWORDS:
            continue
        if re.fullmatch(r"[\W_]+", w):
            continue
        out.append(w)
    return out


def _freq(items, label_keys, n):
    cnt = Counter()
    src = defaultdict_counter()
    for it in items:
        for w in _tokenize(it["text"]):
            cnt[w] += 1
            for k in label_keys:
                src[(w, str(it.get(k, "")))] += 1
    top = []
    for w, c in cnt.most_common(n):
        by_source = {k: v for (ww, k), v in src.items() if ww == w}
        top.append({"term": w, "count": c, "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])[:5])})
    return top


AMBIV_PATTERNS = [
    re.compile(r"又.*又"),
    re.compile(r"既.*又"),
    re.compile(r"一方面.*另一方面"),
    re.compile(r"想要.*但"),
    re.compile(r"喜欢.*讨厌"),
    re.compile(r"靠近.*远离"),
    re.compile(r"想.*怕"),
    re.compile(r"爱.*恨"),
]
AMBIV_PAIRS = [
    ("想要", "不要"), ("喜欢", "讨厌"), ("靠近", "远离"),
    ("爱", "恨"), ("想", "怕"), ("接近", "回避"), ("愿意", "拒绝"),
]
DENIAL_MARKERS = ["不是", "不会", "没有", "别", "不该", "不可能", "不能", "不想", "不愿", "算了"]
EMOTION_MARKERS = ["喜欢", "爱", "恨", "怕", "担心", "想要", "痛苦", "难受", "开心",
                   "激动", "焦虑", "害怕", "希望", "失望", "愤怒", "委屈", "孤独", "期待"]
OTHERNESS_TERMS = ["外人", "陌生", "异质", "他者", "别人", "不同", "孤立", "同化",
                   "移民", "边界", "局外", "异乡", "怪", "奇异", "排外", "融入"]


def _time_bins(items, term):
    bins = set()
    for it in items:
        if term in _tokenize(it["text"]):
            ts = it.get("ts")
            if ts:
                try:
                    if isinstance(ts, str):
                        from datetime import datetime
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                    bins.add(int(float(ts) // (30 * 86400)))
                except Exception:
                    pass
    return bins


def _repetition_difference(items, top_terms, n=20):
    out = []
    for t in top_terms[:n]:
        term = t["term"]
        bins = _time_bins(items, term)
        out.append({
            "term": term,
            "count": t["count"],
            "distinct_time_bins": len(bins),
            "variation_score": round(len(bins) / max(1, t["count"]), 3) if bins else 0.0,
        })
    return out


def _ambivalence(items):
    hits = []
    for it in items:
        text = it["text"] or ""
        pat = [p.pattern for p in AMBIV_PATTERNS if p.search(text)]
        pairs = [a + "/" + b for a, b in AMBIV_PAIRS if a in text and b in text]
        if pat or pairs:
            hits.append({
                "source": it.get("source"), "kind": it.get("kind"),
                "patterns": pat, "pairs": pairs,
                "snippet": text[:120],
            })
    return {"matches": len(hits), "examples": hits[:5]}


def _language_breaks(items):
    latin = 0
    japan = 0
    ellipsis = 0
    omission = 0
    examples = []
    for it in items:
        text = it["text"] or ""
        l = len(re.findall(r"[A-Za-z]{2,}", text))
        j = len(re.findall(r"[\u3040-\u30ff]", text))
        e = len(re.findall(r"……|\.\.\.", text))
        o = sum(text.count(w) for w in ["没说", "没提", "省略", "沉默", "不想说", "说不清", "忘了", "跳过", "略过"])
        latin += l; japan += j; ellipsis += e; omission += o
        if (l + j + e + o) >= 3 and len(examples) < 5:
            examples.append({"source": it.get("source"), "kind": it.get("kind"),
                             "latin": l, "japanese": j, "ellipsis": e, "omission": o,
                             "snippet": text[:100]})
    return {"totals": {"latin_tokens": latin, "japanese_chars": japan,
                       "ellipsis_count": ellipsis, "omission_words": omission},
            "examples": examples}


def _wish_repression_proxy(items, top_terms, n=10):
    res = []
    for t in top_terms[:n]:
        term = t["term"]
        count = 0
        denial = 0
        emotion = 0
        for it in items:
            text = it["text"] or ""
            if term not in text:
                continue
            count += 1
            denial += sum(text.count(w) for w in DENIAL_MARKERS)
            emotion += sum(text.count(w) for w in EMOTION_MARKERS)
        score = count + 2 * denial + 2 * emotion
        res.append({"term": term, "count": count, "denial_markers": denial,
                    "emotion_markers": emotion, "proxy_score": score})
    res.sort(key=lambda x: -x["proxy_score"])
    return res[:n]


def _otherness(items):
    cnt = Counter()
    for it in items:
        text = it["text"] or ""
        for w in OTHERNESS_TERMS:
            n = text.count(w)
            if n:
                cnt[w] += n
    return [{"term": w, "count": c} for w, c in cnt.most_common(20)]


def defaultdict_counter():
    try:
        from collections import defaultdict
        return defaultdict(int)
    except Exception:
        return Counter()


def profile(args):
    media_items = []
    media_meta = {}
    if args.include_media:
        media_items, media_meta = _load_media_sources()
    if args.full_corpus:
        mem = _texts_from_memory(10000)
        tens = _texts_from_tensions(1000)
        diary = _texts_from_diary(1000)
        files = _file_names(DEFAULT_FILE_DIRS, args.files_limit)
        sess = _texts_from_session_zips()
    else:
        mem = _texts_from_memory(args.limit * 3)
        tens = _texts_from_tensions(args.limit)
        diary = _texts_from_diary(args.limit)
        files = _file_names(DEFAULT_FILE_DIRS, args.files_limit)
        sess = _texts_from_session_zips() if args.include_sessions else []
    all_items = mem + tens + diary + files + sess + media_items

    themes = _freq(all_items, ("source", "kind"), args.limit)

    # 第二轮理论增强：重复-差异 / 矛盾双极 / 语言断裂 / 愿望-压抑代理 / 他者性
    rep_diff = _repetition_difference(all_items, themes, args.limit)
    ambiv = _ambivalence(all_items)
    lang = _language_breaks(all_items)
    wish = _wish_repression_proxy(all_items, themes, args.limit)
    other = _otherness(all_items)

    # 情感/记忆层面的候选信号
    con = __import__("sqlite3").connect(str(ms.db_path()))
    con.row_factory = __import__("sqlite3").Row
    val_rows = con.execute(
        "SELECT AVG(valence) AS v, AVG(arousal) AS a, COUNT(*) AS n FROM memories "
        "WHERE archived=0 AND valence IS NOT NULL"
    ).fetchone()
    con.close()
    emotion_state_rows = []
    try:
        main = __import__("sqlite3").connect(str(ms.db_path()))
        main.row_factory = __import__("sqlite3").Row
        for r in main.execute("SELECT scope, valence, arousal, dominance, label FROM emotion_state").fetchall():
            emotion_state_rows.append(dict(r))
        main.close()
    except Exception:
        pass

    # 用九维状态做一次候选三层需求投影（不写任何库）
    lens = {}
    for st in emotion_state_rows:
        try:
            scope = st["scope"]
            if not scope.startswith("character:"):
                continue
            six, _d = _sixdim_for_scope(scope)
            g6 = g6_project(six, scope=scope, source="user_model")
            lens[scope] = g6.get("candidate_needs")
        except Exception:
            continue

    out = {
        "ok": True,
        "mode": "read_only_user_model_candidate",
        "sources": {
            "memory_items": len(mem),
            "mind_tensions": len(tens),
            "diary_items": len(diary),
            "file_names": len(files),
            "session_user_messages": len(sess),
            "media_items": len(media_items),
            "media_meta": media_meta,
            "total": len(all_items),
        },
        "themes": themes,
        "repetition_difference": rep_diff,
        "ambivalence_signal": ambiv,
        "language_break_signal": lang,
        "wish_repression_proxy": wish,
        "otherness_signal": other,
        "emotional_signal": {
            "memory_avg": {"valence": round(float(val_rows["v"] or 0), 3),
                           "arousal": round(float(val_rows["a"] or 0), 3),
                           "n": int(val_rows["n"] or 0)},
            "scope_states": emotion_state_rows,
        },
        "need_projection_candidates": lens,
        "governance": {
            "writes_performed": False,
            "personality_mutation": False,
            "relationship_mutation": False,
            "policy_mutation": False,
            "do_not_use_for": ["diagnosis", "life_decisions", "automatic_persona_rewrite",
                               "automatic_relationship_changes"],
            "note": "所有输出为候选理解信号，需人工审阅/用户确认",
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))




def cmd_media_sources(args):
    """查看已同意接入的社交/IM 来源。"""
    items, meta = _load_media_sources()
    cfg = {}
    if MEDIA_SOURCES.exists():
        cfg = json.loads(MEDIA_SOURCES.read_text(encoding="utf-8"))
    print(json.dumps({"ok": True, "config": cfg, "loaded": meta,
                      "item_count": len(items)}, ensure_ascii=False, indent=2))


def cmd_real_sessions(args):
    """列出已标记的真实会话。"""
    try:
        c = hum_connect()
        rows = c.execute(
            "SELECT * FROM real_session_registry ORDER BY registered_at DESC LIMIT ?",
            (args.limit,)
        ).fetchall()
        c.close()
        print(json.dumps({"ok": True, "real_sessions": [dict(r) for r in rows]},
                         ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:200]},
                         ensure_ascii=False, indent=2))


def cmd_promote(args):
    """用户确认后，把一条 user_model 理解升级为 user_confirmed_archive（写入 H6）。"""
    import sqlite3
    from humanization import connect as hum_connect, HUM_DB
    content = args.content or sys.stdin.read().strip()
    if not content:
        print(json.dumps({"ok": False, "error": "content required"}, ensure_ascii=False, indent=2))
        return 1
    c = hum_connect()
    iid = __import__("uuid").uuid4().hex
    c.execute(
        "INSERT INTO identity_entries(id,scope,kind,content_json,version,evidence_ids,approved_by,approved_at,rolled_back_at,status,reviewed_at,source,consent)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (iid, args.scope or "user:real", "narrative_self",
         json.dumps({"content": content}, ensure_ascii=False),
         "1.0", args.evidence_ids or "", "user", time.time(), None,
         "approved", time.time(), "user_confirmed_archive", "explicit"),
    )
    c.commit()
    c.close()
    print(json.dumps({"ok": True, "id": iid, "status": "approved",
                      "source": "user_confirmed_archive",
                      "note": "user confirmed; entered H6 as approved"}, ensure_ascii=False, indent=2))
    return 0


def sources(args):
    mem = _texts_from_memory(1000)
    tens = _texts_from_tensions(500)
    diary = _texts_from_diary(500)
    files = _file_names(DEFAULT_FILE_DIRS, 300)
    c = hum_connect()
    try:
        rel = c.execute("SELECT COUNT(*) n FROM relationship_events").fetchone()["n"]
    except Exception:
        rel = 0
    try:
        identity = c.execute("SELECT COUNT(*) n FROM identity_entries").fetchone()["n"]
    except Exception:
        identity = 0
    c.close()
    print(json.dumps({
        "ok": True,
        "sources": {
            "memory_items": len(mem),
            "mind_tensions": len(tens),
            "diary_items": len(diary),
            "file_names": len(files),
            "relationship_events": rel,
            "identity_entries": identity,
        },
        "note": "只读；如需扩展社交媒体验证源，需用户明确同意",
    }, ensure_ascii=False, indent=2))


def files(args):
    names = _file_names([Path(args.dir)], args.limit)
    print(json.dumps({"ok": True, "dir": args.dir, "file_names": [n["text"] for n in names]},
                     ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="真实用户人格模型只读候选 sidecar")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("profile")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--files-limit", type=int, default=200)
    p.add_argument("--full-corpus", action="store_true")
    p.add_argument("--include-sessions", action="store_true")
    p.add_argument("--include-media", action="store_true")
    p.set_defaults(fn=profile)
    p = sub.add_parser("sources"); p.set_defaults(fn=sources)
    p = sub.add_parser("files")
    p.add_argument("--dir", required=True); p.add_argument("--limit", type=int, default=50)
    p.set_defaults(fn=files)
    p = sub.add_parser("real-sessions")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(fn=cmd_real_sessions)
    p = sub.add_parser("media-sources")
    p.set_defaults(fn=cmd_media_sources)
    p = sub.add_parser("promote")
    p.add_argument("--content", default="")
    p.add_argument("--scope", default="user:real")
    p.add_argument("--evidence-ids", default="")
    p.set_defaults(fn=cmd_promote)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
