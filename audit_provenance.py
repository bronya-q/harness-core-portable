#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_provenance.py — 轻量 provenance/相似性/许可证审计（只读，快）。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SIGNATURE = {
    "Herta": ["我已至，我已见，我已征服", "天才俱乐部#83", "湛蓝星"],
    "Columbina": ["不是X，也不是Y，而是Z", "墙纸是唯一的日历", "我是派对姬，不是"],
    "Wdoctor": ["不是帮你干活的 Agent", "我们决定要让猫娘占领地球", "让 AI 拥有人的温度"],
    "N.E.K.O": ["网络型情感知性生命体", "同一个她", "五维记忆系统"],
    "Mem0": ["multi-signal", "entity linking", "single-pass"],
}

LICENSES = {
    "Herta": "MIT (fan-content not included)",
    "N.E.K.O": "Apache-2.0",
    "Mem0": "Apache-2.0",
    "Letta": "Apache-2.0 (historical)",
    "Python": "PSF",
    "SQLite": "Public Domain",
    "jieba": "MIT (if used)",
    "Ollama": "MIT",
    "Qwen/Qwen3": "Apache-2.0",
    "BGE-M3": "MIT",
    "DeepSeek": "Model License (check terms)",
}

def main():
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.stat().st_size > 2_000_000 or ".git" in p.parts:
            continue
        if p.name in ("audit_provenance.py", "provenance_audit_report.json"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for src, phrases in SIGNATURE.items():
            for ph in phrases:
                if ph in text:
                    hits.append({"src": src, "file": str(p), "phrase": ph})
    report = {"text_signature_hits": hits, "license_obligations": LICENSES,
              "note": "未做 NEKO 全量代码相似性比对（避免卡死）；需人工/受控对比。"}
    (ROOT / "provenance_audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "text_hits": len(hits), "licenses": len(LICENSES), "note": report["note"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
