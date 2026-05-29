#!/usr/bin/python
#do not put spaces between the variable and the value!
#e.g. SPECIES=CYuria, not SPECIES = "CYuria" (the quotes are not needed)
species="Lea"
images="leamon/lea"
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
"A friendly matriarch.",
"",
"",
""]

pokedexCategory="Deer"
pokedexHeight=16 #in meters/10
pokedexWeight=580 #in kilos/10
pokemonScale=256
pokemonOffset=0
trainerScale=256
trainerOffset=0


baseHP=100
baseAttack=60
baseDefense=80
baseSpAttack=55
baseSpDefense=70
baseSpeed=75
type1="TYPE_NORMAL"
type2="TYPE_NORMAL"
catchRate=150
expYield=108
evHP=2
evAttack=0
evDefense=0 
evSpeed=0
evSpAttack=0
evSpDefense=0
item1="ITEM_NONE"
item2="ITEM_NONE"
genderRatio="PERCENT_FEMALE(50)"
eggCycles=20
friendship=70
growthRate="GROWTH_MEDIUM_SLOW"
eggGroup1="EGG_GROUP_HUMAN_LIKE"
eggGroup2="EGG_GROUP_HUMAN_LIKE"
ability1="ABILITY_NEST_DEFENDER"
ability2="ABILITY_NONE"
ability3="ABILITY_NONE"
bodyColor="BODY_COLOR_BROWN"
noFlip="FALSE"

#dark allure level 30?
learnset="""
static const struct LevelUpMove s""" + species + """LevelUpLearnset[] = {
    LEVEL_UP_MOVE( 1, MOVE_TACKLE),
    LEVEL_UP_MOVE( 1, MOVE_CHARM),
    LEVEL_UP_MOVE( 1, MOVE_BIDE),
    LEVEL_UP_MOVE( 1, MOVE_ENDURE),
    LEVEL_UP_MOVE( 8, MOVE_SWEET_KISS),
    LEVEL_UP_MOVE(12, MOVE_STOMP),
    LEVEL_UP_MOVE(16, MOVE_FALSE_SWIPE),
    LEVEL_UP_MOVE(21, MOVE_FLAIL),
    LEVEL_UP_MOVE(24, MOVE_WORK_UP),
    LEVEL_UP_MOVE(29, MOVE_NATURAL_GIFT),
    LEVEL_UP_MOVE(34, MOVE_RETURN),
    LEVEL_UP_MOVE(37, MOVE_ENTRAINMENT),
    LEVEL_UP_MOVE(42, MOVE_SWIFT),
    LEVEL_UP_MOVE(48, MOVE_PLAY_ROUGH),
    LEVEL_UP_END
};"""



import newmon
newmon.main(species, images, animate, frontSpriteSize, frontYOffset, backSpriteSize, backYOffset, frontAnim, backAnim,iconPalette, pokedexText, pokedexCategory, pokedexHeight, pokedexWeight, pokemonScale, pokemonOffset, trainerScale, trainerOffset, baseHP, baseAttack, baseDefense, baseSpAttack, baseSpDefense, baseSpeed, type1, type2, catchRate, expYield, evHP, evAttack, evDefense, evSpeed, evSpAttack, evSpDefense, item1, item2, genderRatio, eggCycles, friendship, growthRate, eggGroup1, eggGroup2, ability1, ability2, ability3, bodyColor, noFlip, learnset)
