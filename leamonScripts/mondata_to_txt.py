#!/usr/bin/env python3
"""Generate a single species definition txt from leamonScripts/mondata.ods.

Usage:
    python leamonScripts/mondata_to_txt.py Karin

This reads the ODS workbook, finds the exact species row for the requested
character name, and writes leamonScripts/data/karin.txt using the current
template-oriented field order.
"""

from __future__ import annotations

import argparse
import re
import textwrap
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKBOOK_PATH = REPO_ROOT / "leamonScripts" / "mondata.ods"
TEMPLATE_PATH = REPO_ROOT / "leamonScripts" / "data" / "_template.txt"
OUTPUT_DIR = REPO_ROOT / "leamonScripts" / "data"

NS = {
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def sanitize_identifier(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value)
    return ascii_value.strip("_")


def sanitize_constant(value: str, prefix: str) -> str:
    token = sanitize_identifier(value).upper()
    if token.startswith(prefix):
        return token
    return f"{prefix}{token}"


def quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def expand_row(row_elem: ET.Element) -> list[str]:
    cells: list[str] = []
    for cell in row_elem:
        tag = cell.tag.rsplit("}", 1)[-1]
        if tag == "table-cell":
            repeat = int(cell.attrib.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
            text = normalize_text("".join(cell.itertext()))
            cells.extend([text] * repeat)
        elif tag == "covered-table-cell":
            repeat = int(cell.attrib.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
            cells.extend([""] * repeat)
    return cells


def load_workbook(path: Path) -> dict[str, list[list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")

    sheets: dict[str, list[list[str]]] = {}
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
        for table_elem in root.findall(".//table:table", NS):
            sheet_name = table_elem.attrib.get(f"{{{NS['table']}}}name", "")
            rows: list[list[str]] = []
            for row_elem in table_elem.findall("table:table-row", NS):
                repeat = int(row_elem.attrib.get(f"{{{NS['table']}}}number-rows-repeated", "1"))
                row = expand_row(row_elem)
                for _ in range(repeat):
                    rows.append(row[:])
            sheets[sheet_name] = rows
    return sheets


def sheet_row_by_species(rows: list[list[str]], species_name: str) -> list[str]:
    wanted = species_name.casefold()
    matches = [row for row in rows if row and row[0].strip().casefold() == wanted]
    if not matches:
        raise KeyError(f"Could not find species {species_name!r} in sheet")
    if len(matches) > 1:
        raise ValueError(f"Multiple rows matched species {species_name!r}")
    return matches[0]


def parse_defaults(rows: list[list[str]]) -> dict[str, str]:
    defaults: dict[str, str] = {}
    for row in rows:
        if len(row) >= 6 and row[4]:
            defaults[row[4].strip()] = row[5].strip()
    return defaults


def parse_size(raw: str) -> tuple[int, int]:
    match = re.search(r"(\d+)\s*,\s*(\d+)", raw)
    if not match:
        raise ValueError(f"Could not parse sprite size value: {raw!r}")
    return int(match.group(1)), int(match.group(2))


def parse_anim_frames(raw: str) -> str:
    pairs = re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", raw)
    if not pairs:
        return "(0,1)"
    return ",".join(f"({frame},{duration})" for frame, duration in pairs)


def normalize_enum_suffix(value: str) -> str:
    return sanitize_identifier(value).upper()


def format_gender_ratio(value: str, fallback: str = "50") -> str:
    cleaned = normalize_text(value) or fallback
    if cleaned.casefold() == "genderless":
        return "MON_GENDERLESS"
    return f"PERCENT_FEMALE({cleaned.replace(',', '.')})"


def format_move_name(value: str) -> str:
    return f"MOVE_{sanitize_identifier(value).upper()}"


def split_description(raw_parts: list[str]) -> list[str]:
    template = [
        "First line of the Pokédex entry.",
        "Second line.",
        "Third line.",
        "Fourth line.",
    ]
    parts = [normalize_text(part) for part in raw_parts if normalize_text(part)]
    if not parts:
        return template[:]

    if len(parts) >= 4:
        return parts[:4]

    words = " ".join(parts).split()
    if not words:
        return template[:]

    if len(words) < 4:
        lines = words[:]
        while len(lines) < 4:
            lines.append(lines[-1] if lines else template[len(lines)])
        return lines[:4]

    base, extra = divmod(len(words), 4)
    sizes = [base + (1 if index < extra else 0) for index in range(4)]
    lines: list[str] = []
    cursor = 0
    for size in sizes:
        chunk = words[cursor:cursor + size]
        cursor += size
        lines.append(" ".join(chunk))
    return lines


def build_definition(species_name: str, sheets: dict[str, list[list[str]]]) -> tuple[str, str]:
    stats = sheet_row_by_species(sheets["Stats"], species_name)
    pokedex = sheet_row_by_species(sheets["Pokedex"], species_name)
    images = sheet_row_by_species(sheets["Images"], species_name)
    learn_rows = sheets["Learnset"]

    # Learnset rows are stored as paired rows: levels row followed by move names row.
    learnset_levels: list[str] | None = None
    learnset_moves: list[str] | None = None
    wanted = species_name.casefold()
    for index in range(len(learn_rows) - 1):
        if learn_rows[index] and learn_rows[index + 1] and learn_rows[index][0].strip().casefold() == wanted and learn_rows[index + 1][0].strip().casefold() == wanted:
            learnset_levels = learn_rows[index]
            learnset_moves = learn_rows[index + 1]
            break
    if learnset_levels is None or learnset_moves is None:
        raise KeyError(f"Could not find paired learnset rows for {species_name!r}")

    defaults = parse_defaults(sheets.get("Defaults", []))

    stats_map = {
        "BASE_HP": stats[1],
        "BASE_ATTACK": stats[2],
        "BASE_DEFENSE": stats[3],
        "BASE_SP_ATTACK": stats[4],
        "BASE_SP_DEFENSE": stats[5],
        "BASE_SPEED": stats[6],
        "BST": stats[7],
        "TYPE1": stats[8],
        "TYPE2": stats[9],
        "ABILITY1": stats[10],
        "ABILITY2": stats[11],
        "ABILITY_HIDDEN": stats[12],
        "EV_HP": stats[13],
        "EV_ATTACK": stats[14],
        "EV_DEFENSE": stats[15],
        "EV_SP_ATTACK": stats[16],
        "EV_SP_DEFENSE": stats[17],
        "EV_SPEED": stats[18],
        "ITEM_COMMON": stats[19],
        "ITEM_RARE": stats[20],
        "CATCH_RATE": stats[21],
        "EXP_YIELD": stats[22],
        "GENDER_RATIO": stats[23],
        "EGG_CYCLES": stats[24],
        "FRIENDSHIP": stats[25],
        "GROWTH_RATE": stats[26],
        "EGG_GROUP1": stats[27],
        "EGG_GROUP2": stats[28],
    }

    pokedex_map = {
        "CATEGORY_NAME": pokedex[6],
        "HEIGHT": pokedex[7],
        "WEIGHT": pokedex[8],
        "POKEMON_SCALE": pokedex[9],
        "POKEMON_OFFSET": pokedex[10],
        "TRAINER_SCALE": pokedex[11],
        "TRAINER_OFFSET": pokedex[12],
        "BODY_COLOR": pokedex[13],
        "NO_FLIP": pokedex[14],
    }

    image_map = {
        "FRONT_ANIM_FRAMES": images[5] if len(images) > 5 and images[5].strip() else defaults.get("animate", "[(0,1)]"),
        "BACK_ANIM_ID": images[3] if len(images) > 3 and images[3].strip() else defaults.get("backAnim", "BACK_ANIM_NONE"),
        "FRONT_PIC_SIZE": images[6] if len(images) > 6 and images[6].strip() else defaults.get("frontSpriteSize", "(64,64)"),
        "FRONT_PIC_Y_OFFSET": images[7] if len(images) > 7 and images[7].strip() else defaults.get("frontYOffset", "0"),
        "BACK_PIC_SIZE": images[8] if len(images) > 8 and images[8].strip() else defaults.get("backSpriteSize", "(64,64)"),
        "BACK_PIC_Y_OFFSET": images[9] if len(images) > 9 and images[9].strip() else defaults.get("backYOffset", "0"),
        "ICON_PAL_INDEX": images[4] if len(images) > 4 and images[4].strip() else "0",
    }

    display_name = species_name
    file_name = sanitize_identifier(species_name).lower()

    description_lines = split_description(pokedex[2:6])
    if len(description_lines) != 4:
        raise ValueError(f"Expected four description lines for {species_name!r}")

    learnset_lines: list[str] = []
    for level, move in zip(learnset_levels[2:], learnset_moves[2:]):
        if not level.strip() or not move.strip():
            continue
        learnset_lines.append(f"{level.strip()},{format_move_name(move)}")
    if not learnset_lines:
        raise ValueError(f"No learnset moves found for {species_name!r}")

    def add_line(lines: list[str], key: str, value: str, *, allow_blank: bool = False) -> None:
        if value or allow_blank:
            lines.append(f"{key} = {value}")

    out: list[str] = []
    out.append("# Generated from leamonScripts/mondata.ods by mondata_to_txt.py")
    out.append(f"NAME = {file_name}")
    out.append(f"DISPLAY_NAME = {display_name}")
    out.append("")
    out.append(f"BASE_HP = {stats_map['BASE_HP']}")
    out.append(f"BASE_ATTACK = {stats_map['BASE_ATTACK']}")
    out.append(f"BASE_DEFENSE = {stats_map['BASE_DEFENSE']}")
    out.append(f"BASE_SP_ATTACK = {stats_map['BASE_SP_ATTACK']}")
    out.append(f"BASE_SP_DEFENSE = {stats_map['BASE_SP_DEFENSE']}")
    out.append(f"BASE_SPEED = {stats_map['BASE_SPEED']}")
    out.append(f"BST = {stats_map['BST']}")
    out.append("")
    out.append(f"TYPE1 = {sanitize_constant(stats_map['TYPE1'], 'TYPE_')}")
    if normalize_text(stats_map["TYPE2"]):
        out.append(f"TYPE2 = {sanitize_constant(stats_map['TYPE2'], 'TYPE_')}")
    else:
        out.append("TYPE2 = TYPE_NONE")
    out.append("")
    out.append(f"CATCH_RATE = {stats_map['CATCH_RATE']}")
    out.append(f"EXP_YIELD = {stats_map['EXP_YIELD']}")
    for ev_key in ["EV_HP", "EV_ATTACK", "EV_DEFENSE", "EV_SP_ATTACK", "EV_SP_DEFENSE", "EV_SPEED"]:
        if normalize_text(stats_map[ev_key]) and int(stats_map[ev_key]) > 0:
            out.append(f"{ev_key} = {int(stats_map[ev_key])}")
    item_common = normalize_text(stats_map["ITEM_COMMON"])
    item_rare = normalize_text(stats_map["ITEM_RARE"])
    if item_common and item_common not in {"0", "ITEM_NONE"}:
        out.append(f"ITEM_COMMON = {sanitize_constant(item_common, 'ITEM_') if not item_common.startswith('ITEM_') else item_common}")
    if item_rare and item_rare not in {"0", "ITEM_NONE"}:
        out.append(f"ITEM_RARE = {sanitize_constant(item_rare, 'ITEM_') if not item_rare.startswith('ITEM_') else item_rare}")
    out.append("")
    out.append(f"GENDER_RATIO = {format_gender_ratio(stats_map['GENDER_RATIO'])}")
    out.append(f"EGG_CYCLES = {stats_map['EGG_CYCLES']}")
    out.append("FRIENDSHIP = STANDARD_FRIENDSHIP")
    out.append(f"GROWTH_RATE = GROWTH_{normalize_enum_suffix(stats_map['GROWTH_RATE'])}")
    out.append("")
    egg1 = normalize_text(stats_map["EGG_GROUP1"])
    egg2 = normalize_text(stats_map["EGG_GROUP2"])
    out.append(f"EGG_GROUP1 = {sanitize_constant(egg1, 'EGG_GROUP_') if egg1 else 'EGG_GROUP_HUMAN_LIKE'}")
    if egg2 and egg2 != egg1:
        out.append(f"EGG_GROUP2 = {sanitize_constant(egg2, 'EGG_GROUP_')}")
    out.append("")
    out.append(f"ABILITY1 = {sanitize_constant(stats_map['ABILITY1'] or 'none', 'ABILITY_') if normalize_text(stats_map['ABILITY1']) else 'ABILITY_NONE'}")
    out.append(f"ABILITY2 = {sanitize_constant(stats_map['ABILITY2'] or 'none', 'ABILITY_') if normalize_text(stats_map['ABILITY2']) else 'ABILITY_NONE'}")
    out.append(f"ABILITY_HIDDEN = {sanitize_constant(stats_map['ABILITY_HIDDEN'] or 'none', 'ABILITY_') if normalize_text(stats_map['ABILITY_HIDDEN']) else 'ABILITY_NONE'}")
    out.append("")
    out.append(f"BODY_COLOR = {sanitize_constant(pokedex_map['BODY_COLOR'], 'BODY_COLOR_')}")
    out.append("")
    out.append(f"CATEGORY_NAME = {pokedex_map['CATEGORY_NAME']}")
    out.append(f"HEIGHT = {pokedex_map['HEIGHT']}")
    out.append(f"WEIGHT = {pokedex_map['WEIGHT']}")
    for index, description in enumerate(description_lines, start=1):
        out.append(f"DESCRIPTION_{index} = {quote(description)}")
    out.append("")
    out.append(f"POKEMON_SCALE = {pokedex_map['POKEMON_SCALE']}")
    out.append(f"POKEMON_OFFSET = {pokedex_map['POKEMON_OFFSET']}")
    out.append(f"TRAINER_SCALE = {pokedex_map['TRAINER_SCALE']}")
    out.append(f"TRAINER_OFFSET = {pokedex_map['TRAINER_OFFSET']}")
    out.append("")
    front_size = parse_size(image_map["FRONT_PIC_SIZE"])
    back_size = parse_size(image_map["BACK_PIC_SIZE"])
    out.append(f"FRONT_PIC_SIZE = {front_size[0]},{front_size[1]}")
    out.append(f"FRONT_PIC_Y_OFFSET = {image_map['FRONT_PIC_Y_OFFSET']}")
    out.append(f"BACK_PIC_SIZE = {back_size[0]},{back_size[1]}")
    out.append(f"BACK_PIC_Y_OFFSET = {image_map['BACK_PIC_Y_OFFSET']}")
    out.append("")
    out.append(f"FRONT_ANIM_FRAMES = {parse_anim_frames(image_map['FRONT_ANIM_FRAMES'])}")
    out.append(f"BACK_ANIM_ID = {image_map['BACK_ANIM_ID']}")
    out.append("")
    out.append(f"ICON_PAL_INDEX = {image_map['ICON_PAL_INDEX'] or '0'}")
    out.append("")
    out.append("LEARNSET:")
    out.extend(learnset_lines)
    out.append("")

    return file_name, "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a species txt from mondata.ods")
    parser.add_argument("species", help="Character/species name to extract, e.g. Karin")
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to leamonScripts/data/<species>.txt",
    )
    args = parser.parse_args()

    sheets = load_workbook(WORKBOOK_PATH)
    file_name, content = build_definition(args.species, sheets)
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path
    else:
        output_path = OUTPUT_DIR / f"{file_name}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())