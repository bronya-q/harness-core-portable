#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measurement_admin.py — 测量学管理 CLI（construct/reliability）。"""
import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CONSTRUCT_DOC = ROOT / "docs" / "measurement" / "CONSTRUCT_DICTIONARY.md"


def cmd_construct():
    # 简单读取构念字典 Markdown 中的 construct_id 表格
    ids = []
    if CONSTRUCT_DOC.exists():
        for line in CONSTRUCT_DOC.read_text(encoding="utf-8").splitlines():
            if line.startswith("| ") and "construct_id" in line:
                continue
            parts = [x.strip() for x in line.strip("|").split("|")]
            if len(parts) >= 4 and parts[0]:
                ids.append({"construct_id": parts[0], "construct_name": parts[1], "type": parts[2]})
    print(json.dumps({"ok": True, "mode": "construct_list", "count": len(ids), "constructs": ids[:100],
                      "note": "来自 CONSTRUCT_DICTIONARY.md；只有定义，不代表信效度。"}, ensure_ascii=False, indent=2))
    return 0


def cmd_reliability(file):
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "harness-core"))
    from harness_core.measurement_utils import cohen_kappa, krippendorff_alpha
    p = Path(file)
    if not p.exists():
        print(json.dumps({"ok": False, "error": "file_not_found"}, ensure_ascii=False))
        return 1
    data = json.loads(p.read_text(encoding="utf-8"))
    # 支持 {"raters": [[...], [...]]} 或 [[...], [...]]
    raters = data.get("raters") if isinstance(data, dict) else data
    if not isinstance(raters, list) or len(raters) < 2:
        print(json.dumps({"ok": False, "error": "need_at_least_two_raters"}, ensure_ascii=False))
        return 1
    a = raters[0]
    b = raters[1]
    kappa = cohen_kappa(a, b)
    alpha = krippendorff_alpha(raters)
    print(json.dumps({"ok": True, "mode": "reliability", "raters": len(raters),
                      "cohen_kappa": kappa, "krippendorff_alpha": alpha,
                      "note": "工具计算；样本信效度仍需真实数据与研究者判断。"}, ensure_ascii=False, indent=2))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    sub = args[0]
    if sub == "construct":
        return cmd_construct()
    if sub == "reliability":
        ap = argparse.ArgumentParser()
        ap.add_argument("--file", required=True)
        a = ap.parse_args(args[1:])
        return cmd_reliability(a.file)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
