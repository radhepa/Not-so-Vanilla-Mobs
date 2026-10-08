package dev.nsvmobs.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.gamerules.GameRules;

final class Griefing {
    private Griefing() {}

    /** Whether mobs may change blocks (the mobGriefing game rule). */
    static boolean allowed(ServerLevel level) {
        return level.getGameRules().get(GameRules.MOB_GRIEFING);
    }
}
