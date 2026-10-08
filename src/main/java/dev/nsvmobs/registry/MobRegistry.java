package dev.nsvmobs.registry;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import dev.nsvmobs.NsvMobs;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;

/** All registered mobs, in catalogue order, and the wiring every mob gets. */
public final class MobRegistry {
    private MobRegistry() {}

    private static final List<MobEntry<?>> ALL = new ArrayList<>();
    private static final Map<String, String> RPG_FAMILIES = new HashMap<>();

    static void add(MobEntry<?> entry) {
        if (ALL.stream().anyMatch(e -> e.id.equals(entry.id))) throw new IllegalStateException("duplicate mob " + entry.id);
        ALL.add(entry);
        if (entry.rpgFamily != null) RPG_FAMILIES.put(entry.id, entry.rpgFamily);
    }

    public static List<MobEntry<?>> all() {
        return Collections.unmodifiableList(ALL);
    }

    /** Mob id (entity path) to Village Friends RPG Bestiary family, for mobs that have one. */
    public static Map<String, String> rpgFamilies() {
        return Collections.unmodifiableMap(RPG_FAMILIES);
    }

    /** Attributes, spawn eggs, spawn rules and biome spawns for every catalogued mob. */
    public static void wireUp() {
        for (MobEntry<?> e : ALL) {
            FabricDefaultAttributeRegistry.register(e.type, e.attributes.get());
            ResourceKey<Item> egg = ResourceKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath(NsvMobs.MOD_ID, e.id + "_spawn_egg"));
            e.spawnEgg = Registry.register(BuiltInRegistries.ITEM, egg, new SpawnEggItem(new Item.Properties().setId(egg).spawnEgg(e.type)));
            e.registerSpawnPlacement();
            for (MobEntry.BiomeSpawn s : e.spawns) {
                if (e.spawnRule == null) throw new IllegalStateException(e.id + " has biome spawns but no spawn rule");
                BiomeModifications.addSpawn(s.biomes(), e.type.getCategory(), e.type, s.weight(), s.minGroup(), s.maxGroup());
            }
        }
        CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.SPAWN_EGGS).register(out -> ALL.forEach(e -> out.accept(e.spawnEgg)));
    }
}
