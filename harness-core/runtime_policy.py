#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explicit gates for shadow, canary, and controlled production."""
import json, os
from pathlib import Path
DATA=Path(os.environ.get('MEMORY_EMOTION_DATA_DIR',str(Path.home()/'.dsh/memory-emotion')))
FLAGS={'g1_expression':'shadow','dynamic_memory':'shadow','belief':'shadow','three_needs':'shadow','autonomous_tasks':'disabled'}
BOUNDS={'dynamic_memory':{'max_recall_items':3,'max_recall_chars':1200,'allowed_scopes':['character:demo-bob','character:demo-alice','character:demo-storykeeper','persona-cards'],'current_stage':'bounded_canary'}}

def load():
 p=DATA/'runtime-policy.json'
 try:
  d=json.loads(p.read_text(encoding='utf-8')); out={**FLAGS,**d.get('flags',{})}; out['_bounds']=d.get('bounds',BOUNDS); return out
 except Exception:
  out=dict(FLAGS); out['_bounds']=BOUNDS; return out
def enabled(name,mode): return load().get(name)=='production' or load().get(name)==mode
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--set',nargs=2,metavar=('FEATURE','MODE'));a=ap.parse_args();p=DATA/'runtime-policy.json';loaded=load(); d={'schema_version':1,'flags':{k:v for k,v in loaded.items() if not k.startswith('_')},'bounds':loaded.get('_bounds',BOUNDS),'allowed_modes':['disabled','shadow','canary','production'],'note':'belief/needs never authorize behavior'}
 if a.set:
  if a.set[0] not in FLAGS or a.set[1] not in d['allowed_modes']: raise SystemExit('invalid feature or mode')
  d['flags'][a.set[0]]=a.set[1];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(d,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
