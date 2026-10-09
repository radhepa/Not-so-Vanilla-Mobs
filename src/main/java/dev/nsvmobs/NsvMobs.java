package dev.nsvmobs;

import dev.nsvmobs.entity.TemporaryBlocks;
import dev.nsvmobs.registry.MobRegistry;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

public final class NsvMobs implements ModInitializer {
    public static final String MOD_ID = "nsvmobs";

    @Override
    public void onInitialize() {
        NsvEntities.init();
        MobRegistry.wireUp();
        ServerTickEvents.END_LEVEL_TICK.register(TemporaryBlocks::tick);
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> server.getAllLevels().forEach(TemporaryBlocks::flush));
    }
}
