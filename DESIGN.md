# Not-So-Vanilla Mobs: mob design

Fifteen new mobs for Minecraft 26.3 (Fabric). Works alongside Village Friends 2.24 and its RPG add-on.

| # | Mob | Kind | Where | Added |
|---|-----|------|-------|-------|
| 1 | Sporeling | zombie variant | Mushroom Fields, Dark Forest | 1.0 |
| 2 | Frostbitten | zombie variant | snowy biomes | 1.0 |
| 3 | Briarbones | skeleton variant | jungles, Lush Caves | 1.0 |
| 4 | Gravewarden | skeleton variant | Dark Forest, taigas | 1.0 |
| 5 | Bog Lurker | hostile | Swamp, Mangrove Swamp | 1.0 |
| 6 | Gloomwing | hostile (flying) | caves, all overworld biomes | 1.0 |
| 7 | Dune Scorpion | hostile | Desert, Badlands | 1.0 |
| 8 | Mossback Tortoise | friendly | Swamp, jungles | 1.0 |
| 9 | Capybara | friendly | Swamp, Mangrove, Savanna, River, Sparse Jungle | 1.0 |
| 10 | Wyrmling | pet | mountain peaks, Windswept Hills | 1.0 |
| 11 | Lost Miner | zombie variant | deep caves (below y 0), every overworld biome | 1.1 |
| 12 | Soulpyre | skeleton variant | Soul Sand Valley | 1.1 |
| 13 | Glowmoth | friendly (flying) | Flower Forest, Meadow, forests, Cherry Grove | 1.1 |
| 14 | Hermit Crab | friendly | Beach, Stony Shore, Mangrove Swamp | 1.1 |
| 15 | Hedgehog | pet | forests, Meadow, Plains, Flower Forest | 1.1 |

## Hostile

### 1. Sporeling (zombie)
A zombie overgrown by fungus: red mushrooms grow from its head, shoulder and back, white
mycelium creeps over grey-violet skin, eyes glow spore-teal (emissive).
- Hit: Nausea 6 s + Poison I 3 s.
- Death: bursts into a poison spore cloud (radius 2.5, 5 s) and plants up to 3 mushrooms on nearby
  ground (only if `mobGriefing`).
- Burns in daylight like a zombie. Never converts in water. Never spawns as a baby.
- Drops: rotten flesh 0–2, red or brown mushroom 0–2.

### 2. Frostbitten (zombie)
A zombie frozen solid: pale blue skin, icicles on brow, shoulders and arms, a frosted scarf, frosty
breath. Eyes glow ice-blue.
- Hit: Slowness II 4 s and 7 s of powder-snow freezing.
- Immune to freezing. Does not burn in daylight. Never converts in water. No babies.
- Leaves a trail of snow layers on cold ground (only if `mobGriefing`).
- Drops: rotten flesh 0–2, snowball 0–3, ice (10%).

### 3. Briarbones (skeleton)
A skeleton strangled by jungle growth: vines wrap the ribs and limbs, thorny briars on the
shoulders, leaves sprouting from the skull, a mossy jaw.
- Bow archer. Arrows inflict Poison I 5 s.
- Thorns: melee attackers take 1 damage.
- Burns in daylight.
- Drops: bone 0–2, arrow 0–2, vine 0–2.

### 4. Gravewarden (skeleton)
A dead knight: a skeleton in rusted iron plate (helm with a slit visor, pauldrons, breastplate,
greaves), torn dark cape. Carries an iron sword and a shield. 15% larger than a skeleton.
- Melee only. 30 health, 8 armour, slow and heavy (knockback resistant).
- Shield: arrows and other projectiles that hit it from the front are deflected.
- Does not burn in daylight: its helm shields it.
- Drops: bone 1–3, iron nugget 1–4, iron sword (5%, damaged).

### 5. Bog Lurker
A huge mossy toad that ambushes from swamp water. Wide mouth, warty olive back covered in moss
and duckweed, pale belly, amber eyes.
- Sits perfectly still (camouflaged) until a player comes within 6 blocks, then leaps.
- Tongue lash: from 3 to 8 blocks away it lashes its tongue and yanks the target toward itself
  (every 4 s).
- Bite 5 damage, 24 health. Amphibious: swims, never drowns.
- Drops: slime ball 0–2, lily pad 0–1.

### 6. Gloomwing
A cave-dwelling bat-thing the size of a dog, with tattered membrane wings and pale glowing eyes.
- Flies erratically, then swoops. Each hit deals 2 damage and Darkness 4 s.
- 10 health. Burns in sunlight (it belongs underground).
- Spawns only underground (below y 40, no sky above).
- Drops: leather 0–1, glow ink sac (25%).

### 7. Dune Scorpion
A sandy-gold scorpion as long as a person is tall: armoured plates, two big pincers, a segmented
tail with a dark stinger.
- Burrows: lies hidden under sand when it has nothing to do, and bursts out when a player comes
  within 5 blocks.
- Pincers deal 4 damage; 30% of hits also sting (Poison I 5 s).
- Does not burn. Can spawn in daylight (it's a desert animal), but rarely.
- Drops: string 0–2, spider eye 0–1.

### 11. Lost Miner (zombie)
A miner who never came back up: dusty overalls, a dented hard hat with a headlamp that still
burns (emissive), a coal-smudged face, carrying an iron pickaxe.
- Lives deep: spawns only below y 0, in any overworld biome.
- Digs: when it can't reach its target it mines through stone, deepslate, dirt, gravel and the
  like (anything soft enough to dig by hand or pickaxe; never ores, never obsidian), one block
  at a time, with a visible cracking animation. Only if `mobGriefing`.
- Hit: Mining Fatigue I for 6 s.
- Burns in daylight (it isn't meant to be up there). Never converts in water. No babies.
- Drops: rotten flesh 0–2, coal 0–2, torch 0–2, raw iron (10%, killed by a player), raw gold (3%).

### 12. Soulpyre (skeleton)
A skeleton burned black in the Soul Sand Valley, its skull and ribcage wrapped in pale blue soul
fire (emissive).
- Bow archer. Its arrows are on fire and set targets alight.
- Immune to fire and lava. Lives in the Nether, so it never meets daylight.
- Gives off drifting soul-fire particles.
- Drops: bone 0–2, arrow 0–2, soul soil (25%).

## Friendly

### 8. Mossback Tortoise
A big, slow tortoise with a little garden on its shell: moss, grass tufts, a flower or two.
- Shears: harvest the garden for moss blocks (1–2) and sometimes a flower; it regrows in about
  5 minutes.
- When hurt it pulls into its shell for 5 s and takes 70% less damage.
- 30 health, very slow. Breeds with melon slices.
- Drops: moss carpet 0–1.

### 9. Capybara
The calmest animal in the world. Round, brown, small ears, half-closed eyes.
- Small animals (chickens, rabbits, frogs, cats, foxes, parrots, baby animals) sometimes hop on its
  back and ride for a while.
- Comfort: a player crouching next to it gets Regeneration I.
- Swims well. 14 health. Breeds with sugar cane.
- Drops: leather 0–1.

### 13. Glowmoth
A moth as big as a cat: fluffy cream body, feathery antennae, soft wings with eye-spots that glow
faintly at night (emissive).
- Flutters around in forests and meadows. At night it's drawn to light: it seeks out torches,
  lanterns, glowstone and the like within 16 blocks and circles them.
- Every 5–10 minutes it sheds a little glowstone dust.
- Breeds with any flower. 6 health. Never takes fall damage.
- Drops: nothing (it's too gentle).

### 14. Hermit Crab
A small crab living in a borrowed shell. Three shells: a pink conch, a sandy spiral whelk and a
weathered blue snail shell.
- Ducks into its shell when hurt, or when a player sprints within 4 blocks, and takes 80% less
  damage while hidden.
- Treasure hunter: every few minutes on sand it digs and turns up a beach trinket (clay ball,
  bone meal, gold nugget, prismarine shard, sea pickle, and very rarely a nautilus shell).
- Breeds with kelp. Babies get a random shell. 8 health.
- Drops: nothing on death.

## Pet

### 10. Wyrmling
A tiny dragon the size of a cat, with membrane wings, little horns and a spiked tail. Comes in
ember red.
- Wild ones live high up on mountain peaks and windswept hills (rare).
- Tame with blaze powder (1 in 4). Heals and breeds with blaze powder.
- Tamed: flies after its owner, sits when told (use with an empty hand), and spits embers at
  monsters that hurt its owner or that its owner attacks. Embers burn but never set blocks alight.
- Fire immune. 20 health.

### 15. Hedgehog
A palm-sized hedgehog: brown-and-cream quills, a pale face, a black button nose, tiny feet.
- Tame with sweet berries (1 in 3). Heals and breeds with sweet berries.
- Tamed: follows its owner and sits when told (use with an empty hand).
- Curls into a spiky ball when hurt: 60% less damage for 5 s, and anything that hits it in melee
  takes 2 damage.
- Bug hunter: hunts silverfish and endermites, and helps against monsters that hurt its owner.
- Forager: while following you on grass it sometimes snuffles up sweet berries or a mushroom.
- 10 health.

## Compatibility

- Same Minecraft (26.3), Fabric Loader (0.19.5) and Fabric API (0.161.0+26.3) as Village Friends.
- No mixins into vanilla or Village Friends. Hostile mobs are ordinary `Monster`s, so Village
  Friends guards and pets treat them like any other monster.
- RPG add-on (`villagefriends_rpg`): an optional mixin, applied only when the add-on is installed,
  makes its Bestiary count Sporeling, Frostbitten and Lost Miner as Zombies, Briarbones,
  Gravewarden and Soulpyre as Skeletons, and Dune Scorpion as a Spider. Everything else earns
  normal kill XP.

## Model contracts (art <-> code)

Models are authored in `tools/mobs/<id>.py` with `tools/mobkit.py` (see ARCHITECTURE.md). Feet rest at model y = 24.
The Java animation code drives these part names:

| Mob | Required parts |
|-----|----------------|
| sporeling, frostbitten | `head`, `hat` (child of head), `body`, `right_arm`, `left_arm`, `right_leg`, `left_leg` (vanilla humanoid, 4-wide limbs); decorations are children |
| briarbones, gravewarden | same names, skeleton 2x12x2 limbs (`humanoid(..., slim_limbs=True)`) |
| bog_lurker | `body`, `head` (child of root), `jaw` and `tongue` (children of head; tongue is a cube pointing -z, the code stretches it), `right_front_leg`, `left_front_leg`, `right_hind_leg`, `left_hind_leg` |
| gloomwing | `body`, `head` (child of body), `right_wing`, `left_wing` (children of body) each with a child `right_wing_tip` / `left_wing_tip`, `feet` (child of body) |
| dune_scorpion | `body`, `head` (child of body), `tail1`..`tail4` (chain, tail1 child of body, tail4 has the stinger), `right_claw`, `left_claw` (children of body) each with child `right_pincer` / `left_pincer`, legs `right_leg1..3`, `left_leg1..3` (children of body) |
| mossback_tortoise | `body`, `garden` (child of body: every moss/plant cube, hidden when sheared), `head` (child of root), `right_front_leg`, `left_front_leg`, `right_hind_leg`, `left_hind_leg`, optional `tail` |
| capybara | `body`, `head` (child of root), `right_front_leg`, `left_front_leg`, `right_hind_leg`, `left_hind_leg`, optional `right_ear` / `left_ear` (children of head) |
| wyrmling | `body`, `neck` (child of body), `head` (child of neck), `jaw` (child of head), `right_wing` / `left_wing` (children of body) each with child `right_wing_tip` / `left_wing_tip`, `tail` (child of body) with child `tail_tip`, `right_front_leg`, `left_front_leg`, `right_hind_leg`, `left_hind_leg` (children of body) |
| lost_miner | zombie humanoid names (4-wide limbs); hard hat + lamp are children of `head` |
| soulpyre | skeleton humanoid names (slim limbs); flames are children of `head` / `body` |
| glowmoth | `body`, `head` (child of body), `right_antenna` / `left_antenna` (children of head), `right_wing` / `left_wing` (forewings) and `right_hindwing` / `left_hindwing` (children of body, flapping around z), optional `legs` (child of body) |
| hermit_crab | `shell` (child of root; always visible), `body` (child of root: everything that pulls inside the shell when hiding), under `body`: `right_claw` / `left_claw`, `right_eye` / `left_eye`, legs `right_leg1..3` / `left_leg1..3` |
| hedgehog | `body` (with `quills` child), `head` (child of root) with `snout`, `right_front_leg`, `left_front_leg`, `right_hind_leg`, `left_hind_leg`, and `ball` (child of root: the curled-up spiky ball, hidden normally; the code hides everything else when it curls) |

Hitboxes (blocks, width x height): zombies 0.6x1.95, briarbones 0.6x1.99, gravewarden 0.7x2.3
(rendered at 1.15x), bog lurker 1.2x0.9, gloomwing 0.9x0.6, dune scorpion 1.3x0.7, tortoise
1.2x0.9, capybara 0.9x0.9, wyrmling 0.6x0.6, lost miner 0.6x1.95, soulpyre 0.6x1.99, glowmoth
0.7x0.6, hermit crab 0.5x0.45, hedgehog 0.45x0.4.
