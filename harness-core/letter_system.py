#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""letter_system.py — 角色间信件/交流系统（R1）。

信件只存本地 JSON，不上传。用于角色分工、知识域负责人沟通、角色间委派的可视化基础。
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HARNESS_DIR = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh")) / "harness"
LETTERS_FILE = HARNESS_DIR / "letters.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scope_utils import normalize_scope  # noqa: E402


def _load():
    if not LETTERS_FILE.exists():
        return {"schema_version": 1, "letters": []}
    try:
        return json.loads(LETTERS_FILE.read_text(encoding="utf-8")) or {"schema_version": 1, "letters": []}
    except Exception:
        return {"schema_version": 1, "letters": []}


def _save(d):
    HARNESS_DIR.mkdir(parents=True, exist_ok=True)
    LETTERS_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def send(frm, to, subject, body):
    d = _load()
    lid = "letter_" + uuid.uuid4().hex[:12]
    letter = {"id": lid, "from": frm, "to": to, "subject": subject, "body": body,
              "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "replied": False}
    d.setdefault("letters", []).append(letter)
    _save(d)
    try:
        from event_store import record_event
        record_event({"event_type": "letter.send", "scope": frm, "content_type": "fact",
                      "content_provenance": "user_declared", "session_provenance": "demo"})
    except Exception:
        pass
    return letter


def list_letters(scope=None, limit=20):
    d = _load()
    letters = d.get("letters", [])
    if scope:
        letters = [x for x in letters if x.get("from") == scope or x.get("to") == scope]
    return letters[-limit:][::-1]


def reply(letter_id, frm, body):
    d = _load()
    letters = d.get("letters", [])
    target = next((x for x in letters if x.get("id") == letter_id), None)
    if not target:
        return None
    lid = "letter_" + uuid.uuid4().hex[:12]
    reply_letter = {"id": lid, "in_reply_to": letter_id, "from": frm, "to": target.get("from"),
                    "subject": "Re: " + target.get("subject", ""), "body": body,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "replied": True}
    d.setdefault("letters", []).append(reply_letter)
    target["replied"] = True
    _save(d)
    return reply_letter


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if args and args[0] == "letter":
        args = args[1:]
    if not args:
        print(__doc__)
        return 0
    sub = args[0]
    if sub == "send":
        frm = to = subject = body = ""
        _normalize_inputs = lambda frm, to: (normalize_scope(frm), normalize_scope(to))
        i = 1
        while i < len(args):
            if args[i] == "--from" and i + 1 < len(args):
                frm = args[i + 1]; i += 2
            elif args[i] == "--to" and i + 1 < len(args):
                to = args[i + 1]; i += 2
            elif args[i] == "--subject" and i + 1 < len(args):
                subject = args[i + 1]; i += 2
            elif args[i] == "--body" and i + 1 < len(args):
                body = args[i + 1]; i += 2
            else:
                i += 1
        frm, to = _normalize_inputs(frm, to)
        if not frm or not to or not subject:
            print("用法：python harness.py letter send --from <scope> --to <scope> --subject <s> [--body <b>]")
            return 1
        letter = send(frm, to, subject, body)
        print(json.dumps({"ok": True, "letter": letter}, ensure_ascii=False, indent=2))
        return 0
    if sub == "list":
        scope = ""
        limit = 20
        i = 1
        while i < len(args):
            if args[i] == "--scope" and i + 1 < len(args):
                scope = args[i + 1]; i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1]); i += 2
            else:
                i += 1
        if scope:
            scope = normalize_scope(scope)
        letters = list_letters(scope or None, limit)
        print(json.dumps({"ok": True, "letters": letters}, ensure_ascii=False, indent=2))
        return 0
    if sub == "reply":
        lid = frm = body = ""
        i = 1
        while i < len(args):
            if args[i] == "--id" and i + 1 < len(args):
                lid = args[i + 1]; i += 2
            elif args[i] == "--from" and i + 1 < len(args):
                frm = args[i + 1]; i += 2
            elif args[i] == "--body" and i + 1 < len(args):
                body = args[i + 1]; i += 2
            else:
                i += 1
        if not lid or not frm:
            print("用法：python harness.py letter reply --id <id> --from <scope> [--body <b>]")
            return 1
        r = reply(lid, frm, body)
        if not r:
            print(json.dumps({"ok": False, "error": "letter_not_found"}, ensure_ascii=False))
            return 1
        print(json.dumps({"ok": True, "letter": r}, ensure_ascii=False, indent=2))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
