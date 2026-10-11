package dev.nsvmobs.test;

import java.util.List;

import dev.nsvmobs.entity.Cinderhulk;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.world.phys.AABB;

import static dev.nsvmobs.test.ShowcaseClientTest.check;
import static dev.nsvmobs.test.ShowcaseClientTest.shoot;

/**
 * A Cinderhulk walks on lava as a strider does. One dropped into a lava pool six deep comes to rest
 * standing on the top, and one put on the pool's floor rises back up to it. Both are then watched for
 * three seconds, AI on: their feet must stay half a block into the top lava block, the strider's
 * footing, without sinking or hopping. (In 26.3 a lava top only holds up a mob with a liquid collision
 * shape as well as canStandOnFluid.) The screenshot lands in build/run/clientGameTest/screenshots.
 *   gradlew runClientGameTest -PtestHeap=2g -PnsvTests=Lava
 */
@SuppressWarnings("UnstableApiUsage")
public class LavaClientTest implements FabricClientGameTest {
    /** The top lava block of the pool; its lava runs from y -60 (on the floor at -61) up to here. */
    static final int POOL_TOP = -55;
    static final double FEET = POOL_TOP + 0.5;

    @Override
    public void runTest(ClientGameTestContext ctx) {
        String only = System.getProperty("nsvmobs.tests");
        if (only != null && !only.isBlank() && !List.of(only.split(",")).contains("Lava")) return;
        ctx.getInput().resizeWindow(1600, 900);
        try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
            world.getConnection().waitForChunksRender();
            ctx.runOnClient(client -> {
                if (!client.gui.hud.isHidden()) client.gui.hud.toggle();
            });
            TestServerContext server = world.getServer();
            // a basalt pool 9 by 7 and six deep, walled three blocks above the lava so nothing climbs out;
            // the wall facing the camera is glass above the lava, so the photo shows them standing on it
            for (String cmd : List.of("gamemode creative @a", "gamerule advance_time false", "gamerule advance_weather false",
                    "gamerule spawn_mobs false", "time set 6000", "weather clear", "kill @e[type=!player]",
                    "fill 3 -61 3 13 " + (POOL_TOP + 3) + " 11 basalt", "fill 4 -60 4 12 " + (POOL_TOP + 3) + " 10 air",
                    "fill 4 -60 4 12 " + POOL_TOP + " 10 lava", "fill 3 " + (POOL_TOP + 1) + " 3 13 " + (POOL_TOP + 3) + " 3 glass",
                    "setblock 8 " + (POOL_TOP + 1) + " -2 barrier", "tp @a 8.5 " + (POOL_TOP + 2) + " -1.5 0 18")) {
                server.runCommand(cmd);
            }
            ctx.waitTicks(20);
            // one dropped in from four blocks up, one stood on the pool floor
            server.runCommand("summon nsvmobs:cinderhulk 6.0 " + (POOL_TOP + 4) + " 7.0 {PersistenceRequired:1b,Rotation:[180f,0f]}");
            server.runCommand("summon nsvmobs:cinderhulk 11.0 -60 7.0 {PersistenceRequired:1b,Rotation:[180f,0f]}");
            AABB pool = new AABB(3, -62, 3, 14, POOL_TOP + 8, 12);
            ctx.waitTicks(100);
            // then watched every tick for three seconds: both on the top, none sunk, none hopping
            double low = Double.MAX_VALUE, high = -Double.MAX_VALUE;
            for (int i = 0; i < 60; i++) {
                double[] ys = server.computeOnServer(srv -> srv.overworld().getEntitiesOfClass(Cinderhulk.class, pool, Cinderhulk::isAlive)
                        .stream().mapToDouble(Cinderhulk::getY).toArray());
                check(ys.length == 2, "two cinderhulks alive in the pool, found " + ys.length);
                for (double y : ys) {
                    low = Math.min(low, y);
                    high = Math.max(high, y);
                }
                ctx.waitTicks(1);
            }
            System.out.printf("[nsvmobs-test] cinderhulks on lava: feet between %.3f and %.3f (lava top block %d, footing %.1f)%n",
                    low, high, POOL_TOP, FEET);
            check(low > FEET - 0.05, String.format("every cinderhulk is up on the lava top, lowest feet at %.3f (want %.1f)", low, FEET));
            check(high < FEET + 0.05, String.format("no cinderhulk hops on the lava, highest feet at %.3f (want %.1f)", high, FEET));
            shoot(ctx, "nsvmobs-lava-cinderhulks");
        }
    }
}
