#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dashboard.py — 静态本地 HTML 控制台（只读）。

用法：
  python harness.py dashboard build
  python harness.py dashboard open

生成 ~/.dsh/harness-dashboard/index.html，不启动服务、不开放端口、不自动上传。
"""
import html
import json
import os
import sqlite3
import sys
import time
import webbrowser
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "memory-emotion"
sys.path.insert(0, str(SKILL))
from event_store import list_events, list_usage  # noqa: E402
OUT_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness-dashboard"
OUT_FILE = OUT_DIR / "index.html"


def _q(dbpath, sql, args=()):
    if not Path(dbpath).exists():
        return []
    try:
        con = sqlite3.connect(f"file:{dbpath}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute(sql, args)]
        con.close()
        return rows
    except Exception:
        return []


def _html(s):
    return html.escape(str(s))


def _ts(v):
    try:
        v = float(v)
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(v))
    except Exception:
        return str(v or "-")


def _est_tokens(text):
    return max(0, int(len(str(text)) / 4))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("build", "open"):
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "open":
        if not OUT_FILE.exists():
            print("dashboard 未生成，请先运行 `python harness.py dashboard build`")
            return 1
        webbrowser.open("file:///" + str(OUT_FILE).replace(chr(92), "/"))
        print(f"已打开：{OUT_FILE}")
        return 0

    # build
    hs = DATA_DIR / "humanization_sidecar.db"
    nb = DATA_DIR / "notebooks.db"
    sc = DATA_DIR / "story_core.db"
    mem = DATA_DIR / "memory.db"
    has_data = any(p.exists() for p in [hs, nb, sc, mem])

    diaries = _q(hs, "SELECT * FROM diary_entries ORDER BY created_at DESC LIMIT 10") if hs.exists() else []
    episodes = _q(hs, "SELECT * FROM narrative_episodes ORDER BY created_at DESC LIMIT 15") if hs.exists() else []
    events = _q(hs, "SELECT * FROM humanization_events ORDER BY observed_at DESC LIMIT 15") if hs.exists() else []
    identities = _q(hs, "SELECT * FROM identity_entries ORDER BY created_at DESC LIMIT 20") if hs.exists() else []
    notes = _q(nb, "SELECT * FROM notebooks ORDER BY created_at DESC LIMIT 15") if nb.exists() else []
    story = _q(sc, "SELECT * FROM story_core ORDER BY created_at DESC LIMIT 10") if sc.exists() else []
    hist = _q(sc, "SELECT * FROM story_core_history ORDER BY id DESC LIMIT 15") if sc.exists() else []
    mem_total = _q(mem, "SELECT COUNT(*) c FROM memories")[0]["c"] if mem.exists() else 0
    mem_active = _q(mem, "SELECT COUNT(*) c FROM memories WHERE archived=0")[0]["c"] if mem.exists() else 0

    scopes = sorted({r["scope"] for r in episodes + notes + diaries + identities})
    roles = ", ".join(scopes) if scopes else "暂无角色数据"

    # events + usage + characters
    events = list_events(limit=15)
    usage = list_usage(limit=10)
    CHAR_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness" / "characters"
    chars = []
    if CHAR_DIR.exists():
        for d in sorted(CHAR_DIR.iterdir()):
            if not d.is_dir():
                continue
            mf = d / "package-manifest.json"
            if mf.exists():
                try:
                    m = json.loads(mf.read_text(encoding="utf-8"))
                    chars.append({"persona_id": m.get("persona_id", d.name),
                                  "display_name": m.get("display_name", d.name)})
                except Exception:
                    pass

    # estimate token
    est = {"diary": sum(_est_tokens(d.get("content")) for d in diaries),
           "episodes": sum(_est_tokens(e.get("summary")) for e in episodes),
           "notes": sum(_est_tokens(n.get("content")) for n in notes)}

    def li(items, key, fmt=None):
        if not items:
            return "<p class='muted'>暂无记录</p>"
        out = ["<ul>"]
        for it in items:
            title = it.get(key) if fmt is None else fmt(it)
            out.append(f"<li>{_html(title)[:260]}</li>")
        out.append("</ul>")
        return "\n".join(out)

    diary_html = li(diaries, "content")
    eps_html = li(episodes, "summary")
    ev_html = li(events, "metric", lambda e: f"{e.get('metric')} = {e.get('value')} · {_ts(e.get('observed_at'))}")
    note_html = li(notes, "content", lambda n: f"[v{n.get('version')}|{n.get('kind')}] {n.get('content')}")
    story_html = li(story, "content", lambda s: f"[{s.get('namespace')} v{s.get('version')}] {s.get('content')}")

    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>Harness Mind Console</title>
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self'; style-src 'unsafe-inline'; script-src 'none'">
<style>
body{{font-family:system-ui,Segoe UI,Roboto,sans-serif;margin:2rem;max-width:1100px;color:#222;background:#fafafa}}
h1{{font-size:1.5rem}} h2{{font-size:1.1rem;border-bottom:1px solid #ddd;padding-bottom:.2rem}}
.card{{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:1rem;margin:1rem 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}
.muted{{color:#888}} .ok{{color:#2e7d32}} .warn{{color:#b26a00}}
code{{background:#f0f0f0;padding:0 .3em;border-radius:3px}}
</style></head><body>
<h1>Harness Mind Console</h1>
<p class="muted">本地只读静态报告 · 不自动上传 · 不开放端口</p>
<div class="grid">
  <div class="card"><h2>角色/项目</h2>{_html(roles)}</div>
  <div class="card"><h2>记忆</h2>总数 {_html(mem_total)} · active {_html(mem_active)}</div>
  <div class="card"><h2>自动执行</h2><span class="ok">DISABLED</span></div>
  <div class="card"><h2>网络上传</h2><span class="ok">NONE</span></div>
</div>
<div class="grid">
  <div class="card"><h2>今天/最近事件</h2>{ev_html}</div>
  <div class="card"><h2>角色经历</h2>{eps_html}</div>
</div>
<div class="grid">
  <div class="card"><h2>角色日记</h2>{diary_html}</div>
  <div class="card"><h2>经历笔记</h2>{note_html}</div>
</div>
<div class="grid">
  <div class="card"><h2>共享世界设定</h2>{story_html}</div>
  <div class="card"><h2>Story Core 版本历史</h2>{li(hist,'operation',lambda h: f"v{h.get('version')} {h.get('operation')} · {_ts(h.get('created_at'))}")}</div>
</div>
<div class="card"><h2>估算上下文 token（按字符/4 估算）</h2>
<p>日记 {_html(est['diary'])} · 经历摘要 {_html(est['episodes'])} · 笔记 {_html(est['notes'])} tokens</p>
<p class="muted">估算值，不是模型真实 usage；真实 token 以 provider 为准。</p></div>
<div class="card"><h2>运行桥（文本版）</h2>
<pre>
用户输入 → Scope Resolver → [Perspective Card / Memory Recall / Notebook / Story Core / Runtime Policy]
              ↓ 跨 scope 记忆 BLOCK
              ↓ Prompt Builder
              ↓ Ollama / Qwen
              ↓ 输出 → Session Telemetry → Auto-note
</pre></div>
<div class="grid">
  <div class="card"><h2>统一事件时间线</h2>{li(events,'event_type',lambda e: f"[{_ts(e.get('recorded_at'))}] {e.get('event_type')} <span class='muted'>scope={e.get('scope')} · content={e.get('content_type')}</span>")}</div>
  <div class="card"><h2>Token / Context 面板</h2>{li(usage,'model_id',lambda u: f"actual={u.get('actual_tokens')} · baseline={u.get('baseline_tokens')} · avoided={u.get('estimated_avoided_tokens')} · {u.get('usage_source')}")}</div>
</div>
<div class="grid">
  <div class="card"><h2>角色资产</h2>{li(chars,'display_name',lambda c: f"{c.get('display_name')} <span class='muted'>({c.get('persona_id')})</span>") if chars else '<p class="muted">暂无本机角色资产</p>'}</div>
  <div class="card"><h2>隐私数据流</h2><pre>
SQLite            本地
Ollama            127.0.0.1
HTML Dashboard    本地文件
外部网络          无连接
</pre></div>
</div>
<p class="muted">生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')} · 数据目录：{_html(DATA_DIR)}</p>
</body></html>"""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(page, encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(OUT_FILE), "has_private_data": has_data,
                      "roles": len(scopes), "memories_total": mem_total}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
