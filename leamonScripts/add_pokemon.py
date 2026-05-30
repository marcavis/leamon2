#!/usr/bin/env python3
"""
add_pokemon.py  —  Automates adding a new Pokémon to the pokeemerald-expansion ROM hack.

Usage (run from repository root):
    python leamonScripts/add_pokemon.py leamonScripts/data/moe.txt

What this script edits
──────────────────────
  1. include/constants/species.h            — SPECIES_<NAME> constant
  2. include/constants/pokedex.h            — NATIONAL_DEX_<NAME>, HOENN_DEX_<NAME>, count macros
  3. src/data/graphics/pokemon.h            — sprite / palette declarations
  4. src/data/pokemon/level_up_learnsets/leamon_learnsets.h  — level-up moveset
  5. src/data/pokemon/species_info.h        — full [SPECIES_<NAME>] entry in gSpeciesInfo[]
  6. src/data/pokemon/pokedex_orders.h      — alphabetical, weight, height ordering arrays
  7. src/pokemon.c                          — HOENN_TO_NATIONAL(<NAME>) entry

The script refuses to run (with clear error messages) unless:
  • The graphics folder graphics/pokemon/<name>/ exists and contains all required files.
  • All required definition fields are present in the .txt file.
    • In add mode (default), the species has not already been added.
    • In update mode (--update), the species already exists.
"""

import sys
import argparse
import re
from pathlib import Path

# ─── Constants ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent  # leamonScripts/../

REQUIRED_GRAPHICS = [
    "anim_front.png",
    "back.png",
    "normal.pal",
    "shiny.pal",
    "icon.png",
    "footprint.png",
]

REQUIRED_FIELDS = [
    "BASE_HP", "BASE_ATTACK", "BASE_DEFENSE",
    "BASE_SP_ATTACK", "BASE_SP_DEFENSE", "BASE_SPEED",
    "TYPE1",
    "CATCH_RATE", "EXP_YIELD",
    "GENDER_RATIO", "EGG_CYCLES", "FRIENDSHIP", "GROWTH_RATE",
    "EGG_GROUP1",
    "ABILITY1", "ABILITY2", "ABILITY_HIDDEN",
    "BODY_COLOR",
    "CATEGORY_NAME", "HEIGHT", "WEIGHT",
    "DESCRIPTION_1", "DESCRIPTION_2", "DESCRIPTION_3", "DESCRIPTION_4",
    "POKEMON_SCALE", "POKEMON_OFFSET", "TRAINER_SCALE", "TRAINER_OFFSET",
    "FRONT_PIC_SIZE", "FRONT_PIC_Y_OFFSET",
    "BACK_PIC_SIZE", "BACK_PIC_Y_OFFSET",
    "FRONT_ANIM_FRAMES",
    "BACK_ANIM_ID",
    "ICON_PAL_INDEX",
]

# ─── Parsing ──────────────────────────────────────────────────────────────────

def parse_definition(path: Path) -> dict:
    """Parse KEY = VALUE definition file. Returns a dict of uppercased keys."""
    data: dict = {}
    learnset_lines: list = []
    in_learnset = False

    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.upper().rstrip(":") == "LEARNSET":
                in_learnset = True
                continue
            if in_learnset:
                # Strip inline comments
                entry = line.split("#")[0].strip()
                if entry:
                    learnset_lines.append(entry)
            elif "=" in line:
                key, _, value = line.partition("=")
                key = key.strip().upper()
                value = value.split("#")[0].strip()  # strip inline comments
                if value:
                    data[key] = value

    data["_LEARNSET_LINES"] = learnset_lines
    return data


def derive_names(data: dict, def_path: Path) -> tuple[str, str, str]:
    """
    Returns (name, upper, title):
      name  = lowercase folder/identifier  e.g. "moe"
      upper = uppercase constant suffix    e.g. "MOE"
      title = C symbol suffix              e.g. "Moe"
    """
    name = data.get("NAME", def_path.stem).lower().strip()
    upper = name.upper()
    title = data.get("TITLE_NAME", data.get("DISPLAY_NAME", name.capitalize()))
    # title must start with uppercase for C symbols
    title = title[0].upper() + title[1:] if title else name.capitalize()
    return name, upper, title


# ─── Validation ───────────────────────────────────────────────────────────────

def check_graphics(name: str) -> bool:
    """Verify all required graphics files exist. Returns True if all present."""
    gfx_dir = REPO_ROOT / "graphics" / "pokemon" / name
    ok = True

    if not gfx_dir.is_dir():
        print(f"\n  ERROR: Graphics folder does not exist:\n"
              f"         {gfx_dir}\n\n"
              f"  Create or copy the folder and add the following files before running again:\n"
              + "".join(f"    • {f}\n" for f in REQUIRED_GRAPHICS))
        return False

    for fname in REQUIRED_GRAPHICS:
        fpath = gfx_dir / fname
        if not fpath.exists():
            print(f"  ERROR: Missing required graphics file: {fpath}")
            ok = False

    if not ok:
        print("\n  Fix the missing files above, then run the script again.")
    return ok


def check_required_fields(data: dict) -> bool:
    """Verify all required definition fields are present. Returns True if all present."""
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    ok = True

    if missing:
        print("\n  ERROR: Definition file is missing the following required fields:")
        for f in missing:
            print(f"    • {f}")
        ok = False

    if not data.get("_LEARNSET_LINES"):
        print("\n  ERROR: Definition file has no LEARNSET: section (or it is empty).")
        ok = False

    if not ok:
        print("\n  Fill in the missing fields in the definition file, then run again.")
    return ok


def species_exists(upper: str) -> bool:
    """Return True if SPECIES_<upper> is already defined in species.h."""
    species_h = REPO_ROOT / "include" / "constants" / "species.h"
    return f"SPECIES_{upper}" in species_h.read_text(encoding="utf-8")


# ─── File helpers ─────────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.write_text(content, encoding="utf-8")


def insert_before_anchor(content: str, anchor: str, new_text: str) -> str:
    idx = content.find(anchor)
    if idx == -1:
        raise ValueError(f"Anchor not found: {anchor!r}")
    return content[:idx] + new_text + content[idx:]


def insert_after_anchor(content: str, anchor: str, new_text: str) -> str:
    idx = content.find(anchor)
    if idx == -1:
        raise ValueError(f"Anchor not found: {anchor!r}")
    pos = idx + len(anchor)
    return content[:pos] + new_text + content[pos:]


def replace_first_line_containing(content: str, pattern: str, replacement: str) -> str:
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if pattern in line:
            lines[i] = replacement if replacement.endswith("\n") else replacement + "\n"
            return "".join(lines)
    raise ValueError(f"No line contains pattern: {pattern!r}")


def insert_before_closing_brace(content: str, array_decl: str, new_line: str) -> str:
    """
    Find the array declared by array_decl (e.g. 'const u16 gPokedexOrder_Alphabetical[]')
    and insert new_line before its closing '};'.
    """
    decl_match = re.search(re.escape(array_decl), content)
    if not decl_match:
        raise ValueError(f"Array declaration not found: {array_decl!r}")

    # Find the FIRST standalone "};" after the declaration
    tail = content[decl_match.end():]
    close_match = re.search(r"^};", tail, re.MULTILINE)
    if not close_match:
        raise ValueError(f"Could not find closing '}}' for array {array_decl!r}")

    insert_at = decl_match.end() + close_match.start()
    return content[:insert_at] + f"    {new_line},\n" + content[insert_at:]


# ─── Anim frames helper ───────────────────────────────────────────────────────

def parse_anim_frames(raw: str) -> list[tuple[int, int]]:
    """
    Parse FRONT_ANIM_FRAMES value into a list of (frame_index, duration) tuples.
    Accepts formats like:  (0,1)  or  (0,10),(1,20)
    """
    pairs = re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", raw)
    if not pairs:
        raise ValueError(f"Could not parse FRONT_ANIM_FRAMES: {raw!r}\n"
                         "  Expected format: (0,1) or (0,10),(1,20)")
    return [(int(a), int(b)) for a, b in pairs]


def build_learnset_block(title: str, learnset_lines: list[str]) -> str:
    moves = []
    for line in learnset_lines:
        parts = line.split(",", 1)
        if len(parts) != 2:
            print(f"  WARNING: Skipping malformed learnset line: {line!r}")
            continue
        level, move = parts[0].strip(), parts[1].strip()
        moves.append(f"    LEVEL_UP_MOVE({level:>2}, {move}),")

    return (
        f"static const struct LevelUpMove s{title}LevelUpLearnset[] = {{\n"
        + "\n".join(moves)
        + "\n    LEVEL_UP_END\n};"
    )


def build_species_entry(data: dict, upper: str, title: str) -> str:
    # ── Build types ──────────────────────────────────────────────────────────
    t1 = data["TYPE1"]
    t2 = data.get("TYPE2", "")
    if t2 and t2 not in ("", "TYPE_NONE"):
        types_str = f"MON_TYPES({t1}, {t2})"
    else:
        types_str = f"MON_TYPES({t1})"

    # ── EV yields ────────────────────────────────────────────────────────────
    ev_fields = {
        "HP":        int(data.get("EV_HP", 0)),
        "Attack":    int(data.get("EV_ATTACK", 0)),
        "Defense":   int(data.get("EV_DEFENSE", 0)),
        "Speed":     int(data.get("EV_SPEED", 0)),
        "SpAttack":  int(data.get("EV_SP_ATTACK", 0)),
        "SpDefense": int(data.get("EV_SP_DEFENSE", 0)),
    }
    ev_lines = "".join(
        f"        .evYield_{k} = {v},\n"
        for k, v in ev_fields.items() if v > 0
    )

    # ── Items ────────────────────────────────────────────────────────────────
    item_common = data.get("ITEM_COMMON", "ITEM_NONE")
    item_rare = data.get("ITEM_RARE", "ITEM_NONE")
    item_lines = ""
    if item_common != "ITEM_NONE":
        item_lines += f"        .itemCommon = {item_common},\n"
    if item_rare != "ITEM_NONE":
        item_lines += f"        .itemRare = {item_rare},\n"

    # ── Egg groups ───────────────────────────────────────────────────────────
    eg1 = data["EGG_GROUP1"]
    eg2 = data.get("EGG_GROUP2", "").strip()
    if eg2 and eg2 != eg1:
        egg_str = f"MON_EGG_GROUPS({eg1}, {eg2})"
    else:
        egg_str = f"MON_EGG_GROUPS({eg1})"

    # ── Sprite sizes ─────────────────────────────────────────────────────────
    def parse_size(raw: str) -> str:
        parts = [p.strip() for p in raw.split(",")]
        return f"MON_COORDS_SIZE({parts[0]}, {parts[1]})"

    front_size = parse_size(data["FRONT_PIC_SIZE"])
    back_size  = parse_size(data["BACK_PIC_SIZE"])

    # ── Animation frames ─────────────────────────────────────────────────────
    anim_frames = parse_anim_frames(data["FRONT_ANIM_FRAMES"])
    anim_frames_str = "        .frontAnimFrames = ANIM_FRAMES(\n"
    for fi, dur in anim_frames:
        anim_frames_str += f"            ANIMCMD_FRAME({fi},{dur}),\n"
    anim_frames_str += "        ),"

    # ── Optional animation fields ─────────────────────────────────────────────
    front_anim_id = data.get("FRONT_ANIM_ID", "").strip()
    anim_id_line = f"        .frontAnimId = {front_anim_id},\n" if front_anim_id else ""

    front_anim_delay = int(data.get("FRONT_ANIM_DELAY", 0))
    anim_delay_line = f"        .frontAnimDelay = {front_anim_delay},\n" if front_anim_delay else ""

    enemy_elev = int(data.get("ENEMY_MON_ELEVATION", 0))
    elev_line = f"        .enemyMonElevation = {enemy_elev},\n" if enemy_elev else ""

    shadow_size = data.get("SHADOW_SIZE", "").strip()
    shadow_x = int(data.get("SHADOW_X_OFFSET", 0))
    shadow_y = int(data.get("SHADOW_Y_OFFSET", 0))
    shadow_line = (
        f"        SHADOW({shadow_x}, {shadow_y}, {shadow_size})\n"
        if shadow_size
        else ""
    )

    tab = "    "
    return f"""
{tab}[SPECIES_{upper}] =
{tab}{{
{tab}{tab}.baseHP        = {data['BASE_HP']},
{tab}{tab}.baseAttack    = {data['BASE_ATTACK']},
{tab}{tab}.baseDefense   = {data['BASE_DEFENSE']},
{tab}{tab}.baseSpeed     = {data['BASE_SPEED']},
{tab}{tab}.baseSpAttack  = {data['BASE_SP_ATTACK']},
{tab}{tab}.baseSpDefense = {data['BASE_SP_DEFENSE']},
{tab}{tab}.types = {types_str},
{tab}{tab}.catchRate = {data['CATCH_RATE']},
{tab}{tab}.expYield = {data['EXP_YIELD']},
{ev_lines}{item_lines}{tab}{tab}.genderRatio = {data['GENDER_RATIO']},
{tab}{tab}.eggCycles = {data['EGG_CYCLES']},
{tab}{tab}.friendship = {data['FRIENDSHIP']},
{tab}{tab}.growthRate = {data['GROWTH_RATE']},
{tab}{tab}.eggGroups = {egg_str},
{tab}{tab}.abilities = {{ {data['ABILITY1']}, {data['ABILITY2']}, {data['ABILITY_HIDDEN']} }},
{tab}{tab}.bodyColor = {data['BODY_COLOR']},
{tab}{tab}.speciesName = _("{data.get('DISPLAY_NAME', title)}"),
{tab}{tab}.cryId = CRY_NONE,
{tab}{tab}.natDexNum = NATIONAL_DEX_{upper},
{tab}{tab}.categoryName = _("{data['CATEGORY_NAME']}"),
{tab}{tab}.height = {data['HEIGHT']},
{tab}{tab}.weight = {data['WEIGHT']},
{tab}{tab}.description = COMPOUND_STRING(
{tab}{tab}{tab}"{data['DESCRIPTION_1']}\\n"
{tab}{tab}{tab}"{data['DESCRIPTION_2']}\\n"
{tab}{tab}{tab}"{data['DESCRIPTION_3']}\\n"
{tab}{tab}{tab}"{data['DESCRIPTION_4']}"),
{tab}{tab}.pokemonScale = {data['POKEMON_SCALE']},
{tab}{tab}.pokemonOffset = {data['POKEMON_OFFSET']},
{tab}{tab}.trainerScale = {data['TRAINER_SCALE']},
{tab}{tab}.trainerOffset = {data['TRAINER_OFFSET']},
{tab}{tab}.frontPic = gMonFrontPic_{title},
{tab}{tab}.frontPicSize = {front_size},
{tab}{tab}.frontPicYOffset = {data['FRONT_PIC_Y_OFFSET']},
{anim_frames_str}
{anim_id_line}{anim_delay_line}{elev_line}{tab}{tab}.backPic = gMonBackPic_{title},
{tab}{tab}.backPicSize = {back_size},
{tab}{tab}.backPicYOffset = {data['BACK_PIC_Y_OFFSET']},
{tab}{tab}.backAnimId = {data['BACK_ANIM_ID']},
{tab}{tab}.palette = gMonPalette_{title},
{tab}{tab}.shinyPalette = gMonShinyPalette_{title},
{tab}{tab}.iconSprite = gMonIcon_{title},
{tab}{tab}.iconPalIndex = {data['ICON_PAL_INDEX']},
{shadow_line}{tab}{tab}FOOTPRINT({title})
{tab}{tab}.levelUpLearnset = s{title}LevelUpLearnset,
{tab}{tab}.teachableLearnset = sNoneTeachableLearnset,
{tab}}},
"""


# ─── File edit functions ───────────────────────────────────────────────────────

def edit_species_h(name: str, upper: str, dry_run: bool = False) -> None:
    path = REPO_ROOT / "include" / "constants" / "species.h"
    content = read_file(path)

    anchor = "//Leamon species end here"
    if anchor not in content:
        raise ValueError(f"Anchor '{anchor}' not found in include/constants/species.h.\n"
                         "  The file may have an unexpected structure.")

    # Find the highest existing Leamon species number
    leamon_section = content[:content.find(anchor)]
    leamon_defines = re.findall(r"#define SPECIES_(\w+)\s+(\d+)", leamon_section)
    non_meta = [(n, int(v)) for n, v in leamon_defines
                if n not in ("EGG", "NUM_SPECIES", "NONE")]
    if not non_meta:
        raise ValueError("Could not find any Leamon species defines before the anchor.")

    _, last_num = max(non_meta, key=lambda x: x[1])
    new_num = last_num + 1

    # Insert new define before the end marker
    new_define = f"#define SPECIES_{upper:<42}{new_num}\n\n\n"
    content = insert_before_anchor(content, anchor, new_define)

    # Update SPECIES_EGG to reference the new species
    content = re.sub(
        r"#define SPECIES_EGG\s+\(SPECIES_\w+\s*\+\s*1\)",
        f"#define SPECIES_EGG                                     (SPECIES_{upper} + 1)",
        content,
    )

    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} include/constants/species.h           SPECIES_{upper} = {new_num}")


def edit_pokedex_h(upper: str, dry_run: bool = False) -> None:
    path = REPO_ROOT / "include" / "constants" / "pokedex.h"
    content = read_file(path)

    # ── National Dex enum ──────────────────────────────────────────────────────
    # Find what the current last national-dex leamon entry is (= what NATIONAL_DEX_COUNT
    # currently points to, inside the #if P_GEN_9_POKEMON == TRUE block).
    nat_count_match = re.search(
        r"#if P_GEN_9_POKEMON == TRUE\s*\n\s*#define NATIONAL_DEX_COUNT\s+NATIONAL_DEX_(\w+)",
        content,
    )
    if not nat_count_match:
        raise ValueError("Could not find NATIONAL_DEX_COUNT under P_GEN_9_POKEMON in pokedex.h")
    last_nat = nat_count_match.group(1)

    # Insert new entry into the NationalDexOrder enum after the last leamon entry
    nat_anchor = f"    NATIONAL_DEX_{last_nat},\n"
    # The closing "};" of the NationalDexOrder enum comes right after
    content = content.replace(
        nat_anchor + "};",
        nat_anchor + f"    NATIONAL_DEX_{upper},\n}};",
        1,
    )

    # Update NATIONAL_DEX_COUNT (only the P_GEN_9_POKEMON branch)
    content = re.sub(
        r"(#if P_GEN_9_POKEMON == TRUE\s*\n\s*#define NATIONAL_DEX_COUNT\s+)NATIONAL_DEX_\w+",
        rf"\1NATIONAL_DEX_{upper}",
        content,
    )

    # ── Hoenn Dex enum ────────────────────────────────────────────────────────
    hoenn_count_match = re.search(
        r"#define HOENN_DEX_COUNT \(HOENN_DEX_(\w+) \+ 1\)", content
    )
    if not hoenn_count_match:
        raise ValueError("Could not find HOENN_DEX_COUNT in pokedex.h")
    last_hoenn = hoenn_count_match.group(1)

    hoenn_anchor = f"    HOENN_DEX_{last_hoenn},\n"
    content = content.replace(
        hoenn_anchor + "};",
        hoenn_anchor + f"    HOENN_DEX_{upper},\n}};",
        1,
    )

    content = re.sub(
        r"#define HOENN_DEX_COUNT \(HOENN_DEX_\w+ \+ 1\)",
        f"#define HOENN_DEX_COUNT (HOENN_DEX_{upper} + 1)",
        content,
    )

    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} include/constants/pokedex.h           NATIONAL_DEX_{upper}, HOENN_DEX_{upper}")


def edit_graphics_h(name: str, title: str, dry_run: bool = False) -> None:
    path = REPO_ROOT / "src" / "data" / "graphics" / "pokemon.h"
    content = read_file(path)

    sprite_block = (
        f"\n"
        f'    const u32 gMonFrontPic_{title}[] = INCGFX_U32("graphics/pokemon/{name}/anim_front.png", ".4bpp.lz");\n'
        f'    const u32 gMonBackPic_{title}[] = INCGFX_U32("graphics/pokemon/{name}/back.png", ".4bpp.lz");\n'
        f'    const u16 gMonPalette_{title}[] = INCGFX_U16("graphics/pokemon/{name}/normal.pal", ".gbapal");\n'
        f'    const u16 gMonShinyPalette_{title}[] = INCGFX_U16("graphics/pokemon/{name}/shiny.pal", ".gbapal");\n'
        f'    const u8 gMonIcon_{title}[] = INCGFX_U8("graphics/pokemon/{name}/icon.png", ".4bpp");\n'
        f'    const u8 gMonFootprint_{title}[] = INCGFX_U8("graphics/pokemon/{name}/footprint.png", ".1bpp");'
    )

    # Append after the last line of the file (no trailing newline guard)
    content = content.rstrip() + "\n" + sprite_block + "\n"
    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} src/data/graphics/pokemon.h           gMonFrontPic_{title}, ...")


def edit_learnsets_h(upper: str, title: str, learnset_lines: list[str], dry_run: bool = False) -> None:
    path = REPO_ROOT / "src" / "data" / "pokemon" / "level_up_learnsets" / "leamon_learnsets.h"
    content = read_file(path)

    learnset_block = "\n" + build_learnset_block(title, learnset_lines)

    content = content.rstrip() + "\n" + learnset_block + "\n"
    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} leamon_learnsets.h                    s{title}LevelUpLearnset")


def edit_species_info_h(data: dict, upper: str, title: str, dry_run: bool = False) -> None:
    path = REPO_ROOT / "src" / "data" / "pokemon" / "species_info.h"
    content = read_file(path)

    entry = build_species_entry(data, upper, title)

    anchor = "    /* You may add any custom species below this point"
    if anchor not in content:
        raise ValueError(f"Anchor not found in species_info.h:\n  {anchor!r}")

    content = insert_before_anchor(content, anchor, entry)
    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} src/data/pokemon/species_info.h       [SPECIES_{upper}]")


def edit_learnsets_h_update(title: str, learnset_lines: list[str], dry_run: bool = False) -> None:
    path = REPO_ROOT / "src" / "data" / "pokemon" / "level_up_learnsets" / "leamon_learnsets.h"
    content = read_file(path)

    new_block = build_learnset_block(title, learnset_lines)
    pattern = re.compile(
        rf"static const struct LevelUpMove s{re.escape(title)}LevelUpLearnset\[\] = \{{[\s\S]*?\n\}};",
        re.MULTILINE,
    )
    if not pattern.search(content):
        raise ValueError(f"Could not find existing learnset block for s{title}LevelUpLearnset")

    content = pattern.sub(new_block, content, count=1)
    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} leamon_learnsets.h                    s{title}LevelUpLearnset (updated)")


def edit_species_info_h_update(data: dict, upper: str, title: str, dry_run: bool = False) -> None:
    path = REPO_ROOT / "src" / "data" / "pokemon" / "species_info.h"
    content = read_file(path)

    marker = f"[SPECIES_{upper}]"
    marker_idx = content.find(marker)
    if marker_idx == -1:
        raise ValueError(f"Could not find existing species entry for {marker}")

    block_start = content.rfind("\n", 0, marker_idx) + 1
    open_idx = content.find("{", marker_idx)
    if open_idx == -1:
        raise ValueError(f"Malformed species entry for {marker}: missing '{{'")

    depth = 0
    close_idx = -1
    for i in range(open_idx, len(content)):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                close_idx = i
                break

    if close_idx == -1:
        raise ValueError(f"Malformed species entry for {marker}: unmatched braces")

    block_end = close_idx + 1
    while block_end < len(content) and content[block_end] in " \t":
        block_end += 1
    if block_end < len(content) and content[block_end] == ",":
        block_end += 1
    if block_end < len(content) and content[block_end] == "\n":
        block_end += 1

    new_entry = build_species_entry(data, upper, title).lstrip("\n")
    content = content[:block_start] + new_entry + content[block_end:]

    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} src/data/pokemon/species_info.h       [SPECIES_{upper}] (updated)")


def edit_pokedex_orders_h(data: dict, upper: str, dry_run: bool = False) -> None:
    path = REPO_ROOT / "src" / "data" / "pokemon" / "pokedex_orders.h"
    content = read_file(path)

    entry = f"NATIONAL_DEX_{upper}"

    for array_decl, opt_key, label in [
        ("const u16 gPokedexOrder_Alphabetical[]", "ALPHA_INSERT_BEFORE",  "Alphabetical"),
        ("const u16 gPokedexOrder_Weight[]",       "WEIGHT_INSERT_BEFORE", "Weight"),
        ("const u16 gPokedexOrder_Height[]",       "HEIGHT_INSERT_BEFORE", "Height"),
    ]:
        anchor_before = data.get(opt_key, "").strip()
        if anchor_before:
            # Insert before the specified entry
            target = f"    {anchor_before},"
            if target in content:
                content = content.replace(target, f"    {entry},\n{target}", 1)
            else:
                print(f"  WARNING: {opt_key}={anchor_before!r} not found in "
                      f"pokedex_orders.h — appending {label} to end of array instead.")
                content = insert_before_closing_brace(content, array_decl, entry)
        else:
            # Append before the closing }; of this array
            content = insert_before_closing_brace(content, array_decl, entry)

    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} src/data/pokemon/pokedex_orders.h     {entry} (Alphabetical / Weight / Height)")


def edit_pokemon_c(upper: str, dry_run: bool = False) -> None:
    path = REPO_ROOT / "src" / "pokemon.c"
    content = read_file(path)

    # Find sHoennToNationalOrder array and insert before its closing };
    array_decl = "sHoennToNationalOrder["
    content = insert_before_closing_brace(content, array_decl, f"HOENN_TO_NATIONAL({upper})")

    write_file(path, content, dry_run)
    status = "[DRY-RUN]" if dry_run else "[OK]"
    print(f"  {status} src/pokemon.c                         HOENN_TO_NATIONAL({upper})")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a custom Pokemon from a definition file"
    )
    parser.add_argument(
        "definition_file",
        help="Path to definition txt (example: leamonScripts/data/moe.txt)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview all edits without writing files",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update an existing species from definition file (species_info + learnset) instead of adding a new one",
    )
    args = parser.parse_args()

    def_path = Path(args.definition_file).resolve()
    if not def_path.exists():
        print(f"ERROR: Definition file not found: {def_path}")
        sys.exit(1)

    # ── Parse definition file ──────────────────────────────────────────────────
    print(f"\nReading definition file: {def_path.name}")
    data = parse_definition(def_path)
    name, upper, title = derive_names(data, def_path)
    print(f"  Pokémon: {name}  (SPECIES_{upper}, gMonFrontPic_{title})")
    if args.dry_run:
        print("  Mode: dry run (no files will be written)")

    # ── Step 1: Check graphics ─────────────────────────────────────────────────
    print(f"\nChecking graphics/pokemon/{name}/ ...")
    if not check_graphics(name):
        sys.exit(1)
    print("  All required graphics files found.")

    # ── Step 2: Check definition fields ───────────────────────────────────────
    print("\nChecking required definition fields ...")
    if not check_required_fields(data):
        sys.exit(1)
    print("  All required fields present.")

    # ── Step 3: Existence / duplicate guard ───────────────────────────────────
    exists = species_exists(upper)
    if args.update and not exists:
        print(f"\n  ERROR: SPECIES_{upper} does not exist in include/constants/species.h.")
        print("         Use add mode (without --update) to add a brand new species first.")
        sys.exit(1)
    if not args.update and exists:
        print(f"\n  ERROR: SPECIES_{upper} already exists in include/constants/species.h.")
        print("         This species has probably already been added.")
        print("         If you want to apply new data from the definition file, run with --update.")
        sys.exit(1)

    # ── Step 4: Apply all file edits ───────────────────────────────────────────
    print("\nApplying edits ..." if not args.dry_run else "\nSimulating edits (--dry-run) ...")
    errors = []

    if args.update:
        tasks = [
            (edit_learnsets_h_update, (title, data["_LEARNSET_LINES"], args.dry_run), "leamon_learnsets.h"),
            (edit_species_info_h_update, (data, upper, title, args.dry_run), "src/data/pokemon/species_info.h"),
        ]
    else:
        tasks = [
            (edit_species_h,       (name, upper, args.dry_run),                      "include/constants/species.h"),
            (edit_pokedex_h,       (upper, args.dry_run),                            "include/constants/pokedex.h"),
            (edit_graphics_h,      (name, title, args.dry_run),                      "src/data/graphics/pokemon.h"),
            (edit_learnsets_h,     (upper, title, data["_LEARNSET_LINES"], args.dry_run), "leamon_learnsets.h"),
            (edit_species_info_h,  (data, upper, title, args.dry_run),               "src/data/pokemon/species_info.h"),
            (edit_pokedex_orders_h,(data, upper, args.dry_run),                      "src/data/pokemon/pokedex_orders.h"),
            (edit_pokemon_c,       (upper, args.dry_run),                            "src/pokemon.c"),
        ]

    for fn, fn_args, desc in tasks:
        try:
            fn(*fn_args)
        except Exception as e:
            print(f"  [FAIL] {desc}: {e}")
            errors.append(desc)

    # ── Summary ────────────────────────────────────────────────────────────────
    print()
    if errors:
        print(f"Finished with {len(errors)} error(s). Files that failed may need manual edits:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        if args.dry_run:
            action = "update" if args.update else "add"
            print(f"Dry run complete. SPECIES_{upper} passed validation and {action} edits are ready.")
            print("No files were modified.")
            return

        if args.update:
            print(f"Done! SPECIES_{upper} has been updated from the definition file.")
            return

        print(f"Done! SPECIES_{upper} has been added to all source files.")
        print("Reminders:")
        print("  • Add a cry:        see docs tutorial section 5.")
        print("  • Add evolutions:   edit .evolutions field in species_info.h manually.")
        print("  • Wild encounters:  edit src/data/wild_encounters.json.")
        print("  • Overworld sprite: see docs tutorial Optional section 4.")


if __name__ == "__main__":
    main()
