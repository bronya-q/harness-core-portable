#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""schema_commands.py — 统一 schema 清单与基础校验。

用法：
  python harness.py schema list
  python harness.py schema validate --role <file>
  python harness.py schema validate --event <file>
  python harness.py schema validate --token <file>
  python harness.py schema validate --mode <file>
  python harness.py schema validate --measurement <file>
  python harness.py schema validate --adapter-permission <file>
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
SCHEMAS = {
    "unified-role": SCHEMAS_DIR / "unified-role.schema.json",
    "event-envelope": SCHEMAS_DIR / "event-envelope.schema.json",
    "token-usage": SCHEMAS_DIR / "token-usage.schema.json",
    "situated-mode": SCHEMAS_DIR / "situated-mode.schema.json",
    "measurement": SCHEMAS_DIR / "measurement.schema.json",
    "adapter-permission": SCHEMAS_DIR / "adapter-permission.schema.json",
}


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _validate_required(obj, schema):
    issues = []
    missing = [k for k in schema.get("required", []) if k not in obj]
    issues.extend("missing:" + k for k in missing)
    props = schema.get("properties", {})
    for key, spec in props.items():
        if key not in obj:
            continue
        val = obj[key]
        expected = spec.get("type")
        if expected and isinstance(expected, list):
            if type(val).__name__ not in expected and val is not None:
                issues.append("type_mismatch:%s:expected=%s" % (key, expected))
        elif expected and expected in ("string", "integer", "number", "boolean", "array", "object"):
            if expected == "integer" and not isinstance(val, int):
                issues.append("type_mismatch:%s:expected=integer" % key)
            elif expected == "number" and not isinstance(val, (int, float)):
                issues.append("type_mismatch:%s:expected=number" % key)
            elif expected == "boolean" and not isinstance(val, bool):
                issues.append("type_mismatch:%s:expected=boolean" % key)
            elif expected == "string" and not isinstance(val, str):
                issues.append("type_mismatch:%s:expected=string" % key)
            elif expected == "array" and not isinstance(val, list):
                issues.append("type_mismatch:%s:expected=array" % key)
            elif expected == "object" and not isinstance(val, dict):
                issues.append("type_mismatch:%s:expected=object" % key)
        enum = spec.get("enum")
        if enum and val not in enum:
            issues.append("enum_mismatch:%s:%s not in %s" % (key, val, enum))
    return issues


def cmd_list():
    items = []
    for name, path in SCHEMAS.items():
        items.append({"name": name, "path": str(path), "exists": path.exists()})
    print(json.dumps({"ok": True, "schemas": items}, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(kind, path):
    schema_key = {"--role": "unified-role", "--event": "event-envelope", "--token": "token-usage",
                  "--mode": "situated-mode", "--measurement": "measurement",
                  "--adapter-permission": "adapter-permission"}.get(kind)
    if not schema_key or schema_key not in SCHEMAS:
        print(json.dumps({"ok": False, "error": "invalid_schema_type", "type": kind}, ensure_ascii=False))
        return 1
    if not path:
        print(f"用法：python harness.py schema validate {kind} <file>")
        return 1
    sp = Path(path)
    if not sp.exists():
        print(json.dumps({"ok": False, "error": "file_not_found", "path": str(sp)}, ensure_ascii=False))
        return 1
    try:
        obj = _load(sp)
        schema = _load(SCHEMAS[schema_key])
    except Exception as e:
        print(json.dumps({"ok": False, "error": "invalid_json", "detail": str(e)}, ensure_ascii=False))
        return 1
    issues = []
    targets = []
    if isinstance(obj, dict) and isinstance(obj.get("modes"), list):
        parent_scalars = {k: v for k, v in obj.items() if k != "modes"}
        targets = [(f"modes[{i}]", {**parent_scalars, **item})
                   for i, item in enumerate(obj["modes"]) if isinstance(item, dict)]
        if not targets:
            issues.append("modes:empty_or_invalid")
    elif isinstance(obj, list):
        targets = [(f"[{i}]", item) for i, item in enumerate(obj) if isinstance(item, dict)]
        if not targets:
            issues.append("root:empty_or_invalid")
    else:
        targets = [("root", obj)]
    for label, item in targets:
        for issue in _validate_required(item, schema):
            issues.append(f"{label}:{issue}")
    ok = not issues
    print(json.dumps({"ok": ok, "schema": schema_key, "path": str(sp), "issues": issues},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if args[0] == "schema":
        args = args[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0]
    if cmd == "list":
        return cmd_list()
    if cmd == "validate":
        kind = ""
        path = None
        i = 1
        while i < len(args):
            if args[i] in ("--role", "--event", "--token", "--mode", "--measurement", "--adapter-permission"):
                kind = args[i]
                if i + 1 < len(args):
                    path = args[i + 1]
                    break
            i += 1
        return cmd_validate(kind, path)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
