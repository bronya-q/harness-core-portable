#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single source of truth for local runtime entry resolution.

v2：优先从 manifest.json 加载；manifest 存在时即唯一生成源。
"""
import json
import shutil
from pathlib import Path

ROOT = Path(r'~\Documents\harness\whale-sister')
SKILL = Path(__file__).resolve().parent

_FALLBACK = {
    'jingyuaniang': {'persona_id': 'jingyuaniang', 'model': 'whale-sister', 'scope': 'character:demo-bob', 'source': ROOT / 'persona.md', 'entrypoint': ROOT / 'roleplay_memory_chat.py'},
    'demo-alice': {'persona_id': 'demo-alice', 'model': 'paipai', 'scope': 'character:demo-alice', 'source': ROOT / 'paipai.md', 'entrypoint': ROOT / 'roleplay_memory_chat.py'},
    'demo-storykeeper': {'persona_id': 'demo-storykeeper', 'model': 'saoxing', 'scope': 'character:demo-storykeeper', 'source': ROOT / 'saoxing.md', 'entrypoint': ROOT / 'roleplay_memory_chat.py'},
    'markus': {'persona_id': 'markus', 'model': None, 'scope': 'character:markus', 'source': Path(r'~\.dsh\skills\celebrity-markus\persona.md'), 'entrypoint': Path(r'~\.dsh\skills\celebrity-markus\manifest.json')},
    'blanche': {'persona_id': 'blanche', 'model': None, 'scope': 'character:blanche', 'source': Path(r'~\feminism_kb\14_人格布兰奇.md'), 'entrypoint': Path(r'~\Desktop\blanche_terminal.bat')},
    'mutsumi': {'persona_id': 'mutsumi', 'model': None, 'scope': 'character:mutsumi', 'source': Path(r'~\.dsh\skills\celebrity-mutsumi\persona.md'), 'entrypoint': Path(r'~\.dsh\skills\celebrity-mutsumi\SKILL.md')},
    'persona-cards': {'persona_id': 'persona-cards', 'model': 'local-backend', 'scope': 'persona-cards', 'source': Path(r'~\persona-cards\card_game.py'), 'entrypoint': Path(r'~\persona-cards\card_game.py')},
}

def _load_entries():
    m = SKILL / 'manifest.json'
    if m.exists():
        try:
            data = json.loads(m.read_text(encoding='utf-8'))
            out = {}
            for pid, e in data.get('personas', {}).items():
                out[pid] = {
                    'persona_id': pid,
                    'model': e.get('model'),
                    'scope': e.get('scope'),
                    'source': Path(str(e.get('source', ''))),
                    'entrypoint': Path(str(e.get('entrypoint', ''))),
                }
            if out:
                return out
        except Exception:
            pass
    return dict(_FALLBACK)

ENTRIES = _load_entries()

def resolve(persona):
 if persona not in ENTRIES: raise ValueError('unknown persona: '+str(persona))
 e=dict(ENTRIES[persona]); e['source']=str(e['source']);e['entrypoint']=str(e['entrypoint']);e['source_exists']=Path(e['source']).exists();e['entrypoint_exists']=Path(e['entrypoint']).exists(); return e
def resolve_dsh():
 return shutil.which('dsh') or next((str(p) for p in sorted(Path.home().glob('AppData/Local/npm-cache/_npx/*/node_modules/.bin/dsh.cmd'),key=lambda p:p.stat().st_mtime,reverse=True)),None)
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--persona');ap.add_argument('--all',action='store_true');ap.add_argument('--dsh',action='store_true');a=ap.parse_args()
 if a.dsh: print(json.dumps({'executable':resolve_dsh()},ensure_ascii=False,indent=2));return
 print(json.dumps([resolve(x) for x in ENTRIES] if a.all else resolve(a.persona),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
