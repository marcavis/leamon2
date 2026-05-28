#!/usr/bin/python
#do not put spaces between the variable and the value!
#e.g. SPECIES=CYuria, not SPECIES = "CYuria" (the quotes are not needed)
species="CGemma"
images="leamon/cgemma"
animate=[(0,1)] #must be a list of tuples, like [(0,10),(1,20)]
frontSpriteSize = (64,64)
frontYOffset = 0
backSpriteSize = (64,64)
backYOffset = 0
frontAnim = "ANIM_V_SQUISH_AND_BOUNCE"
backAnim = "BACK_ANIM_H_VIBRATE"
iconPalette = 0 #0, 1 or 2
#don't put newlines in here
pokedexText = [
"Has trouble showing expressions.",
"",
"",
""]

pokedexCategory="Crystal Fox"
pokedexHeight=15 #in meters/10
pokedexWeight=800 #in kilos/10
pokemonScale=256
pokemonOffset=0
trainerScale=256
trainerOffset=0


baseHP=50
baseAttack=70
baseDefense=90
baseSpAttack=50
baseSpDefense=60
baseSpeed=50
type1="TYPE_ROCK"
type2="TYPE_ROCK"
catchRate=150
expYield=70
evHP=0
evAttack=0
evDefense=1
evSpeed=0
evSpAttack=0
evSpDefense=0
item1="ITEM_NONE"
item2="ITEM_NONE"
genderRatio="PERCENT_FEMALE(25)"
eggCycles=20
friendship=30
growthRate="GROWTH_MEDIUM_SLOW"
eggGroup1="EGG_GROUP_HUMAN_LIKE"
eggGroup2="EGG_GROUP_HUMAN_LIKE"
ability1="ABILITY_AMULET_LINK"
ability2="ABILITY_NONE"
ability3="ABILITY_NONE"
bodyColor="BODY_COLOR_GREEN"
noFlip="FALSE"

#dark allure level 30?
#tweak her moveset
learnset="""
static const struct LevelUpMove s""" + species + """LevelUpLearnset[] = {
    LEVEL_UP_MOVE( 1, MOVE_TACKLE),
    LEVEL_UP_MOVE( 1, MOVE_STONE_EDGE),
    LEVEL_UP_MOVE( 5, MOVE_RECOVER),
    LEVEL_UP_MOVE( 6, MOVE_DAZZLING_GLEAM),
    LEVEL_UP_END
};"""



import newmon
newmon.main(species, images, animate, frontSpriteSize, frontYOffset, backSpriteSize, backYOffset, frontAnim, backAnim,iconPalette, pokedexText, pokedexCategory, pokedexHeight, pokedexWeight, pokemonScale, pokemonOffset, trainerScale, trainerOffset, baseHP, baseAttack, baseDefense, baseSpAttack, baseSpDefense, baseSpeed, type1, type2, catchRate, expYield, evHP, evAttack, evDefense, evSpeed, evSpAttack, evSpDefense, item1, item2, genderRatio, eggCycles, friendship, growthRate, eggGroup1, eggGroup2, ability1, ability2, ability3, bodyColor, noFlip, learnset)
