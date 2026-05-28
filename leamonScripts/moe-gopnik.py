#!/usr/bin/python
#do not put spaces between the variable and the value!
#e.g. SPECIES=CYuria, not SPECIES = "CYuria" (the quotes are not needed)
species="GMoe"
images="leamon/moe-gopnik"
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
"You've come to the wrong turf!",
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


baseHP=70
baseAttack=90
baseDefense=80
baseSpAttack=40
baseSpDefense=50
baseSpeed=70
type1="TYPE_NORMAL"
type2="TYPE_DARK"
catchRate=150
expYield=90
evHP=0
evAttack=1
evDefense=1 
evSpeed=0
evSpAttack=0
evSpDefense=0
item1="ITEM_NONE"
item2="ITEM_NONE"
genderRatio="PERCENT_FEMALE(25)"
eggCycles=20
friendship=70
growthRate="GROWTH_MEDIUM_SLOW"
eggGroup1="EGG_GROUP_HUMAN_LIKE"
eggGroup2="EGG_GROUP_HUMAN_LIKE"
ability1="ABILITY_INSOMNIA"
ability2="ABILITY_NONE"
ability3="ABILITY_NONE"
bodyColor="BODY_COLOR_BROWN"
noFlip="FALSE"

#dark allure level 30?
learnset="""
static const struct LevelUpMove s""" + species + """LevelUpLearnset[] = {
    LEVEL_UP_MOVE( 1, MOVE_TACKLE),
    LEVEL_UP_MOVE( 8, MOVE_BULLET_SEED),
    LEVEL_UP_MOVE(12, MOVE_THIEF),
    LEVEL_UP_MOVE(16, MOVE_FLING),
    LEVEL_UP_MOVE(23, MOVE_HEADBUTT),
    LEVEL_UP_MOVE(27, MOVE_SLACK_OFF),
    LEVEL_UP_END
};"""



import newmon
newmon.main(species, images, animate, frontSpriteSize, frontYOffset, backSpriteSize, backYOffset, frontAnim, backAnim,iconPalette, pokedexText, pokedexCategory, pokedexHeight, pokedexWeight, pokemonScale, pokemonOffset, trainerScale, trainerOffset, baseHP, baseAttack, baseDefense, baseSpAttack, baseSpDefense, baseSpeed, type1, type2, catchRate, expYield, evHP, evAttack, evDefense, evSpeed, evSpAttack, evSpDefense, item1, item2, genderRatio, eggCycles, friendship, growthRate, eggGroup1, eggGroup2, ability1, ability2, ability3, bodyColor, noFlip, learnset)
