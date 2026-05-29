#!/usr/bin/python
#do not put spaces between the variable and the value!
#e.g. SPECIES=CYuria, not SPECIES = "CYuria" (the quotes are not needed)
species="Sayo"
images="leamon/sayo"
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
"Vengeance in humanoid form.",
"",
"",
""]

pokedexCategory="Nogitsune"
pokedexHeight=24 #in meters/10
pokedexWeight=3352 #in kilos/10
pokemonScale=256
pokemonOffset=0
trainerScale=256
trainerOffset=0


baseHP=140
baseAttack=100
baseDefense=80
baseSpAttack=160
baseSpDefense=140
baseSpeed=60
type1="TYPE_DARK"
type2="TYPE_GHOST"
catchRate=10
expYield=345
evHP=0
evAttack=0
evDefense=0 
evSpeed=0
evSpAttack=2
evSpDefense=1
item1="ITEM_NONE"
item2="ITEM_NONE"
genderRatio="PERCENT_FEMALE(50)"
eggCycles=20
friendship=0
growthRate="GROWTH_SLOW"
eggGroup1="EGG_GROUP_HUMAN_LIKE"
eggGroup2="EGG_GROUP_HUMAN_LIKE"
ability1="ABILITY_OPPRESSION_AURA"
ability2="ABILITY_NONE"
ability3="ABILITY_NONE"
bodyColor="BODY_COLOR_BLACK"
noFlip="FALSE"

#dark allure level 30?
learnset="""
static const struct LevelUpMove s""" + species + """LevelUpLearnset[] = {
    LEVEL_UP_MOVE( 1, MOVE_DOUBLE_SLAP),
    LEVEL_UP_MOVE( 1, MOVE_TAIL_WHIP),
    LEVEL_UP_MOVE( 1, MOVE_ASTONISH),
    LEVEL_UP_MOVE( 6, MOVE_DISABLE),
    LEVEL_UP_MOVE(10, MOVE_ENCORE),
    LEVEL_UP_MOVE(14, MOVE_STOMP),
    LEVEL_UP_MOVE(19, MOVE_SNARL),
    LEVEL_UP_MOVE(26, MOVE_BODY_SLAM),
    LEVEL_UP_MOVE(30, MOVE_TAUNT),
    LEVEL_UP_MOVE(35, MOVE_HEX),
    LEVEL_UP_MOVE(46, MOVE_OUTRAGE),
    LEVEL_UP_MOVE(52, MOVE_ATTACK_ORDER),
    LEVEL_UP_MOVE(60, MOVE_VOID_FLAME),
    LEVEL_UP_END
};"""



import newmon
newmon.main(species, images, animate, frontSpriteSize, frontYOffset, backSpriteSize, backYOffset, frontAnim, backAnim,iconPalette, pokedexText, pokedexCategory, pokedexHeight, pokedexWeight, pokemonScale, pokemonOffset, trainerScale, trainerOffset, baseHP, baseAttack, baseDefense, baseSpAttack, baseSpDefense, baseSpeed, type1, type2, catchRate, expYield, evHP, evAttack, evDefense, evSpeed, evSpAttack, evSpDefense, item1, item2, genderRatio, eggCycles, friendship, growthRate, eggGroup1, eggGroup2, ability1, ability2, ability3, bodyColor, noFlip, learnset)
