#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plugin_sandbox.py — 高风险插件沙盒隔离/禁用看板。

配置：plugin_sandbox.json
模式：
  disabled   禁止运行
  sandbox    只在隔离临时目录 + DSH_SANDBOX=1 下运行
  allowed    允许正常运行
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CFG = Path(__file__).resolve().parent / "plugin_sandbox.json"
DEFAULT = {
    "schema_version": 1,
    "plugins": {
        "deepseek-eyes-src": {"mode": "disabled", "reason": "用户指定不用，含大量二进制/第三方产物"},
        "dsh-openbiliclaw": {"mode": "disabled", "reason": "用户指定不用，第三方 npm 插件未完整审计"},
        "dsh-crew": {"mode": "sandbox", "reason": "原生依赖 koffi/node-pty，需隔离运行"},
        "dsh-bili-agent": {"mode": "sandbox", "reason": "含测试 secret 占位符，先隔离"},
    },
}


def load():
    if not CFG.exists():
        return DEFAULT
    try:
        data = json.loads(CFG.read_text(encoding="utf-8"))
        return {**DEFAULT, **data}
    except Exception:
        return DEFAULT


def save(data):
    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def status(args):
    data = load()
    print(json.dumps({"ok": True, "config": data["plugins"]}, ensure_ascii=False, indent=2))


def set_mode(args):
    data = load()
    if args.name not in data["plugins"]:
        print(json.dumps({"ok": False, "error": "unknown plugin", "name": args.name}, ensure_ascii=False, indent=2))
        return 1
    data["plugins"][args.name]["mode"] = args.mode
    data["plugins"][args.name]["reason"] = args.reason or data["plugins"][args.name].get("reason", "")
    save(data)
    print(json.dumps({"ok": True, "updated": data["plugins"][args.name]}, ensure_ascii=False, indent=2))
    return 0


def _plugin_root(name):
    for base in [Path.home() / "Documents" / "harness", Path.home() / ".dsh" / "profiles" / "node_modules"]:
        cand = base / name
        if cand.exists() and cand.is_dir():
            return cand
    return None


def run(args):
    data = load()
    info = data["plugins"].get(args.name)
    if not info:
        print(json.dumps({"ok": False, "error": "unknown plugin"}, ensure_ascii=False, indent=2))
        return 1
    mode = info.get("mode", "allowed")
    if mode == "disabled":
        print(json.dumps({"ok": False, "error": "plugin_disabled", "name": args.name,
                          "reason": info.get("reason")}, ensure_ascii=False, indent=2))
        return 1
    cmd = args.cmd
    workdir = args.workdir or str(_plugin_root(args.name) or Path.cwd())
    if mode == "sandbox":
        with tempfile.TemporaryDirectory(prefix="dsh-sandbox-") as td:
            env = dict(os.environ)
            env["DSH_SANDBOX"] = "1"
            env["CI"] = "true"
            env["TMP"] = td
            env["TEMP"] = td
            env["TMPDIR"] = td
            env.pop("DSH_ALLOW_NETWORK", None)
            if args.no_network:
                env["HTTP_PROXY"] = "http://127.0.0.1:9"
                env["HTTPS_PROXY"] = "http://127.0.0.1:9"
                env["ALL_PROXY"] = "http://127.0.0.1:9"
                env["NO_PROXY"] = "*"
            if args.wsl:
                # best-effort WSL sandbox: convert Windows path to /mnt/c/...
                wd = workdir.replace("C:", "/mnt/c").replace("\\", "/")
                wcmd = "cd " + wd + " && " + " ".join(cmd)
                print(json.dumps({"ok": True, "mode": "wsl_sandbox", "workdir": wd,
                                  "cmd": cmd, "no_network": args.no_network}, ensure_ascii=False))
                return subprocess.call(["wsl.exe", "bash", "-lc", wcmd], env=env)
            print(json.dumps({"ok": True, "mode": "sandbox", "workdir": workdir,
                              "cmd": cmd}, ensure_ascii=False))
            return subprocess.call(cmd, cwd=workdir, env=env, shell=True)
    return subprocess.call(cmd, cwd=workdir, shell=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("status"); p.set_defaults(fn=status)
    p = sub.add_parser("set")
    p.add_argument("--name", required=True)
    p.add_argument("--mode", choices=("disabled", "sandbox", "allowed"), required=True)
    p.add_argument("--reason", default="")
    p.set_defaults(fn=set_mode)
    p = sub.add_parser("run")
    p.add_argument("--name", required=True)
    p.add_argument("--cmd", nargs=argparse.REMAINDER, required=True)
    p.add_argument("--workdir", default="")
    p.add_argument("--wsl", action="store_true", help="run inside WSL sandbox if available")
    p.add_argument("--no-network", action="store_true", help="best-effort strip network proxy env")
    p.set_defaults(fn=run)
    args = ap.parse_args()
    rc = args.fn(args)
    if rc:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
