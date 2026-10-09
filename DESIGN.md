# Not-So-Vanilla Mobs: mob design

Twenty-five new mobs for Minecraft 26.3 (Fabric). Works alongside Village Friends 2.24 and its RPG add-on.

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
| 16 | Scarecrow | hostile (humanoid) | Plains, Sunflower Plains, Meadow | 1.2 |
| 17 | Sculkbones | skeleton variant | Deep Dark | 1.2 |
| 18 | Vulture | hostile (flying) | Desert, Badlands, Savanna | 1.2 |
| 19 | Dripfang | hostile | Dripstone Caves | 1.2 |
| 20 | Angler | hostile (swimming) | deep oceans | 1.2 |
| 21 | Driftcap | hostile (floating) | Warped Forest (Nether) | 1.2 |
| 22 | Meerkat | friendly | Desert, Savanna, Badlands | 1.2 |
| 23 | Penguin | friendly | Snowy Beach, frozen oceans, Frozen River | 1.2 |
| 24 | Wild Boar | neutral | taigas, Forest, Dark Forest | 1.2 |
| 25 | Otter | pet | River, Frozen River | 1.2 |

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

### 16. Scarecrow
A field scarecrow come to life: a stuffed burlap-sack head with button eyes that glow ember-orange
(emissive) and a stitched grin, a battered straw hat, a patched plaid shirt, rope belt, and straw
bursting from the collar, cuffs and hems.
- By night it walks and fights like a zombie (it goes after villagers too). Hits blind you for a
  moment (a face full of straw).
- By day, under the open sky, it can't move at all: it freezes in a scarecrow T-pose, arms out, and
  won't fight back. That's the time to deal with it. It doesn't burn in sunlight.
- Straw burns: fire hurts it twice as much.
- Never calls for reinforcements, never a baby, never converts in water. 18 health.
- Drops: wheat 0–3, stick 0–2, hay bale (5%, killed by a player).

### 17. Sculkbones (skeleton)
A skeleton swallowed by the sculk in the Deep Dark: cold dark bones under creeping sculk, eye
sockets crusted shut, glowing cyan sculk veins and two twitching sensor tendrils on its skull.
- Blind: it hunts by sound. Walking, running and jumping within 16 blocks give you away; sneaking or
  standing still doesn't. It loses you a few seconds after the footsteps stop.
- Bow archer. Its arrows mark you (Glowing 6 s), and while you're marked it hears you even sneaking.
- 24 health. Burns in daylight (not that the Deep Dark has any).
- Drops: bone 0–2, arrow 0–2, sculk (15%), echo shard (2%, killed by a player).

### 18. Vulture
A big scruffy vulture: sooty brown wings with fingered tips, a bald wrinkled red head on a bare neck,
a cream feather ruff and a hooked beak. Wingspan nearly three blocks.
- Soars in wide slow circles 14–22 blocks over open desert, badlands and savanna, in daylight too.
- Scavenger: it leaves healthy players alone. A player at half health or less draws every vulture
  around: they circle overhead, then swoop to peck (3 damage) and climb away again. Heal back above
  70% and they lose interest (unless you hit one).
- 16 health. Never takes fall damage.
- Drops: feather 0–2, bone 0–1.

### 19. Dripfang
A Dripstone Caves predator that mimics pointed dripstone: a many-legged crawler armoured in
dripstone plates, with a dripstone tail spike, calcite legs, hooked fangs and dim amber eyes.
- Hangs from the ceiling disguised as a stalactite (two tiny amber eyes are the only tell). Natural
  spawns go straight up to the nearest ceiling.
- When a player walks underneath (within about a block sideways, up to 12 blocks down) it drops on
  them point-first: 6 damage, like falling dripstone. Hitting it also knocks it down.
- Then it fights on the ground: bites for 4, leaps. 18 health, 4 armour.
- Left alone for 15 seconds under a ceiling, it springs back up and hangs again.
- Never takes fall damage.
- Drops: pointed dripstone 0–2, flint 0–1.

### 20. Angler
A deep-sea anglerfish: a lumpy charcoal body, a huge underbite of needle teeth, milky eyes, ragged
fins and a glowing lure dangling from a stalk over its mouth (emissive).
- Lives in deep, dark ocean water (12+ blocks down) in the deep ocean biomes.
- Snaps up cod, salmon and other fish that come near its lure (and heals from them).
- Rushes swimmers and bites hard (6 damage). It only hunts players who are in the water.
- A fish: out of water it flops about and suffocates. 20 health.
- Drops: cod 0–2, glow ink sac (30%, killed by a player), prismarine crystals (10%).

### 21. Driftcap
A floating jellyfish of warped fungus from the Warped Forest: a teal domed cap with glowing spots,
a purple frilled skirt, a faintly glowing core and six trailing twisting-vine tendrils.
- Drifts slowly 1–3 blocks above the ground and toward anyone nearby.
- Its tendrils sting (3 damage, Nausea 4 s) and the sting warps you up to 8 blocks away, like
  chorus fruit.
- Hit it and it may warp away itself. Fire-immune, never takes fall damage. 14 health.
- About as common as the Warped Forest's endermen.
- Drops: twisting vines 0–2, warped fungus 0–1, ender pearl (8%, killed by a player).

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

### 22. Meerkat
A slim sandy meerkat with dark "sunglasses" eye patches, a pale belly and a dark-tipped tail.
- Lives in groups of 3–5 in Desert, Savanna and Badlands.
- Lookout: now and then one stands bolt upright on its hind legs to keep watch. If it spots a
  monster within 16 blocks (a Dune Scorpion buried in the sand included) it chirps the alarm, the
  monster glows for 6 s, and the rest of the group sits up to look.
- Scorpion hunters: immune to poison, and when two or more grown-ups are together they gang up on
  Dune Scorpions.
- Breeds with spider eyes. 10 health.
- Drops: nothing.

### 23. Penguin
A chunky penguin in king-penguin colours: blue-black back, white belly, golden ear patches, a long
beak with an orange stripe. Chicks are fluffy and grey with a white face.
- Waddles about in colonies of 3–6 on snowy beaches, frozen oceans and frozen rivers.
- Belly slide: on ice and snow it flops onto its belly and toboggans along, much faster than it
  walks.
- A fast swimmer that holds its breath for two minutes. Keeps clear of polar bears.
- Breeds with raw cod or salmon. 10 health. Immune to freezing.
- Drops: feather 0–1.

### 24. Wild Boar
A bristly dark boar with a crest of stiff bristles down its spine, a flat nose disc and two curved
ivory tusks. Piglets are striped cream and brown.
- Roams taigas, forests and dark forests in sounders of 2–4.
- Neutral: it leaves you alone until you hurt it or one of its piglets. Then the whole sounder
  charges, head down: 4 damage and a knockback that tosses you up and back.
- Breeds with mushrooms (red or brown). 20 health.
- Drops: raw porkchop 1–3, leather 0–1.

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

### 25. Otter
A sleek dark-brown river otter with a cream face and chest, whiskers, webbed paws and a thick tail.
- Lives along rivers (frozen ones too) in ones and twos.
- Tame with raw cod or salmon (1 in 3). Heals and breeds with them.
- Tamed: follows its owner and sits when told (use with an empty hand).
- Swims like a fish and holds its breath for two minutes. With nothing to do in the water it rolls
  onto its back and floats, paws up.
- Swim buddy: while its owner swims near it, the owner gets Dolphin's Grace.
- Fisher: every few minutes in the water it dives and brings something up: mostly cod and salmon,
  sometimes an ink sac, kelp or a lily pad, and very rarely a nautilus shell.
- Hunts the fish it swims among. 12 health.

## Compatibility

- Same Minecraft (26.3), Fabric Loader (0.19.5) and Fabric API (0.161.0+26.3) as Village Friends.
- No mixins into vanilla or Village Friends. Hostile mobs are ordinary `Monster`s, so Village
  Friends guards and pets treat them like any other monster.
- RPG add-on (`villagefriends_rpg`): an optional mixin, applied only when the add-on is installed,
  makes its Bestiary count Sporeling, Frostbitten and Lost Miner as Zombies, Briarbones,
  Gravewarden, Soulpyre and Sculkbones as Skeletons, Dune Scorpion and Dripfang as Spiders, Angler
  as a Guardian and Driftcap as an Enderman. Everything else earns normal kill XP.

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
| scarecrow | zombie humanoid names (4-wide limbs); hat brim and straw tufts are children of them. By day the code puts the arms straight out (zRot ±π/2) |
| sculkbones | skeleton humanoid names (slim limbs) plus `right_tendril` / `left_tendril` (children of `head`) |
| vulture | `body`, `neck` (child of body) with `head`, `right_wing` / `left_wing` (children of body, rest pose spread for gliding) each with `right_wing_tip` / `left_wing_tip`, `tail`, `right_leg` / `left_leg`, optional `ruff` |
| dripfang | `body` with `head` (`right_fang` / `left_fang`), `tail`, legs `right_leg1..3` / `left_leg1..3`; `stalactite` (child of root: the hanging disguise, shown only while hanging, when `body` is hidden) |
| angler | `body` with `jaw`, `lure_stalk` (with `lure`), `tail` (with `tail_fin`), `right_fin` / `left_fin`, optional `top_fin` |
| driftcap | `cap` (the bell; the code squashes it to pulse) with `tendril1`..`tendril6` |
| meerkat | `body` (pivot at the hips) with `head`, `right_front_leg` / `left_front_leg` and `tail`; `right_hind_leg` / `left_hind_leg` (children of root). On watch the code turns `body` straight up |
| penguin | `body` (pivot at its base) with `head`, `right_flipper` / `left_flipper`; `right_foot` / `left_foot` (children of root). The code tips `body` forward to slide or swim |
| wild_boar | `body` with `mane` and `tail`, `head` (child of root), `right_front_leg`, `left_front_leg`, `right_hind_leg`, `left_hind_leg` |
| otter | `body` (pivot at the centre) with `head`, `tail` (with `tail_tip`) and all four legs, so the code can roll it onto its back |

Hitboxes (blocks, width x height): zombies 0.6x1.95, briarbones 0.6x1.99, gravewarden 0.7x2.3
(rendered at 1.15x), bog lurker 1.2x0.9, gloomwing 0.9x0.6, dune scorpion 1.3x0.7, tortoise
1.2x0.9, capybara 0.9x0.9, wyrmling 0.6x0.6, lost miner 0.6x1.95, soulpyre 0.6x1.99, glowmoth
0.7x0.6, hermit crab 0.5x0.45, hedgehog 0.45x0.4, scarecrow 0.6x1.95, sculkbones 0.6x1.99, vulture 0.9x0.7,
dripfang 0.9x0.55, angler 0.9x0.8, driftcap 0.8x1.2, meerkat 0.4x0.6, penguin 0.55x0.95, wild boar
0.9x0.9, otter 0.6x0.5.
