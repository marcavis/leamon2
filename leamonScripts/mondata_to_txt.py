#!/usr/bin/env python3
"""Generate a single species definition txt from mondata sources.

Usage:
    python leamonScripts/mondata_to_txt.py Karin
    python leamonScripts/mondata_to_txt.py Karin --google-sheet <url-or-id>
    python leamonScripts/mondata_to_txt.py Karin --local-ods

By default, this reads a public Google Sheets workbook.
The URL/ID is read from an ignored local config file unless passed via
--google-sheet. You can opt in to the local ODS workbook with --local-ods.

The script finds the exact species row for the requested
character name, and writes leamonScripts/data/karin.txt using the current
template-oriented field order.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import textwrap
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKBOOK_PATH = REPO_ROOT / "leamonScripts" / "mondata.ods"
TEMPLATE_PATH = REPO_ROOT / "leamonScripts" / "data" / "_template.txt"
OUTPUT_DIR = REPO_ROOT / "leamonScripts" / "data"
GOOGLE_SHEET_CONFIG_PATH = REPO_ROOT / "leamonScripts" / ".mondata_to_txt.google_sheet_url"
DEFAULT_GOOGLE_SHEET_NAMES = ["Stats", "Pokedex", "Images", "Learnset", "Evo", "Defaults"]
SHEET_HEADER_MARKERS: dict[str, tuple[str, ...]] = {
    "Stats": ("species", "type1", "type2"),
    "Pokedex": ("species", "pokedexheight", "pokemonscale"),
    "Images": ("imagefolder", "frontspritesize", "backspritesize"),
    "Learnset": ("species", "lvmove1 move1"),
    "Evo": ("method1", "target"),
}

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
            rows = normalize_sheet_rows(sheet_name, rows)
            sheets[sheet_name] = rows
    return sheets


def normalize_sheet_rows(sheet_name: str, rows: list[list[str]]) -> list[list[str]]:
    markers = SHEET_HEADER_MARKERS.get(sheet_name)
    if not markers or not rows:
        return rows

    for idx, row in enumerate(rows[:5]):
        sample = " ".join(normalize_text(cell) for cell in row if normalize_text(cell)).casefold()
        if sample and all(marker in sample for marker in markers):
            return rows[idx:]
    return rows


def parse_google_sheet_id(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("Google Sheet URL/ID cannot be empty")

    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", raw)
    if match:
        return match.group(1)

    if re.fullmatch(r"[a-zA-Z0-9-_]+", raw):
        return raw

    raise ValueError(
        "Could not parse Google Sheet ID. Provide a full URL like "
        "https://docs.google.com/spreadsheets/d/<ID>/edit or pass the raw <ID>."
    )


def load_google_sheet_source(config_path: Path) -> str:
    if not config_path.exists():
        raise FileNotFoundError(
            f"Google Sheet config not found: {config_path}. "
            "Create this file with the sheet URL or ID, or pass --google-sheet."
        )

    for line in config_path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        return value

    raise ValueError(
        f"Google Sheet config file is empty: {config_path}. "
        "Add the sheet URL or ID on a non-comment line."
    )


def load_google_sheets(spreadsheet_id_or_url: str, sheet_names: list[str] | None = None) -> dict[str, list[list[str]]]:
    spreadsheet_id = parse_google_sheet_id(spreadsheet_id_or_url)
    names = sheet_names if sheet_names is not None else DEFAULT_GOOGLE_SHEET_NAMES
    sheets: dict[str, list[list[str]]] = {}

    expected_markers: dict[str, tuple[str, ...]] = {
        "Stats": ("base stats", "ability", "evyield"),
        "Pokedex": ("pokedex", "category(max11chars)", "pokedexheight"),
        "Images": ("imagefolder", "frontspritesize", "backspritesize"),
        "Learnset": ("lvmove1 move1", "species", "move"),
        "Evo": ("method1", "target", "species"),
        "Defaults": ("animate", "exp types", "backspritesize"),
    }

    def validate_sheet_rows(sheet_name: str, rows: list[list[str]]) -> None:
        if not rows:
            raise RuntimeError(
                f"Downloaded sheet {sheet_name!r} but it returned no rows. "
                "Verify the tab exists and is publicly readable."
            )

        markers = expected_markers.get(sheet_name)
        if not markers:
            return

        sample_lines: list[str] = []
        for row in rows[:4]:
            if row:
                sample_lines.append(" ".join(normalize_text(cell) for cell in row if normalize_text(cell)))
        sample = normalize_text(" ".join(sample_lines)).casefold()

        if not any(marker in sample for marker in markers):
            raise RuntimeError(
                f"Downloaded sheet {sheet_name!r}, but the content does not look like that tab. "
                "Check tab names in Google Sheets and ensure the workbook URL/ID is correct."
            )

    for sheet_name in names:
        query = urllib.parse.urlencode({"tqx": "out:csv", "sheet": sheet_name})
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?{query}"
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                payload = response.read().decode("utf-8-sig")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Failed to download sheet {sheet_name!r} from Google Sheets (HTTP {exc.code}). "
                "Ensure the sheet is shared for view access and the tab name matches."
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Failed to download sheet {sheet_name!r} from Google Sheets: {exc.reason}"
            ) from exc

        reader = csv.reader(io.StringIO(payload))
        rows = [[normalize_text(cell) for cell in row] for row in reader]
        validate_sheet_rows(sheet_name, rows)
        sheets[sheet_name] = normalize_sheet_rows(sheet_name, rows)

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


def format_symbol_name(value: str) -> str:
    words = [word for word in re.split(r"[^A-Za-z0-9]+", value.strip()) if word]
    if not words:
        raise ValueError(f"Could not derive a symbol name from {value!r}")
    return "".join(word[:1].upper() + word[1:] for word in words)


def format_gender_ratio(value: str, fallback: str = "50") -> str:
    cleaned = normalize_text(value) or fallback
    if cleaned.casefold() == "genderless":
        return "MON_GENDERLESS"
    return f"PERCENT_FEMALE({cleaned.replace(',', '.')})"


def format_move_name(value: str) -> str:
    return f"MOVE_{sanitize_identifier(value).upper()}"


def format_learnset_level(value: str) -> str:
    cleaned = normalize_text(value)
    if re.fullmatch(r"\d+,\d+", cleaned):
        return cleaned.replace(",", ".")
    return cleaned


def format_evolution_method(value: str) -> str:
    cleaned = normalize_text(value)
    if not cleaned:
        raise ValueError("Evolution method cannot be blank")
    if cleaned.startswith("EVO_"):
        return cleaned
    return f"EVO_{sanitize_identifier(cleaned).upper()}"


def format_evolution_arg(value: str) -> str:
    cleaned = normalize_text(value)
    if not cleaned:
        return "0"
    if re.fullmatch(r"-?\d+", cleaned):
        return cleaned
    if cleaned.startswith(("ITEM_", "TYPE_", "MAP_", "REGION_", "TIME_", "SPECIES_", "MOVE_")):
        return cleaned
    return sanitize_constant(cleaned, "ITEM_")


def format_evolution_target(value: str) -> str:
    cleaned = normalize_text(value)
    if not cleaned:
        raise ValueError("Evolution target cannot be blank")
    if cleaned.startswith("SPECIES_"):
        return cleaned
    return sanitize_constant(cleaned, "SPECIES_")


def format_shadow_size(value: str, fallback: str = "SHADOW_SIZE_M") -> str:
    cleaned = normalize_text(value)
    if not cleaned:
        return fallback
    if cleaned.startswith("SHADOW_SIZE_"):
        return cleaned
    return f"SHADOW_SIZE_{sanitize_identifier(cleaned).upper()}"


def split_description(raw_parts: list[str]) -> list[str]:
    parts = [normalize_text(part) for part in raw_parts if normalize_text(part)]
    return parts[:4]


def parse_evolutions(rows: list[list[str]], species_name: str) -> list[str]:
    wanted = species_name.casefold()
    matches = [row for row in rows if row and row[0].strip().casefold() == wanted]
    if not matches:
        return []
    if len(matches) > 1:
        raise ValueError(f"Multiple evolution rows matched species {species_name!r}")

    row = matches[0]
    evolution_lines: list[str] = []
    for index in range(1, len(row), 3):
        method = row[index].strip() if index < len(row) else ""
        arg = row[index + 1].strip() if index + 1 < len(row) else ""
        target = row[index + 2].strip() if index + 2 < len(row) else ""
        if not method or not target:
            continue
        evolution_lines.append(
            f"{{{format_evolution_method(method)}, {format_evolution_arg(arg)}, {format_evolution_target(target)}}}"
        )
    return evolution_lines


def build_definition(
    species_name: str,
    sheets: dict[str, list[list[str]]],
    source_label: str = "leamonScripts/mondata.ods",
) -> tuple[str, str]:
    stats = sheet_row_by_species(sheets["Stats"], species_name)
    pokedex_rows = sheets["Pokedex"]
    pokedex = sheet_row_by_species(pokedex_rows, species_name)
    images = sheet_row_by_species(sheets["Images"], species_name)
    learn_rows = sheets["Learnset"]
    evolution_rows = sheets.get("Evo", [])

    pokedex_header = pokedex_rows[0] if pokedex_rows else []
    pokedex_header_map: dict[str, int] = {}

    for idx, value in enumerate(pokedex_header):
        key = normalize_text(value).casefold()
        if key:
            pokedex_header_map[key] = idx

    def get_pokedex_cell(header_name: str, fallback_index: int) -> str:
        header_index = pokedex_header_map.get(header_name.casefold())
        if header_index is not None and header_index < len(pokedex):
            return pokedex[header_index]
        if fallback_index < len(pokedex):
            return pokedex[fallback_index]
        return ""

    # Learnset is usually stored as paired rows: levels row followed by move names row.
    # Some sources collapse level+move into a single cell; we support both layouts.
    learnset_levels: list[str] | None = None
    learnset_moves: list[str] | None = None
    wanted = species_name.casefold()
    for index in range(len(learn_rows) - 1):
        if learn_rows[index] and learn_rows[index + 1] and learn_rows[index][0].strip().casefold() == wanted and learn_rows[index + 1][0].strip().casefold() == wanted:
            learnset_levels = learn_rows[index]
            learnset_moves = learn_rows[index + 1]
            break

    learnset_lines: list[str] = []
    if learnset_levels is not None and learnset_moves is not None:
        for level, move in zip(learnset_levels[1:], learnset_moves[1:]):
            if not level.strip() or not move.strip():
                continue
            learnset_lines.append(f"{format_learnset_level(level)},{format_move_name(move)}")

    if not learnset_lines:
        single_rows = [row for row in learn_rows if row and row[0].strip().casefold() == wanted]
        for row in single_rows:
            for cell in row[1:]:
                entry = normalize_text(cell)
                if not entry:
                    continue
                parts = [part.strip() for part in re.split(r"\s*,\s*|\s+", entry, maxsplit=1) if part.strip()]
                if len(parts) != 2:
                    continue
                level, move = parts
                learnset_lines.append(f"{format_learnset_level(level)},{format_move_name(move)}")

    if not learnset_lines:
        if learnset_levels is None or learnset_moves is None:
            raise KeyError(f"Could not find paired learnset rows for {species_name!r}")
        raise ValueError(f"No learnset moves found for {species_name!r}")

    defaults = parse_defaults(sheets.get("Defaults", []))

    file_name = sanitize_identifier(species_name).lower()

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
        "CATEGORY_NAME": get_pokedex_cell("category(max11chars)", 6),
        "HEIGHT": get_pokedex_cell("pokedexHeight", 8),
        "WEIGHT": get_pokedex_cell("pokedexWeight", 9),
        "POKEMON_SCALE": get_pokedex_cell("pokemonScale", 10),
        "POKEMON_OFFSET": get_pokedex_cell("pokemonOffset", 11),
        "TRAINER_SCALE": get_pokedex_cell("trainerScale", 12),
        "TRAINER_OFFSET": get_pokedex_cell("trainerOffset", 13),
        "BODY_COLOR": get_pokedex_cell("color", 14),
        "NO_FLIP": get_pokedex_cell("noflip", 15),
    }

    image_map = {
        "IMAGE_FOLDER": images[1] if len(images) > 1 and images[1].strip() else file_name,
        "FRONT_ANIM_FRAMES": images[5] if len(images) > 5 and images[5].strip() else defaults.get("animate", "[(0,1)]"),
        "BACK_ANIM_ID": images[3] if len(images) > 3 and images[3].strip() else defaults.get("backAnim", "BACK_ANIM_NONE"),
        "FRONT_PIC_SIZE": images[6] if len(images) > 6 and images[6].strip() else defaults.get("frontSpriteSize", "(64,64)"),
        "FRONT_PIC_Y_OFFSET": images[7] if len(images) > 7 and images[7].strip() else defaults.get("frontYOffset", "0"),
        "BACK_PIC_SIZE": images[8] if len(images) > 8 and images[8].strip() else defaults.get("backSpriteSize", "(64,64)"),
        "BACK_PIC_Y_OFFSET": images[9] if len(images) > 9 and images[9].strip() else defaults.get("backYOffset", "0"),
        "SHADOW_X_OFFSET": images[10] if len(images) > 10 and images[10].strip() else defaults.get("shadowXOffset", "2"),
        "SHADOW_Y_OFFSET": images[11] if len(images) > 11 and images[11].strip() else defaults.get("shadowYOffset", "16"),
        "SHADOW_SIZE": images[12] if len(images) > 12 and images[12].strip() else defaults.get("shadowSize", "SHADOW_SIZE_M"),
        "ICON_PAL_INDEX": images[4] if len(images) > 4 and images[4].strip() else "0",
    }

    display_name_raw = get_pokedex_cell("name", 1)
    display_name = normalize_text(display_name_raw) if normalize_text(display_name_raw) else species_name

    description_lines = split_description([
        get_pokedex_cell("pkdx1", 2),
        get_pokedex_cell("pkdx2", 3),
        get_pokedex_cell("pkdx3", 4),
        get_pokedex_cell("pkdx4", 5),
    ])
    if not description_lines:
        description_lines = ["TODO: Pokedex description"]

    evolution_lines = parse_evolutions(evolution_rows, species_name)

    def add_line(lines: list[str], key: str, value: str, *, allow_blank: bool = False) -> None:
        if value or allow_blank:
            lines.append(f"{key} = {value}")

    out: list[str] = []
    out.append(f"# Generated from {source_label} by mondata_to_txt.py")
    out.append(f"NAME = {file_name}")
    out.append(f"DISPLAY_NAME = {display_name}")
    image_folder = sanitize_identifier(image_map["IMAGE_FOLDER"]).lower()
    if image_folder and image_folder != file_name:
        out.append(f"IMAGE_FOLDER = {image_folder}")
        out.append(f"GRAPHICS_TITLE_NAME = {format_symbol_name(image_map['IMAGE_FOLDER'])}")
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
    out.append("# Battle shadow tuning (optional; consumed by add_pokemon.py)")
    out.append("# Negative X moves shadow left; positive Y moves it down toward feet.")
    out.append(f"SHADOW_X_OFFSET = {image_map['SHADOW_X_OFFSET']}")
    out.append(f"SHADOW_Y_OFFSET = {image_map['SHADOW_Y_OFFSET']}")
    out.append(f"SHADOW_SIZE = {format_shadow_size(image_map['SHADOW_SIZE'])}")
    out.append("")
    out.append(f"FRONT_ANIM_FRAMES = {parse_anim_frames(image_map['FRONT_ANIM_FRAMES'])}")
    out.append(f"BACK_ANIM_ID = {image_map['BACK_ANIM_ID']}")
    out.append("")
    out.append(f"ICON_PAL_INDEX = {image_map['ICON_PAL_INDEX'] or '0'}")
    out.append("")

    if evolution_lines:
        out.append("EVOLUTIONS:")
        out.extend(evolution_lines)
        out.append("")

    out.append("LEARNSET:")
    out.extend(learnset_lines)
    out.append("")

    return file_name, "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a species txt from Google Sheets (default) or local ODS")
    parser.add_argument("species", help="Character/species name to extract, e.g. Karin")
    parser.add_argument(
        "--google-sheet",
        help=(
            "Google Sheets URL or spreadsheet ID to use as source. "
            "If omitted, reads leamonScripts/.mondata_to_txt.google_sheet_url."
        ),
    )
    parser.add_argument(
        "--local-ods",
        action="store_true",
        help="Use local leamonScripts/mondata.ods instead of Google Sheets",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to leamonScripts/data/<species>.txt",
    )
    args = parser.parse_args()

    if args.local_ods and args.google_sheet:
        print("ERROR: Use either --local-ods or --google-sheet, not both.")
        return 1

    if args.local_ods:
        sheets = load_workbook(WORKBOOK_PATH)
        source_label = "leamonScripts/mondata.ods"
    else:
        try:
            google_sheet = args.google_sheet or load_google_sheet_source(GOOGLE_SHEET_CONFIG_PATH)
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}")
            print(f"Tip: create {GOOGLE_SHEET_CONFIG_PATH} or pass --google-sheet.")
            print(f"Tip: rerun with --local-ods to use {WORKBOOK_PATH}")
            return 1
        try:
            sheets = load_google_sheets(google_sheet)
        except RuntimeError as exc:
            print(f"ERROR: {exc}")
            print(f"Tip: rerun with --local-ods to use {WORKBOOK_PATH}")
            return 1
        source_label = f"Google Sheets ({parse_google_sheet_id(google_sheet)})"

    file_name, content = build_definition(args.species, sheets, source_label)
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