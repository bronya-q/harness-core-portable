#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_write_confirm.py — 本地网页确认写入（loopback only）。

在浏览器里点“确认写入”后，才真正写入 notebook。不会自动上传，不开放外部端口。
"""
import json
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent


def _write(scope, text):
    p = subprocess.run([sys.executable, str(SKILL / "notebook.py"), "note",
                        "--scope", scope, "--text", text, "--kind", "manual"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    try:
        return json.loads(p.stdout), p.returncode
    except Exception:
        return {"ok": False, "raw": p.stdout[-300:], "stderr": p.stderr[-300:]}, p.returncode


class Handler(BaseHTTPRequestHandler):
    scope = ""
    text = ""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>Memory Write Confirm</title>
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'unsafe-inline'; script-src 'none'">
<style>body{{font-family:system-ui;margin:2rem;max-width:640px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}}
button{{font-size:1rem;padding:.5rem 1rem}}</style></head><body>
<h1>写操作确认</h1>
<div class="card"><h2>Scope</h2><p>{self.scope}</p></div>
<div class="card"><h2>内容</h2><p>{self.text}</p></div>
<form method="post" action="/confirm">
<input type="hidden" name="scope" value="{self.scope}">
<input type="hidden" name="text" value="{self.text}">
<button type="submit">确认写入</button>
</form>
<p>不会自动上传；本页只监听 127.0.0.1。</p>
</body></html>"""
        self.wfile.write(body.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length).decode("utf-8")
        qs = parse_qs(raw)
        scope = qs.get("scope", [self.scope])[0]
        text = qs.get("text", [self.text])[0]
        result, rc = _write(scope, text)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        safe_id = (result.get("id") if isinstance(result, dict) else None) or "?"
        body = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>Write Result</title></head><body><h1>写入结果</h1>
<p>ok={result.get("ok")} · id={safe_id} · version={result.get("version")}</p>
<p>撤销命令：<code>python harness.py memory undo --id {safe_id}</code></p>
<p><a href="/">再写一条</a></p></body></html>"""
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *args):
        pass


def main():
    import argparse
    args_all = sys.argv[1:]
    if args_all and args_all[0] == "memory-write-confirm":
        args_all = args_all[1:]
    sys.argv = [sys.argv[0]] + args_all
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()
    Handler.scope = args.scope
    Handler.text = args.text
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(json.dumps({"ok": True, "mode": "memory_write_confirm",
                      "url": "http://127.0.0.1:%d/" % args.port,
                      "note": "监听 loopback；点确认后才写入。"}, ensure_ascii=False))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
