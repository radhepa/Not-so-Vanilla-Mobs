# Not-So-Vanilla Mobs: mob design

Thirty-five new mobs for Minecraft 26.3 (Fabric). Works alongside Village Friends 2.26 and its RPG add-on.

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
| 26 | Broodmother | challenger | deep caves (below y 0), Dark Forest | 1.3 |
| 27 | Sandmaw | challenger (burrowing) | Desert | 1.3 |
| 28 | Cinderhulk | challenger | Basalt Deltas (Nether) | 1.3 |
| 29 | Crag Troll | challenger | Windswept Hills, Stony and Jagged Peaks | 1.3 |
| 30 | Prowler | challenger | jungles | 1.3 |
| 31 | Stormcaller | challenger (illager) | taigas, Dark Forest, Windswept Hills | 1.3 |
| 32 | Brineclaw | challenger | Beach, Stony Shore | 1.3 |
| 33 | Rimewraith | challenger (floating) | Frozen and Jagged Peaks, Snowy Slopes, Ice Spikes, Grove | 1.3 |
| 34 | Riftstalker | challenger | the outer End islands | 1.3 |
| 35 | Oregorger | challenger | deep caves (below y 0) | 1.3 |

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

## Challengers

Big, rare, dangerous monsters, one per corner of the world. Each has a signature attack that
announces itself (a sound, a pose, particles) and a way to beat it that a player can learn, the
way a creeper's hiss or a shield against a skeleton works. They spawn alone, never within 64 blocks
of another of their kind, give 15 to 30 XP and drop more than ordinary monsters.

### 26. Broodmother
A spider queen twice a spider's size: a bloated, mottled plum-black abdomen with a bone-white
marking and a clutch of pale egg sacs on her back, a hairy body, eight long banded legs with high
knees, big fangs and eight glowing red eyes.
- Climbs walls like a spider. Bite 7 with Poison (8 s; Poison II on Hard). 60 health, 4 armour.
- Web spit: from 4 to 16 blocks she rears up (a hiss and her front legs in the air) and spits a web.
  It sticks you in a cobweb where you stand for 8 seconds (then the web melts away); with
  mobGriefing off it only slows you.
- Brood: at two-thirds and one-third health three cave spiders spill off her back.
- Counter: fight her in the open, where her webs have nothing to stick to and you can see her
  rear up; keep a sword or shears ready for webs; hold some of your damage for the broods.
- Lives below y 0 in every overworld biome, and on the dark floor of Dark Forests. Rare.
- Drops: string 2-5, spider eye 1-2, cobweb 0-2, fermented spider eye (25%, killed by a player).

### 27. Sandmaw
A colossal desert worm. Only its front ever leaves the ground: a sandy, segmented column three
blocks high with sandstone plates down its back and a blunt beak of four jaws around rings of
teeth.
- Burrowed, it swims under loose ground (sand, red sand, dirt, grass, gravel, clay, snow blocks) at
  6 blocks a second, faster than you can sprint, trailing trembling sand. Nothing can hurt it down
  there. It feels footsteps: it notices a sneaking player only within 4 blocks.
- Under its prey the ground shakes for most of a second, then it bursts out: 9 damage and a toss
  into the air to everything within a block and a half.
- Surfaced for about five seconds, it rears and bites anything within 3.6 blocks (8 damage), then
  dives again and comes back for another pass. 70 health, 6 armour.
- Counter: when the sand shakes under you, move. It can't follow you onto hard ground (sandstone,
  stone, planks, any block you place) and gives up after ten seconds of that; fight it in the
  window after it surfaces.
- Lives in Deserts, mostly by night (by day, much more rarely). Rare.
- Drops: bone 1-3, gold nugget 2-6, diamond (6%, killed by a player).

### 28. Cinderhulk
A hulking gorilla-shaped brute of basalt from the Basalt Deltas: huge shoulders and arms on short
legs, blackstone fists with gold flecks, a ridge of basalt spikes, molten cracks glowing through its
chest, arms and back, and ember eyes.
- Punch 11 and sets you alight. 90 health, 10 armour, can't be knocked back. Walks across lava like
  a strider; immune to fire.
- Ground slam (within 7 blocks): it roars and raises both fists for a second, then slams the
  ground. A ring of fire races outward to 9 blocks; everyone standing on the ground as it passes
  takes 9 damage, catches fire and is thrown up.
- Magma hurl (7 to 24 blocks): lobs a chunk of molten rock (6 damage and fire, splashes 4).
- Enraged below a third of its health: its cracks blaze, it's faster and slams twice as often.
- Counter: jump as the ring reaches you. Freezing hurts it five times as much (powder snow), and
  water and rain hurt it.
- Basalt Deltas only. Rare.
- Drops: magma cream 1-3, basalt 2-4, gold nugget 3-8, netherite scrap (3%, killed by a player).

### 29. Crag Troll
A lanky, hunched mountain troll with grey-green stony hide, lichen and moss, rocks growing out of
its back and shoulders, a long warty nose, tusks, small yellow eyes and a hide pouch with an
emerald glint (it collects tolls).
- Punch 10 with a huge knockback that lifts you off your feet: dangerous on a cliff edge.
  80 health, 6 armour.
- Boulder throw (6 to 28 blocks): it rips a boulder out of the ground and lifts it overhead (that's
  your warning), then hurls it in an arc: 9 damage and knockback, 4 splash.
- Regenerates a heart every two seconds (green specks) unless it's burned: any fire damage stops
  the healing for ten seconds (smoke).
- Counter: fire (Flame, Fire Aspect, a lava bucket, flint and steel); keep away from cliff edges;
  sidestep the boulder.
- Windswept Hills (all three kinds), Stony Peaks and Jagged Peaks, at night. Rare.
- Drops: emerald 1-3, flint 0-3, mossy cobblestone 1-3.

### 30. Prowler
A black jungle panther with faint rosettes, big paws, a long curling tail and glowing green eyes.
- Stalks you crouched and silent through the undergrowth (at night only the eyes show).
- Pounce: it sinks lower, lashes its tail and growls for most of a second, then leaps up to ten
  blocks with a roar. If it lands: 8 damage and you're pinned (heavily slowed) while it mauls you
  three more times, then it slinks off to stalk again.
- Up close it swipes (7). 40 health, takes no fall damage.
- Counter: raise a shield as it leaps: it's dazed for three seconds and takes half again as much
  damage. Hitting it hard while it's mauling throws it off.
- Jungles, Bamboo Jungles and Sparse Jungles, at night (and in the dark under the canopy).
- Drops: leather 1-3, bone 0-2.

### 31. Stormcaller
An illager storm mystic in a slate-blue robe with oxidised copper trim, a copper circlet with a
lightning-rod spike, a glowing lightning sigil and pale electric-blue eyes.
- Keeps its distance. Calls lightning: rings of sparks crackle on the ground under you, where
  you're heading and nearby for a second and a half, then lightning strikes each one (7 damage
  and fire within a block and a half). In a thunderstorm it calls five bolts, faster.
- Gale: get within four and a half blocks and it blasts everything around it away (2 damage and a
  big push).
- 36 health. It's a raider: it fights alongside other illagers, attacks villagers and iron golems,
  and a village bell makes it glow. It never spawns as a captain.
- Counter: keep moving when the sparks appear; close in between casts; arrows.
- Taigas, Snowy Taiga, Dark Forest, Windswept Hills and Windswept Forest, at night. Rare.
- Drops: emerald 0-2, copper ingot 1-3, wind charge 1-3 (35%).

### 32. Brineclaw
A giant armoured shore crab: a rough crimson carapace crusted with barnacles and draped with
seaweed, a huge spiny crusher claw on its right, a smaller cutter on its left, stalked eyes and
eight spiky legs.
- Front shell: blows and arrows from within 70 degrees of its front do a quarter of their damage
  (a clang and sparks). Its sides and back take full damage. 60 health, 8 armour.
- Turns slowly (100 degrees a second), so you can get round it.
- Claw: it raises the claw with the pincer gaping (a clack), then snaps it shut on whatever is in
  front of it: 9 damage, held for a second, then flung aside.
- Breathes underwater and walks along the sea floor.
- Counter: circle it (sprinting round it close outpaces its turning) and hit it from the side or
  behind; tridents do extra damage (Impaling).
- Beaches and Stony Shores, at night.
- Drops: bone meal 1-4, kelp 0-3, nautilus shell (12%, killed by a player).

### 33. Rimewraith
A floating spectre of ice and snow: a deep snow hood with darkness and two ice-blue eyes inside,
a ribcage of glacial ice with a faint glow behind it, long icy arms with icicle claws, a crown of
ice crystals and a tattered frost-white robe trailing into wisps.
- Its cold freezes any player (and anything it's hunting) within six blocks, the way powder snow
  does; frozen through, you also take 2 damage a second near it.
- Hurls fans of three ice shards (4 damage, freezing and Slowness); claws for 6 and freezing.
- Still water freezes over under it (frosted ice, which melts back).
- 40 health. Fire hurts it twice as much, and it wastes away in warm biomes. Undead.
- Counter: wear leather armour (any piece makes you immune to freezing, as with powder snow);
  fire.
- Frozen Peaks, Jagged Peaks, Snowy Slopes, Ice Spikes and Groves, at night.
- Drops: snowball 1-4, packed ice 0-2, blue ice (15%, killed by a player).

### 34. Riftstalker
A tall, gaunt void predator of the outer End: matte black skin cracked by glowing magenta rift
seams, a smooth eyeless bone mask with one glowing slit, long arms ending in bone scythe blades,
reverse-jointed legs and a whip tail with a bone spike.
- Every few seconds it vanishes and a rift opens two blocks behind you (swirling purple particles
  and a hum) for most of a second; then it steps out, raises its blade and slashes for 10.
- Turn round and hit it in the half second before the slash and it staggers: helpless for two and
  a half seconds and taking half again as much damage.
- Projectiles never touch it: it blinks away from them, like an enderman. Water hurts it.
  Claws for 8 between blinks. 60 health, 4 armour.
- Counter: listen for the rift, turn and be ready to strike.
- End Highlands, End Midlands and End Barrens. Rare.
- Drops: ender pearl 1-2, chorus fruit 0-2, eye of ender (12%, killed by a player).

### 35. Oregorger
A massive armoured beast of the deep caves, like a giant pangolin crossed with a boulder: a domed
back of deepslate plates studded with chunks of raw iron, copper and gold (and a diamond glint), a
blunt stone snout with a crushing jaw, amber eyes and digging claws.
- 80 health, 12 armour and toughness: most blows barely scratch it. Bites for 9.
- Rolling charge: it curls into a ball and revs (grit sprays behind it) for a second, then bowls
  straight at you at 12 blocks a second: 12 damage and you're thrown.
- If the roll ends against a wall it's stunned for three and a half seconds, uncurled with its
  armour useless.
- Eats exposed ore veins (with mobGriefing on), leaving bare rock, and keeps the ore: it drops
  everything it ate when it dies.
- Counter: stand in front of a wall and dodge aside at the last moment, then hit it while it's
  stunned.
- Lives below y 0 in every overworld biome. Rare.
- Drops: raw iron 1-3, raw copper 2-5, raw gold 0-2, diamond (5%, killed by a player), plus the ore
  it ate.

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
  Gravewarden, Soulpyre and Sculkbones as Skeletons, Dune Scorpion, Dripfang, Broodmother and
  Brineclaw as Spiders, Angler as a Guardian, Driftcap and Riftstalker as Endermen, Sandmaw as
  Vermin, Cinderhulk as a Blaze and Stormcaller as an Illager. Everything else earns normal kill XP.

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
| broodmother | `body` with `head` (`right_fang` / `left_fang`), `abdomen` (pivot at its joint; the code bobs and pulses it) and legs `right_leg1..4` / `left_leg1..4`, each with a `_lower` child (knee to foot) |
| sandmaw | `segment1` (child of root, pivot at ground level; the code slides it down to sink the worm) > `segment2` > `segment3` > `head` with `jaw_top`, `jaw_bottom`, `jaw_left`, `jaw_right` |
| cinderhulk | `body` (pivot at the waist) with `head`, `right_arm` / `left_arm`; `right_leg` / `left_leg` (children of root) |
| crag_troll | as cinderhulk, plus `jaw` (child of head) and `boulder` (child of root, where the hands are with both arms raised to xRot -2.9; shown only while it holds one) |
| prowler | `body`, `head` (child of root) with `jaw`, `tail` (child of body) with `tail_tip`, four legs (children of root) |
| stormcaller | vanilla illager names and layout (`head` with `hat` and `nose`, `body`, `arms` with `left_shoulder`, `right_arm`, `left_arm`, `right_leg`, `left_leg`); decorations are children of `head` or `body`, never `hat` (the game hides it) |
| brineclaw | `body` with `right_eye` / `left_eye`, `right_claw` (the big one) / `left_claw` each with `right_pincer` / `left_pincer`, legs `right_leg1..4` / `left_leg1..4` |
| rimewraith | `body` with `head`, `right_arm` / `left_arm` and `robe` (optional `robe_tail` child) |
| riftstalker | `body` (pivot at the hips) with `head`, `right_arm` / `left_arm` (each with `right_forearm` / `left_forearm`), `tail` with `tail_tip`; `right_leg` / `left_leg` (children of root) each with `right_shin` / `left_shin` |
| oregorger | `body` with `head` (`jaw`) and `tail`, four legs (children of root), and `ball` (child of root, pivot at its centre: the rolled-up form, shown only while rolling) |

Hitboxes (blocks, width x height): zombies 0.6x1.95, briarbones 0.6x1.99, gravewarden 0.7x2.3
(rendered at 1.15x), bog lurker 1.2x0.9, gloomwing 0.9x0.6, dune scorpion 1.3x0.7, tortoise
1.2x0.9, capybara 0.9x0.9, wyrmling 0.6x0.6, lost miner 0.6x1.95, soulpyre 0.6x1.99, glowmoth
0.7x0.6, hermit crab 0.5x0.45, hedgehog 0.45x0.4, scarecrow 0.6x1.95, sculkbones 0.6x1.99, vulture 0.9x0.7,
dripfang 0.9x0.55, angler 0.9x0.8, driftcap 0.8x1.2, meerkat 0.4x0.6, penguin 0.55x0.95, wild boar
0.9x0.9, otter 0.6x0.5, broodmother 2.2x1.3, sandmaw 1.5x3.0
(surfaced), cinderhulk 1.8x2.8, crag troll 1.6x2.9, prowler 1.0x1.0, stormcaller 0.6x1.95, brineclaw
1.8x1.0, rimewraith 0.8x2.2, riftstalker 0.7x2.7, oregorger 1.6x1.3.