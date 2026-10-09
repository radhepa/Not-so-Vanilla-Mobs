package dev.nsvmobs;

import dev.nsvmobs.entity.Angler;
import dev.nsvmobs.entity.Boulder;
import dev.nsvmobs.entity.Brineclaw;
import dev.nsvmobs.entity.Broodmother;
import dev.nsvmobs.entity.Cinderhulk;
import dev.nsvmobs.entity.CragTroll;
import dev.nsvmobs.entity.BogLurker;
import dev.nsvmobs.entity.Briarbones;
import dev.nsvmobs.entity.Capybara;
import dev.nsvmobs.entity.Driftcap;
import dev.nsvmobs.entity.Dripfang;
import dev.nsvmobs.entity.DuneScorpion;
import dev.nsvmobs.entity.Frostbitten;
import dev.nsvmobs.entity.Gloomwing;
import dev.nsvmobs.entity.Glowmoth;
import dev.nsvmobs.entity.Gravewarden;
import dev.nsvmobs.entity.Hedgehog;
import dev.nsvmobs.entity.HermitCrab;
import dev.nsvmobs.entity.IceShard;
import dev.nsvmobs.entity.LostMiner;
import dev.nsvmobs.entity.Meerkat;
import dev.nsvmobs.entity.MossbackTortoise;
import dev.nsvmobs.entity.Oregorger;
import dev.nsvmobs.entity.Otter;
import dev.nsvmobs.entity.Penguin;
import dev.nsvmobs.entity.Prowler;
import dev.nsvmobs.entity.Riftstalker;
import dev.nsvmobs.entity.Rimewraith;
import dev.nsvmobs.entity.Sandmaw;
import dev.nsvmobs.entity.Scarecrow;
import dev.nsvmobs.entity.Sculkbones;
import dev.nsvmobs.entity.Soulpyre;
import dev.nsvmobs.entity.Sporeling;
import dev.nsvmobs.entity.Stormcaller;
import dev.nsvmobs.entity.Vulture;
import dev.nsvmobs.entity.WebGlob;
import dev.nsvmobs.entity.WildBoar;
import dev.nsvmobs.entity.Wyrmling;
import dev.nsvmobs.entity.WyrmlingEmber;
import dev.nsvmobs.registry.MobEntry;

import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * The mob catalogue. One entry per mob: hitbox, attributes, spawn rule, biomes and RPG family.
 * Spawn eggs, spawn rules and biome spawns are wired up from here by MobRegistry; the client
 * registers a model and renderer for every entry (see ARCHITECTURE.md, "Adding a mob").
 */
public final class NsvEntities {
    private NsvEntities() {}

    // -- zombie variants -------------------------------------------------------------------------
    public static final EntityType<Sporeling> SPORELING = MobEntry.builder("sporeling", Sporeling::new, MobCategory.MONSTER)
            .size(0.6F, 1.95F, 1.74F).type(t -> t.passengerAttachments(2.0125F).ridingOffset(-0.7F))
            .attributes(Sporeling::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(100, 1, 3, Biomes.MUSHROOM_FIELDS)
            .spawnsIn(40, 1, 2, Biomes.DARK_FOREST, Biomes.PALE_GARDEN)
            .rpgFamily("zombie")
            .register();

    public static final EntityType<Frostbitten> FROSTBITTEN = MobEntry.builder("frostbitten", Frostbitten::new, MobCategory.MONSTER)
            .size(0.6F, 1.95F, 1.74F).type(t -> t.passengerAttachments(2.0125F).ridingOffset(-0.7F))
            .attributes(Frostbitten::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(80, 2, 4, Biomes.SNOWY_PLAINS, Biomes.ICE_SPIKES, Biomes.SNOWY_TAIGA, Biomes.SNOWY_SLOPES,
                    Biomes.FROZEN_PEAKS, Biomes.JAGGED_PEAKS, Biomes.GROVE, Biomes.FROZEN_RIVER, Biomes.SNOWY_BEACH)
            .rpgFamily("zombie")
            .register();

    public static final EntityType<LostMiner> LOST_MINER = MobEntry.builder("lost_miner", LostMiner::new, MobCategory.MONSTER)
            .size(0.6F, 1.95F, 1.74F).type(t -> t.passengerAttachments(2.0125F).ridingOffset(-0.7F))
            .attributes(LostMiner::createAttributes)
            .spawnRule(LostMiner::checkSpawnRules)              // below y 0 only
            .spawnsIn(BiomeSelectors.foundInOverworld(), 25, 1, 2)
            .rpgFamily("zombie")
            .register();

    /** Not a zombie, but it walks and fights like one (and by day it doesn't move at all). */
    public static final EntityType<Scarecrow> SCARECROW = MobEntry.builder("scarecrow", Scarecrow::new, MobCategory.MONSTER)
            .size(0.6F, 1.95F, 1.74F).type(t -> t.passengerAttachments(2.0125F).ridingOffset(-0.7F))
            .attributes(Scarecrow::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(30, 1, 1, Biomes.PLAINS, Biomes.SUNFLOWER_PLAINS, Biomes.MEADOW)
            .register();

    // -- skeleton variants -----------------------------------------------------------------------
    public static final EntityType<Briarbones> BRIARBONES = MobEntry.builder("briarbones", Briarbones::new, MobCategory.MONSTER)
            .size(0.6F, 1.99F, 1.74F).type(t -> t.ridingOffset(-0.7F))
            .attributes(Briarbones::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(70, 1, 3, Biomes.JUNGLE, Biomes.BAMBOO_JUNGLE, Biomes.SPARSE_JUNGLE, Biomes.LUSH_CAVES)
            .rpgFamily("skeleton")
            .register();

    public static final EntityType<Gravewarden> GRAVEWARDEN = MobEntry.builder("gravewarden", Gravewarden::new, MobCategory.MONSTER)
            .size(0.6F, 1.99F, 1.74F).type(t -> t.ridingOffset(-0.7F))   // drawn and sized 1.15x by its scale attribute
            .attributes(Gravewarden::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(15, 1, 1, Biomes.DARK_FOREST, Biomes.OLD_GROWTH_PINE_TAIGA, Biomes.OLD_GROWTH_SPRUCE_TAIGA, Biomes.TAIGA, Biomes.PALE_GARDEN)
            .rpgFamily("skeleton")
            .register();

    public static final EntityType<Soulpyre> SOULPYRE = MobEntry.builder("soulpyre", Soulpyre::new, MobCategory.MONSTER)
            .size(0.6F, 1.99F, 1.74F).type(t -> t.ridingOffset(-0.7F).fireImmune())
            .attributes(Soulpyre::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(40, 1, 3, Biomes.SOUL_SAND_VALLEY)
            .rpgFamily("skeleton")
            .register();

    public static final EntityType<Sculkbones> SCULKBONES = MobEntry.builder("sculkbones", Sculkbones::new, MobCategory.MONSTER)
            .size(0.6F, 1.99F, 1.74F).type(t -> t.ridingOffset(-0.7F))
            .attributes(Sculkbones::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(60, 1, 2, Biomes.DEEP_DARK)
            .rpgFamily("skeleton")
            .register();

    // -- other hostiles --------------------------------------------------------------------------
    public static final EntityType<BogLurker> BOG_LURKER = MobEntry.builder("bog_lurker", BogLurker::new, MobCategory.MONSTER)
            .size(1.2F, 0.9F, 0.7F)
            .attributes(BogLurker::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(40, 1, 1, Biomes.SWAMP, Biomes.MANGROVE_SWAMP)
            .register();

    public static final EntityType<Gloomwing> GLOOMWING = MobEntry.builder("gloomwing", Gloomwing::new, MobCategory.MONSTER)
            .size(0.9F, 0.6F, 0.4F)
            .attributes(Gloomwing::createAttributes)
            .spawnRule(Gloomwing::checkSpawnRules)
            .spawnsIn(BiomeSelectors.foundInOverworld(), 20, 1, 2)
            .register();

    public static final EntityType<DuneScorpion> DUNE_SCORPION = MobEntry.builder("dune_scorpion", DuneScorpion::new, MobCategory.MONSTER)
            .size(1.3F, 0.7F, 0.45F)
            .attributes(DuneScorpion::createAttributes)
            .spawnRule(DuneScorpion::checkSpawnRules)
            .spawnsIn(30, 1, 2, Biomes.DESERT, Biomes.BADLANDS, Biomes.ERODED_BADLANDS, Biomes.WOODED_BADLANDS)
            .rpgFamily("spider")
            .register();

    public static final EntityType<Vulture> VULTURE = MobEntry.builder("vulture", Vulture::new, MobCategory.MONSTER)
            .size(0.9F, 0.7F, 0.5F)
            .attributes(Vulture::createAttributes)
            .spawnRule(Vulture::checkSpawnRules)
            .spawnsIn(12, 1, 3, Biomes.DESERT, Biomes.BADLANDS, Biomes.ERODED_BADLANDS, Biomes.WOODED_BADLANDS,
                    Biomes.SAVANNA, Biomes.SAVANNA_PLATEAU, Biomes.WINDSWEPT_SAVANNA)
            .register();

    public static final EntityType<Dripfang> DRIPFANG = MobEntry.builder("dripfang", Dripfang::new, MobCategory.MONSTER)
            .size(0.9F, 0.55F, 0.35F)
            .attributes(Dripfang::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(60, 1, 3, Biomes.DRIPSTONE_CAVES)
            .rpgFamily("spider")
            .register();

    public static final EntityType<Angler> ANGLER = MobEntry.builder("angler", Angler::new, MobCategory.MONSTER)
            .size(0.9F, 0.8F, 0.4F)
            .attributes(Angler::createAttributes)
            .placement(SpawnPlacementTypes.IN_WATER, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES)
            .spawnRule(Angler::checkSpawnRules)                  // deep, dark water only
            .spawnsIn(15, 1, 1, Biomes.DEEP_OCEAN, Biomes.DEEP_COLD_OCEAN, Biomes.DEEP_LUKEWARM_OCEAN, Biomes.DEEP_FROZEN_OCEAN)
            .rpgFamily("guardian")
            .register();

    public static final EntityType<Driftcap> DRIFTCAP = MobEntry.builder("driftcap", Driftcap::new, MobCategory.MONSTER)
            .size(0.8F, 1.2F, 0.6F).type(EntityType.Builder::fireImmune)
            .attributes(Driftcap::createAttributes)
            .spawnRule(Driftcap::checkSpawnRules)
            .spawnsIn(1, 1, 2, Biomes.WARPED_FOREST)          // about as common as the endermen there
            .rpgFamily("enderman")
            .register();

    // -- challengers: big, rare, dangerous hostiles, each with an attack you can learn to beat -----
    public static final EntityType<Broodmother> BROODMOTHER = MobEntry.builder("broodmother", Broodmother::new, MobCategory.MONSTER)
            .size(2.2F, 1.3F, 0.9F)
            .attributes(Broodmother::createAttributes)
            .spawnRule(Broodmother::checkSpawnRules)            // below y 0, or a Dark Forest floor
            .spawnsIn(BiomeSelectors.foundInOverworld(), 4, 1, 1)
            .spawnsIn(8, 1, 1, Biomes.DARK_FOREST)
            .rpgFamily("spider")
            .solitary(64)
            .register();

    public static final EntityType<Sandmaw> SANDMAW = MobEntry.builder("sandmaw", Sandmaw::new, MobCategory.MONSTER)
            .size(1.5F, 3.0F, 2.6F)
            .attributes(Sandmaw::createAttributes)
            .spawnRule(Sandmaw::checkSpawnRules)               // open desert sand, day or night
            .spawnsIn(6, 1, 1, Biomes.DESERT)
            .rpgFamily("vermin")
            .solitary(64)
            .register();

    public static final EntityType<Cinderhulk> CINDERHULK = MobEntry.builder("cinderhulk", Cinderhulk::new, MobCategory.MONSTER)
            .size(1.8F, 2.8F, 2.3F).type(EntityType.Builder::fireImmune)
            .attributes(Cinderhulk::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(6, 1, 1, Biomes.BASALT_DELTAS)
            .rpgFamily("blaze")
            .solitary(64)
            .register();

    public static final EntityType<CragTroll> CRAG_TROLL = MobEntry.builder("crag_troll", CragTroll::new, MobCategory.MONSTER)
            .size(1.6F, 2.9F, 2.4F)
            .attributes(CragTroll::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(8, 1, 1, Biomes.WINDSWEPT_HILLS, Biomes.WINDSWEPT_GRAVELLY_HILLS, Biomes.WINDSWEPT_FOREST, Biomes.STONY_PEAKS, Biomes.JAGGED_PEAKS)
            .solitary(64)
            .register();

    public static final EntityType<Prowler> PROWLER = MobEntry.builder("prowler", Prowler::new, MobCategory.MONSTER)
            .size(1.0F, 1.0F, 0.8F)
            .attributes(Prowler::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(10, 1, 1, Biomes.JUNGLE, Biomes.BAMBOO_JUNGLE, Biomes.SPARSE_JUNGLE)
            .solitary(64)
            .register();

    public static final EntityType<Stormcaller> STORMCALLER = MobEntry.builder("stormcaller", Stormcaller::new, MobCategory.MONSTER)
            .size(0.6F, 1.95F, 1.62F).type(t -> t.passengerAttachments(2.0F).ridingOffset(-0.6F))
            .attributes(Stormcaller::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(5, 1, 1, Biomes.TAIGA, Biomes.SNOWY_TAIGA, Biomes.OLD_GROWTH_PINE_TAIGA, Biomes.OLD_GROWTH_SPRUCE_TAIGA,
                    Biomes.DARK_FOREST, Biomes.WINDSWEPT_HILLS, Biomes.WINDSWEPT_FOREST)
            .rpgFamily("illager")
            .solitary(64)
            .register();

    public static final EntityType<Brineclaw> BRINECLAW = MobEntry.builder("brineclaw", Brineclaw::new, MobCategory.MONSTER)
            .size(1.8F, 1.0F, 0.7F)
            .attributes(Brineclaw::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(10, 1, 1, Biomes.BEACH, Biomes.STONY_SHORE)
            .rpgFamily("spider")
            .solitary(64)
            .register();

    public static final EntityType<Rimewraith> RIMEWRAITH = MobEntry.builder("rimewraith", Rimewraith::new, MobCategory.MONSTER)
            .size(0.8F, 2.2F, 1.9F)
            .attributes(Rimewraith::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(10, 1, 1, Biomes.FROZEN_PEAKS, Biomes.JAGGED_PEAKS, Biomes.SNOWY_SLOPES, Biomes.ICE_SPIKES, Biomes.GROVE)
            .solitary(64)
            .register();

    public static final EntityType<Riftstalker> RIFTSTALKER = MobEntry.builder("riftstalker", Riftstalker::new, MobCategory.MONSTER)
            .size(0.7F, 2.7F, 2.45F)
            .attributes(Riftstalker::createAttributes)
            .spawnRule(Monster::checkMonsterSpawnRules)
            .spawnsIn(3, 1, 1, Biomes.END_HIGHLANDS, Biomes.END_MIDLANDS, Biomes.END_BARRENS)
            .rpgFamily("enderman")
            .solitary(64)
            .register();

    public static final EntityType<Oregorger> OREGORGER = MobEntry.builder("oregorger", Oregorger::new, MobCategory.MONSTER)
            .size(1.6F, 1.3F, 0.9F)
            .attributes(Oregorger::createAttributes)
            .spawnRule(Oregorger::checkSpawnRules)              // below y 0 only
            .spawnsIn(BiomeSelectors.foundInOverworld(), 6, 1, 1)
            .solitary(64)
            .register();

    // -- friendly ---------------------------------------------------------------------------------
    public static final EntityType<MossbackTortoise> MOSSBACK_TORTOISE = MobEntry.builder("mossback_tortoise", MossbackTortoise::new, MobCategory.CREATURE)
            .size(1.2F, 0.9F, 0.6F).type(t -> t.clientTrackingRange(10))
            .attributes(MossbackTortoise::createAttributes)
            .spawnRule(Animal::checkAnimalSpawnRules)
            .spawnsIn(6, 1, 2, Biomes.SWAMP, Biomes.JUNGLE, Biomes.SPARSE_JUNGLE, Biomes.BAMBOO_JUNGLE)
            .register();

    public static final EntityType<Capybara> CAPYBARA = MobEntry.builder("capybara", Capybara::new, MobCategory.CREATURE)
            .size(0.9F, 0.9F, 0.75F).type(t -> t.passengerAttachments(0.86F).clientTrackingRange(10))
            .attributes(Capybara::createAttributes)
            .spawnRule(Animal::checkAnimalSpawnRules)
            .spawnsIn(8, 2, 4, Biomes.SWAMP, Biomes.MANGROVE_SWAMP, Biomes.SAVANNA, Biomes.SPARSE_JUNGLE, Biomes.RIVER)
            .register();

    public static final EntityType<Glowmoth> GLOWMOTH = MobEntry.builder("glowmoth", Glowmoth::new, MobCategory.CREATURE)
            .size(0.7F, 0.6F, 0.4F).type(t -> t.clientTrackingRange(10))
            .attributes(Glowmoth::createAttributes)
            .spawnRule(Animal::checkAnimalSpawnRules)
            .spawnsIn(6, 1, 3, Biomes.FLOWER_FOREST, Biomes.MEADOW, Biomes.FOREST, Biomes.BIRCH_FOREST,
                    Biomes.OLD_GROWTH_BIRCH_FOREST, Biomes.CHERRY_GROVE)
            .register();

    public static final EntityType<HermitCrab> HERMIT_CRAB = MobEntry.builder("hermit_crab", HermitCrab::new, MobCategory.CREATURE)
            .size(0.5F, 0.45F, 0.3F).type(t -> t.clientTrackingRange(10))
            .attributes(HermitCrab::createAttributes)
            .spawnRule(HermitCrab::checkSpawnRules)
            .spawnsIn(8, 2, 4, Biomes.BEACH, Biomes.STONY_SHORE, Biomes.MANGROVE_SWAMP)
            .register();

    public static final EntityType<Meerkat> MEERKAT = MobEntry.builder("meerkat", Meerkat::new, MobCategory.CREATURE)
            .size(0.4F, 0.6F, 0.5F).type(t -> t.clientTrackingRange(10))
            .attributes(Meerkat::createAttributes)
            .spawnRule(Meerkat::checkSpawnRules)
            .spawnsIn(6, 3, 5, Biomes.DESERT, Biomes.SAVANNA, Biomes.SAVANNA_PLATEAU, Biomes.BADLANDS)
            .register();

    public static final EntityType<Penguin> PENGUIN = MobEntry.builder("penguin", Penguin::new, MobCategory.CREATURE)
            .size(0.55F, 0.95F, 0.8F).type(t -> t.clientTrackingRange(10))
            .attributes(Penguin::createAttributes)
            .spawnRule(Penguin::checkSpawnRules)
            .spawnsIn(10, 3, 6, Biomes.SNOWY_BEACH, Biomes.FROZEN_OCEAN, Biomes.DEEP_FROZEN_OCEAN, Biomes.FROZEN_RIVER)
            .register();

    /** Neutral: harmless until something hurts it or its piglets. */
    public static final EntityType<WildBoar> WILD_BOAR = MobEntry.builder("wild_boar", WildBoar::new, MobCategory.CREATURE)
            .size(0.9F, 0.9F, 0.75F).type(t -> t.clientTrackingRange(10))
            .attributes(WildBoar::createAttributes)
            .spawnRule(WildBoar::checkSpawnRules)
            .spawnsIn(8, 2, 4, Biomes.TAIGA, Biomes.OLD_GROWTH_PINE_TAIGA, Biomes.OLD_GROWTH_SPRUCE_TAIGA, Biomes.FOREST, Biomes.DARK_FOREST)
            .register();

    // -- pets -------------------------------------------------------------------------------------
    public static final EntityType<Wyrmling> WYRMLING = MobEntry.builder("wyrmling", Wyrmling::new, MobCategory.CREATURE)
            .size(0.6F, 0.6F, 0.45F).type(EntityType.Builder::fireImmune)
            .attributes(Wyrmling::createAttributes)
            .spawnRule(Wyrmling::checkSpawnRules)
            .spawnsIn(3, 1, 2, Biomes.STONY_PEAKS, Biomes.JAGGED_PEAKS, Biomes.WINDSWEPT_HILLS, Biomes.WINDSWEPT_GRAVELLY_HILLS, Biomes.WINDSWEPT_FOREST)
            .register();

    public static final EntityType<Hedgehog> HEDGEHOG = MobEntry.builder("hedgehog", Hedgehog::new, MobCategory.CREATURE)
            .size(0.45F, 0.4F, 0.3F)
            .attributes(Hedgehog::createAttributes)
            .spawnRule(Animal::checkAnimalSpawnRules)
            .spawnsIn(5, 1, 2, Biomes.FOREST, Biomes.BIRCH_FOREST, Biomes.FLOWER_FOREST, Biomes.MEADOW, Biomes.PLAINS)
            .register();

    public static final EntityType<Otter> OTTER = MobEntry.builder("otter", Otter::new, MobCategory.CREATURE)
            .size(0.6F, 0.5F, 0.4F).type(t -> t.clientTrackingRange(10))
            .attributes(Otter::createAttributes)
            .spawnRule(Otter::checkSpawnRules)
            .spawnsIn(6, 1, 2, Biomes.RIVER, Biomes.FROZEN_RIVER)
            .register();

    // -- projectiles and other non-mob entities -------------------------------------------------
    public static final EntityType<WyrmlingEmber> WYRMLING_EMBER = misc("wyrmling_ember",
            EntityType.Builder.<WyrmlingEmber>of(WyrmlingEmber::new, MobCategory.MISC).noLootTable().sized(0.3125F, 0.3125F)
                    .clientTrackingRange(4).updateInterval(10));
    /** A Crag Troll's boulder, or a Cinderhulk's chunk of magma. */
    public static final EntityType<Boulder> BOULDER = misc("boulder",
            EntityType.Builder.<Boulder>of(Boulder::new, MobCategory.MISC).noLootTable().sized(0.75F, 0.75F)
                    .clientTrackingRange(6).updateInterval(10));
    public static final EntityType<IceShard> ICE_SHARD = misc("ice_shard",
            EntityType.Builder.<IceShard>of(IceShard::new, MobCategory.MISC).noLootTable().sized(0.25F, 0.25F)
                    .clientTrackingRange(4).updateInterval(10));
    public static final EntityType<WebGlob> WEB_GLOB = misc("web_glob",
            EntityType.Builder.<WebGlob>of(WebGlob::new, MobCategory.MISC).noLootTable().sized(0.4F, 0.4F)
                    .clientTrackingRange(4).updateInterval(10));

    private static <T extends net.minecraft.world.entity.Entity> EntityType<T> misc(String id, EntityType.Builder<T> builder) {
        ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, Identifier.fromNamespaceAndPath(NsvMobs.MOD_ID, id));
        return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
    }

    /** Loads the catalogue (class initialisation registers every entry). */
    static void init() {}
}
