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
from vector_queue import queue_status  # noqa: E402
import assets_commands  # noqa: E402
import runtime_policy  # noqa: E402
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


def _display_data_dir():
    try:
        home = str(Path.home()).lower()
        dd = str(DATA_DIR)
        if dd.lower().startswith(home):
            return "~" + dd[len(str(Path.home())):]
        if "harness-demo-" in dd.lower():
            return "<demo>/.dsh/memory-emotion"
        return dd
    except Exception:
        return str(DATA_DIR)


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
    t0 = time.perf_counter()

    diaries = _q(hs, "SELECT * FROM diary_entries ORDER BY created_at DESC LIMIT 10") if hs.exists() else []
    episodes = _q(hs, "SELECT * FROM narrative_episodes ORDER BY created_at DESC LIMIT 15") if hs.exists() else []
    events = _q(hs, "SELECT * FROM humanization_events ORDER BY observed_at DESC LIMIT 15") if hs.exists() else []
    identities = _q(hs, "SELECT * FROM identity_entries ORDER BY created_at DESC LIMIT 20") if hs.exists() else []
    humanization_read_ms = (time.perf_counter() - t0) * 1000

    notes = _q(nb, "SELECT * FROM notebooks ORDER BY created_at DESC LIMIT 15") if nb.exists() else []
    story = _q(sc, "SELECT * FROM story_core ORDER BY created_at DESC LIMIT 10") if sc.exists() else []
    hist = _q(sc, "SELECT * FROM story_core_history ORDER BY id DESC LIMIT 15") if sc.exists() else []
    mem_total = _q(mem, "SELECT COUNT(*) c FROM memories")[0]["c"] if mem.exists() else 0
    mem_active = _q(mem, "SELECT COUNT(*) c FROM memories WHERE archived=0")[0]["c"] if mem.exists() else 0
    storage_read_ms = (time.perf_counter() - t0) * 1000

    scopes = sorted({r["scope"] for r in episodes + notes + diaries + identities})
    roles = ", ".join(scopes) if scopes else "暂无角色数据"

    # events + usage + characters
    events = list_events(limit=15)
    usage = list_usage(limit=10)
    event_usage_read_ms = (time.perf_counter() - t0) * 1000
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
                                  "display_name": m.get("display_name", d.name),
                                  "scope": m.get("scope", "character:" + d.name),
                                  "role_types": m.get("role_types", []),
                                  "knowledge_bindings": m.get("knowledge_bindings", []),
                                  "distribution": m.get("distribution", "private_local")})
                except Exception:
                    pass

    char_read_ms = (time.perf_counter() - t0) * 1000
    total_ms = (time.perf_counter() - t0) * 1000
    spans = [
        ("Humanization reads", round(humanization_read_ms, 1)),
        ("Notebook/Story/Memory reads", round(storage_read_ms - humanization_read_ms, 1)),
        ("Event/Usage reads", round(event_usage_read_ms - storage_read_ms, 1)),
        ("Character assets", round(char_read_ms - event_usage_read_ms, 1)),
        ("Total data collection", round(total_ms, 1)),
    ]

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
    from collections import Counter
    def prov_counts(items, key):
        counts = Counter((x.get(key) or "unknown") for x in items)
        if not counts:
            return "<p class='muted'>暂无事件</p>"
        return "".join(f"<span class='prov-chip'>{_html(k)} {_html(v)}</span> " for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    provenance_html = f"<p>Session provenance（会话来源）：{prov_counts(events, 'session_provenance')}</p>"
    provenance_html += f"<p>Content provenance（内容来源）：{prov_counts(events, 'content_provenance')}</p>"

    # 知识域/向量队列/usage 可视化（纯 CSS，无 JS，符合 CSP）
    try:
        kh = assets_commands._knowledge_health()
        mounts = assets_commands._load_mounts().get("mounts", [])
    except Exception:
        kh = {"ok": False, "checks": []}
        mounts = []
    kn_html = ""
    if kh.get("checks"):
        for c in kh["checks"]:
            pct = {"ok": 100, "unreadable": 50, "missing": 0, "not_dir": 0}.get(c.get("status"), 0)
            kn_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:%d%%'>%s</div></div>"
                        % (_html(c.get("display_name") or c.get("source_id")), pct, _html(c.get("status"))))
    else:
        kn_html = "<p class='muted'>暂无知识源配置。</p>"
    if mounts:
        kn_html += "<p class='muted'>挂载登记：</p>"
        for m in mounts[:6]:
            kn_html += "<p class='muted'>- %s ↔ %s · %s</p>" % (_html(m.get("persona_id")), _html(m.get("source_id")), _html(m.get("mount_mode") or "read_only"))

    try:
        vq = queue_status()
    except Exception:
        vq = {"ok": False}
    vq_html = ""
    vq_total = int(vq.get("total") or 0)
    if vq_total > 0:
        for key in ("pending", "processing", "deferred", "done", "failed"):
            val = int(vq.get(key) or 0)
            pct = int(round(val * 100 / max(1, vq_total)))
            vq_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:%d%%'>%d</div></div>"
                        % (_html(key), pct, val))
        vq_html += "<p class='muted'>retryable=%s · stale=%s</p>" % (_html(vq.get("retryable", 0)), _html(vq.get("stale", 0)))
    else:
        vq_html = "<p class='muted'>暂无向量队列记录。</p>"

    by_provider = {}
    for u in usage:
        prov = u.get("provider") or "unreported"
        by_provider.setdefault(prov, {"rows": 0, "tokens": 0})
        by_provider[prov]["rows"] += 1
        by_provider[prov]["tokens"] += u.get("actual_tokens") or 0
    max_tokens = max([v["tokens"] for v in by_provider.values()] + [1])
    prov_html = ""
    for prov, v in sorted(by_provider.items(), key=lambda kv: (-kv[1]["tokens"], kv[0])):
        pct = int(round(v["tokens"] * 100 / max_tokens))
        prov_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:%d%%'>%d tokens · %d rows</div></div>"
                      % (_html(prov), pct, v["tokens"], v["rows"]))
    if not prov_html:
        prov_html = "<p class='muted'>暂无 usage。</p>"

    # 最近写操作（可撤销预览）
    notes_db = DATA_DIR / "notebooks.db"
    manual_notes = _q(notes_db, "SELECT id,scope,kind,content,version,status,created_at FROM notebooks WHERE kind='manual' ORDER BY created_at DESC LIMIT 8")
    manual_html = ""
    if manual_notes:
        for n in manual_notes:
            status = "active" if n.get("status") in (None, "", "active") else n.get("status")
            undo_hint = ("python harness.py memory undo --id %s" % n.get("id")) if status == "active" else "已归档，可用 restore 恢复"
            manual_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:100%%'>v%s · %s</div>"
                            "<span class='st-muted'>%s · %s</span></div>"
                            % (_html(n.get("scope")), _html(n.get("version")), _html(status),
                               _html((n.get("content") or "")[:60]), _html(undo_hint)))
    else:
        manual_html = "<p class='muted'>暂无手动写操作记录。</p>"

    # 工程工作区 / Evidence / A-B 可视化
    ws_dir = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness" / "workspaces"
    workspaces = []
    if ws_dir.exists():
        for d in sorted(ws_dir.iterdir()):
            if d.is_dir() and (d / "workspace.json").exists():
                try:
                    w = json.loads((d / "workspace.json").read_text(encoding="utf-8"))
                    workspaces.append({"name": d.name, **w})
                except Exception:
                    pass
    ws_html = ""
    if workspaces:
        for w in workspaces[:8]:
            st = w.get("status", "unknown")
            ws_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:100%%'>%s</div>"
                        "<span class='st-muted'>role=%s · worktree=%s · actual_execution=%s</span></div>"
                        % (_html(w.get("name")), _html(st), _html(w.get("role") or "-"),
                           _html(w.get("worktree_path") or "-"), _html(w.get("actual_execution"))))
    else:
        ws_html = "<p class='muted'>暂无工作区 lease。</p>"

    ev_dir = SKILL.parent / "docs" / "evidence"
    evidence = []
    if ev_dir.exists():
        for fp in sorted(ev_dir.glob("*.json")):
            try:
                d = json.loads(fp.read_text(encoding="utf-8"))
                evidence.append({"task_id": d.get("task_id", fp.stem),
                                 "working_tree": d.get("working_tree", "?"),
                                 "checks": len(d.get("checks", [])),
                                 "unverified": len(d.get("unverified", [])),
                                 "approval_required": d.get("approval_required", True),
                                 "source": fp.name})
            except Exception:
                pass
    ev_html = ""
    if evidence:
        for ev in evidence[:8]:
            ev_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:80%%'>%s</div>"
                        "<span class='st-muted'>checks=%s · unverified=%s · approval=%s</span></div>"
                        % (_html(ev.get("task_id")), _html(ev.get("working_tree")),
                           _html(ev.get("checks")), _html(ev.get("unverified")), _html(ev.get("approval_required"))))
    else:
        ev_html = "<p class='muted'>暂无 evidence 包。</p>"

    ab_records = []
    if ev_dir.exists():
        for fp in sorted(ev_dir.glob("ab-*.json")):
            try:
                d = json.loads(fp.read_text(encoding="utf-8"))
                ab_records.append({"source": fp.name, "mode": d.get("mode"),
                                   "a": d.get("retriever_a", {}).get("name") or d.get("a", {}).get("file"),
                                   "b": d.get("retriever_b", {}).get("name") or d.get("b", {}).get("file"),
                                   "generated_at": d.get("generated_at", "")})
            except Exception:
                pass
    ab_html = ""
    if ab_records:
        for r in ab_records[:10]:
            ab_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:80%%'>%s</div>"
                        "<span class='st-muted'>%s vs %s · %s</span></div>"
                        % (_html(r.get("mode") or "ab"), _html(r.get("source")),
                           _html(r.get("a") or "?"), _html(r.get("b") or "?"), _html(r.get("generated_at"))))
    else:
        ab_html = "<p class='muted'>暂无 A/B 记录（用 `ab role/retriever --save <name>` 可保存）。</p>"

    suggest_hist = []
    hist_path = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness" / "knowledge-suggest-history.json"
    if hist_path.exists():
        try:
            hd = json.loads(hist_path.read_text(encoding="utf-8"))
            suggest_hist = hd.get("entries", []) if isinstance(hd, dict) else []
        except Exception:
            pass
    suggest_html = ""
    if suggest_hist:
        for e in suggest_hist[:8]:
            suggest_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:70%%'>%s</div>"
                             "<span class='st-muted'>%s · sources=%s · matches=%s</span></div>"
                             % (_html(e.get("role") or "?"), _html((e.get("question") or "")[:40]),
                                _html(e.get("at", "")), _html(e.get("sources", 0)), _html(e.get("matches", 0))))
    else:
        suggest_html = "<p class='muted'>暂无 knowledge suggest 记录。</p>"

    web_html = "<p>Workspaces: %d · Evidence: %d · A/B: %d · Suggest: %d</p>" % (len(workspaces), len(evidence), len(ab_records), len(suggest_hist))

    # 公共边界快照（粗略扫描，不替代人工审查）
    boundary_patterns = [
        ("demo-alice", ["demo-alice"]),
        ("demo-storykeeper", ["demo-storykeeper"]),
        ("demo-bob", ["demo-bob"]),
        ("local-persona", ["local-persona"]),
        ("本机知识管理员 A", ["本机知识管理员 A"]),
        ("本机知识管理员 B", ["本机知识管理员 B"]),
        ("本机综合人格 A", ["本机综合人格 A"]),
        ("windows_abs_path", [r"c:\users", "c:/users", r"c:\documents", "c:/documents"]),
        ("private_overlay", [".dsh/harness-local", "personas.local.json"]),
    ]
    boundary_files = ["README.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE"]
    found = []
    for rel in boundary_files:
        f = SKILL.parent / rel
        if not f.exists():
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for label, needles in boundary_patterns:
            for needle in needles:
                if needle.lower() in txt.lower():
                    found.append({"file": rel, "pattern": label, "count": txt.lower().count(needle.lower())})
    boundary_html = ""
    if found:
        for item in found[:12]:
            boundary_html += ("<div class='hb-row'><span>%s</span><div class='hb' style='width:100%%'>%s</div>"
                              "<span class='st-muted'>%s · x%d</span></div>"
                              % (_html(item["file"]), _html(item["pattern"]), _html(item["file"]), item["count"]))
        boundary_html += "<p class='st-muted'>⚠️ 命中公共文件，需人工确认是否属于边界文档/示例。</p>"
    else:
        boundary_html = "<p class='ok'>未在关键公开文件中命中明显私人标识/绝对路径。</p>"

    # 运行桥彩色状态条（纯 CSS CSP-safe）
    try:
        policy = runtime_policy.load()
    except Exception:
        policy = {}
    flags = policy.get("flags", {}) if isinstance(policy, dict) else {}
    bounds = policy.get("_bounds", {}) if isinstance(policy, dict) else {}
    dyn_mode = flags.get("dynamic_memory", "shadow")
    g1_mode = flags.get("g1_expression", "canary")

    def _status_bar(label, state, color, extra=""):
        pct = {"ok": 100, "warn": 70, "block": 20, "info": 50}.get(color.split("_")[0] if "_" in color else color, 50)
        cls = {"green": "st-green", "yellow": "st-yellow", "red": "st-red", "blue": "st-blue"}.get(color, "st-blue")
        return ("<div class='st-row'><span class='st-label'>%s</span>"
                "<div class='st-bar %s' style='width:%d%%'>%s</div>"
                "<span class='st-muted'>%s</span></div>"
                % (_html(label), cls, pct, _html(state), _html(extra)))

    bridge_html = _status_bar("① Scope Resolver", "已解析", "green",
                              "角色/项目 %d 个；跨角色默认 BLOCK" % len(scopes))
    bridge_html += _status_bar("② Perspective Card", "已加载", "green",
                               "%s 角色资产" % (", ".join(scopes[:2]) if scopes else "暂无"))
    bridge_html += _status_bar("③ Memory Recall", dyn_mode, {"canary": "yellow", "shadow": "yellow", "disabled": "blue"}.get(dyn_mode, "yellow"),
                               "active %d 条；recall limit %s" % (mem_active, bounds.get("dynamic_memory", {}).get("max_recall_items", "N/A")))
    bridge_html += _status_bar("④ Notebook / Story Core", "%d 笔记 / v%s" % (len(notes), (story[0].get("version") if story else "-")),
                               "green" if notes or story else "blue", "本地只读")
    bridge_html += _status_bar("⑤ Runtime Policy", "autonomous disabled", "green",
                               "network NONE · g1=%s" % (g1_mode or "canary"))
    bridge_html += _status_bar("⑥ Model → Output → Telemetry", "记录", "green" if usage else "blue",
                               "usage %d 条 · provider_reported=%d" % (len(usage), sum(1 for u in usage if u.get("usage_source") == "provider_reported")))

    # 知识域关系网格：角色 ↔ 知识域 ↔ 权限
    roles_for_grid = [c.get("persona_id") for c in chars] or ["demo-archivist"]
    sources_for_grid = kh.get("checks", [])
    grid_html = "<div class='kgrid'><div class='kgrid-row kgrid-head'><span>角色</span>"
    for c in sources_for_grid:
        grid_html += "<span>%s</span>" % _html(c.get("display_name") or c.get("source_id"))
    grid_html += "</div>"
    for role in roles_for_grid[:10]:
        grid_html += "<div class='kgrid-row'><span class='kgrid-role'>%s</span>" % _html(role)
        for c in sources_for_grid:
            stewards = c.get("stewards", [])
            bound = c.get("bound_roles", [])
            if role in stewards:
                cell = ("<span class='kgrid-cell st-green'>steward<small>read/quote/summarize/propose_edit</small></span>")
            elif role in bound:
                cell = ("<span class='kgrid-cell st-blue'>reader<small>read/quote</small></span>")
            elif c.get("default_access") == "deny":
                cell = ("<span class='kgrid-cell st-red'>blocked<small>none</small></span>")
            else:
                cell = ("<span class='kgrid-cell st-yellow'>guest<small>read</small></span>")
            grid_html += cell
        grid_html += "</div>"

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
.char-gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.8rem}}
.char-card{{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:.8rem}}
.char-card h3{{margin:.1rem 0 .4rem;font-size:1rem}}
.span-track{{display:flex;gap:2px;align-items:flex-end;flex-wrap:wrap}}
.span-bar{{background:#8bb8d8;color:#fff;padding:.2rem .4rem;border-radius:4px;font-size:.75rem;white-space:nowrap;min-width:64px}}
.span-muted{{color:#888}}
code{{background:#f0f0f0;padding:0 .3em;border-radius:3px}}
.prov-chip{{display:inline-block;background:#eef2f7;border:1px solid #d8e0ea;border-radius:4px;padding:.1rem .35rem;margin:.1rem;font-size:.8rem}}
.hb-row{{display:flex;align-items:center;gap:.5rem;margin:.3rem 0;font-size:.85rem}}
.hb-row>span{{width:130px;flex-shrink:0;text-align:right;color:#444}}
.hb{{background:#8bb8d8;color:#fff;border-radius:3px;padding:.15rem .3rem;min-width:2rem;font-size:.75rem;white-space:nowrap}}
.st-row{{display:flex;align-items:center;gap:.5rem;margin:.35rem 0;font-size:.85rem}}
.st-label{{width:160px;flex-shrink:0;text-align:right;color:#444}}
.st-bar{{color:#fff;border-radius:3px;padding:.15rem .3rem;font-size:.75rem;white-space:nowrap;min-width:3rem;text-align:center}}
.st-green{{background:#2e7d32}} .st-yellow{{background:#f9a825}} .st-red{{background:#c62828}} .st-blue{{background:#1565c0}}
.st-muted{{color:#888;font-size:.8rem;margin-left:.3rem}}
.kgrid{{display:grid;gap:.3rem;font-size:.8rem}}
.kgrid-row{{display:grid;grid-template-columns:130px repeat(auto-fit,minmax(110px,1fr));gap:.3rem;align-items:center}}
.kgrid-head span{{font-weight:bold;background:#eef2f7;border-radius:4px;padding:.3rem}}
.kgrid-role{{background:#f5f5f5;border-radius:4px;padding:.3rem}}
.kgrid-cell{{border-radius:4px;padding:.3rem;text-align:center;color:#fff}}
.kgrid-cell small{{display:block;font-size:.65rem;opacity:.85;margin-top:.1rem}}
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
<div class="card"><h2>运行桥（彩色状态条）</h2>
<div class="st-track">{bridge_html}</div>
<p class="st-muted">状态条为只读投影，不表示真实推理/接线；颜色只表示当前本地状态。</p>
</div>
<div class="card"><h2>知识域关系网格（角色 ↔ 知识域 ↔ 权限）</h2>
<div class="kgrid">{grid_html}</div>
<p class="st-muted">grid 只显示本地角色资产与知识源配置；没有真实知识正文访问。</p>
</div>
<div class="grid">
  <div class="card"><h2>知识域与挂载</h2>{kn_html}</div>
  <div class="card"><h2>向量队列</h2>{vq_html}</div>
</div>
<div class="card"><h2>Token 来源 / Provider</h2>{prov_html}</div>
<div class="card"><h2>最近写操作（可撤销预览）</h2>{manual_html}</div>
<div class="card"><h2>工程工作区 / Evidence</h2>{web_html}<div class="grid" style="margin-top:.4rem"><div class="card" style="margin:0"><h2>Workspace</h2>{ws_html}</div><div class="card" style="margin:0"><h2>Evidence Bundle</h2>{ev_html}</div></div></div>
<div class="card"><h2>A/B 记录</h2>{ab_html}</div>
<div class="card"><h2>知识桥 Suggest 历史</h2>{suggest_html}</div>
<div class="card"><h2>公共边界快照</h2>{boundary_html}</div>
<div class="grid">
  <div class="card"><h2>统一事件时间线</h2>{li(events,'event_type',lambda e: f"[{_ts(e.get('recorded_at'))}] {e.get('event_type')} <span class='muted'>scope={e.get('scope')} · content={e.get('content_type')}</span>")}</div>
  <div class="card"><h2>Token / Context 面板</h2>{li(usage,'model_id',lambda u: f"actual={u.get('actual_tokens')} · baseline={u.get('baseline_tokens')} · avoided={u.get('estimated_avoided_tokens')} · {u.get('usage_source')}")}</div>
</div>
<div class="card"><h2>数据来源分组</h2>{provenance_html}</div>
<div class="card"><h2>Span 时间线（数据读取真实耗时）</h2>
<div class="span-track">
{''.join(f"<div class='span-bar' style='flex-grow:{v}'> {n}</div>" for n,v in spans)}
</div>
<p class="span-muted">当前为 Dashboard 数据读取的真实耗时；不包含 HTML 渲染与模型推理 span。</p>
</div>
<div class="grid">
  <div class="card"><h2>角色画廊</h2>
  <div class="char-gallery">
  {''.join(f"<div class='char-card'><h3>{_html(c.get('display_name'))}</h3><p>{_html(c.get('persona_id'))}</p><p class='muted'>scope: {_html(c.get('scope'))}</p><p class='muted'>role: {_html(', '.join(c.get('role_types') or []))}</p><p class='muted'>knowledge: {len(c.get('knowledge_bindings') or [])} · dist: {_html(c.get('distribution'))}</p></div>" for c in chars) if chars else '<p class="muted">暂无本机角色资产</p>'}
  </div>
  </div>
  <div class="card"><h2>隐私数据流</h2><pre>
SQLite            本地
Ollama            127.0.0.1
HTML Dashboard    本地文件
外部网络          无连接
</pre></div>
</div>
<p class="muted">生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')} · 数据目录：{_html(_display_data_dir())}</p>
</body></html>"""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(page, encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(OUT_FILE), "has_private_data": has_data,
                      "roles": len(scopes), "memories_total": mem_total}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
