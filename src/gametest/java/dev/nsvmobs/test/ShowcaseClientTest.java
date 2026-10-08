package dev.nsvmobs.test;

import java.util.List;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.entity.MossbackTortoise;
import dev.nsvmobs.entity.Wyrmling;
import dev.nsvmobs.registry.MobEntry;
import dev.nsvmobs.registry.MobRegistry;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.AABB;

/**
 * Spawns every catalogued mob in a lit pen (new mobs join automatically), checks each one exists
 * and has a spawn egg, photographs the lineup and every mob up close, then checks a few behaviours
 * (shearing, hiding, taming, burrowing). Screenshots land in build/run/clientGameTest/screenshots.
 *   gradlew runClientGameTest -PtestHeap=2g
 */
@SuppressWarnings("UnstableApiUsage")
public class ShowcaseClientTest implements FabricClientGameTest {
    static final int PER_ROW = 5;
    static final double SPACING = 4.0, FLOOR = -60;
    static final AABB PEN = new AABB(-40, -70, -20, 40, -40, 60);

    static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError(what);
    }

    /** Where the i-th mob stands: rows of five, the camera at z = -8 looking +z. */
    static double[] spot(int i) {
        int row = i / PER_ROW, col = i % PER_ROW;
        return new double[]{(col - (PER_ROW - 1) / 2.0) * SPACING, FLOOR, 1 + row * SPACING};
    }

    @Override
    public void runTest(ClientGameTestContext ctx) {
        String only = System.getProperty("nsvmobs.tests");
        if (only != null && !only.isBlank() && !List.of(only.split(",")).contains("Showcase")) return;
        List<MobEntry<?>> mobs = MobRegistry.all();
        int rows = (mobs.size() + PER_ROW - 1) / PER_ROW;
        double back = 1 + rows * SPACING;
        ctx.getInput().resizeWindow(1600, 900);
        try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
            world.getConnection().waitForChunksRender();
            var server = world.getServer();
            for (String cmd : List.of("gamemode creative @a", "gamerule advance_time false", "gamerule advance_weather false",
                    "gamerule spawn_mobs false", "time set 18000", "weather clear",
                    "effect give @a night_vision infinite 0 true", "tp @a 0 -60 -8 0 12",
                    "fill -14 -61 -6 14 -61 " + (int) back + " grass_block", "fill -14 -60 -6 14 -50 " + (int) back + " air",
                    "fill -14 -60 " + (int) back + " 14 -57 " + (int) back + " mossy_cobblestone", "kill @e[type=!player]")) {
                server.runCommand(cmd);
            }
            ctx.waitTicks(20);
            for (int i = 0; i < mobs.size(); i++) {
                double[] p = spot(i);
                // NoGravity keeps fliers in the air; ground mobs stand where they're put either way
                server.runCommand(String.format("summon nsvmobs:%s %.1f %.1f %.1f {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[180f,0f]}",
                        mobs.get(i).id, p[0], p[1] + (mobs.get(i).type.getHeight() < 0.7F ? 0.5 : 0.0), p[2]));
            }
            world.getConnection().waitForClientboundEntityUpdates(mobs.getLast().type);
            ctx.waitTicks(40);

            for (MobEntry<?> m : mobs) {
                EntityType<?> type = m.type;
                int found = server.computeOnServer(srv -> srv.overworld().getEntities(type, PEN, e -> true).size());
                check(found == 1, m.id + " spawned (found " + found + ")");
                check(m.spawnEgg() != null, m.id + " has a spawn egg");
            }
            ctx.takeScreenshot("nsvmobs-01-lineup");
            server.runCommand("tp @a 0 -56 -10 0 25");
            ctx.waitTicks(10);
            ctx.takeScreenshot("nsvmobs-02-lineup-high");

            // close-ups from the front-right
            for (int i = 0; i < mobs.size(); i++) {
                double[] p = spot(i);
                boolean tall = mobs.get(i).type.getHeight() > 1.5F;
                double dist = tall ? 3.6 : 2.6;
                server.runCommand(String.format("tp @a %.2f %.2f %.2f 22 %d", p[0] + dist * 0.42, FLOOR, p[2] - dist, tall ? 8 : 28));
                ctx.waitTicks(8);
                ctx.takeScreenshot(String.format("nsvmobs-%02d-%s", i + 3, mobs.get(i).id));
            }

            // behaviour checks
            server.runOnServer(srv -> {
                ServerLevel level = srv.overworld();
                MossbackTortoise t = first(level, NsvEntities.MOSSBACK_TORTOISE);
                check(t.readyForShearing(), "tortoise starts with a garden");
                t.shear(level, SoundSource.PLAYERS, new ItemStack(Items.SHEARS));
                check(t.isSheared() && !t.readyForShearing(), "shearing strips the garden");
                t.hurtServer(level, level.damageSources().generic(), 1.0F);
                check(t.isHiding(), "a hurt tortoise hides in its shell");
            });
            server.runCommand("data merge entity @e[type=nsvmobs:dune_scorpion,limit=1] {Burrowed:1b}");
            server.runOnServer(srv -> {
                ServerLevel level = srv.overworld();
                ServerPlayer player = srv.getPlayerList().getPlayers().getFirst();
                Wyrmling w = first(level, NsvEntities.WYRMLING);
                player.setGameMode(GameType.SURVIVAL);
                for (int i = 0; i < 60 && !w.isTame(); i++) {
                    player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.BLAZE_POWDER, 8));
                    w.mobInteract(player, InteractionHand.MAIN_HAND);
                }
                check(w.isTame() && w.isOwnedBy(player), "blaze powder tames a wyrmling");
                check(w.isOrderedToSit(), "a freshly tamed wyrmling sits");
                player.setGameMode(GameType.CREATIVE);
            });
            ctx.waitTicks(10);
            server.runOnServer(srv -> check(first(srv.overworld(), NsvEntities.DUNE_SCORPION).isBurrowed(), "scorpion burrowed"));
            server.runCommand("tp @a 0 -55 -6 0 40");
            ctx.waitTicks(10);
            ctx.takeScreenshot(String.format("nsvmobs-%02d-sheared-burrowed-tamed", mobs.size() + 3));
        }
    }

    static <T extends Entity> T first(ServerLevel level, EntityType<T> type) {
        List<? extends T> all = level.getEntities(type, PEN, e -> true);
        check(!all.isEmpty(), "no " + type);
        return all.getFirst();
    }
}
