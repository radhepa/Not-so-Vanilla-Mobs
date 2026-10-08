# Not-So-Vanilla Mobs

Fifteen new mobs for **Minecraft 26.3** (Fabric): three zombie variants, three skeleton variants,
three new hostile creatures, four friendly animals and two pets.

| Mob | Kind | Where to find it | What it does |
|-----|------|------------------|--------------|
| **Sporeling** | zombie | Mushroom Fields, Dark Forest, Pale Garden | Hits cause Nausea and Poison. Dies in a poison spore cloud and plants mushrooms. |
| **Frostbitten** | zombie | snowy biomes | Hits cause Slowness II and freezing. Immune to cold, doesn't burn, leaves a trail of snow. |
| **Briarbones** | skeleton | jungles, Lush Caves | Poison arrows. Thorns hurt anyone who hits it up close. |
| **Gravewarden** | skeleton | Dark Forest, taigas, Pale Garden (rare) | Armoured knight with sword and shield. 30 health, 8 armour, shrugs off arrows from the front. |
| **Bog Lurker** | hostile | Swamp, Mangrove Swamp | A huge toad that sits still until you come close, then leaps. Lashes its tongue to drag you in from up to 8 blocks. |
| **Gloomwing** | hostile, flying | caves below y 40, any overworld biome | Circles, then swoops. Each bite brings the Darkness effect. |
| **Dune Scorpion** | hostile | Desert, Badlands | Hides under the sand and bursts out when you walk by. 30% of hits sting with Poison. |
| **Mossback Tortoise** | friendly | Swamp, jungles | Shear the garden on its shell for moss (it grows back). Hides in its shell when hurt. Breeds with melon slices. |
| **Capybara** | friendly | Swamp, Mangrove, Savanna, River, Sparse Jungle | Small animals hop on its back for a ride. Crouch next to it for Regeneration. Breeds with sugar cane. |
| **Wyrmling** | pet | Stony and Jagged Peaks, Windswept Hills (rare) | A tiny dragon. Tame it with blaze powder. It flies after you, sits when told and spits embers at monsters. |
| **Lost Miner** | zombie | deep caves below y 0, any overworld biome | Hard hat and glowing headlamp. Tunnels through stone to reach you. Hits cause Mining Fatigue. |
| **Soulpyre** | skeleton | Soul Sand Valley | Wreathed in blue soul fire. Immune to fire; its arrows set you alight. |
| **Glowmoth** | friendly, flying | Flower Forest, Meadow, forests, Cherry Grove | Drawn to torches and lanterns at night. Sheds glowstone dust. Breeds with flowers. |
| **Hermit Crab** | friendly | Beach, Stony Shore, Mangrove Swamp | Three shell styles. Ducks into its shell when startled. Digs up beach trinkets. Breeds with kelp. |
| **Hedgehog** | pet | forests, Meadow, Plains, Flower Forest | Tame it with sweet berries. Curls into a spiky ball when hurt, hunts silverfish and endermites, forages berries. |

All fifteen have spawn eggs in the Spawn Eggs creative tab. The full design is in [DESIGN.md](DESIGN.md).
More mobs are on the way; [ARCHITECTURE.md](ARCHITECTURE.md) explains how the mod is put together
and walks through adding one.

## The Wyrmling
- Feed a wild Wyrmling **blaze powder**; each feeding has a 1 in 4 chance to tame it.
- Use it with an empty hand to make it sit or follow.
- It attacks only monsters: ones that hurt you, and ones you attack. Its embers set mobs on fire,
  never blocks, and never hit players, villagers or your other pets.
- Feed it blaze powder to heal it, or feed two tamed Wyrmlings to breed them.

## The Hedgehog
- Feed a wild Hedgehog **sweet berries**; each feeding has a 1 in 3 chance to tame it.
- Use it with an empty hand to make it sit or follow. Feed it sweet berries to heal it or breed it.
- When hurt it curls into a ball: it takes much less damage, and anything that hits it gets
  pricked. It hunts silverfish and endermites, and helps against monsters that hurt you.
- While following you on grass it sometimes snuffles up sweet berries or a mushroom.

## Compatibility
- Same Minecraft (26.3), Fabric Loader (0.19.5) and Fabric API (0.161.0+26.3) as
  [Village Friends](https://github.com/radhepa/Village-Friends-Minecraft-Mod).
- No mixins into Minecraft or Village Friends. The hostile mobs are ordinary monsters, so Village
  Friends guards and pets fight them like any other.
- **Village Friends RPG add-on:** when it's installed, its Bestiary counts Sporelings,
  Frostbitten and Lost Miners as Zombies, Briarbones, Gravewardens and Soulpyres as Skeletons, and
  Dune Scorpions as Spiders.
  The other mobs earn normal kill XP. Without the add-on, that hook stays switched off.

## Install
Put `not-so-vanilla-mobs-1.1.0.jar` in your `mods` folder next to Fabric API. It's tested together
with Village Friends 2.25 and its RPG add-on as one modpack.

## Building
```
gradlew build                                  # jar in build/libs
gradlew runClientGameTest -PtestHeap=2g        # spawns every mob and saves screenshots
gradlew runClientGameTest -PtestHeap=2560m -PcompatMods=<mods folder>   # same, inside a modpack
```
Needs JDK 25.

## How the mobs are made
Each mob's model and pixel-art texture are written in Python (`tools/mobs/<id>.py`, using
`tools/mobkit.py`). The script outputs the model as JSON, which the game loads at startup, plus
the texture and the spawn egg. The same script holds the mob's name, loot and tags.

```
python tools/build_mobs.py                     # rebuild every model, texture and egg
python tools/preview/preview.py wyrmling --views 4
python tools/gen_data.py                       # language, egg item models, loot tables, tags
python tools/check_mobs.py                     # every mob has all its pieces
```
The previewer renders a mob with headless Edge, using Minecraft's exact cube and texture mapping,
so you can check the art without launching the game. See [ARCHITECTURE.md](ARCHITECTURE.md) for
the full picture.

## License
MIT
