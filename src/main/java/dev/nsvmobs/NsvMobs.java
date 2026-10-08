package dev.nsvmobs;

import dev.nsvmobs.registry.MobRegistry;

import net.fabricmc.api.ModInitializer;

public final class NsvMobs implements ModInitializer {
    public static final String MOD_ID = "nsvmobs";

    @Override
    public void onInitialize() {
        NsvEntities.init();
        MobRegistry.wireUp();
    }
}
