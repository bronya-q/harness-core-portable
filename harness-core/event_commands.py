#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""event_commands.py — event / usage CLI 入口。"""
import json
import sys
from pathlib import Path
from event_store import record_event, list_events, record_usage, list_usage
from scope_utils import normalize_scope

BASELINE_FILE = Path.home() / ".dsh" / "harness" / "usage-baseline.json"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def cmd_event(args):
    if not args:
        print("用法：harness.py event add|list")
        return 1
    sub = args[0]
    if sub == "add":
        scope = event_type = content_type = ""
        session_id = ""
        session_provenance = "unknown"
        content_provenance = "unknown"
        i = 1
        while i < len(args):
            if args[i] == "--scope" and i + 1 < len(args):
                scope = args[i + 1]; i += 2
            elif args[i] == "--event-type" and i + 1 < len(args):
                event_type = args[i + 1]; i += 2
            elif args[i] == "--content-type" and i + 1 < len(args):
                content_type = args[i + 1]; i += 2
            elif args[i] == "--session-id" and i + 1 < len(args):
                session_id = args[i + 1]; i += 2
            elif args[i] == "--session-provenance" and i + 1 < len(args):
                session_provenance = args[i + 1]; i += 2
            elif args[i] == "--content-provenance" and i + 1 < len(args):
                content_provenance = args[i + 1]; i += 2
            else:
                i += 1
        scope = normalize_scope(scope)
        if not scope or not event_type:
            print("用法：harness.py event add --scope <s> --event-type <t> [--content-type <c>] [--session-id <id>] "
                  "[--session-provenance real|demo|smoke|regression|unknown] "
                  "[--content-provenance observed|derived|inferred|unknown]")
            return 1
        eid = record_event({"event_type": event_type, "scope": scope, "content_type": content_type or "fact",
                            "session_id": session_id or None,
                            "session_provenance": session_provenance,
                            "content_provenance": content_provenance,
                            "occurred_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")})
        print(json.dumps({"ok": True, "event_id": eid}, ensure_ascii=False))
        return 0
    if sub == "list":
        limit = 20
        scope = None
        i = 1
        while i < len(args):
            if args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1]); i += 2
            elif args[i] == "--scope" and i + 1 < len(args):
                scope = args[i + 1]; i += 2
            else:
                i += 1
        if scope:
            scope = normalize_scope(scope)
        print(json.dumps({"ok": True, "events": list_events(limit, scope)}, ensure_ascii=False, indent=2))
        return 0
    print("未知 event 子命令：" + sub)
    return 1


def cmd_usage(args):
    if not args:
        print("用法：harness.py usage record|list")
        return 1
    sub = args[0]
    if sub == "record":
        u = {"usage_source": "character_estimate", "model_id": "undisclosed", "actual_tokens": 0,
             "baseline_id": "all_eligible_same_scope", "baseline_tokens": 0, "estimated_avoided_tokens": 0,
             "components": {}}
        i = 1
        while i < len(args):
            if args[i] == "--actual" and i + 1 < len(args):
                u["actual_tokens"] = int(args[i + 1]); i += 2
            elif args[i] == "--baseline" and i + 1 < len(args):
                u["baseline_tokens"] = int(args[i + 1]); i += 2
            elif args[i] == "--avoided" and i + 1 < len(args):
                u["estimated_avoided_tokens"] = int(args[i + 1]); i += 2
            elif args[i] == "--model" and i + 1 < len(args):
                u["model_id"] = args[i + 1]; i += 2
            elif args[i] == "--source" and i + 1 < len(args):
                u["usage_source"] = args[i + 1]; i += 2
            elif args[i] == "--components" and i + 1 < len(args):
                try:
                    u["components"] = json.loads(args[i + 1])
                except Exception:
                    u["components"] = {}
                i += 2
            else:
                i += 1
        uid = record_usage(u)
        print(json.dumps({"ok": True, "usage_id": uid}, ensure_ascii=False))
        return 0
    if sub == "list":
        limit = 20
        i = 1
        while i < len(args):
            if args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1]); i += 2
            else:
                i += 1
        print(json.dumps({"ok": True, "usage": list_usage(limit)}, ensure_ascii=False, indent=2))
        return 0
    if sub == "summary":
        rows = list_usage(limit=1000)
        actual = sum(r.get("actual_tokens") or 0 for r in rows)
        baseline = sum(r.get("baseline_tokens") or 0 for r in rows)
        avoided = sum(r.get("estimated_avoided_tokens") or 0 for r in rows)
        by_source = {}
        for r in rows:
            src = r.get("usage_source") or "unknown"
            by_source.setdefault(src, {"rows": 0, "actual_tokens": 0})
            by_source[src]["rows"] += 1
            by_source[src]["actual_tokens"] += r.get("actual_tokens") or 0
        by_provider = {}
        for r in rows:
            prov = r.get("provider") or "unreported"
            by_provider.setdefault(prov, {"rows": 0, "prompt_tokens": 0, "completion_tokens": 0})
            by_provider[prov]["rows"] += 1
            by_provider[prov]["prompt_tokens"] += r.get("prompt_tokens") or 0
            by_provider[prov]["completion_tokens"] += r.get("completion_tokens") or 0
        print(json.dumps({"ok": True, "mode": "usage_summary", "rows": len(rows),
                          "actual_tokens": actual, "baseline_tokens": baseline,
                          "avoided_tokens": avoided, "by_source": by_source,
                          "by_provider": by_provider}, ensure_ascii=False, indent=2))
        return 0
    if sub == "baseline":
        bsub = args[1] if len(args) > 1 else ""
        if bsub == "set":
            base_tokens = 0
            base_id = "all_eligible_same_scope"
            i = 2
            while i < len(args):
                if args[i] == "--baseline-tokens" and i + 1 < len(args):
                    base_tokens = int(args[i + 1]); i += 2
                elif args[i] == "--baseline-id" and i + 1 < len(args):
                    base_id = args[i + 1]; i += 2
                else:
                    i += 1
            BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {"baseline_tokens": base_tokens, "baseline_id": base_id, "set_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")}
            BASELINE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
            print(json.dumps({"ok": True, "baseline": data}, ensure_ascii=False, indent=2))
            return 0
        if bsub == "check":
            if not BASELINE_FILE.exists():
                print(json.dumps({"ok": False, "error": "baseline_not_set"}, ensure_ascii=False))
                return 1
            base = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
            rows = list_usage(limit=1000)
            actual = sum(r.get("actual_tokens") or 0 for r in rows)
            ok = actual <= base.get("baseline_tokens", 0)
            print(json.dumps({"ok": ok, "mode": "usage_baseline_check",
                              "baseline_tokens": base.get("baseline_tokens"), "actual_tokens": actual,
                              "within_baseline": ok}, ensure_ascii=False, indent=2))
            return 0 if ok else 1
        print("用法：usage baseline set|check")
        return 1
    print("未知 usage 子命令：" + sub)
    return 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if args[0] == "event":
        return cmd_event(args[1:])
    if args[0] == "usage":
        return cmd_usage(args[1:])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
