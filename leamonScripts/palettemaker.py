#!/usr/bin/env python3
"""Generate a JASC palette and annotated preview for a PNG.

Usage:
  ./palettemaker.py image.png

Outputs:
  - image.pal
  - image_annotated.png
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from check_sprite_colors import (
    DEFAULT_BG_RGB,
    parse_png_rgba_pixels,
    write_jasc_palette,
    write_rgba_png,
)

RgbaColor = tuple[int, int, int, int]


def sorted_visible_colors_by_usage(pixels: list[RgbaColor]) -> list[RgbaColor]:
    counts = Counter(pixel for pixel in pixels if pixel[3] > 0)
    sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [color for color, _count in sorted_counts]


def build_palette_colors(pixels: list[RgbaColor], max_entries: int = 16) -> list[tuple[int, int, int]]:
    palette: list[tuple[int, int, int]] = [DEFAULT_BG_RGB]
    seen: set[tuple[int, int, int]] = {DEFAULT_BG_RGB}

    for color in sorted_visible_colors_by_usage(pixels):
        rgb = color[:3]
        if rgb not in seen:
            palette.append(rgb)
            seen.add(rgb)

    if len(palette) > max_entries:
        raise ValueError(
            f"Image needs {len(palette)} palette entries, which exceeds {max_entries}. "
            "Reduce colors first or increase --max-entries."
        )

    while len(palette) < max_entries:
        palette.append((0, 0, 0))

    return palette


def make_annotated_image(
    width: int,
    height: int,
    pixels: list[RgbaColor],
    palette_rgb: list[tuple[int, int, int]],
) -> tuple[int, int, list[RgbaColor]]:
    panel_gap = 8
    panel_pad = 6
    swatch_size = 10
    swatch_gap = 2
    bg = (24, 24, 24, 255)
    border = (255, 255, 255, 255)

    palette_height = panel_pad * 2 + len(palette_rgb) * swatch_size + max(0, len(palette_rgb) - 1) * swatch_gap
    panel_width = panel_pad * 2 + swatch_size

    out_w = width + panel_gap + panel_width
    out_h = max(height, palette_height)
    out_pixels: list[RgbaColor] = [bg] * (out_w * out_h)

    def blit(src_w: int, src_h: int, src: list[RgbaColor], dx: int, dy: int) -> None:
        for y in range(src_h):
            src_start = y * src_w
            dst_start = (dy + y) * out_w + dx
            out_pixels[dst_start : dst_start + src_w] = src[src_start : src_start + src_w]

    def fill_rect(x: int, y: int, w: int, h: int, color: RgbaColor) -> None:
        for yy in range(y, y + h):
            row = yy * out_w
            out_pixels[row + x : row + x + w] = [color] * w

    blit(width, height, pixels, 0, 0)

    sw_x = width + panel_gap + panel_pad
    sw_y = panel_pad
    for rgb in palette_rgb:
        fill_rect(sw_x, sw_y, swatch_size, swatch_size, border)
        fill_rect(sw_x + 1, sw_y + 1, swatch_size - 2, swatch_size - 2, (rgb[0], rgb[1], rgb[2], 255))
        sw_y += swatch_size + swatch_gap

    return out_w, out_h, out_pixels


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate .pal and annotated PNG for an image")
    parser.add_argument("image", type=Path, help="Path to input PNG image")
    parser.add_argument(
        "--max-entries",
        type=int,
        default=16,
        help="Palette entry count (default: 16, same as normal.pal workflow)",
    )
    args = parser.parse_args()

    image_path = args.image.resolve()
    if not image_path.exists():
        print(f"Input image not found: {image_path}")
        return 2

    try:
        width, height, pixels = parse_png_rgba_pixels(image_path)
        palette_rgb = build_palette_colors(pixels, args.max_entries)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    pal_path = image_path.with_suffix(".pal")
    annotated_path = image_path.with_name(f"{image_path.stem}_annotated.png")

    write_jasc_palette(pal_path, palette_rgb)
    out_w, out_h, out_pixels = make_annotated_image(width, height, pixels, palette_rgb)
    write_rgba_png(annotated_path, out_w, out_h, out_pixels)

    print(f"Wrote {pal_path}")
    print(f"Wrote {annotated_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
