#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_game.py — 可玩的卡牌游戏（Harness Memory Match）。

规则：
- 牌面全部来自公开合成记忆线索，不包含私人角色/私人知识库。
- 每轮从牌堆抽出一手牌；玩家找出属于同一记忆线索的两张牌。
- 正确配对 +10 分；配错 -3 分；跳过不扣分。
- 默认玩 3 轮，按总分结束。

本文件是“可玩”的最小游戏引擎（R1），不宣称心理效度或生产级游戏。
"""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))


THREADS = [
    {
        "thread_id": "archival_sky",
        "label": "档案观星",
        "cards": [
            {"title": "档案室旧书", "content": "在档案室整理了一本关于星空的旧书。"},
            {"title": "共享世界设定", "content": "观星记录被写入共享 Story Core。"},
        ],
    },
    {
        "thread_id": "garden_glow",
        "label": "会发光的花",
        "cards": [
            {"title": "花园发现", "content": "花园里发现一棵会发光的花。"},
            {"title": "角色经历", "content": "角色把发光花写进自己的日记。"},
        ],
    },
    {
        "thread_id": "workspace_evidence",
        "label": "工程工作区",
        "cards": [
            {"title": "worktree 创建", "content": "用户创建了一个真实 git worktree。"},
            {"title": "Evidence 归档", "content": "任务证据包被归档为 Evidence Bundle。"},
        ],
    },
    {
        "thread_id": "memory_correction",
        "label": "记忆纠错",
        "cards": [
            {"title": "用户纠错", "content": "用户指出某条记忆需要修正。"},
            {"title": "版本恢复", "content": "旧版本记忆被归档并保留可恢复。"},
        ],
    },
    {
        "thread_id": "role_switch",
        "label": "角色切换",
        "cards": [
            {"title": "模式切换", "content": "角色从陪伴模式切换到档案研究模式。"},
            {"title": "激活回滚", "content": "激活失败时自动回滚到上一个可用角色。"},
        ],
    },
]

DISTRACTORS = [
    {"title": "无关线索", "content": "一只猫在窗台上打哈欠。"},
    {"title": "无关设定", "content": "今天天气很好，适合散步。"},
    {"title": "无关事件", "content": "电视里播放了一场足球比赛。"},
    {"title": "无关提醒", "content": "记得给植物浇水。"},
]

ENGINEERING_THREADS = [
    {
        "thread_id": "review_loop",
        "label": "审查循环",
        "cards": [{"title": "草稿提交", "content": "角色提交一份草稿等待审查。"},
                  {"title": "对抗审查", "content": "Adversarial Review 提出反例与修订建议。"}],
    },
    {
        "thread_id": "migration_plan",
        "label": "迁移计划",
        "cards": [{"title": "schema 检查", "content": "迁移前检查本地 SQLite schema 版本。"},
                  {"title": "备份准备", "content": "迁移前创建备份，失败可回滚。"}],
    },
    {
        "thread_id": "knowledge_bridge",
        "label": "知识桥",
        "cards": [{"title": "委派匹配", "content": "知识桥匹配问题对应的负责域。"},
                  {"title": "只读访问", "content": "知识桥按授权返回有限上下文。"}],
    },
]

DECKS = {"classic": THREADS, "engineering": ENGINEERING_THREADS}


def build_deck(deck_name="classic"):
    threads = DECKS.get(deck_name, THREADS)
    deck = []
    for thread in threads:
        for ci, card in enumerate(thread["cards"]):
            deck.append({
                "id": "%s-%d" % (thread["thread_id"], ci + 1),
                "thread_id": thread["thread_id"],
                "thread_label": thread["label"],
                "title": card["title"],
                "content": card["content"],
            })
    for i, d in enumerate(DISTRACTORS):
        deck.append({
            "id": "distractor-%d" % (i + 1),
            "thread_id": None,
            "thread_label": None,
            "title": d["title"],
            "content": d["content"],
        })
    return deck


def deal(deck, size):
    return random.sample(deck, min(size, len(deck)))


def _print_hand(hand, round_no):
    print("\n===== 第 %d 轮手牌 =====" % round_no)
    for i, card in enumerate(hand, start=1):
        print("  %d. [%s] %s" % (i, card.get("thread_label") or "无关", card["title"]))
    print()


def _parse_pair(text, n):
    words = text.strip().split()
    if len(words) != 2:
        return None
    try:
        a, b = int(words[0]), int(words[1])
    except Exception:
        return None
    if not (1 <= a <= n and 1 <= b <= n) or a == b:
        return None
    return a - 1, b - 1


def play(rounds=3, hand_size=8, seed=None, auto=False, deck="classic", players=1):
    rng = random.Random(seed)
    deck_cards = build_deck(deck)
    scores = [0] * players
    matched = [0] * players
    rounds_played = 0
    for rnd in range(1, rounds + 1):
        hand = rng.sample(deck_cards, min(hand_size, len(deck_cards)))
        rounds_played += 1
        _print_hand(hand, rounds_played)
        if auto:
            for pi in range(players):
                found = False
                for i in range(0, len(hand) - 1):
                    a, b = hand[i], hand[i + 1]
                    if a.get("thread_id") and a["thread_id"] == b.get("thread_id"):
                        print("  [auto P%d] 选择 %d %d" % (pi + 1, i + 1, i + 2))
                        scores[pi] += 10
                        matched[pi] += 1
                        found = True
                        break
                if not found:
                    print("  [auto P%d] pass" % (pi + 1))
            continue
        if players > 1:
            print("  多人交互模式暂未完整实现；自动模式支持 P1/P2 轮流演示。")
        seen = set()
        while True:
            try:
                line = input("输入两个牌号（如 1 4），或 pass 结束本轮：").strip()
            except EOFError:
                line = "pass"
            if not line:
                continue
            low = line.lower()
            if low in ("pass", "跳过", "结束"):
                break
            if low in ("end", "quit", "exit", "结束游戏"):
                return _finish(scores, matched, rounds_played, players)
            pair = _parse_pair(line, len(hand))
            if pair is None:
                print("  格式不对，请输入两个不同牌号。")
                continue
            i, j = pair
            if i in seen or j in seen:
                print("  其中一张已经配对过了。")
                continue
            a, b = hand[i], hand[j]
            if a.get("thread_id") and a["thread_id"] == b.get("thread_id"):
                scores[0] += 10
                matched[0] += 1
                seen.add(i)
                seen.add(j)
                print("  ✓ 命中！+10，当前 %d 分。" % scores[0])
            else:
                scores[0] = max(0, scores[0] - 3)
                print("  ✗ 配对失败，-3，当前 %d 分。" % scores[0])
        if sum(matched) >= rounds * 2:
            break
    return _finish(scores, matched, rounds_played, players)


def _finish(scores, matched, rounds_played, players=1):
    print()
    print("===== 游戏结束 =====")
    for i in range(players):
        print("  玩家%d：得分 %d · 正确配对 %d" % (i + 1, scores[i], matched[i]))
    if players == 1:
        print("  轮次：%d" % rounds_played)
    try:
        from event_store import record_event
        record_event({
            "event_type": "card_game.result",
            "scope": "character:demo-archivist",
            "content_type": "fact",
            "session_provenance": "demo",
            "content_provenance": "derived",
            "session_id": "card-game",
            "source_ids": [],
            "root_source_ids": [],
            "version": 1,
            "visibility": "private",
        })
    except Exception:
        pass
    return {"ok": True, "scores": scores, "matched": matched, "rounds": rounds_played}


def main():
    ap = argparse.ArgumentParser(description="Harness Memory Match card game")
    ap.add_argument("subcommand", nargs="?", default="play", choices=["play", "deal", "deck"])
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--hand-size", type=int, default=8)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--auto", action="store_true", help="automated smoke play")
    ap.add_argument("--deck", default="classic", choices=list(DECKS.keys()))
    ap.add_argument("--players", type=int, default=1)
    args = ap.parse_args()
    if args.subcommand == "deck":
        print(json.dumps({"deck": args.deck, "count": len(build_deck(args.deck)),
                          "cards": build_deck(args.deck)}, ensure_ascii=False, indent=2))
        return 0
    if args.subcommand == "deal":
        deck = build_deck(args.deck)
        hand = deal(deck, args.hand_size)
        print(json.dumps(hand, ensure_ascii=False, indent=2))
        return 0
    result = play(rounds=args.rounds, hand_size=args.hand_size, seed=args.seed,
                  auto=args.auto, deck=args.deck, players=args.players)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
