package dev.nsvmobs.compat;

import dev.nsvmobs.registry.MobRegistry;

/** Which vanilla family each mob counts toward in the RPG add-on's Bestiary (set per mob in NsvEntities). */
public final class RpgFamilies {
    private RpgFamilies() {}

    public static String alias(String path) {
        return MobRegistry.rpgFamilies().getOrDefault(path, path);
    }
}
