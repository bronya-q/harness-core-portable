#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a scrolling GIF preview from the real dashboard screenshot.

The base image is produced by:
  python harness.py demo --offline --keep
  HOME=<demo> USERPROFILE=<demo> DSH_HOME=<demo>/.dsh python harness.py dashboard build
  msedge --headless --screenshot=... file:///.../index.html

This script then crops the tall screenshot into scrolling frames and encodes a GIF.
No browser/network needed at GIF-encode time.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "images" / "harness-dashboard-preview.png"
OUT = ROOT / "docs" / "images" / "harness-dashboard-demo.gif"


def main():
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    frame_w = min(900, w)
    frame_h = min(900, h)
    # 多少帧，每帧向下移动多少
    n_frames = 8
    max_start = max(1, h - frame_h)
    step = max(1, max_start // (n_frames - 1))
    frames = []
    for i in range(n_frames):
        y = min(max_start, i * step)
        crop = img.crop((0, y, frame_w, y + frame_h))
        crop = crop.resize((800, int(frame_h * 800 / frame_w)), Image.LANCZOS)
        frames.append(crop)
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=800,
        loop=0,
    )
    print("saved", OUT)


if __name__ == "__main__":
    main()
