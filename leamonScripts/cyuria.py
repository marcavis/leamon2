#!/usr/bin/python
#do not put spaces between the variable and the value!
#e.g. SPECIES=CYuria, not SPECIES = "CYuria" (the quotes are not needed)
species="CYuria"
images="leamon/cyuria"
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
"Always looking to score.",
"",
"",
""]

pokedexCategory="Fox-deer"
pokedexHeight=15 #in meters/10
pokedexWeight=410 #in kilos/10
pokemonScale=256
pokemonOffset=0
trainerScale=256
trainerOffset=0


baseHP=40
baseAttack=70
baseDefense=30
baseSpAttack=25
baseSpDefense=40
baseSpeed=85
type1="TYPE_DARK"
type2="TYPE_DARK"
catchRate=150
expYield=70
evHP=0
evAttack=0
evDefense=0 
evSpeed=1
evSpAttack=0
evSpDefense=0
item1="ITEM_NONE"
item2="ITEM_NONE"
genderRatio="PERCENT_FEMALE(50)"
eggCycles=20
friendship=100
growthRate="GROWTH_MEDIUM_SLOW"
eggGroup1="EGG_GROUP_HUMAN_LIKE"
eggGroup2="EGG_GROUP_HUMAN_LIKE"
ability1="ABILITY_GLAD_HANDING"
ability2="ABILITY_NONE"
ability3="ABILITY_NONE"
bodyColor="BODY_COLOR_BROWN"
noFlip="FALSE"

#dark allure level 30?
learnset="""
static const struct LevelUpMove s""" + species + """LevelUpLearnset[] = {
    LEVEL_UP_MOVE( 1, MOVE_SCRATCH),
    LEVEL_UP_MOVE( 1, MOVE_LEER),
    LEVEL_UP_MOVE( 6, MOVE_QUICK_ATTACK),
    LEVEL_UP_MOVE(12, MOVE_BITE),
    LEVEL_UP_MOVE(16, MOVE_CHARM),
    LEVEL_UP_MOVE(18, MOVE_PURSUIT),
    LEVEL_UP_MOVE(23, MOVE_SWAGGER),
    LEVEL_UP_MOVE(26, MOVE_HEART_STAMP),
    LEVEL_UP_MOVE(29, MOVE_FACADE),
    LEVEL_UP_MOVE(33, MOVE_U_TURN),
    LEVEL_UP_MOVE(37, MOVE_CONFIDE),
    LEVEL_UP_MOVE(40, MOVE_RETALIATE),
    LEVEL_UP_MOVE(44, MOVE_SUCKER_PUNCH),
    LEVEL_UP_MOVE(49, MOVE_NIGHT_SLASH),
    LEVEL_UP_MOVE(56, MOVE_FAKE_TEARS),
    LEVEL_UP_END
};"""



import newmon
newmon.main(species, images, animate, frontSpriteSize, frontYOffset, backSpriteSize, backYOffset, frontAnim, backAnim,iconPalette, pokedexText, pokedexCategory, pokedexHeight, pokedexWeight, pokemonScale, pokemonOffset, trainerScale, trainerOffset, baseHP, baseAttack, baseDefense, baseSpAttack, baseSpDefense, baseSpeed, type1, type2, catchRate, expYield, evHP, evAttack, evDefense, evSpeed, evSpAttack, evSpDefense, item1, item2, genderRatio, eggCycles, friendship, growthRate, eggGroup1, eggGroup2, ability1, ability2, ability3, bodyColor, noFlip, learnset)
