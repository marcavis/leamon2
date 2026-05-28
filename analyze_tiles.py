#!/usr/bin/env python3
"""Analyze repeated 8x8 tiles in a map image.

Given an input image (for example a Pokemon region map), this script:
1) Splits it into fixed-size tiles (default 8x8)
2) Detects repeated tiles by exact pixel equality
3) Writes a text report with tile counts and tile placement by grid position
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split an image into tiles and find repeated tiles."
    )
    parser.add_argument(
        "image",
        nargs="?",
        default="mapasimples.png",
        help="Input image path (default: mapasimples.png)",
    )
    parser.add_argument(
        "--tile-size",
        type=int,
        default=8,
        help="Tile width and height in pixels (default: 8)",
    )
    parser.add_argument(
        "--report",
        default="mapasimples_tile_report.txt",
        help="Output text report path",
    )
    parser.add_argument(
        "--max-different-pixels",
        type=int,
        default=0,
        help=(
            "Treat tiles as equal if at most this many pixels differ "
            "(default: 0, exact match)"
        ),
    )
    parser.add_argument(
        "--pixel-diff-threshold",
        type=int,
        default=0,
        help=(
            "Per-channel tolerance for a pixel to be considered different "
            "(default: 0)"
        ),
    )
    parser.add_argument(
        "--no-prefer-solid-colors",
        action="store_true",
        help="Disable solid-color seed preference in fuzzy mode",
    )
    return parser.parse_args()


def analyze_tiles(
    image_path: Path,
    tile_size: int,
    max_different_pixels: int = 0,
    pixel_diff_threshold: int = 0,
    prefer_solid_colors: bool = True,
) -> dict:
    img = Image.open(image_path)
    w, h = img.size

    if w % tile_size != 0 or h % tile_size != 0:
        raise ValueError(
            f"Image size {w}x{h} is not divisible by tile size {tile_size}."
        )

    cols = w // tile_size
    rows = h // tile_size

    # Fast path for exact matching.
    tile_key_to_id: dict[bytes, int] = {}
    unique_tile_arrays: list[np.ndarray] = []
    unique_tiles: list[Image.Image] = []
    solid_seed_ids: list[int] = []
    placements: list[list[int]] = [[-1 for _ in range(cols)] for _ in range(rows)]
    occurrences: dict[int, list[tuple[int, int]]] = defaultdict(list)

    def changed_pixel_count(a: np.ndarray, b: np.ndarray) -> int:
        diff = np.abs(a - b)
        if diff.ndim == 2:
            pixel_changed = diff > pixel_diff_threshold
        else:
            pixel_changed = np.any(diff > pixel_diff_threshold, axis=-1)
        return int(np.count_nonzero(pixel_changed))

    def make_solid_image(color: np.ndarray | int) -> tuple[np.ndarray, Image.Image]:
        if img.mode in ("P", "L"):
            value = int(color)
            solid_arr = np.full((tile_size, tile_size), value, dtype=np.uint8)
            if img.mode == "P":
                solid_img = Image.fromarray(solid_arr, mode="P")
                palette = img.getpalette()
                if palette is not None:
                    solid_img.putpalette(palette)
            else:
                solid_img = Image.fromarray(solid_arr, mode="L")
            return solid_arr.astype(np.int16), solid_img

        color_vec = np.asarray(color, dtype=np.uint8)
        channels = int(color_vec.shape[0])
        solid_arr = np.tile(color_vec, (tile_size, tile_size, 1)).astype(np.uint8)
        if channels not in (3, 4):
            raise ValueError(f"Unsupported channel count for solid tile seed: {channels}")
        solid_img = Image.fromarray(solid_arr)
        return solid_arr.astype(np.int16), solid_img

    if max_different_pixels > 0 and prefer_solid_colors:
        full_arr = np.asarray(img)
        if full_arr.ndim == 2:
            colors, counts = np.unique(full_arr, return_counts=True)
            order = np.argsort(-counts)
            for idx in order:
                solid_arr, solid_img = make_solid_image(int(colors[idx]))
                tile_id = len(unique_tiles)
                unique_tiles.append(solid_img)
                unique_tile_arrays.append(solid_arr)
                solid_seed_ids.append(tile_id)
        else:
            flat = full_arr.reshape(-1, full_arr.shape[-1])
            colors, counts = np.unique(flat, axis=0, return_counts=True)
            order = np.argsort(-counts)
            for idx in order:
                solid_arr, solid_img = make_solid_image(colors[idx])
                tile_id = len(unique_tiles)
                unique_tiles.append(solid_img)
                unique_tile_arrays.append(solid_arr)
                solid_seed_ids.append(tile_id)

    for row in range(rows):
        for col in range(cols):
            left = col * tile_size
            top = row * tile_size
            tile = img.crop((left, top, left + tile_size, top + tile_size))
            if max_different_pixels == 0:
                key = tile.tobytes()
                if key in tile_key_to_id:
                    tile_id = tile_key_to_id[key]
                else:
                    tile_id = len(unique_tiles)
                    tile_key_to_id[key] = tile_id
                    unique_tiles.append(tile.copy())
            else:
                tile_arr = np.asarray(tile, dtype=np.int16)
                tile_id = -1

                # Prefer mapping near-solid noisy tiles to seeded solid colors.
                if solid_seed_ids:
                    best_solid_id = -1
                    best_solid_diff = max_different_pixels + 1
                    for existing_id in solid_seed_ids:
                        changed_count = changed_pixel_count(tile_arr, unique_tile_arrays[existing_id])
                        if changed_count <= max_different_pixels and changed_count < best_solid_diff:
                            best_solid_id = existing_id
                            best_solid_diff = changed_count
                    if best_solid_id != -1:
                        tile_id = best_solid_id

                if tile_id == -1:
                    best_id = -1
                    best_diff = max_different_pixels + 1
                    for existing_id, existing_arr in enumerate(unique_tile_arrays):
                        changed_count = changed_pixel_count(tile_arr, existing_arr)
                        if changed_count <= max_different_pixels and changed_count < best_diff:
                            best_id = existing_id
                            best_diff = changed_count
                            if best_diff == 0:
                                break
                    tile_id = best_id

                if tile_id == -1:
                    tile_id = len(unique_tiles)
                    unique_tiles.append(tile.copy())
                    unique_tile_arrays.append(tile_arr)

            placements[row][col] = tile_id
            occurrences[tile_id].append((col, row))

    return {
        "image_path": image_path,
        "image_size": (w, h),
        "tile_size": tile_size,
        "max_different_pixels": max_different_pixels,
        "pixel_diff_threshold": pixel_diff_threshold,
        "prefer_solid_colors": prefer_solid_colors,
        "solid_seed_count": len(solid_seed_ids),
        "grid": (cols, rows),
        "total_tiles": cols * rows,
        "unique_tiles": len(unique_tiles),
        "unique_tile_images": unique_tiles,
        "placements": placements,
        "occurrences": occurrences,
    }


def write_report(result: dict, report_path: Path) -> None:
    cols, rows = result["grid"]
    total_tiles = result["total_tiles"]
    unique_tiles = result["unique_tiles"]
    repeated_tiles = total_tiles - unique_tiles

    lines: list[str] = []
    lines.append("Tile Repetition Report")
    lines.append("======================")
    lines.append(f"Image: {result['image_path']}")
    lines.append(f"Image size: {result['image_size'][0]}x{result['image_size'][1]}")
    lines.append(f"Tile size: {result['tile_size']}x{result['tile_size']}")
    lines.append(
        "Matching mode: "
        f"max_different_pixels={result['max_different_pixels']}, "
        f"pixel_diff_threshold={result['pixel_diff_threshold']}, "
        f"prefer_solid_colors={result['prefer_solid_colors']}"
    )
    lines.append(f"Solid seed tiles: {result['solid_seed_count']}")
    lines.append(f"Grid: {cols}x{rows}")
    lines.append(f"Total tiles: {total_tiles}")
    lines.append(f"Unique tiles: {unique_tiles}")
    lines.append(f"Repeated tiles: {repeated_tiles}")
    lines.append(f"Within 250 unique tiles: {'YES' if unique_tiles <= 250 else 'NO'}")
    lines.append("")

    lines.append("Placement Grid (tile IDs by [col,row])")
    lines.append("--------------------------------------")
    for row in range(rows):
        row_ids = " ".join(f"{tile_id:03d}" for tile_id in result["placements"][row])
        lines.append(f"row {row:02d}: {row_ids}")
    lines.append("")

    lines.append("Unique Tile Occurrences")
    lines.append("-----------------------")
    for tile_id in range(unique_tiles):
        coords = result["occurrences"][tile_id]
        first_col, first_row = coords[0]
        lines.append(
            f"tile {tile_id:03d}: count={len(coords):3d}, first=[{first_col},{first_row}], positions={coords}"
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    image_path = Path(args.image)
    report_path = Path(args.report)

    result = analyze_tiles(
        image_path=image_path,
        tile_size=args.tile_size,
        max_different_pixels=args.max_different_pixels,
        pixel_diff_threshold=args.pixel_diff_threshold,
        prefer_solid_colors=not args.no_prefer_solid_colors,
    )
    write_report(result=result, report_path=report_path)

    print(f"Report saved to: {report_path}")
    print(
        f"Unique tiles: {result['unique_tiles']} / {result['total_tiles']} "
        f"({'OK' if result['unique_tiles'] <= 250 else 'TOO MANY'})"
    )


if __name__ == "__main__":
    main()