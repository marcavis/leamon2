#!/usr/bin/env python3
"""Check how many colors a Pokemon sprite PNG uses.

Usage:
  python leamonScripts/check_sprite_colors.py yuria
  python leamonScripts/check_sprite_colors.py --path graphics/pokemon/yuria
    python leamonScripts/check_sprite_colors.py yuria --check-gba

This script reads PNG files directly (no Pillow dependency) and reports:
- Total unique RGBA colors
- Unique visible colors (alpha > 0)
- Whether visible colors exceed the 15-color sprite limit
"""

from __future__ import annotations

import argparse
from collections import Counter
import math
import struct
import sys
from typing import TypeAlias
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAGENTA = (255, 0, 255)

RgbaColor: TypeAlias = tuple[int, int, int, int]


class PngDecodeError(Exception):
    pass


def png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    length = struct.pack(">I", len(chunk_data))
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(chunk_data, crc)
    return length + chunk_type + chunk_data + struct.pack(">I", crc & 0xFFFFFFFF)


def write_rgba_png(png_path: Path, width: int, height: int, pixels: list[RgbaColor]) -> None:
    if len(pixels) != width * height:
        raise ValueError("Pixel count does not match image dimensions")

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    raw_rows = bytearray()
    for row_index in range(height):
        raw_rows.append(0)
        start = row_index * width
        end = start + width
        for r, g, b, a in pixels[start:end]:
            raw_rows.extend((r, g, b, a))

    idat = zlib.compress(bytes(raw_rows))
    png_data = bytearray(PNG_SIGNATURE)
    png_data.extend(png_chunk(b"IHDR", ihdr))
    png_data.extend(png_chunk(b"IDAT", idat))
    png_data.extend(png_chunk(b"IEND", b""))
    png_path.write_bytes(png_data)


def paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def unpack_sub_byte_samples(row: bytes, width: int, bit_depth: int) -> list[int]:
    if bit_depth == 8:
        return list(row[:width])

    mask = (1 << bit_depth) - 1
    samples: list[int] = []
    bits_left = 0
    current = 0

    for byte in row:
        current = (current << 8) | byte
        bits_left += 8
        while bits_left >= bit_depth and len(samples) < width:
            shift = bits_left - bit_depth
            value = (current >> shift) & mask
            samples.append(value)
            bits_left -= bit_depth
            current &= (1 << bits_left) - 1 if bits_left else 0

    if len(samples) != width:
        raise PngDecodeError("Failed to unpack indexed samples from row")

    return samples


def parse_png_rgba_pixels(png_path: Path) -> tuple[int, int, list[RgbaColor]]:
    data = png_path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise PngDecodeError("Not a PNG file")

    offset = len(PNG_SIGNATURE)
    width = height = None
    bit_depth = color_type = interlace = None
    palette: list[tuple[int, int, int]] | None = None
    palette_alpha: list[int] | None = None
    idat_chunks: list[bytes] = []

    while offset < len(data):
        if offset + 8 > len(data):
            raise PngDecodeError("Truncated PNG chunk header")

        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        offset += 8

        if offset + length + 4 > len(data):
            raise PngDecodeError("Truncated PNG chunk data")

        chunk_data = data[offset : offset + length]
        offset += length
        _crc = data[offset : offset + 4]
        offset += 4

        if chunk_type == b"IHDR":
            if length != 13:
                raise PngDecodeError("Invalid IHDR length")
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if compression != 0 or filter_method != 0:
                raise PngDecodeError("Unsupported PNG compression/filter method")
            if interlace not in (0, 1):
                raise PngDecodeError("Invalid interlace value")
        elif chunk_type == b"PLTE":
            if length % 3 != 0:
                raise PngDecodeError("Invalid PLTE chunk length")
            palette = [
                (chunk_data[i], chunk_data[i + 1], chunk_data[i + 2])
                for i in range(0, length, 3)
            ]
        elif chunk_type == b"tRNS":
            palette_alpha = list(chunk_data)
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None:
        raise PngDecodeError("Missing IHDR")

    if interlace == 1:
        raise PngDecodeError("Interlaced PNG not supported")

    if not idat_chunks:
        raise PngDecodeError("Missing IDAT")

    # Channels per pixel by color type.
    channels_by_type = {
        0: 1,  # grayscale
        2: 3,  # RGB
        3: 1,  # indexed
        4: 2,  # grayscale + alpha
        6: 4,  # RGBA
    }
    if color_type not in channels_by_type:
        raise PngDecodeError(f"Unsupported PNG color type: {color_type}")

    channels = channels_by_type[color_type]
    bytes_per_pixel_for_filter = max(1, math.ceil((channels * bit_depth) / 8))
    bits_per_row = width * channels * bit_depth
    bytes_per_row = (bits_per_row + 7) // 8

    raw = zlib.decompress(b"".join(idat_chunks))
    expected = height * (1 + bytes_per_row)
    if len(raw) != expected:
        raise PngDecodeError(
            f"Unexpected decompressed size: got {len(raw)}, expected {expected}"
        )

    rows: list[bytes] = []
    pos = 0
    prev_row = b"\x00" * bytes_per_row

    for _ in range(height):
        filter_type = raw[pos]
        pos += 1
        row_data = bytearray(raw[pos : pos + bytes_per_row])
        pos += bytes_per_row

        if filter_type == 0:
            pass
        elif filter_type == 1:
            for i in range(bytes_per_row):
                left = row_data[i - bytes_per_pixel_for_filter] if i >= bytes_per_pixel_for_filter else 0
                row_data[i] = (row_data[i] + left) & 0xFF
        elif filter_type == 2:
            for i in range(bytes_per_row):
                row_data[i] = (row_data[i] + prev_row[i]) & 0xFF
        elif filter_type == 3:
            for i in range(bytes_per_row):
                left = row_data[i - bytes_per_pixel_for_filter] if i >= bytes_per_pixel_for_filter else 0
                up = prev_row[i]
                row_data[i] = (row_data[i] + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            for i in range(bytes_per_row):
                left = row_data[i - bytes_per_pixel_for_filter] if i >= bytes_per_pixel_for_filter else 0
                up = prev_row[i]
                up_left = prev_row[i - bytes_per_pixel_for_filter] if i >= bytes_per_pixel_for_filter else 0
                row_data[i] = (row_data[i] + paeth_predictor(left, up, up_left)) & 0xFF
        else:
            raise PngDecodeError(f"Unsupported PNG filter type: {filter_type}")

        row_bytes = bytes(row_data)
        rows.append(row_bytes)
        prev_row = row_bytes

    pixels: list[RgbaColor] = []

    for row in rows:
        if color_type == 3:
            if palette is None:
                raise PngDecodeError("Indexed PNG missing PLTE")
            indices = unpack_sub_byte_samples(row, width, bit_depth)
            for idx in indices:
                if idx >= len(palette):
                    raise PngDecodeError(f"Palette index out of range: {idx}")
                r, g, b = palette[idx]
                if palette_alpha is not None and idx < len(palette_alpha):
                    a = palette_alpha[idx]
                else:
                    a = 255
                pixels.append((r, g, b, a))
        elif color_type == 2:
            if bit_depth not in (8, 16):
                raise PngDecodeError(f"Unsupported RGB bit depth: {bit_depth}")
            step = 3 * (2 if bit_depth == 16 else 1)
            for i in range(0, len(row), step):
                if bit_depth == 8:
                    r, g, b = row[i], row[i + 1], row[i + 2]
                else:
                    r, g, b = row[i], row[i + 2], row[i + 4]
                pixels.append((r, g, b, 255))
        elif color_type == 6:
            if bit_depth not in (8, 16):
                raise PngDecodeError(f"Unsupported RGBA bit depth: {bit_depth}")
            step = 4 * (2 if bit_depth == 16 else 1)
            for i in range(0, len(row), step):
                if bit_depth == 8:
                    r, g, b, a = row[i], row[i + 1], row[i + 2], row[i + 3]
                else:
                    r, g, b, a = row[i], row[i + 2], row[i + 4], row[i + 6]
                pixels.append((r, g, b, a))
        elif color_type == 0:
            if bit_depth not in (1, 2, 4, 8, 16):
                raise PngDecodeError(f"Unsupported grayscale bit depth: {bit_depth}")
            values = unpack_sub_byte_samples(row, width, bit_depth) if bit_depth < 8 else list(row[:width])
            for v in values:
                pixels.append((v, v, v, 255))
        elif color_type == 4:
            if bit_depth not in (8, 16):
                raise PngDecodeError(f"Unsupported grayscale-alpha bit depth: {bit_depth}")
            step = 2 * (2 if bit_depth == 16 else 1)
            for i in range(0, len(row), step):
                if bit_depth == 8:
                    gray, a = row[i], row[i + 1]
                else:
                    gray, a = row[i], row[i + 2]
                pixels.append((gray, gray, gray, a))

    return width, height, pixels


def create_testing_ground_image(
    png_path: Path,
    width: int,
    height: int,
    pixels: list[RgbaColor],
    colors_to_mark: set[RgbaColor],
) -> Path:
    marked_pixels = [
        (MAGENTA[0], MAGENTA[1], MAGENTA[2], pixel[3]) if pixel in colors_to_mark else pixel
        for pixel in pixels
    ]

    combined_pixels: list[RgbaColor] = []
    for row_index in range(height):
        start = row_index * width
        end = start + width
        combined_pixels.extend(pixels[start:end])
        combined_pixels.extend(marked_pixels[start:end])

    output_path = png_path.with_name(f"testing-ground-{png_path.stem}.png")
    write_rgba_png(output_path, width * 2, height, combined_pixels)
    return output_path


def analyze_pokemon_sprite_folder(folder: Path, limit: int, check_gba: bool) -> int:
    png_files = sorted(folder.glob("*.png"))
    png_files = [p for p in png_files if not p.name.startswith("testing-ground-")]
    if not check_gba:
        png_files = [p for p in png_files if not p.stem.endswith("_gba")]

    if not png_files:
        print(f"No PNG files found in {folder}")
        return 2

    mode_text = "including _gba variants" if check_gba else "excluding _gba variants"
    print(f"Analyzing {len(png_files)} sprite file(s) in: {folder} ({mode_text})\n")

    over_limit = False
    for png_path in png_files:
        try:
            width, height, pixels = parse_png_rgba_pixels(png_path)
        except Exception as exc:
            print(f"{png_path.name}: ERROR - {exc}")
            over_limit = True
            continue

        colors = set(pixels)
        visible_colors = {c for c in colors if c[3] > 0}
        transparent_colors = {c for c in colors if c[3] == 0}

        status = "OK"
        if len(visible_colors) > limit:
            status = "OVER LIMIT"
            over_limit = True

        print(
            f"{png_path.name}: visible={len(visible_colors):2d}, "
            f"total_rgba={len(colors):2d}, transparent_variants={len(transparent_colors):2d} -> {status}"
        )

        if len(visible_colors) > limit:
            visible_counts = Counter(pixel for pixel in pixels if pixel[3] > 0)
            sorted_counts = sorted(
                visible_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
            print("  Colors by usage (descending):")
            for color, count in sorted_counts:
                print(f"    {count:4d} px  {color}")

            colors_to_mark = {color for color, _count in sorted_counts[limit:]}
            testing_ground_path = create_testing_ground_image(
                png_path,
                width,
                height,
                pixels,
                colors_to_mark,
            )
            if any(color[:3] == MAGENTA for color in visible_colors):
                print(f"  Warning: {png_path.name} already uses magenta {MAGENTA}.")
            print(
                f"  Testing ground: {testing_ground_path.name} "
                f"(right half marks {len(colors_to_mark)} least-used over-budget colors in {MAGENTA})"
            )

    print(f"\nVisible-color limit: <= {limit}")
    if over_limit:
        print("Result: One or more files exceed the limit (or failed to parse).")
        return 1

    print("Result: All checked files are within the limit.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check color counts in Pokemon sprite PNGs"
    )
    parser.add_argument(
        "pokemon",
        nargs="?",
        help="Pokemon folder name under graphics/pokemon (e.g. yuria)",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Direct path to a sprite folder (alternative to pokemon name)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Visible-color limit (default: 15)",
    )
    parser.add_argument(
        "--check-gba",
        action="store_true",
        help="Include *_gba.png files in the check (default: ignored)",
    )
    args = parser.parse_args()

    if args.path is None and not args.pokemon:
        parser.error("Provide either a pokemon name or --path")

    repo_root = Path(__file__).resolve().parent.parent

    if args.path is not None:
        folder = args.path
        if not folder.is_absolute():
            folder = (repo_root / folder).resolve()
    else:
        folder = (repo_root / "graphics" / "pokemon" / args.pokemon).resolve()

    if not folder.exists():
        print(f"Folder not found: {folder}")
        return 2
    if not folder.is_dir():
        print(f"Not a folder: {folder}")
        return 2

    return analyze_pokemon_sprite_folder(folder, args.limit, args.check_gba)


if __name__ == "__main__":
    sys.exit(main())
