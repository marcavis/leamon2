#!/usr/bin/env python3
"""
grid_map.py — Pokémon romhack region map grid labeller
Usage: python grid_map.py <input_image> [output_image]

- Doubles the image with nearest-neighbour scaling
- Draws a grid every 16 px (matching one GBA tile)
- Adds a 16 px header row and left column with A–Z / AA–AD column labels
  and 1–20 row labels
"""

import sys
import string
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CELL      = 16          # grid cell size in the doubled image (px)
MARGIN    = 16          # header/left-margin width (px)
GRID_COLOR  = (255, 255, 255, 160)   # semi-transparent white grid lines
LABEL_COLOR = (255, 255, 255, 255)   # white text
BG_COLOR    = (30, 30, 30, 255)      # dark background for the margin strip


def col_label(n: int) -> str:
    """Return Excel-style column label for 0-based index n (0→A, 25→Z, 26→AA …)."""
    label = ""
    n += 1  # 1-based
    while n:
        n, rem = divmod(n - 1, 26)
        label = string.ascii_uppercase[rem] + label
    return label


def process(input_path: str, output_path: str) -> None:
    src = Image.open(input_path).convert("RGBA")
    w, h = src.size

    # 1. Double with nearest-neighbour
    doubled = src.resize((w * 2, h * 2), Image.NEAREST)
    dw, dh = doubled.size

    cols = dw // CELL   # number of grid columns
    rows = dh // CELL   # number of grid rows

    # 2. Create canvas with extra margin on top and left
    canvas_w = dw + MARGIN
    canvas_h = dh + MARGIN
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 255))

    # Dark strips for margin areas
    overlay = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw_bg = ImageDraw.Draw(overlay)
    draw_bg.rectangle([0, 0, canvas_w - 1, MARGIN - 1], fill=BG_COLOR)   # top strip
    draw_bg.rectangle([0, 0, MARGIN - 1, canvas_h - 1], fill=BG_COLOR)   # left strip

    # Paste the doubled map into the canvas (offset by margin)
    canvas.paste(doubled, (MARGIN, MARGIN))
    canvas = Image.alpha_composite(canvas, overlay)

    # 3. Draw grid lines
    grid_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid_layer)

    # Vertical lines
    for c in range(cols + 1):
        x = MARGIN + c * CELL
        draw.line([(x, MARGIN), (x, canvas_h - 1)], fill=GRID_COLOR, width=1)

    # Horizontal lines
    for r in range(rows + 1):
        y = MARGIN + r * CELL
        draw.line([(0, y), (canvas_w - 1, y)], fill=GRID_COLOR, width=1)

    canvas = Image.alpha_composite(canvas, grid_layer)

    # 4. Draw labels
    label_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw_lbl = ImageDraw.Draw(label_layer)

    # Try to load a small bitmap/truetype font; fall back to default
    font = None
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        try:
            font = ImageFont.truetype(candidate, size=9)
            break
        except (IOError, OSError):
            pass
    if font is None:
        font = ImageFont.load_default()

    # Column labels (A, B, … Z, AA, AB … AD)
    for c in range(cols):
        label = col_label(c)
        x = MARGIN + c * CELL + CELL // 2
        y = MARGIN // 2
        bbox = draw_lbl.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw_lbl.text((x - tw // 2, y - th // 2), label, font=font, fill=LABEL_COLOR)

    # Row labels (1, 2, … 20)
    for r in range(rows):
        label = str(r + 1)
        x = MARGIN // 2
        y = MARGIN + r * CELL + CELL // 2
        bbox = draw_lbl.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw_lbl.text((x - tw // 2, y - th // 2), label, font=font, fill=LABEL_COLOR)

    canvas = Image.alpha_composite(canvas, label_layer)

    # 5. Save
    canvas.convert("RGB").save(output_path)
    print(f"Saved → {output_path}  ({canvas_w}×{canvas_h} px, {cols} cols × {rows} rows)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grid_map.py <input_image> [output_image]")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else str(Path(inp).stem) + "_grid.png"
    process(inp, out)
