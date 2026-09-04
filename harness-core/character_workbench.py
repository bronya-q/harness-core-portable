#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""character_workbench.py — Character Card 映射 + 语料→角色草稿审批。"""
import json
import re
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
HARNESS_DIR = Path.home() / ".dsh" / "harness"
CHARACTERS_DIR = HARNESS_DIR / "characters"


def _slugify(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name or "character").strip("-").lower()
    return s or "character"


def _read_png_card(path):
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"tEXt":
            parts = chunk.split(b"\x00", 1)
            if len(parts) == 2 and parts[0] == b"chara":
                try:
                    return json.loads(parts[1].decode("utf-8", "replace"))
                except Exception:
                    return None
        if ctype == b"IEND":
            break
        pos += 12 + length
    return None


def read_card(path):
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(str(p))
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    if p.suffix.lower() in (".png", ".webp"):
        card = _read_png_card(p)
        if card:
            return card
        raise ValueError("PNG 中未找到 chara tEXt 块")
    raise ValueError("不支持的 Character Card 格式（支持 .json / .png）")


def map_card(card):
    pid = _slugify(card.get("name"))
    return {
        "persona_id": pid,
        "display_name": card.get("name", pid),
        "scope": "character:" + pid,
        "description": card.get("description", ""),
        "personality": card.get("personality", ""),
        "scenario": card.get("scenario", ""),
        "mes_example": card.get("mes_example", ""),
        "first_mes": card.get("first_mes", ""),
        "creator_notes": card.get("creator_notes", ""),
        "mapping_preview": {
            "name": card.get("name"),
            "personality": "已识别",
            "scenario": "将导入 Story Core 草稿",
            "mes_example": "将导入 corpus（%d 段）" % len(card.get("mes_example", "").split("\n")),
            "avatar": "PNG 内嵌图（不复制到公开包）",
            "unmapped": ["alternate_greetings", "creator_notes"] if card.get("creator_notes") else [],
        },
    }


def write_import(m, output, yes):
    out = Path(output).expanduser()
    if not yes:
        print(json.dumps({"ok": True, "preview": True, "output": str(out), "mapping": m}, ensure_ascii=False, indent=2))
        return 0
    missing = []
    if not m.get("display_name"):
        missing.append("missing_name")
    if not (m.get("description") or m.get("personality") or m.get("scenario")):
        missing.append("missing_character_fields")
    if m.get("first_mes") is None:
        missing.append("missing_first_mes")
    if missing:
        print(json.dumps({"ok": False, "error": "validation_failed", "missing": missing}, ensure_ascii=False))
        return 1
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "persona_id": m["persona_id"],
        "display_name": m["display_name"],
        "scope": m["scope"],
        "distribution": "private_local",
        "contains_private_memory": False,
        "contains_real_person_data": False,
        "license_status": "needs_review",
        "visibility": "private_local",
        "knowledge_bindings": [],
    }
    (out / "package-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    card = m
    (out / "character.json").write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pc = {"persona_id": m["persona_id"], "identity": {"description": m["description"], "personality": m["personality"]},
          "provenance": {"status": "needs_review", "source": "character_card_import"}}
    (out / "perspective-card.json").write_text(json.dumps(pc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if m["scenario"]:
        (out / "story-core.json").write_text(json.dumps({"namespace": "story:" + m["persona_id"], "content": m["scenario"]},
                                                         ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if m["mes_example"]:
        (out / "corpus").mkdir(parents=True, exist_ok=True)
        with open(out / "corpus" / "mes-example.jsonl", "w", encoding="utf-8") as f:
            for line in m["mes_example"].split("\n"):
                if line.strip():
                    f.write(json.dumps({"text": line.strip(), "source": "character_card"}, ensure_ascii=False) + "\n")
    print(json.dumps({"ok": True, "written": True, "output": str(out), "persona_id": m["persona_id"]},
                     ensure_ascii=False, indent=2))
    return 0


def _collect_corpus(corpus_dir):
    corpus = Path(corpus_dir).expanduser()
    lines = []
    src = []
    if corpus.is_file():
        files = [corpus]
    else:
        files = [f for f in sorted(corpus.rglob("*")) if f.suffix.lower() in (".txt", ".md", ".jsonl")]
    for f in files:
        try:
            if f.suffix.lower() == ".jsonl":
                for i, line in enumerate(f.read_text(encoding="utf-8").splitlines()):
                    if line.strip():
                        lines.append(line.strip())
                        src.append(f"{f.name}:{i}")
            else:
                for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines()):
                    if line.strip():
                        lines.append(line.strip())
                        src.append(f"{f.name}:{i}")
        except Exception:
            pass
    return lines, src


def build_draft(corpus_dir, output, approve):
    lines, src = _collect_corpus(corpus_dir)
    if not lines:
        print(json.dumps({"ok": False, "error": "no_corpus_found", "path": corpus_dir}, ensure_ascii=False))
        return 1
    identity_claims = []
    expr_samples = []
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in line for k in ["我是", "我的名字", "我是谁", "我喜欢", "我不喜欢", "我会", "我不会"]):
            identity_claims.append({"claim": line[:120], "type": "inference", "confidence": 0.5,
                                    "evidence": [{"source_id": src[i], "excerpt": line[:120]}],
                                    "counterevidence": [], "status": "needs_review"})
        if "：" in line or ":" in line and i < 50:
            expr_samples.append({"text": line[:160], "source_id": src[i]})
    coverage = {
        "identity_claims": len(identity_claims),
        "expression_samples": len(expr_samples),
        "total_lines": len(lines),
        "conflicts": 0,
        "source_files": len(set(s.split(":")[0] for s in src)),
    }
    draft = {
        "persona_id": "draft-" + _slugify(Path(corpus_dir).name),
        "display_name": Path(corpus_dir).name,
        "scope": "character:draft-" + _slugify(Path(corpus_dir).name),
        "distribution": "private_local",
        "visibility": "private_local",
        "coverage": coverage,
        "identity_claims": identity_claims,
        "expression_samples": expr_samples[:20],
        "provenance": {"status": "needs_review", "source_kinds": ["user_corpus"]},
    }
    out = Path(output).expanduser()
    bs = chr(92)
    has_abs = any(("C:"+bs+"Users") in line or "/Users/" in line for line in lines)
    draft["contains_abs_path"] = has_abs
    if has_abs and approve:
        print(json.dumps({"ok": False, "error": "corpus_contains_abs_path",
                          "note": "语料包含绝对路径，拒绝 --approve 写入"}, ensure_ascii=False))
        return 1
    if not approve:
        print(json.dumps({"ok": True, "preview": True, "output": str(out) + "（--approve 写入）", "draft": draft},
                         ensure_ascii=False, indent=2))
        return 0
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "persona_id": draft["persona_id"], "display_name": draft["display_name"],
                "scope": draft["scope"], "distribution": "private_local", "visibility": "private_local",
                "contains_private_memory": False, "contains_real_person_data": False, "license_status": "needs_review"}
    (out / "package-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "perspective-card.json").write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "written": True, "output": str(out), "persona_id": draft["persona_id"]},
   
                     ensure_ascii=False, indent=2))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "card-import":
        path = output = ""
        yes = False
        i = 0
        while i < len(args):
            if args[i] in ("--output", "-o") and i + 1 < len(args):
                output = args[i + 1]; i += 2
            elif args[i] == "--yes":
                yes = True; i += 1
            else:
                path = args[i]; i += 1
        try:
            card = read_card(path)
            m = map_card(card)
            return write_import(m, output or "hcp-import", yes)
        except Exception as e:
            print(json.dumps({"ok": False, "error": type(e).__name__, "detail": str(e)}, ensure_ascii=False))
            return 1
    if cmd == "build":
        corpus = output = ""
        approve = False
        i = 0
        while i < len(args):
            if args[i] == "--from" and i + 1 < len(args):
                corpus = args[i + 1]; i += 2
            elif args[i] == "--output" and i + 1 < len(args):
                output = args[i + 1]; i += 2
            elif args[i] == "--approve":
                approve = True; i += 1
            else:
                i += 1
        if not corpus:
            print("用法：harness.py character build --from <corpus> [--output <dir>] [--approve]")
            return 1
        return build_draft(corpus, output or "draft-output", approve)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
