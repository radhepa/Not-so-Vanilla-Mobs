package dev.nsvmobs.entity;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

/**
 * Blocks a mob puts down for a little while (a Broodmother's webs). Each one is removed again after
 * its time is up, if it's still there and its chunk is loaded, whether or not the mob is still around.
 */
public final class TemporaryBlocks {
    private TemporaryBlocks() {}

    private record Placed(BlockPos pos, Block block, long removeAt) {}

    private static final Map<ServerLevel, List<Placed>> PLACED = new IdentityHashMap<>();

    /** Put {@code block} at {@code pos} (only into air) and take it away again after {@code ticks}. */
    static boolean place(ServerLevel level, BlockPos pos, Block block, int ticks) {
        if (!level.getBlockState(pos).isAir() || !block.defaultBlockState().canSurvive(level, pos)) return false;
        level.setBlockAndUpdate(pos, block.defaultBlockState());
        PLACED.computeIfAbsent(level, l -> new ArrayList<>()).add(new Placed(pos.immutable(), block, level.getGameTime() + ticks));
        return true;
    }

    /** Called at the end of every level tick (registered in NsvMobs). */
    public static void tick(ServerLevel level) {
        List<Placed> list = PLACED.get(level);
        if (list == null || list.isEmpty()) return;
        long now = level.getGameTime();
        list.removeIf(p -> {
            if (p.removeAt > now) return false;
            if (!level.isLoaded(p.pos)) return true;
            if (level.getBlockState(p.pos).is(p.block)) level.setBlockAndUpdate(p.pos, Blocks.AIR.defaultBlockState());
            return true;
        });
    }

    /** Take everything away now: the server is stopping, so nothing outlives a save. */
    public static void flush(ServerLevel level) {
        List<Placed> list = PLACED.remove(level);
        if (list == null) return;
        for (Placed p : list) {
            if (level.isLoaded(p.pos) && level.getBlockState(p.pos).is(p.block)) level.setBlockAndUpdate(p.pos, Blocks.AIR.defaultBlockState());
        }
    }
}
