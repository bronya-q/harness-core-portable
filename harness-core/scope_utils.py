# -*- coding: utf-8 -*-
"""scope_utils.py — 跨前端 scope 规范化。"""
import re


def normalize_scope(scope):
    if not scope:
        return "default"
    s = str(scope).strip()
    if not s:
        return "default"
    if s.startswith("character:"):
        return s
    # 去掉可能误传的空白/引号
    s = re.sub(r"^[\"'#]+|[\"'#]+$", "", s)
    return s
