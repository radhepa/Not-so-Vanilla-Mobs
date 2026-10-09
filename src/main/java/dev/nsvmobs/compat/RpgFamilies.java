package dev.nsvmobs.compat;

import java.util.Map;

import dev.nsvmobs.registry.MobRegistry;

/** Which vanilla family each mob counts toward in the RPG add-on's Bestiary (set per mob in NsvEntities). */
public final class RpgFamilies {
    private RpgFamilies() {}

    /**
     * The add-on looks families up by vanilla mob path. Most family ids are also a member's path
     * ("zombie", "spider"); for the ones that aren't, this names a member to stand in for them.
     */
    private static final Map<String, String> MEMBER = Map.of("vermin", "silverfish", "illager", "evoker");

    public static String alias(String path) {
        String family = MobRegistry.rpgFamilies().get(path);
        return family == null ? path : MEMBER.getOrDefault(family, family);
    }
}
