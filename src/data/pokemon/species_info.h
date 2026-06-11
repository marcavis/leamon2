#include "constants/abilities.h"
#include "constants/teaching_types.h"
#include "species_info/shared_dex_text.h"
#include "species_info/shared_front_pic_anims.h"

// Macros for ease of use.

#define EVOLUTION(...) (const struct Evolution[]) { __VA_ARGS__, { EVOLUTIONS_END }, }
#define CONDITIONS(...) ((const struct EvolutionParam[]) { __VA_ARGS__, {CONDITIONS_END} })

#define ANIM_FRAMES(...) (const union AnimCmd *const[]) { sAnim_GeneralFrame0, (const union AnimCmd[]) { __VA_ARGS__ ANIMCMD_END, }, }

#if P_FOOTPRINTS
#define FOOTPRINT(sprite) .footprint = gMonFootprint_## sprite,
#else
#define FOOTPRINT(sprite)
#endif

#if B_ENEMY_MON_SHADOW_STYLE >= GEN_4 && P_GBA_STYLE_SPECIES_GFX == FALSE
#define SHADOW(x, y, size)  .enemyShadowXOffset = x, .enemyShadowYOffset = y, .enemyShadowSize = size,
#define NO_SHADOW           .suppressEnemyShadow = TRUE,
#else
#define SHADOW(x, y, size)  .enemyShadowXOffset = 0, .enemyShadowYOffset = 0, .enemyShadowSize = 0,
#define NO_SHADOW           .suppressEnemyShadow = FALSE,
#endif

#define SIZE_32x32 1
#define SIZE_64x64 0

// Set .compressed = OW_GFX_COMPRESS
#define COMP OW_GFX_COMPRESS

#if OW_POKEMON_OBJECT_EVENTS
#if OW_PKMN_OBJECTS_SHARE_PALETTES == FALSE
#define OVERWORLD_PAL(...)                                  \
    .overworldPalette = DEFAULT(NULL, __VA_ARGS__),         \
    .overworldShinyPalette = DEFAULT_2(NULL, __VA_ARGS__),
#if P_GENDER_DIFFERENCES
#define OVERWORLD_PAL_FEMALE(...)                                 \
    .overworldPaletteFemale = DEFAULT(NULL, __VA_ARGS__),         \
    .overworldShinyPaletteFemale = DEFAULT_2(NULL, __VA_ARGS__),
#else
#define OVERWORLD_PAL_FEMALE(...)
#endif //P_GENDER_DIFFERENCES
#else
#define OVERWORLD_PAL(...)
#define OVERWORLD_PAL_FEMALE(...)
#endif //OW_PKMN_OBJECTS_SHARE_PALETTES == FALSE

#define OVERWORLD_DATA(picTable, _size, shadow, _tracks, _anims)                                                                     \
{                                                                                                                                       \
    .tileTag = TAG_NONE,                                                                                                                \
    .paletteTag = OBJ_EVENT_PAL_TAG_DYNAMIC,                                                                                            \
    .reflectionPaletteTag = OBJ_EVENT_PAL_TAG_NONE,                                                                                     \
    .size = (_size == SIZE_32x32 ? 512 : 2048),                                                                                         \
    .width = (_size == SIZE_32x32 ? 32 : 64),                                                                                           \
    .height = (_size == SIZE_32x32 ? 32 : 64),                                                                                          \
    .paletteSlot = PALSLOT_NPC_1,                                                                                                       \
    .shadowSize = shadow,                                                                                                               \
    .inanimate = FALSE,                                                                                                                 \
    .compressed = COMP,                                                                                                                 \
    .tracks = _tracks,                                                                                                                  \
    .oam = (_size == SIZE_32x32 ? &gObjectEventBaseOam_32x32 : &gObjectEventBaseOam_64x64),                                             \
    .subspriteTables = (_size == SIZE_32x32 ? sOamTables_32x32 : sOamTables_64x64),                                                     \
    .anims = _anims,                                                                                                                    \
    .images = picTable,                                                                                                                 \
}

#define OVERWORLD(objEventPic, _size, shadow, _tracks, _anims, ...)                                 \
    .overworldData = OVERWORLD_DATA(objEventPic, _size, shadow, _tracks, _anims),                   \
    OVERWORLD_PAL(__VA_ARGS__)

#if P_GENDER_DIFFERENCES
#define OVERWORLD_FEMALE(objEventPic, _size, shadow, _tracks, _anims, ...)                          \
    .overworldDataFemale = OVERWORLD_DATA(objEventPic, _size, shadow, _tracks, _anims),             \
    OVERWORLD_PAL_FEMALE(__VA_ARGS__)
#else
#define OVERWORLD_FEMALE(...)
#endif //P_GENDER_DIFFERENCES

#else
#define OVERWORLD(...)
#define OVERWORLD_FEMALE(...)
#define OVERWORLD_PAL(...)
#define OVERWORLD_PAL_FEMALE(...)
#endif //OW_POKEMON_OBJECT_EVENTS

// Maximum value for a female Pokémon is 254 (MON_FEMALE) which is 100% female.
// 255 (MON_GENDERLESS) is reserved for genderless Pokémon.
#define PERCENT_FEMALE(percent) min(254, ((percent * 255) / 100))

#define MON_TYPES(type1, ...) { type1, DEFAULT(type1, __VA_ARGS__) }
#define MON_EGG_GROUPS(group1, ...) { group1, DEFAULT(group1, __VA_ARGS__) }

#define FLIP    0
#define NO_FLIP 1

const struct SpeciesInfo gSpeciesInfo[] =
{
    [SPECIES_NONE] =
    {
        .speciesName = _("??????????"),
        .cryId = CRY_PORYGON,
        .natDexNum = NATIONAL_DEX_NONE,
        .categoryName = _("Unknown"),
        .height = 0,
        .weight = 0,
        .description = gFallbackPokedexText,
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_CircledQuestionMark,
        .frontPicSize = MON_COORDS_SIZE(40, 40),
        .frontPicYOffset = 12,
        .frontAnimFrames = sAnims_TwoFramePlaceHolder,
        .frontAnimId = ANIM_V_SQUISH_AND_BOUNCE,
        .backPic = gMonBackPic_CircledQuestionMark,
        .backPicSize = MON_COORDS_SIZE(40, 40),
        .backPicYOffset = 12,
        .backAnimId = BACK_ANIM_NONE,
        .palette = gMonPalette_CircledQuestionMark,
        .shinyPalette = gMonShinyPalette_CircledQuestionMark,
        .iconSprite = gMonIcon_QuestionMark,
        .iconPalIndex = 0,
        .pokemonJumpType = PKMN_JUMP_TYPE_NONE,
        FOOTPRINT(QuestionMark)
        SHADOW(-1, 0, SHADOW_SIZE_M)
    #if OW_POKEMON_OBJECT_EVENTS
        .overworldData = {
            .tileTag = TAG_NONE,
            .paletteTag = OBJ_EVENT_PAL_TAG_SUBSTITUTE,
            .reflectionPaletteTag = OBJ_EVENT_PAL_TAG_NONE,
            .size = 512,
            .width = 32,
            .height = 32,
            .paletteSlot = PALSLOT_NPC_1,
            .shadowSize = SHADOW_SIZE_M,
            .inanimate = FALSE,
            .compressed = COMP,
            .tracks = TRACKS_FOOT,
            .oam = &gObjectEventBaseOam_32x32,
            .subspriteTables = sOamTables_32x32,
            .anims = sAnimTable_Following,
            .images = sPicTable_Substitute,
        },
    #endif
        .levelUpLearnset = sNoneLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .eggMoveLearnset = sNoneEggMoveLearnset,
    },

    #include "species_info/gen_1_families.h"
    #include "species_info/gen_2_families.h"
    #include "species_info/gen_3_families.h"
    #include "species_info/gen_4_families.h"
    #include "species_info/gen_5_families.h"
    #include "species_info/gen_6_families.h"
    #include "species_info/gen_7_families.h"
    #include "species_info/gen_8_families.h"
    #include "species_info/gen_9_families.h"

    [SPECIES_EGG] =
    {
        .frontPic = gMonFrontPic_Egg,
        .frontPicSize = MON_COORDS_SIZE(24, 24),
        .frontPicYOffset = 20,
        .backPic = gMonFrontPic_Egg,
        .backPicSize = MON_COORDS_SIZE(24, 24),
        .backPicYOffset = 20,
        .palette = gMonPalette_Egg,
        .shinyPalette = gMonPalette_Egg,
        .iconSprite = gMonIcon_Egg,
        .iconPalIndex = 1,
    },

    [SPECIES_YURIA] =
    {
        .baseHP        = 40,
        .baseAttack    = 70,
        .baseDefense   = 30,
        .baseSpeed     = 85,
        .baseSpAttack  = 25,
        .baseSpDefense = 40,
        .types = MON_TYPES(TYPE_DARK),
        .catchRate = 255,
        .expYield = 67,
        .evYield_Attack = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_FAST,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_NO_EGGS_DISCOVERED),
        .abilities = { ABILITY_GLAD_HANDING, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BLACK,
        .speciesName = _("Yuria"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_YURIA,
        .categoryName = _("Unknown"),
        .height = 15,
        .weight = 410,
        .description = COMPOUND_STRING(
            "Always looking to score.\n"
            "ononono.\n"
            "nonononon\n"
            "onononon."),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Yuria,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Yuria,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_NONE,
        .palette = gMonPalette_Yuria,
        .shinyPalette = gMonShinyPalette_Yuria,
        .iconSprite = gMonIcon_Yuria,
        .iconPalIndex = 0,
        SHADOW(-2, 16, SHADOW_SIZE_S)
        FOOTPRINT(Yuria)
        .levelUpLearnset = sYuriaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },


    [SPECIES_ZEPHYRA] =
    {
        .baseHP        = 55,
        .baseAttack    = 90,
        .baseDefense   = 55,
        .baseSpeed     = 100,
        .baseSpAttack  = 60,
        .baseSpDefense = 55,
        .types = MON_TYPES(TYPE_FIGHTING, TYPE_FLYING),
        .catchRate = 200,
        .expYield = 150,
        .evYield_Speed = 2,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_RECKLESS, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_RED,
        .speciesName = _("Zephyra"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_ZEPHYRA,
        .categoryName = _("Demon-deer"),
        .height = 16,
        .weight = 480,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Zephyra,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Zephyra,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Zephyra,
        .shinyPalette = gMonShinyPalette_Zephyra,
        .iconSprite = gMonIcon_Zephyra,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Zephyra)
        .levelUpLearnset = sZephyraLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_LEA] =
    {
        .baseHP        = 90,
        .baseAttack    = 55,
        .baseDefense   = 75,
        .baseSpeed     = 60,
        .baseSpAttack  = 50,
        .baseSpDefense = 70,
        .types = MON_TYPES(TYPE_NORMAL),
        .catchRate = 140,
        .expYield = 150,
        .evYield_HP = 2,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_FAST,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_NEST_DEFENDER, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BLACK,
        .speciesName = _("Lea"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_LEA,
        .categoryName = _("Matriarch"),
        .height = 16,
        .weight = 600,
        .description = COMPOUND_STRING(
            "A friendly matriarch.\n"
            "ononono.\n"
            "nonononon\n"
            "onononon."),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Lea,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Lea,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_NONE,
        .palette = gMonPalette_Lea,
        .shinyPalette = gMonShinyPalette_Lea,
        .iconSprite = gMonIcon_Lea,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Lea)
        .levelUpLearnset = sLeaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_KARIN] =
    {
        .baseHP        = 50,
        .baseAttack    = 60,
        .baseDefense   = 45,
        .baseSpeed     = 85,
        .baseSpAttack  = 70,
        .baseSpDefense = 105,
        .types = MON_TYPES(TYPE_GHOST, TYPE_FAIRY),
        .catchRate = 140,
        .expYield = 150,
        .evYield_SpDefense = 2,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_NONE, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_YELLOW,
        .speciesName = _("Karin"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_KARIN,
        .categoryName = _("Fox-deer"),
        .height = 17,
        .weight = 530,
        .description = COMPOUND_STRING(
            "Slowly recovering her self-control."),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Karin,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Karin,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Karin,
        .shinyPalette = gMonShinyPalette_Karin,
        .iconSprite = gMonIcon_Karin,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Karin)
        .levelUpLearnset = sKarinLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_CZEPHYRA] =
    {
        .baseHP        = 40,
        .baseAttack    = 60,
        .baseDefense   = 40,
        .baseSpeed     = 80,
        .baseSpAttack  = 50,
        .baseSpDefense = 40,
        .types = MON_TYPES(TYPE_FIGHTING, TYPE_FLYING),
        .catchRate = 200,
        .expYield = 70,
        .evYield_Speed = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_RECKLESS, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_RED,
        .speciesName = _("CZephyra"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_CZEPHYRA,
        .categoryName = _("Demon-deer"),
        .height = 16,
        .weight = 480,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Zephyra,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Zephyra,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Zephyra,
        .shinyPalette = gMonShinyPalette_Zephyra,
        .iconSprite = gMonIcon_Zephyra,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Zephyra)
        .levelUpLearnset = sCzephyraLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_EZEPHYRA] =
    {
        .baseHP        = 70,
        .baseAttack    = 110,
        .baseDefense   = 65,
        .baseSpeed     = 130,
        .baseSpAttack  = 80,
        .baseSpDefense = 65,
        .types = MON_TYPES(TYPE_FIGHTING, TYPE_FLYING),
        .catchRate = 200,
        .expYield = 260,
        .evYield_Speed = 3,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_RECKLESS, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_RED,
        .speciesName = _("EZephyra"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_EZEPHYRA,
        .categoryName = _("Demon-deer"),
        .height = 16,
        .weight = 480,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Zephyra,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Zephyra,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Zephyra,
        .shinyPalette = gMonShinyPalette_Zephyra,
        .iconSprite = gMonIcon_Zephyra,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Zephyra)
        .levelUpLearnset = sEzephyraLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_CADELAIDE] =
    {
        .baseHP        = 40,
        .baseAttack    = 65,
        .baseDefense   = 55,
        .baseSpeed     = 50,
        .baseSpAttack  = 30,
        .baseSpDefense = 50,
        .types = MON_TYPES(TYPE_STEEL),
        .catchRate = 180,
        .expYield = 70,
        .evYield_Attack = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_FAST,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_TURBO_CLAW, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_PINK,
        .speciesName = _("CAdelaide"),
        .cryId = CRY_ADELAIDE,
        .natDexNum = NATIONAL_DEX_CADELAIDE,
        .categoryName = _("Cat"),
        .height = 15,
        .weight = 430,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Adelaide,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Adelaide,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Adelaide,
        .shinyPalette = gMonShinyPalette_Adelaide,
        .iconSprite = gMonIcon_Adelaide,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Adelaide)
        .levelUpLearnset = sCadelaideLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .evolutions = EVOLUTION({EVO_LEVEL, 15, SPECIES_ADELAIDE}),
    },

    [SPECIES_ADELAIDE] =
    {
        .baseHP        = 50,
        .baseAttack    = 75,
        .baseDefense   = 65,
        .baseSpeed     = 60,
        .baseSpAttack  = 40,
        .baseSpDefense = 60,
        .types = MON_TYPES(TYPE_STEEL),
        .catchRate = 180,
        .expYield = 115,
        .evYield_Attack = 1,
        .evYield_Defense = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_FAST,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_TURBO_CLAW, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_PINK,
        .speciesName = _("Adelaide"),
        .cryId = CRY_ADELAIDE,
        .natDexNum = NATIONAL_DEX_ADELAIDE,
        .categoryName = _("Cat"),
        .height = 15,
        .weight = 430,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Adelaide,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Adelaide,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Adelaide,
        .shinyPalette = gMonShinyPalette_Adelaide,
        .iconSprite = gMonIcon_Adelaide,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Adelaide)
        .levelUpLearnset = sAdelaideLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .evolutions = EVOLUTION({EVO_LEVEL, 32, SPECIES_EADELAIDE}),
    },

    [SPECIES_EADELAIDE] =
    {
        .baseHP        = 75,
        .baseAttack    = 115,
        .baseDefense   = 105,
        .baseSpeed     = 70,
        .baseSpAttack  = 50,
        .baseSpDefense = 85,
        .types = MON_TYPES(TYPE_STEEL),
        .catchRate = 180,
        .expYield = 230,
        .evYield_Attack = 2,
        .evYield_Defense = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_FAST,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_TURBO_CLAW, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_PINK,
        .speciesName = _("EAdelaide"),
        .cryId = CRY_ADELAIDE,
        .natDexNum = NATIONAL_DEX_EADELAIDE,
        .categoryName = _("Cat"),
        .height = 15,
        .weight = 430,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Adelaide,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Adelaide,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Adelaide,
        .shinyPalette = gMonShinyPalette_Adelaide,
        .iconSprite = gMonIcon_Adelaide,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Adelaide)
        .levelUpLearnset = sEadelaideLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_GEMMA] =
    {
        .baseHP        = 50,
        .baseAttack    = 70,
        .baseDefense   = 90,
        .baseSpeed     = 50,
        .baseSpAttack  = 50,
        .baseSpDefense = 60,
        .types = MON_TYPES(TYPE_ROCK),
        .catchRate = 180,
        .expYield = 120,
        .evYield_Defense = 2,
        .genderRatio = PERCENT_FEMALE(25),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        // .abilities = { ABILITY_AMULET_LINK, ABILITY_HIGH_MOHS, ABILITY_NONE },
        .abilities = { ABILITY_NONE, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_GREEN,
        .speciesName = _("Gemma"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_GEMMA,
        .categoryName = _("Crystal Fox"),
        .height = 15,
        .weight = 800,
        .description = COMPOUND_STRING(
            "Has trouble showing expressions."),
        .pokemonScale = 800,
        .pokemonOffset = 256,
        .trainerScale = 0,
        .trainerOffset = 256,
        .frontPic = gMonFrontPic_Gemma,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Gemma,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Gemma,
        .shinyPalette = gMonShinyPalette_Gemma,
        .iconSprite = gMonIcon_Gemma,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Gemma)
        .levelUpLearnset = sGemmaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .evolutions = EVOLUTION({EVO_LEVEL, 28, SPECIES_EGEMMA}),
    },

    [SPECIES_EGEMMA] =
    {
        .baseHP        = 70,
        .baseAttack    = 90,
        .baseDefense   = 130,
        .baseSpeed     = 70,
        .baseSpAttack  = 70,
        .baseSpDefense = 80,
        .types = MON_TYPES(TYPE_ROCK),
        .catchRate = 180,
        .expYield = 230,
        .evYield_Defense = 3,
        .genderRatio = PERCENT_FEMALE(25),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_NONE, ABILITY_NONE, ABILITY_NONE },
        //.abilities = { ABILITY_AMULET_LINK, ABILITY_HIGH_MOHS, ABILITY_NONE },
        .bodyColor = BODY_COLOR_GREEN,
        .speciesName = _("EGemma"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_EGEMMA,
        .categoryName = _("Crystal Fox"),
        .height = 15,
        .weight = 800,
        .description = COMPOUND_STRING(
            "Has trouble showing expressions."),
        .pokemonScale = 800,
        .pokemonOffset = 256,
        .trainerScale = 0,
        .trainerOffset = 256,
        .frontPic = gMonFrontPic_Gemma,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Gemma,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Gemma,
        .shinyPalette = gMonShinyPalette_Gemma,
        .iconSprite = gMonIcon_Gemma,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Gemma)
        .levelUpLearnset = sEgemmaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_CAZALEA] =
    {
        .baseHP        = 60,
        .baseAttack    = 30,
        .baseDefense   = 60,
        .baseSpeed     = 30,
        .baseSpAttack  = 75,
        .baseSpDefense = 55,
        .types = MON_TYPES(TYPE_PSYCHIC),
        .catchRate = 200,
        .expYield = 70,
        .evYield_SpAttack = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_ANALYTIC, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BROWN,
        .speciesName = _("CAzalea"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_CAZALEA,
        .categoryName = _("Demon-deer"),
        .height = 16,
        .weight = 715,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Azalea,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Azalea,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Azalea,
        .shinyPalette = gMonShinyPalette_Azalea,
        .iconSprite = gMonIcon_Azalea,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Azalea)
        .levelUpLearnset = sCazaleaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .evolutions = EVOLUTION({EVO_LEVEL, 20, SPECIES_AZALEA}),
    },

    [SPECIES_AZALEA] =
    {
        .baseHP        = 75,
        .baseAttack    = 45,
        .baseDefense   = 75,
        .baseSpeed     = 45,
        .baseSpAttack  = 90,
        .baseSpDefense = 85,
        .types = MON_TYPES(TYPE_PSYCHIC),
        .catchRate = 200,
        .expYield = 150,
        .evYield_SpAttack = 2,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_ANALYTIC, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BROWN,
        .speciesName = _("Azalea"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_AZALEA,
        .categoryName = _("Demon-deer"),
        .height = 16,
        .weight = 715,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Azalea,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Azalea,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Azalea,
        .shinyPalette = gMonShinyPalette_Azalea,
        .iconSprite = gMonIcon_Azalea,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Azalea)
        .levelUpLearnset = sAzaleaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .evolutions = EVOLUTION({EVO_LEVEL, 40, SPECIES_EAZALEA}),
    },

    [SPECIES_EAZALEA] =
    {
        .baseHP        = 90,
        .baseAttack    = 60,
        .baseDefense   = 90,
        .baseSpeed     = 60,
        .baseSpAttack  = 120,
        .baseSpDefense = 100,
        .types = MON_TYPES(TYPE_PSYCHIC),
        .catchRate = 200,
        .expYield = 260,
        .evYield_SpAttack = 3,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_ANALYTIC, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BROWN,
        .speciesName = _("EAzalea"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_EAZALEA,
        .categoryName = _("Demon-deer"),
        .height = 16,
        .weight = 715,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Azalea,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Azalea,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Azalea,
        .shinyPalette = gMonShinyPalette_Azalea,
        .iconSprite = gMonIcon_Azalea,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Azalea)
        .levelUpLearnset = sEazaleaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_CELINE] =
    {
        .baseHP        = 70,
        .baseAttack    = 88,
        .baseDefense   = 60,
        .baseSpeed     = 69,
        .baseSpAttack  = 103,
        .baseSpDefense = 62,
        .types = MON_TYPES(TYPE_ELECTRIC, TYPE_DRAGON),
        .catchRate = 200,
        .expYield = 215,
        .evYield_SpAttack = 2,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_PUNK_ROCK, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BLUE,
        .speciesName = _("Celine"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_CELINE,
        .categoryName = _("Dragon-fox"),
        .height = 17,
        .weight = 615,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Celine,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Celine,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Celine,
        .shinyPalette = gMonShinyPalette_Celine,
        .iconSprite = gMonIcon_Celine,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Celine)
        .levelUpLearnset = sCelineLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_SAYO] =
    {
        .baseHP        = 140,
        .baseAttack    = 100,
        .baseDefense   = 80,
        .baseSpeed     = 60,
        .baseSpAttack  = 160,
        .baseSpDefense = 140,
        .types = MON_TYPES(TYPE_DARK, TYPE_GHOST),
        .catchRate = 15,
        .expYield = 370,
        .evYield_SpAttack = 2,
        .evYield_SpDefense = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 40,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_OPPRESSION_AURA, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BLACK,
        .speciesName = _("Sayo"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_SAYO,
        .categoryName = _("Nogitsune"),
        .height = 24,
        .weight = 3352,
        .description = COMPOUND_STRING(
            "Vengeance in humanoid form."),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 384,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Sayo,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Sayo,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Sayo,
        .shinyPalette = gMonShinyPalette_Sayo,
        .iconSprite = gMonIcon_Sayo,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Sayo)
        .levelUpLearnset = sSayoLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_GONYA] =
    {
        .baseHP        = 95,
        .baseAttack    = 100,
        .baseDefense   = 95,
        .baseSpeed     = 70,
        .baseSpAttack  = 70,
        .baseSpDefense = 100,
        .types = MON_TYPES(TYPE_ICE, TYPE_FAIRY),
        .catchRate = 85,
        .expYield = 285,
        .evYield_HP = 1,
        .evYield_Attack = 1,
        .evYield_Defense = 1,
        .genderRatio = PERCENT_FEMALE(100),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_CUTE_CHARM, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_BROWN,
        .speciesName = _("Gonya"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_GONYA,
        .categoryName = _("Cat"),
        .height = 13,
        .weight = 465,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Gonya,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Gonya,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Gonya,
        .shinyPalette = gMonShinyPalette_Gonya,
        .iconSprite = gMonIcon_Gonya,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Gonya)
        .levelUpLearnset = sGonyaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_CRENSA] =
    {
        .baseHP        = 55,
        .baseAttack    = 61,
        .baseDefense   = 44,
        .baseSpeed     = 56,
        .baseSpAttack  = 60,
        .baseSpDefense = 46,
        .types = MON_TYPES(TYPE_FIRE),
        .catchRate = 110,
        .expYield = 80,
        .evYield_Attack = 1,
        .genderRatio = PERCENT_FEMALE(100),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_ARENA_TRAP, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_PINK,
        .speciesName = _("CRensa"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_CRENSA,
        .categoryName = _("Succubus"),
        .height = 16,
        .weight = 550,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Rensa,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Rensa,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Rensa,
        .shinyPalette = gMonShinyPalette_Rensa,
        .iconSprite = gMonIcon_Rensa,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Rensa)
        .levelUpLearnset = sCrensaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_RENSA] =
    {
        .baseHP        = 68,
        .baseAttack    = 82,
        .baseDefense   = 64,
        .baseSpeed     = 74,
        .baseSpAttack  = 82,
        .baseSpDefense = 66,
        .types = MON_TYPES(TYPE_FIRE, TYPE_STEEL),
        .catchRate = 110,
        .expYield = 165,
        .evYield_Attack = 1,
        .evYield_SpAttack = 1,
        .genderRatio = PERCENT_FEMALE(100),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_ARENA_TRAP, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_PINK,
        .speciesName = _("Rensa"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_RENSA,
        .categoryName = _("Succubus"),
        .height = 16,
        .weight = 550,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Rensa,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Rensa,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Rensa,
        .shinyPalette = gMonShinyPalette_Rensa,
        .iconSprite = gMonIcon_Rensa,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Rensa)
        .levelUpLearnset = sRensaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_ERENSA] =
    {
        .baseHP        = 80,
        .baseAttack    = 100,
        .baseDefense   = 73,
        .baseSpeed     = 90,
        .baseSpAttack  = 100,
        .baseSpDefense = 77,
        .types = MON_TYPES(TYPE_FIRE, TYPE_STEEL),
        .catchRate = 110,
        .expYield = 260,
        .evYield_Attack = 2,
        .evYield_SpAttack = 1,
        .genderRatio = PERCENT_FEMALE(100),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_SKILL_LINK, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_PINK,
        .speciesName = _("ERensa"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_ERENSA,
        .categoryName = _("Succubus"),
        .height = 16,
        .weight = 550,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Rensa,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Rensa,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Rensa,
        .shinyPalette = gMonShinyPalette_Rensa,
        .iconSprite = gMonIcon_Rensa,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Rensa)
        .levelUpLearnset = sErensaLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },

    [SPECIES_LUCILLER] =
    {
        .baseHP        = 80,
        .baseAttack    = 80,
        .baseDefense   = 70,
        .baseSpeed     = 60,
        .baseSpAttack  = 30,
        .baseSpDefense = 50,
        .types = MON_TYPES(TYPE_FIGHTING),
        .catchRate = 110,
        .expYield = 120,
        .evYield_HP = 1,
        .evYield_Attack = 1,
        .genderRatio = PERCENT_FEMALE(25),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_NONE, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_YELLOW,
        .speciesName = _("LucilleR"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_LUCILLER,
        .categoryName = _("Mino-deer"),
        .height = 17,
        .weight = 740,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Lucille,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Lucille,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Lucille,
        .shinyPalette = gMonShinyPalette_Lucille,
        .iconSprite = gMonIcon_Lucille,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Lucille)
        .levelUpLearnset = sLucillerLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .evolutions = EVOLUTION({EVO_LEVEL, 28, SPECIES_ELUCILLER}),
    },

    [SPECIES_ELUCILLER] =
    {
        .baseHP        = 110,
        .baseAttack    = 110,
        .baseDefense   = 100,
        .baseSpeed     = 70,
        .baseSpAttack  = 50,
        .baseSpDefense = 70,
        .types = MON_TYPES(TYPE_FIGHTING),
        .catchRate = 110,
        .expYield = 230,
        .evYield_HP = 1,
        .evYield_Attack = 1,
        .evYield_Defense = 1,
        .genderRatio = PERCENT_FEMALE(25),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_SLOW,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_HUMAN_LIKE),
        .abilities = { ABILITY_NONE, ABILITY_NONE, ABILITY_NONE },
        .bodyColor = BODY_COLOR_YELLOW,
        .speciesName = _("ELucilleR"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_ELUCILLER,
        .categoryName = _("Mino-deer"),
        .height = 17,
        .weight = 740,
        .description = COMPOUND_STRING(
            "TODO: Pokedex description"),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 288,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_Lucille,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = ANIM_FRAMES(
            ANIMCMD_FRAME(0,1),
        ),
        .backPic = gMonBackPic_Lucille,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .backAnimId = BACK_ANIM_H_VIBRATE,
        .palette = gMonPalette_Lucille,
        .shinyPalette = gMonShinyPalette_Lucille,
        .iconSprite = gMonIcon_Lucille,
        .iconPalIndex = 0,
        SHADOW(2, 16, SHADOW_SIZE_M)
        FOOTPRINT(Lucille)
        .levelUpLearnset = sElucillerLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
    },
    /* You may add any custom species below this point based on the following structure: */

    /*
    [SPECIES_NONE] =
    {
        .baseHP        = 1,
        .baseAttack    = 1,
        .baseDefense   = 1,
        .baseSpeed     = 1,
        .baseSpAttack  = 1,
        .baseSpDefense = 1,
        .types = MON_TYPES(TYPE_MYSTERY),
        .catchRate = 255,
        .expYield = 67,
        .evYield_HP = 1,
        .evYield_Defense = 1,
        .evYield_SpDefense = 1,
        .genderRatio = PERCENT_FEMALE(50),
        .eggCycles = 20,
        .friendship = STANDARD_FRIENDSHIP,
        .growthRate = GROWTH_MEDIUM_FAST,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_NO_EGGS_DISCOVERED),
        .abilities = { ABILITY_NONE, ABILITY_CURSED_BODY, ABILITY_DAMP },
        .bodyColor = BODY_COLOR_BLACK,
        .speciesName = _("??????????"),
        .cryId = CRY_NONE,
        .natDexNum = NATIONAL_DEX_NONE,
        .categoryName = _("Unknown"),
        .height = 0,
        .weight = 0,
        .description = COMPOUND_STRING(
            "This is a newly discovered Pokémon.\n"
            "It is currently under investigation.\n"
            "No detailed information is available\n"
            "at this time."),
        .pokemonScale = 256,
        .pokemonOffset = 0,
        .trainerScale = 256,
        .trainerOffset = 0,
        .frontPic = gMonFrontPic_CircledQuestionMark,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = sAnims_None,
        //.frontAnimId = ANIM_V_SQUISH_AND_BOUNCE,
        .backPic = gMonBackPic_CircledQuestionMark,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 7,
#if P_GENDER_DIFFERENCES
        .frontPicFemale = gMonFrontPic_CircledQuestionMark,
        .frontPicSizeFemale = MON_COORDS_SIZE(64, 64),
        .backPicFemale = gMonBackPic_CircledQuestionMarkF,
        .backPicSizeFemale = MON_COORDS_SIZE(64, 64),
        .paletteFemale = gMonPalette_CircledQuestionMarkF,
        .shinyPaletteFemale = gMonShinyPalette_CircledQuestionMarkF,
        .iconSpriteFemale = gMonIcon_QuestionMarkF,
        .iconPalIndexFemale = 1,
#endif //P_GENDER_DIFFERENCES
        .backAnimId = BACK_ANIM_NONE,
        .palette = gMonPalette_CircledQuestionMark,
        .shinyPalette = gMonShinyPalette_CircledQuestionMark,
        .iconSprite = gMonIcon_QuestionMark,
        .iconPalIndex = 0,
        FOOTPRINT(QuestionMark)
        .levelUpLearnset = sNoneLevelUpLearnset,
        .teachableLearnset = sNoneTeachableLearnset,
        .evolutions = EVOLUTION({EVO_LEVEL, 100, SPECIES_NONE},
                                {EVO_ITEM, ITEM_MOOMOO_MILK, SPECIES_NONE}),
        //.formSpeciesIdTable = sNoneFormSpeciesIdTable,
        //.formChangeTable = sNoneFormChangeTable,
        //.perfectIVCount = NUM_STATS,
    },
    */
};

const struct EggData gEggDatas[EGG_ID_COUNT] =
{
#include "egg_data.h"
};
