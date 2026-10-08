package dev.nsvmobs;

import dev.nsvmobs.entity.BogLurker;
import dev.nsvmobs.entity.Briarbones;
import dev.nsvmobs.entity.Capybara;
import dev.nsvmobs.entity.DuneScorpion;
import dev.nsvmobs.entity.Frostbitten;
import dev.nsvmobs.entity.Gloomwing;
import dev.nsvmobs.entity.Gravewarden;
import dev.nsvmobs.entity.MossbackTortoise;
import dev.nsvmobs.entity.Sporeling;
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
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.biome.Biomes;

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

    // -- pets -------------------------------------------------------------------------------------
    public static final EntityType<Wyrmling> WYRMLING = MobEntry.builder("wyrmling", Wyrmling::new, MobCategory.CREATURE)
            .size(0.6F, 0.6F, 0.45F).type(EntityType.Builder::fireImmune)
            .attributes(Wyrmling::createAttributes)
            .spawnRule(Wyrmling::checkSpawnRules)
            .spawnsIn(3, 1, 2, Biomes.STONY_PEAKS, Biomes.JAGGED_PEAKS, Biomes.WINDSWEPT_HILLS, Biomes.WINDSWEPT_GRAVELLY_HILLS, Biomes.WINDSWEPT_FOREST)
            .register();

    // -- projectiles and other non-mob entities -------------------------------------------------
    public static final EntityType<WyrmlingEmber> WYRMLING_EMBER = misc("wyrmling_ember",
            EntityType.Builder.<WyrmlingEmber>of(WyrmlingEmber::new, MobCategory.MISC).noLootTable().sized(0.3125F, 0.3125F)
                    .clientTrackingRange(4).updateInterval(10));

    private static <T extends net.minecraft.world.entity.Entity> EntityType<T> misc(String id, EntityType.Builder<T> builder) {
        ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, Identifier.fromNamespaceAndPath(NsvMobs.MOD_ID, id));
        return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
    }

    /** Loads the catalogue (class initialisation registers every entry). */
    static void init() {}
}
