#!/usr/bin/python
#do not put spaces between the variable and the value!
#e.g. SPECIES=CYuria, not SPECIES = "CYuria" (the quotes are not needed)
species="WMoe"
images="leamon/moe-waiter"
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
"What's your order today?",
"",
"",
""]

pokedexCategory="Deer"
pokedexHeight=15 #in meters/10
pokedexWeight=450 #in kilos/10
pokemonScale=256
pokemonOffset=0
trainerScale=256
trainerOffset=0


baseHP=60
baseAttack=55
baseDefense=65
baseSpAttack=75
baseSpDefense=65
baseSpeed=80
type1="TYPE_NORMAL"
type2="TYPE_WATER"
catchRate=150
expYield=90
evHP=0
evAttack=0
evDefense=0 
evSpeed=1
evSpAttack=1
evSpDefense=0
item1="ITEM_NONE"
item2="ITEM_NONE"
genderRatio="PERCENT_FEMALE(25)"
eggCycles=20
friendship=70
growthRate="GROWTH_MEDIUM_SLOW"
eggGroup1="EGG_GROUP_HUMAN_LIKE"
eggGroup2="EGG_GROUP_HUMAN_LIKE"
ability1="ABILITY_OVERTIME"
ability2="ABILITY_NONE"
ability3="ABILITY_NONE"
bodyColor="BODY_COLOR_BROWN"
noFlip="FALSE"

#TODO: needs more moves
learnset="""
static const struct LevelUpMove s""" + species + """LevelUpLearnset[] = {
    LEVEL_UP_MOVE( 1, MOVE_TACKLE),
    LEVEL_UP_MOVE( 1, MOVE_GROWL),
    LEVEL_UP_MOVE( 5, MOVE_BUBBLE),
    LEVEL_UP_MOVE( 9, MOVE_BESTOW),
    LEVEL_UP_MOVE(12, MOVE_MILK_DRINK),
    LEVEL_UP_MOVE(16, MOVE_AGILITY),
    LEVEL_UP_MOVE(25, MOVE_FLING),
    LEVEL_UP_MOVE(29, MOVE_SCALD),
    LEVEL_UP_MOVE(36, MOVE_GRASSY_GLIDE),
    LEVEL_UP_END
};"""

import newmon
newmon.main(species, images, animate, frontSpriteSize, frontYOffset, backSpriteSize, backYOffset, frontAnim, backAnim,iconPalette, pokedexText, pokedexCategory, pokedexHeight, pokedexWeight, pokemonScale, pokemonOffset, trainerScale, trainerOffset, baseHP, baseAttack, baseDefense, baseSpAttack, baseSpDefense, baseSpeed, type1, type2, catchRate, expYield, evHP, evAttack, evDefense, evSpeed, evSpAttack, evSpDefense, item1, item2, genderRatio, eggCycles, friendship, growthRate, eggGroup1, eggGroup2, ability1, ability2, ability3, bodyColor, noFlip, learnset)
