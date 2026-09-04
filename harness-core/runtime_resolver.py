#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single source of truth for local runtime entry resolution.

v3：优先从 manifest.json / personas.example.json 加载通用注册表；
不硬编码任何私人角色、本机目录或私人知识库。
"""
import json
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parent

# 公开合成示例；不是任何真实人物。
_FALLBACK = {
    'demo-archivist': {
        'persona_id': 'demo-archivist', 'model': None, 'scope': 'character:demo-archivist',
        'source': SKILL / 'personas' / 'demo-archivist.md',
        'entrypoint': SKILL / 'roleplay_memory_chat.py',
    },
    'demo-storykeeper': {
        'persona_id': 'demo-storykeeper', 'model': None, 'scope': 'character:demo-storykeeper',
        'source': SKILL / 'personas' / 'demo-storykeeper.md',
        'entrypoint': SKILL / 'roleplay_memory_chat.py',
    },
}


def _load_from_manifest(path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        out = {}
        personas = data.get('personas', {}) if isinstance(data, dict) else {}
        for pid, e in personas.items():
            out[pid] = {
                'persona_id': pid,
                'model': e.get('model'),
                'scope': e.get('scope'),
                'source': Path(str(e.get('source', ''))),
                'entrypoint': Path(str(e.get('entrypoint', ''))),
            }
        return out or None
    except Exception:
        return None


def _load_local_overlay():
    """加载本机 overlay（~/.dsh/harness/personas.local.json），仅本机存在时生效。"""
    p = Path.home() / ".dsh" / "harness" / "personas.local.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        out = {}
        for pid, e in (data.get('personas', {}) or {}).items():
            out[pid] = {
                'persona_id': e.get('persona_id', pid),
                'model': e.get('model'),
                'scope': e.get('scope', 'character:' + pid),
                'source': Path(str(e.get('persona_source', ''))),
                'entrypoint': Path(str(e.get('entrypoint', 'roleplay_memory_chat.py'))),
            }
        return out
    except Exception:
        return {}


def _load_entries():
    merged = {}
    for name in ('manifest.json', 'personas.example.json'):
        data = _load_from_manifest(SKILL / name)
        if data:
            merged.update(data)
            break
    if not merged:
        merged.update(dict(_FALLBACK))
    # 本机 overlay 最后加载，可覆盖/补充私有角色。
    merged.update(_load_local_overlay())
    return merged


ENTRIES = _load_entries()


def resolve(persona):
    if persona not in ENTRIES:
        raise ValueError('unknown persona: ' + str(persona))
    e = dict(ENTRIES[persona])
    e['source'] = str(e['source'])
    e['entrypoint'] = str(e['entrypoint'])
    e['source_exists'] = Path(e['source']).exists()
    e['entrypoint_exists'] = Path(e['entrypoint']).exists()
    return e


def resolve_dsh():
    return shutil.which('dsh') or next(
        (str(p) for p in sorted(Path.home().glob('AppData/Local/npm-cache/_npx/*/node_modules/.bin/dsh.cmd'),
                                key=lambda p: p.stat().st_mtime, reverse=True)), None)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--persona')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--dsh', action='store_true')
    a = ap.parse_args()
    if a.dsh:
        print(json.dumps({'executable': resolve_dsh()}, ensure_ascii=False, indent=2))
        return
    if a.all:
        print(json.dumps([resolve(x) for x in ENTRIES], ensure_ascii=False, indent=2))
        return
    print(json.dumps(resolve(a.persona), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
