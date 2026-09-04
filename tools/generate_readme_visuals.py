#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate synthetic README preview images (PNG + animated GIF).

These are illustrative mockups of the local dashboard, not a real browser
screenshot. They use the same visual language as `harness.py dashboard build`
and are CSP-safe (no embedded scripts).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "images"
W, H = 1200, 900
BG = "#fafafa"
CARD_BG = "#ffffff"
BORDER = "#e5e5e5"
TITLE = "#222"
MUTED = "#888"
BLUE = "#1565c0"
GREEN = "#2e7d32"
YELLOW = "#f9a825"
RED = "#c62828"

BG_IMG = "#ffd54f"


def load_font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)
    except Exception:
        try:
            return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def card(draw, xy, title, lines, title_font, body_font):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=10, fill=CARD_BG, outline=BORDER, width=2)
    draw.text((x0 + 14, y0 + 10), title, font=title_font, fill=BLUE)
    y = y0 + 40
    for line in lines:
        draw.text((x0 + 14, y), line, font=body_font, fill=TITLE)
        y += 24


def bar(draw, x, y, w, label, state, color, extra):
    draw.text((x, y), label, font=load_font(16), fill="#444")
    x2 = x + 170
    bw = int(w * 0.55)
    draw.rounded_rectangle([x2, y, x2 + bw, y + 18], radius=4, fill=color)
    draw.text((x2 + 6, y - 1), state, font=load_font(12), fill="#fff")
    draw.text((x2 + bw + 10, y), extra, font=load_font(12), fill="#888")


def draw_frame(highlight=0):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title_font = load_font(28)
    h1 = load_font(22)
    body = load_font(16)
    small = load_font(13)

    d.text((40, 30), "Harness Mind Console", font=title_font, fill=TITLE)
    d.text((40, 68), "本地只读静态报告 · 不自动上传 · 不开放端口", font=body, fill=MUTED)

    # top cards
    card(d, (40, 110, 360, 220), "角色/项目", ["demo-archivist", "demo-storykeeper"], h1, body)
    card(d, (380, 110, 700, 220), "记忆", ["总数 12 · active 9", "无网络上传"], h1, body)
    card(d, (720, 110, 1160, 220), "自动执行 / 网络", ["DISABLED", "NONE"], h1, body)

    # runtime bridge status bars
    d.rounded_rectangle([40, 240, 1160, 440], radius=10, fill=CARD_BG, outline=BORDER, width=2)
    d.text((54, 250), "运行桥（彩色状态条）", font=h1, fill=BLUE)
    bar_items = [
        ("① Scope Resolver", "已解析", GREEN, "角色/项目 2 个；跨角色默认 BLOCK"),
        ("② Perspective Card", "已加载", GREEN, "已加载人格/边界"),
        ("③ Memory Recall", "canary", YELLOW, "active 9；recall limit 3"),
        ("④ Notebook / Story Core", "3 笔记 / v2", GREEN, "本地只读"),
        ("⑤ Runtime Policy", "autonomous disabled", GREEN, "network NONE · g1=canary"),
        ("⑥ Model → Output", "记录", BLUE, "usage 5 条 · provider_reported=3"),
    ]
    y = 290
    for i, item in enumerate(bar_items):
        color = item[2]
        if i == highlight:
            color = RED if item[0].startswith("⑤") else BLUE
        bar(d, 60, y, 1060, item[0], item[1], color, item[3])
        y += 30

    # knowledge grid
    d.rounded_rectangle([40, 460, 1160, 700], radius=10, fill=CARD_BG, outline=BORDER, width=2)
    d.text((54, 470), "知识域关系网格（角色 ↔ 知识域 ↔ 权限）", font=h1, fill=BLUE)
    grid = [
        ["角色", "女性主义理论库", "政治经济学"],
        ["demo-archivist", "steward", "blocked"],
        ["demo-storykeeper", "reader", "steward"],
        ["adversarial-review", "critic", "critic"],
    ]
    gx, gy = 60, 510
    for row in grid:
        d.text((gx, gy), row[0], font=small, fill="#444")
        gx2 = gx + 150
        vals = row[1:]
        for val in vals:
            if "steward" in val:
                col = GREEN
            elif val in ("reader", "critic"):
                col = BLUE
            elif val == "blocked":
                col = RED
            else:
                col = YELLOW
            d.rounded_rectangle([gx2, gy, gx2 + 350, gy + 26], radius=4, fill=col)
            d.text((gx2 + 8, gy + 3), val, font=small, fill="#fff")
            gx2 += 370
        gy += 40

    # token / provider bars
    d.rounded_rectangle([40, 720, 1160, 870], radius=10, fill=CARD_BG, outline=BORDER, width=2)
    d.text((54, 730), "Token 来源 / Provider", font=h1, fill=BLUE)
    prov = [("ollama", 1200), ("character_estimate", 300), ("unreported", 100)]
    maxv = max(v for _, v in prov)
    y = 770
    for name, v in prov:
        d.text((60, y), name, font=body, fill="#444")
        bw = int(800 * v / maxv)
        d.rounded_rectangle([260, y, 260 + bw, y + 20], radius=4, fill=BLUE if name == "ollama" else YELLOW)
        d.text((270, y - 1), "%d tokens" % v, font=small, fill="#fff")
        y += 32

    d.text((40, 885), "生成时间：2026-09-04 · 示例数据（合成） · 本地只读", font=small, fill=MUTED)
    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_DIR / "harness-dashboard-preview.png"
    draw_frame(highlight=0).save(png)
    print("saved", png)

    frames = [draw_frame(i) for i in range(6)]
    gif = OUT_DIR / "harness-dashboard-demo.gif"
    frames[0].save(
        gif,
        save_all=True,
        append_images=frames[1:],
        duration=700,
        loop=0,
    )
    print("saved", gif)


if __name__ == "__main__":
    main()
