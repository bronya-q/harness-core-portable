#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fill_vec.py — 给活跃记忆回填 bge-m3 向量（整改方案 P2-2 / 附录 E-1）

复用既有轮子，零改动：
  - nine_dim._embed / _pack / VEC_DB   —— 向量格式与 associate 命令完全一致
  - memory_store.db_path()             —— 主库路径
只写 sidecar 库 nine_dim_vectors.db，绝不碰主库 schema。

用法:
  python fill_vec.py --dry-run        # 只统计，不写
  python fill_vec.py                  # 正式回填（可断点续跑，已回填的跳过）
  python fill_vec.py --scope default  # 只回填某 scope
"""
import argparse
import sqlite3
import sys
import time

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
import memory_store as ms
from nine_dim import _embed, _pack, VEC_DB  # 复用，不复制


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scope", default=None, help="只处理该 scope（默认全部活跃）")
    ap.add_argument("--limit", type=int, default=0, help="本次最多回填条数（0=不限）")
    args = ap.parse_args()

    main_db = sqlite3.connect(str(ms.db_path()))
    vec_db = sqlite3.connect(str(VEC_DB))

    where = "archived=0"
    params = []
    if args.scope:
        where += " AND scope=?"
        params.append(args.scope)
    rows = main_db.execute(
        f"SELECT id, scope, content FROM memories WHERE {where}", params
    ).fetchall()

    have = {r[0] for r in vec_db.execute("SELECT memory_id FROM vec").fetchall()}
    todo = [(i, s, c) for (i, s, c) in rows if i not in have]
    if args.limit > 0:
        todo = todo[: args.limit]

    print(f"[fill_vec] active={len(rows)} already={len(rows)-len(todo)} todo={len(todo)} dry_run={args.dry_run}")
    if args.dry_run or not todo:
        return 0

    t0, done, fail = time.time(), 0, 0
    for mid, scope, content in todo:
        try:
            vec_db.execute(
                "INSERT OR REPLACE INTO vec(memory_id,scope,ts,vec) VALUES(?,?,?,?)",
                (mid, scope, time.time(), _pack(_embed(content))),
            )
            done += 1
            if done % 50 == 0:
                vec_db.commit()
                print(f"  ... {done}/{len(todo)} ({time.time()-t0:.0f}s)")
        except Exception as exc:
            fail += 1
            print(f"  FAIL #{mid}: {exc}")
            if fail > 20:
                print("连续失败过多，中止（可重跑续传）")
                break
    vec_db.commit()
    print(f"[fill_vec] done={done} fail={fail} elapsed={time.time()-t0:.0f}s")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
