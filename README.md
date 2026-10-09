# Not-So-Vanilla Mobs

Twenty-five new mobs for **Minecraft 26.3** (Fabric): three zombie variants, four skeleton variants,
eight other hostile creatures, six friendly animals, one neutral animal and three pets.

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
| **Scarecrow** | hostile | Plains, Sunflower Plains, Meadow (at night) | Walks and fights like a zombie at night; its hits blind you for a moment. By day it freezes in a scarecrow pose and can't fight back. Fire hurts it double. |
| **Sculkbones** | skeleton | Deep Dark | Blind: it hunts by sound, so sneak past. Its arrows mark you (Glowing), and then it hears you even when you sneak. |
| **Vulture** | hostile, flying | Desert, Badlands, Savanna | Soars high in circles. Ignores healthy players, but drop below half health and the vultures circle overhead and swoop to peck. |
| **Dripfang** | hostile | Dripstone Caves | Hangs from the ceiling disguised as pointed dripstone and drops on you point-first. Then bites; later springs back up to wait again. |
| **Angler** | hostile, swimming | deep oceans | Lurks in deep dark water with a glowing lure, eats passing fish and rushes swimmers with a big bite. |
| **Driftcap** | hostile, floating | Warped Forest (Nether) | A warped-fungus jellyfish. Its tendrils sting and warp you a few blocks away like chorus fruit. |
| **Meerkat** | friendly | Desert, Savanna, Badlands | Stands up to keep watch; any monster it spots (buried scorpions too) glows. Immune to poison, and a group hunts Dune Scorpions. Breeds with spider eyes. |
| **Penguin** | friendly | Snowy Beach, frozen oceans, Frozen River | Belly-slides fast over ice and snow, swims fast, keeps clear of polar bears. Fluffy grey chicks. Breeds with raw fish. |
| **Wild Boar** | neutral | taigas, Forest, Dark Forest | Leaves you alone until you hurt it or a piglet; then the whole group charges with a big knockback. Striped piglets. Breeds with mushrooms. |
| **Otter** | pet | River, Frozen River | Tame it with raw cod or salmon. Floats on its back, gives you Dolphin's Grace while you swim together, and fishes things up for you. |

All twenty-five have spawn eggs in the Spawn Eggs creative tab. The full design is in [DESIGN.md](DESIGN.md).
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

## The Otter
- Feed a wild Otter **raw cod or salmon**; each feeding has a 1 in 3 chance to tame it.
- Use it with an empty hand to make it sit or follow. Feed it fish to heal it or breed it.
- Swim near it and you get Dolphin's Grace. With nothing to do in the water it floats on its back.
- Every few minutes in the water it dives and brings something up for you: usually a fish, sometimes
  ink, kelp or a lily pad, and very rarely a nautilus shell.

## Compatibility
- Same Minecraft (26.3), Fabric Loader (0.19.5) and Fabric API (0.161.0+26.3) as
  [Village Friends](https://github.com/radhepa/Village-Friends-Minecraft-Mod).
- No mixins into Minecraft or Village Friends. The hostile mobs are ordinary monsters, so Village
  Friends guards and pets fight them like any other.
- **Village Friends RPG add-on:** when it's installed, its Bestiary counts Sporelings,
  Frostbitten and Lost Miners as Zombies, Briarbones, Gravewardens, Soulpyres and Sculkbones as
  Skeletons, Dune Scorpions and Dripfangs as Spiders, Anglers as Guardians and Driftcaps as
  Endermen.
  The other mobs earn normal kill XP. Without the add-on, that hook stays switched off.

## Install
Put `not-so-vanilla-mobs-1.2.0.jar` in your `mods` folder next to Fabric API. It's tested together
with Village Friends 2.26 and its RPG add-on as one modpack.

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
