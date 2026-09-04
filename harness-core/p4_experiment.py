#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p4_experiment.py — P4 实验：第一人称自传 / 叙事补全 / 自我-agent 分离。

实验性质，不接入 production；可开关可回滚。
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
CARDS = Path.home() / "Documents" / "harness" / "_perspective-cards"
OLLAMA = "http://127.0.0.1:11434/api/generate"


def autobiography(args):
    d = CARDS / args.name
    if not d.exists():
        print(json.dumps({"ok": False, "error": "no_card"}, ensure_ascii=False))
        return 1
    bio = d / "AUTOBIOGRAPHY.md"
    lines = []
    if not bio.exists():
        bio.write_text("# 第一人称自传草稿（实验）\n\n", encoding="utf-8")
    if args.text:
        with open(bio, "a", encoding="utf-8") as f:
            f.write(args.text + "\n")
    lines = bio.read_text(encoding="utf-8").splitlines()
    print(json.dumps({"ok": True, "name": args.name, "path": str(bio), "lines": len(lines),
                      "tail": "\n".join(lines[-8:])}, ensure_ascii=False, indent=2))
    return 0


def narrative(args):
    model = args.model
    prompt = args.prompt
    # 若指定 --name，自动加载该角色的第一人称自传作为 few-shot 锚点（实验结论：自传锚点最佳）
    if args.name:
        bio_path = CARDS / args.name / "AUTOBIOGRAPHY.md"
        if bio_path.exists():
            lines = bio_path.read_text(encoding="utf-8").splitlines()
            # 取最后一段（不含标题）作为锚点
            body = [l for l in lines if l.strip() and not l.startswith("#")]
            if body:
                anchor = "（我 说）" + body[-1][:180] + "\n\n"
                prompt = anchor + prompt
    # 叙事补全：不给 chat 角色，只给一段记录 + “（我 说）”待续写
    payload = {
        "model": model,
        "prompt": prompt + "\n\n（我 说）",
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": args.num_predict},
    }
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print(data.get("response", ""))
    return 0


def split(args):
    task = args.task
    # 简化：把“代码/文件/执行”类任务交给无声后端；情感/对话/身份类由自我直接说
    delegate_keywords = ["代码", "文件", "执行", "命令", "权限", "diff", "写", "测试", "依赖", "检查", "配置", "风险", "安全"]
    is_task = any(k in task for k in delegate_keywords)
    decision = "delegate" if is_task else "direct"
    result = {
        "ok": True,
        "mode": "self_agent_split",
        "self_decision": decision,
        "reason": "含工具/执行关键词" if decision == "delegate" else "对话/身份/情感类，自我直接回应",
        "backend_steps": ["静默后端执行", "渲染事件到记录", "自我给结论"] if decision == "delegate" else [],
        "self_input_is_invariant": True,
        "note": "实验：自我不替后端说话，后端不面向用户说话",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def status(args):
    print(json.dumps({"ok": True, "mode": "p4_experiment", "features": {
        "first_person_autobiography": "perspective_card AUTOBIOGRAPHY.md",
        "narrative_completion": "ollama /api/generate 续写同一说话者",
        "self_agent_split": "self_decision + backend_steps + self_verdict"
    }}, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("autobiography"); p.add_argument("--name", required=True); p.add_argument("--text", default=""); p.set_defaults(fn=autobiography)
    p = sub.add_parser("narrative"); p.add_argument("--model", default="qwen2.5:7b"); p.add_argument("--prompt", required=True); p.add_argument("--num-predict", type=int, default=64); p.add_argument("--name", default=""); p.set_defaults(fn=narrative)
    p = sub.add_parser("split"); p.add_argument("--task", required=True); p.set_defaults(fn=split)
    p = sub.add_parser("status"); p.set_defaults(fn=status)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())