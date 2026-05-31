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
- Whether a paired source sprite and back sprite can share one normal palette
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
DEFAULT_BG_RGB = (152, 208, 160)

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


def write_indexed_png(
    png_path: Path,
    width: int,
    height: int,
    pixels: list[RgbaColor],
    palette_rgb: list[tuple[int, int, int]],
) -> None:
    if len(pixels) != width * height:
        raise ValueError("Pixel count does not match image dimensions")
    if len(palette_rgb) == 0 or len(palette_rgb) > 16:
        raise ValueError("Indexed writer expects 1..16 palette entries")

    palette_index = {rgb: idx for idx, rgb in enumerate(palette_rgb)}

    ihdr = struct.pack(">IIBBBBB", width, height, 4, 3, 0, 0, 0)
    plte = bytearray()
    for r, g, b in palette_rgb:
        plte.extend((r, g, b))

    raw_rows = bytearray()
    for row_index in range(height):
        raw_rows.append(0)
        start = row_index * width
        end = start + width
        row = pixels[start:end]
        idx_values = []
        for px in row:
            rgb = px[:3]
            if rgb not in palette_index:
                raise ValueError(f"Pixel color {rgb} missing from palette")
            idx_values.append(palette_index[rgb])

        for i in range(0, len(idx_values), 2):
            hi = idx_values[i]
            lo = idx_values[i + 1] if i + 1 < len(idx_values) else 0
            raw_rows.append((hi << 4) | lo)

    idat = zlib.compress(bytes(raw_rows))
    png_data = bytearray(PNG_SIGNATURE)
    png_data.extend(png_chunk(b"IHDR", ihdr))
    png_data.extend(png_chunk(b"PLTE", bytes(plte)))
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


def sorted_visible_colors_by_usage(pixels: list[RgbaColor]) -> list[RgbaColor]:
    counts = Counter(pixel for pixel in pixels if pixel[3] > 0)
    sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [color for color, _count in sorted_counts]


def apply_magenta_marks(
    pixels: list[RgbaColor],
    colors_to_mark: set[RgbaColor],
) -> list[RgbaColor]:
    return [
        (MAGENTA[0], MAGENTA[1], MAGENTA[2], pixel[3]) if pixel in colors_to_mark else pixel
        for pixel in pixels
    ]


def build_palette_strip_pixels(
    colors: list[RgbaColor],
    target_height: int,
    swatch_size: int = 4,
) -> tuple[int, int, list[RgbaColor]]:
    cols = 1 if len(colors) <= 16 else 2
    rows = max(1, math.ceil(len(colors) / cols))
    strip_width = cols * swatch_size
    strip_height = max(target_height, rows * swatch_size)
    strip_pixels: list[RgbaColor] = [(0, 0, 0, 0)] * (strip_width * strip_height)

    for index, color in enumerate(colors):
        col = index // rows
        row = index % rows
        x0 = col * swatch_size
        y0 = row * swatch_size
        for dy in range(swatch_size):
            for dx in range(swatch_size):
                x = x0 + dx
                y = y0 + dy
                strip_pixels[y * strip_width + x] = color

    return strip_width, strip_height, strip_pixels


def build_triptych_with_palettes(
    width: int,
    height: int,
    left_pixels: list[RgbaColor],
    middle_pixels: list[RgbaColor],
    right_pixels: list[RgbaColor],
) -> tuple[int, int, list[RgbaColor]]:
    left_palette = sorted_visible_colors_by_usage(left_pixels)
    middle_palette = sorted_visible_colors_by_usage(middle_pixels)
    right_palette = sorted_visible_colors_by_usage(right_pixels)

    left_pw, left_ph, left_pp = build_palette_strip_pixels(left_palette, height)
    middle_pw, middle_ph, middle_pp = build_palette_strip_pixels(middle_palette, height)
    right_pw, right_ph, right_pp = build_palette_strip_pixels(right_palette, height)

    canvas_height = max(height, left_ph, middle_ph, right_ph)
    canvas_width = (width + left_pw) + (width + middle_pw) + (width + right_pw)
    canvas_pixels: list[RgbaColor] = [(0, 0, 0, 0)] * (canvas_width * canvas_height)

    def blit(src_width: int, src_height: int, src_pixels: list[RgbaColor], dst_x: int, dst_y: int) -> None:
        for y in range(src_height):
            src_start = y * src_width
            dst_start = (dst_y + y) * canvas_width + dst_x
            canvas_pixels[dst_start : dst_start + src_width] = src_pixels[src_start : src_start + src_width]

    section0_x = 0
    section1_x = section0_x + width + left_pw
    section2_x = section1_x + width + middle_pw

    blit(width, height, left_pixels, section0_x, 0)
    blit(left_pw, left_ph, left_pp, section0_x + width, 0)
    blit(width, height, middle_pixels, section1_x, 0)
    blit(middle_pw, middle_ph, middle_pp, section1_x + width, 0)
    blit(width, height, right_pixels, section2_x, 0)
    blit(right_pw, right_ph, right_pp, section2_x + width, 0)

    return canvas_width, canvas_height, canvas_pixels


def write_testing_ground_variants(
    png_path: Path,
    width: int,
    height: int,
    original_pixels: list[RgbaColor],
    colors_to_mark: set[RgbaColor],
    remap_map: dict[RgbaColor, RgbaColor],
) -> tuple[Path, int, int, list[RgbaColor]]:
    left_pixels = apply_magenta_marks(original_pixels, colors_to_mark)
    middle_pixels = original_pixels
    right_pixels = [remap_map.get(pixel, pixel) for pixel in original_pixels]

    canvas_width, canvas_height, canvas_pixels = build_triptych_with_palettes(
        width,
        height,
        left_pixels,
        middle_pixels,
        right_pixels,
    )

    output_path = png_path.with_name(f"testing-ground-{png_path.stem}.png")
    write_rgba_png(output_path, canvas_width, canvas_height, canvas_pixels)
    return output_path, canvas_width, canvas_height, canvas_pixels


def write_testing_grounds_combined(
    folder: Path,
    front_stem: str,
    top_width: int,
    top_height: int,
    top_pixels: list[RgbaColor],
    bottom_width: int,
    bottom_height: int,
    bottom_pixels: list[RgbaColor],
) -> Path:
    combined_width = max(top_width, bottom_width)
    combined_height = top_height + bottom_height
    combined_pixels: list[RgbaColor] = [(0, 0, 0, 0)] * (combined_width * combined_height)

    def blit(src_width: int, src_height: int, src_pixels: list[RgbaColor], dst_x: int, dst_y: int) -> None:
        for y in range(src_height):
            src_start = y * src_width
            dst_start = (dst_y + y) * combined_width + dst_x
            combined_pixels[dst_start : dst_start + src_width] = src_pixels[src_start : src_start + src_width]

    blit(top_width, top_height, top_pixels, 0, 0)
    blit(bottom_width, bottom_height, bottom_pixels, 0, top_height)

    combined_path = folder / f"testing-grounds-combined-{front_stem}.png"
    write_rgba_png(combined_path, combined_width, combined_height, combined_pixels)
    return combined_path


def build_shared_palette_colors(
    front_sorted: list[RgbaColor],
    back_sorted: list[RgbaColor],
    background_rgb: tuple[int, int, int],
    max_entries: int = 16,
) -> list[tuple[int, int, int]]:
    ordered: list[tuple[int, int, int]] = [background_rgb]
    seen: set[tuple[int, int, int]] = {background_rgb}

    for color in front_sorted:
        rgb = color[:3]
        if rgb not in seen:
            ordered.append(rgb)
            seen.add(rgb)

    for color in back_sorted:
        rgb = color[:3]
        if rgb not in seen:
            ordered.append(rgb)
            seen.add(rgb)

    if len(ordered) > max_entries:
        raise ValueError(f"Palette has {len(ordered)} colors, exceeds {max_entries} entries")

    while len(ordered) < max_entries:
        ordered.append((0, 0, 0))

    return ordered


def write_jasc_palette(pal_path: Path, colors_rgb: list[tuple[int, int, int]]) -> None:
    lines = ["JASC-PAL", "0100", str(len(colors_rgb))]
    lines.extend(f"{r} {g} {b}" for r, g, b in colors_rgb)
    pal_path.write_text("\n".join(lines) + "\n", encoding="ascii")


def prompt_yes_no(prompt: str) -> bool:
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def should_offer_promote(front_path: Path) -> bool:
    excluded_stems = {"anim_front", "front", "icon", "overworld", "footprint"}
    return front_path.stem not in excluded_stems and not front_path.stem.startswith("testing-ground")


def fill_transparent_with_bg(pixels: list[RgbaColor], bg_rgb: tuple[int, int, int]) -> list[RgbaColor]:
    br, bg, bb = bg_rgb
    return [
        (br, bg, bb, 255) if pixel[3] == 0 else pixel
        for pixel in pixels
    ]


def make_two_frame_vertical_stack(
    width: int,
    height: int,
    pixels: list[RgbaColor],
) -> tuple[int, int, list[RgbaColor]]:
    stacked_height = height * 2
    stacked_pixels: list[RgbaColor] = pixels + pixels
    return width, stacked_height, stacked_pixels


def color_distance_sq(a: RgbaColor, b: RgbaColor) -> int:
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    da = a[3] - b[3]
    return dr * dr + dg * dg + db * db + da * da


def map_unpopular_to_nearest_popular(
    unpopular_colors: list[RgbaColor],
    popular_colors: list[RgbaColor],
) -> dict[RgbaColor, RgbaColor]:
    if not popular_colors:
        return {}

    mapping: dict[RgbaColor, RgbaColor] = {}
    for unpopular in unpopular_colors:
        nearest = min(
            popular_colors,
            key=lambda popular: color_distance_sq(unpopular, popular),
        )
        mapping[unpopular] = nearest
    return mapping


def pair_candidate_path(png_path: Path) -> Path | None:
    stem = png_path.stem
    if stem.endswith("back"):
        return None
    return png_path.with_name(f"{stem}back.png")


def analyze_paired_source_sprites(
    front_path: Path,
    front_width: int,
    front_height: int,
    front_pixels: list[RgbaColor],
    front_limit: int,
    folder: Path,
    offer_promote: bool,
) -> None:
    back_path = pair_candidate_path(front_path)
    if back_path is None or not back_path.exists():
        return

    try:
        back_width, back_height, back_pixels = parse_png_rgba_pixels(back_path)
    except Exception as exc:
        print(f"  Paired source check skipped for {back_path.name}: ERROR - {exc}")
        return

    front_visible = {pixel for pixel in front_pixels if pixel[3] > 0}
    back_visible = {pixel for pixel in back_pixels if pixel[3] > 0}
    shared_visible = front_visible | back_visible
    matching_visible = front_visible & back_visible
    front_only_visible = front_visible - back_visible
    back_only_visible = back_visible - front_visible

    print(f"  Paired source check: {front_path.name} + {back_path.name}")
    print(
        f"    front_visible={len(front_visible):2d}, back_visible={len(back_visible):2d}, "
        f"matching={len(matching_visible):2d}, shared_visible={len(shared_visible):2d}"
    )
    print(
        f"    front-only colors={len(front_only_visible):2d}, back-only colors={len(back_only_visible):2d}"
    )
    print(
        f"    same visible colors: {'yes' if front_visible == back_visible else 'no'}"
    )
    print("    front-first plan: finalize the front palette, then fit the back sprite to it")

    front_visible_counts = Counter(pixel for pixel in front_pixels if pixel[3] > 0)
    front_sorted = sorted(front_visible_counts.items(), key=lambda item: (-item[1], item[0]))
    front_popular = [color for color, _count in front_sorted[:front_limit]]
    front_unpopular = [color for color, _count in front_sorted[front_limit:]]
    front_unpopular_set = set(front_unpopular)
    front_remap = map_unpopular_to_nearest_popular(front_unpopular, front_popular)
    front_testing_path, front_tg_w, front_tg_h, front_tg_pixels = write_testing_ground_variants(
        front_path,
        front_width,
        front_height,
        front_pixels,
        front_unpopular_set,
        front_remap,
    )
    print(
        f"    front testing ground: {front_testing_path.name} "
        "(magenta=front colors outside top 15; includes palette strips)"
    )

    back_visible_counts = Counter(pixel for pixel in back_pixels if pixel[3] > 0)
    back_sorted = sorted(back_visible_counts.items(), key=lambda item: (-item[1], item[0]))
    back_only_sorted = sorted(
        back_only_visible,
        key=lambda color: (-back_visible_counts[color], color),
    )
    back_remap_to_front = map_unpopular_to_nearest_popular(back_only_sorted, front_popular)
    back_testing_path, back_tg_w, back_tg_h, back_tg_pixels = write_testing_ground_variants(
        back_path,
        back_width,
        back_height,
        back_pixels,
        back_only_visible,
        back_remap_to_front,
    )
    print(
        f"    back testing ground: {back_testing_path.name} "
        "(magenta=colors not found in front; includes palette strips)"
    )

    if len(shared_visible) <= front_limit:
        print(
            f"    shared normal.pal fits the limit: yes (<= {front_limit})"
        )
        print(f"    promote with shared palette: {folder / 'normal.pal'}")
        print(f"    target files: anim_front.png, back.png")

        if offer_promote and should_offer_promote(front_path):
            front_target = folder / "anim_front.png"
            back_target = folder / "back.png"
            normal_pal_target = folder / "normal.pal"
            print(
                f"    palette slot 0 (background/transparent key): {DEFAULT_BG_RGB[0]} {DEFAULT_BG_RGB[1]} {DEFAULT_BG_RGB[2]}"
            )
            if prompt_yes_no(
                "    Promote this pair (overwrite anim_front.png/back.png and regenerate normal.pal)?"
            ):
                front_src_w, front_src_h, front_src_pixels = parse_png_rgba_pixels(front_path)
                back_src_w, back_src_h, back_src_pixels = parse_png_rgba_pixels(back_path)

                front_filled_pixels = fill_transparent_with_bg(front_src_pixels, DEFAULT_BG_RGB)
                back_filled_pixels = fill_transparent_with_bg(back_src_pixels, DEFAULT_BG_RGB)

                front_out_w, front_out_h, front_out_pixels = make_two_frame_vertical_stack(
                    front_src_w,
                    front_src_h,
                    front_filled_pixels,
                )

                palette_colors = build_shared_palette_colors(
                    [color for color, _count in front_sorted],
                    [color for color, _count in back_sorted],
                    DEFAULT_BG_RGB,
                    16,
                )
                write_indexed_png(front_target, front_out_w, front_out_h, front_out_pixels, palette_colors)
                write_indexed_png(back_target, back_src_w, back_src_h, back_filled_pixels, palette_colors)
                write_jasc_palette(normal_pal_target, palette_colors)
                print(
                    f"    promoted: {front_target.name} ({front_out_w}x{front_out_h}), "
                    f"{back_target.name} ({back_src_w}x{back_src_h}), {normal_pal_target.name}"
                )
            else:
                print("    promote skipped")
    else:
        print(
            f"    shared normal.pal fits the limit: no (needs {len(shared_visible)} colors)"
        )
        print(
            "    note: a single normal.pal must cover both front and back sprites, "
            "so the union of their visible colors has to fit the limit"
        )
        combined_path = write_testing_grounds_combined(
            folder,
            front_path.stem,
            front_tg_w,
            front_tg_h,
            front_tg_pixels,
            back_tg_w,
            back_tg_h,
            back_tg_pixels,
        )
        print(f"    combined testing grounds: {combined_path.name}")


def analyze_pokemon_sprite_folder(folder: Path, limit: int, check_gba: bool, offer_promote: bool) -> int:
    png_files = sorted(folder.glob("*.png"))
    png_files = [p for p in png_files if not p.name.startswith("testing-ground")]
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

            popular_colors = [color for color, _count in sorted_counts[:limit]]
            unpopular_list = [color for color, _count in sorted_counts[limit:]]
            unpopular_colors = set(unpopular_list)
            unpopular_to_popular_map = map_unpopular_to_nearest_popular(
                unpopular_list,
                popular_colors,
            )
            paired_candidate = pair_candidate_path(png_path)
            paired_source_exists = (
                not png_path.stem.endswith("back")
                and paired_candidate is not None
                and paired_candidate.exists()
            )
            if not paired_source_exists:
                testing_ground_path, _tg_w, _tg_h, _tg_pixels = write_testing_ground_variants(
                    png_path,
                    width,
                    height,
                    pixels,
                    unpopular_colors,
                    unpopular_to_popular_map,
                )
                if any(color[:3] == MAGENTA for color in visible_colors):
                    print(f"  Warning: {png_path.name} already uses magenta {MAGENTA}.")
                print(
                    f"  Testing ground: {testing_ground_path.name} "
                    f"(left marks {len(unpopular_colors)} over-budget colors in {MAGENTA}; "
                    "each variant includes a vertical palette strip; "
                    "right remaps them to nearest popular colors)"
                )

        if not png_path.stem.endswith("back"):
            analyze_paired_source_sprites(png_path, width, height, pixels, limit, folder, offer_promote)

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
    parser.add_argument(
        "--no-promote-offer",
        action="store_true",
        help="Do not prompt to promote <foo>.png + <foo>back.png into anim_front.png/back.png and regenerate normal.pal",
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

    return analyze_pokemon_sprite_folder(folder, args.limit, args.check_gba, not args.no_promote_offer)


if __name__ == "__main__":
    sys.exit(main())
