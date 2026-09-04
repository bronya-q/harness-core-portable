# -*- coding: utf-8 -*-
"""
九维情绪心智空间引擎 · 融合版（派对姬 20260823）
================================================
设计原则：不重复造轮子 —— memory_store.py 零改动，本模块作为扩展层：
  - 复用 memory_store 的 SQLite（emotion_state/memories 表）与 emotion_set/rel_update 函数
  - 复用 paipai.md Layer 0.5 的六维情绪基线（喜悦/愤怒/悲伤/恐惧/惊讶/厌恶）
  - 移植下载区实测报告的三大机制：
    1) ΔH 事件规则表（65 轮验证的增量方向与量级；LLM 只生成语言、规则管算数）
    2) 海马体衰减：烈度(重要性×访问) × 时间 的个体化遗忘，替代一刀切 factor
    3) 记忆联想链：写入新记忆时用本地 bge-m3(Ollama) 找相似旧记忆并回填联想
  - 向量缓存在 sidecar 库 nine_dim_vectors.db（绝不碰主库 schema）

用法：
  python nine_dim.py event --scope character:demo-alice --activity "被夸奖可爱"
  python nine_dim.py state --scope character:demo-alice
  python nine_dim.py associate --scope character:demo-alice --content "主人带我看星星" --top 3
  python nine_dim.py hippocampus --dry-run
"""
import argparse, contextlib, io, json, math, re, sqlite3, struct, sys, time, urllib.request
from pathlib import Path

import memory_store as ms   # 零改动复用主存储

NS = argparse.Namespace  # memory_store 函数吃 Namespace

DATA_DIR = Path(ms.data_dir())
VEC_DB = DATA_DIR / 'nine_dim_vectors.db'
OLLAMA = 'http://127.0.0.1:11434'
EMBED_MODEL = 'qwen3-embedding:0.6b'

# ---------- 六维基线（= paipai.md Layer 0.5，可按 scope 覆盖） ----------
BASELINE = {
    'character:demo-alice': dict(joy=90, anger=10, sad=5, fear=5, surprise=65, disgust=5),
    'default':            dict(joy=70, anger=20, sad=15, fear=10, surprise=40, disgust=10),
}
DEFAULT_BASELINE = dict(joy=60, anger=25, sad=20, fear=15, surprise=35, disgust=15)

# ---------- ΔH 事件规则表（源自 65 轮实测报告的增量方向与量级） ----------
EVENT_RULES = [
    (r'夸奖|夸夸|可爱|厉害|最棒',        +2.0, +0.30, '被夸奖'),
    (r'投喂|小鱼干|零食|请客|好吃的',     +1.6, +0.25, '被投喂'),
    (r'摸摸头|贴贴|抱抱|蹭蹭',           +1.4, +0.28, '肢体贴贴'),
    (r'一起玩|散步|看电影|看星星',        +1.2, +0.22, '共同活动'),
    (r'安慰|温柔|哄',                   +2.5, +0.35, '被温柔安慰'),
    (r'道歉|重归于好|和好',              +3.0, +0.40, '重归于好'),
    (r'冷落|无视|已读不回',              -8.0, -0.20, '被冷落'),
    (r'欺负|威胁|吼|骂',                -15.0, -0.50, '被欺负'),
    (r'欺骗|失信|撒谎',                 -12.0, -0.45, '失信欺骗'),
    (r'争吵|冲突|争执|吵架',             -6.0, -0.30, '冲突争执'),
]
NEGATIVE_FLOOR = 0.24   # 悲伤不扣穿：负面事件 joy 不低于基线的 24%（报告 V3.3.x 核心机制）

def _baseline(scope):
    return dict(BASELINE.get(scope, DEFAULT_BASELINE))

def _read_state(scope):
    con = sqlite3.connect(str(ms.db_path()))
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT * FROM emotion_state WHERE scope=?', (scope,)).fetchone()
    con.close()
    return dict(r) if r else {}

def _joy_now(scope):
    st = _read_state(scope)
    try:
        return float(st.get('valence', 0.6) or 0.6) * 100.0, st
    except Exception:
        return 60.0, {}

def _synthetic_sixdim(scope, joy, st=None, base=None):
    """Existing synthetic U: joy from valence; other axes relative to baseline."""
    base = base if base is not None else _baseline(scope)
    return {
        "joy": round(float(joy), 1),
        "anger": round(base["anger"] + (base["joy"] - float(joy)) * 0.3, 1),
        "sad": round(base["sad"] + (base["joy"] - float(joy)) * 0.2, 1),
        "fear": base["fear"],
        "surprise": base["surprise"],
        "disgust": base["disgust"],
    }


def _normalize_stored_sixdim(sd, base):
    """Accept both 'sad' and 'sadness'; fill missing axes from baseline."""
    out = {}
    for key in ("joy", "anger", "sad", "fear", "surprise", "disgust"):
        v = sd.get(key)
        if v is None and key == "sad":
            v = sd.get("sadness")
        try:
            out[key] = round(max(-100.0, min(100.0, float(v))), 1)
        except (TypeError, ValueError):
            out[key] = base.get(key, 0.0)
    return out


def _sixdim_for_scope(scope, st=None):
    """Return (sixdim, derivation). Prefer persisted sixdim; fallback to synthetic.

    This is the single source used by nine_dim.state, recall_context, and
    humanization so the reconstructed state no longer diverges from stored data.
    """
    st = st if st is not None else _read_state(scope)
    base = _baseline(scope)
    raw = st.get("sixdim") if st else None
    if raw:
        try:
            sd = json.loads(raw)
        except Exception:
            sd = None
        if isinstance(sd, dict):
            return _normalize_stored_sixdim(sd, base), "stored"
    joy = float(st.get("valence", 0.6) or 0.6) * 100.0 if st else 60.0
    return _synthetic_sixdim(scope, joy, base=base), "synthetic"


def _vec_db():
    con = sqlite3.connect(str(VEC_DB))
    con.execute('''CREATE TABLE IF NOT EXISTS vec(
        memory_id INTEGER PRIMARY KEY, scope TEXT, ts REAL, vec BLOB)''')
    con.execute('''CREATE TABLE IF NOT EXISTS perceived(
        scope TEXT PRIMARY KEY, value REAL, ts REAL)''')
    return con

def _perceived_get(scope):
    con = sqlite3.connect(str(VEC_DB))
    try:
        con.execute('''CREATE TABLE IF NOT EXISTS perceived(
            scope TEXT PRIMARY KEY, value REAL, ts REAL)''')
        r = con.execute('SELECT value FROM perceived WHERE scope=?', (scope,)).fetchone()
        return float(r[0]) if r else None
    except Exception:
        return None
    finally:
        con.close()

def _perceived_set(scope, value):
    con = sqlite3.connect(str(VEC_DB))
    con.execute('''CREATE TABLE IF NOT EXISTS perceived(
        scope TEXT PRIMARY KEY, value REAL, ts REAL)''')
    con.execute('INSERT OR REPLACE INTO perceived(scope,value,ts) VALUES(?,?,?)',
                (scope, round(float(value), 3), time.time()))
    con.commit(); con.close()

def _embed(text):
    req = urllib.request.Request(OLLAMA + '/api/embeddings',
        data=json.dumps({'model': EMBED_MODEL, 'prompt': text[:500]}).encode(),
        headers={'Content-Type': 'application/json'})
    r = json.load(urllib.request.urlopen(req, timeout=30))
    return r['embedding']

def _pack(f): return struct.pack('%df' % len(f), *f)
def _unpack(b): n = len(b) // 4; return list(struct.unpack('%df' % n, b))

def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

# ---------- 1) ΔH 事件引擎 ----------
def cmd_event(args):
    scope, act = args.scope, args.activity
    base = _baseline(scope)
    joy_now, cur = _joy_now(scope)
    before = {"joy": round(joy_now, 1), "arousal": cur.get("arousal"), "dominance": cur.get("dominance"), "affinity": cur.get("affinity"), "trust": cur.get("trust")}
    hit = None
    for pat, jd, ad, name in EVENT_RULES:
        if re.search(pat, act):
            hit = (jd, ad, name); break
    if hit:
        jd, ad, name = hit
        floor = base['joy'] * NEGATIVE_FLOOR
        joy_new = max(joy_now + jd, floor) if jd < 0 else min(joy_now + jd, base['joy'] * 1.25)
        joy_new += (base['joy'] - joy_new) * 0.10
        with contextlib.redirect_stdout(io.StringIO()):
            ms.emotion_set(NS(scope=scope,
                              valence=round(joy_new / 100.0, 3),
                              arousal=float(cur.get('arousal', 0.6) or 0.6),
                              dominance=float(cur.get('dominance', 0.4) or 0.4),
                              label='%s|joy=%.0f' % (name, joy_new), context=cur.get('context'),
                              rel_level=cur.get('rel_level'), trust=cur.get('trust'),
                              affinity=cur.get('affinity'),
                              sixdim=_synthetic_sixdim(scope, joy_new, base=base)))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                ms.rel_update(NS(scope=scope, affinity_delta=ad, trust_delta=None,
                                 rel_level=None, rel_adjust=None, no_auto=False))
        except Exception:
            pass
        _sink = io.StringIO()
        with contextlib.redirect_stdout(_sink):
            memory_result = ms.add_memory(NS(scope=scope, entity=scope.split(':')[-1],
                         content='%s（九维规则：%s，joyDelta%+.1f，affDelta%+.2f）' % (act, name, jd, ad),
                         kind='event',
                         importance=min(0.9, 0.4 + abs(jd) / 20.0),
                         valence=max(-1.0, min(1.0, jd / 20.0)), arousal=None,
                         tags='九维,%s' % name, source='nine_dim', sixdim=None))
        out = {'ok': True, 'rule': name, 'rule_id': 'nine_dim.event.' + name, 'joyDelta': jd, 'affDelta': ad,
               'joyNow': round(joy_new, 1), 'baselineJoy': base['joy'], 'evidence_memory_id': memory_result.get('id') if isinstance(memory_result, dict) else None}
    else:
        joy_new = joy_now + (base['joy'] - joy_now) * 0.05
        with contextlib.redirect_stdout(io.StringIO()):
            ms.emotion_set(NS(scope=scope,
                              valence=round(joy_new / 100.0, 3),
                              arousal=float(cur.get('arousal', 0.6) or 0.6),
                              dominance=float(cur.get('dominance', 0.4) or 0.4),
                              label=cur.get('label'), context=cur.get('context'),
                              rel_level=cur.get('rel_level'), trust=cur.get('trust'),
                              affinity=cur.get('affinity'),
                              sixdim=_synthetic_sixdim(scope, joy_new, base=base)))
        out = {'ok': True, 'rule': None, 'note': 'no rule hit, baseline drift only',
               'joyNow': round(joy_new, 1)}

    perceived_out = None
    try:
        per = _perceived_get(scope)
        if per is None:
            per = joy_new
        rel_row = _read_state(scope)
        rl = int(rel_row.get('rel_level') or 0)
        if hit:
            damp_pos = 0.5 if rl <= 1 else (0.8 if rl == 2 else 1.0)
            damp_neg = 1.2 if rl <= 1 else 1.0
            per += hit[0] * (damp_pos if hit[0] > 0 else damp_neg)
        per += (joy_new - per) * 0.06
        per = max(2.4, min(per, 115.0))
        _perceived_set(scope, per)
        perceived_out = round(per, 1)
    except Exception:
        pass
    if perceived_out is not None:
        out['perceived'] = perceived_out
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from continuity_store import record_emotion
        after = {"joy": out.get("joyNow"), "arousal": _read_state(scope).get("arousal"),
                 "dominance": _read_state(scope).get("dominance"), "affinity": _read_state(scope).get("affinity"),
                 "trust": _read_state(scope).get("trust")}
        delta = {"joy": round((after.get("joy") or 0) - (before.get("joy") or 0), 2)}
        event_id = record_emotion(scope, "event" if hit else "baseline_drift", out.get("rule_id"), before, delta, after,
                                  [out.get("evidence_memory_id")] if out.get("evidence_memory_id") else [], "nine_dim")
        out['emotion_event_id'] = event_id
    except Exception as exc:
        out['emotion_event_error'] = type(exc).__name__

    print(json.dumps(out, ensure_ascii=False))


def cmd_associate(args):
    scope, content, k = args.scope, args.content, args.top
    q = _embed(content)
    con = _vec_db()
    main = sqlite3.connect(str(ms.db_path()))
    rows = con.execute('SELECT memory_id, vec FROM vec WHERE scope=?', (scope,)).fetchall()
    scored = sorted(((_cos(q, _unpack(blob)), mid) for mid, blob in rows), reverse=True)
    hits = []
    for sim, mid in scored[:k]:
        r = main.execute('SELECT content, kind FROM memories WHERE id=?', (mid,)).fetchone()
        if r:
            hits.append({'id': mid, 'sim': round(sim, 3), 'kind': r[1], 'content': r[0][:80]})
    ts = ms.now_iso()
    cur = main.execute(
        "INSERT INTO memories(scope,entity,content,kind,importance,valence,tags,source,created_at,updated_at)"
        " VALUES(?,?,?,?,?,?,?,?,?,?)",
        (scope, scope.split(':')[-1], content, 'event', 0.45, 0.1, '九维,联想源', 'nine_dim', ts, ts))
    mid_new = cur.lastrowid; main.commit()
    con.execute('INSERT OR REPLACE INTO vec(memory_id,scope,ts,vec) VALUES(?,?,?,?)',
                (mid_new, scope, time.time(), _pack(q)))
    # 给历史记忆补向量（渐进索引），上限每次 50 条防阻塞
    have = {r[0] for r in con.execute('SELECT memory_id FROM vec WHERE scope=?', (scope,)).fetchall()}
    cand = [r[0] for r in main.execute(
        'SELECT id FROM memories WHERE scope=? ORDER BY id DESC LIMIT 200', (scope,)).fetchall()]
    need = [mid for mid in cand if mid not in have][:50]
    for mid in need:
        txt = main.execute('SELECT content FROM memories WHERE id=?', (mid,)).fetchone()[0]
        try:
            con.execute('INSERT INTO vec(memory_id,scope,ts,vec) VALUES(?,?,?,?)',
                        (mid, scope, time.time(), _pack(_embed(txt))))
        except Exception:
            break
    con.commit()
    if hits:
        link = ','.join('#%d(%.2f)' % (h['id'], h['sim']) for h in hits[:3])
        main.execute("UPDATE memories SET tags=tags||? WHERE id=?", ((',联想:' + link), mid_new))
        main.commit()
    main.close(); con.close()
    print(json.dumps({'ok': True, 'newId': mid_new, 'indexedTotal': len(rows) + 1 + len(need),
                      'associations': hits}, ensure_ascii=False))

# ---------- 3) 海马体衰减（烈度×时间个体化） ----------
def cmd_hippocampus(args):
    dry = args.dry_run
    main = sqlite3.connect(str(ms.db_path()))
    rows = main.execute("""SELECT id, importance, access_count,
                                  julianday('now') - julianday(coalesce(last_access_at, updated_at, created_at))
                           FROM memories WHERE archived=0""").fetchall()
    touched, sample = 0, []
    for mid, imp, acc, days in rows:
        imp = imp or 0.5; acc = acc or 0; days = days or 0
        strength = (imp * 2.0) + min(acc, 10) / 10.0       # 烈度 = 重要性×2 + 访问频次
        per_day = 0.010 / (0.5 + strength)                  # 强记忆衰减慢（固化效应）
        new_imp = round(max(0.05, imp * (1.0 - per_day * days)), 4)
        if new_imp < imp - 0.01:
            touched += 1
            if len(sample) < 3:
                sample.append({'id': mid, 'imp': imp, 'new': new_imp,
                               'strength': round(strength, 2), 'days': round(days)})
            if not dry:
                main.execute('UPDATE memories SET importance=? WHERE id=?', (new_imp, mid))
    if not dry:
        main.commit()
    main.close()
    print(json.dumps({'ok': True, 'scanned': len(rows), 'decayed': touched,
                      'sample': sample, 'dryRun': dry}, ensure_ascii=False))

# ---------- 4) 状态查看（PAD → 六维全输出） ----------
def cmd_state(args):
    scope = args.scope
    cur = _read_state(scope)
    base = _baseline(scope)
    six, derivation = _sixdim_for_scope(scope, cur)
    print(json.dumps({'scope': scope,
                      'pad': {k: cur.get(k) for k in ('valence', 'arousal', 'dominance', 'label')},
                      'sixdim': six,
                      'derivation': derivation,
                      'relLevel': cur.get('rel_level'), 'affinity': cur.get('affinity'),
                      'trust': cur.get('trust'), 'baselineJoy': base['joy']},
                     ensure_ascii=False))

def main():
    p = argparse.ArgumentParser(description='九维情绪心智空间引擎（融合版）')
    sp = p.add_subparsers(dest='cmd', required=True)
    e = sp.add_parser('event'); e.add_argument('--scope', required=True); e.add_argument('--activity', required=True)
    e.set_defaults(fn=cmd_event)
    a = sp.add_parser('associate'); a.add_argument('--scope', required=True)
    a.add_argument('--content', required=True); a.add_argument('--top', type=int, default=3)
    a.set_defaults(fn=cmd_associate)
    h = sp.add_parser('hippocampus'); h.add_argument('--dry-run', action='store_true')
    h.set_defaults(fn=cmd_hippocampus)
    s = sp.add_parser('state'); s.add_argument('--scope', required=True)
    s.set_defaults(fn=cmd_state)
    args = p.parse_args()
    args.fn(args)

if __name__ == '__main__':
    main()
