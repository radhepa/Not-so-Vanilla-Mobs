package dev.nsvmobs.test;

import java.util.List;
import java.util.function.Predicate;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.entity.Cheetah;
import dev.nsvmobs.entity.Elephant;
import dev.nsvmobs.entity.Kangaroo;
import dev.nsvmobs.entity.MantaRay;
import dev.nsvmobs.entity.OrchidMantis;
import dev.nsvmobs.registry.MobRegistry;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.AABB;

import static dev.nsvmobs.test.ShowcaseClientTest.check;
import static dev.nsvmobs.test.ShowcaseClientTest.photo;
import static dev.nsvmobs.test.ShowcaseClientTest.player;
import static dev.nsvmobs.test.ShowcaseClientTest.shoot;
import static dev.nsvmobs.test.ShowcaseClientTest.tame;

/**
 * The 1.5 mobs in action, west of the pen (x -79 to -55, z -14 to 44), on ground the 1.4 scenes
 * have already cleared: a cheetah runs down a rabbit and is left panting, a tamed cheetah paces a
 * sprinting player (real key presses), an elephant hoses down a burning pig, a buck squares up to
 * box while a frightened doe's joey dives into her pouch, an orchid mantis snags a survival player
 * who walks up to it, a manta ray carries its rider along a pool and breaches, and then all five
 * run loose in a paddock. Everything is cleared again afterwards.
 */
@SuppressWarnings("UnstableApiUsage")
final class SafariScenes {
    private SafariScenes() {}

    static final AABB ZONE = new AABB(-80, -66, -15, -54, -40, 45);

    static <T extends Entity> T only(ServerLevel level, EntityType<T> type, AABB box, Predicate<T> filter) {
        List<? extends T> all = level.getEntities(type, box, filter::test);
        check(all.size() == 1, "expected one " + type + " in " + box + ", found " + all.size());
        return all.getFirst();
    }

    static AABB around(double x, double z, double r) {
        return new AABB(x - r, -64, z - r, x + r, -50, z + r);
    }

    /** Tick until {@code cond} holds on the server (true), or give up after {@code max} ticks (false). */
    static boolean waitFor(ClientGameTestContext ctx, TestServerContext server, Predicate<MinecraftServer> cond, int max) {
        for (int t = 0; t < max; t++) {
            if (server.computeOnServer(cond::test)) return true;
            ctx.waitTicks(1);
        }
        return server.computeOnServer(cond::test);
    }

    static int run(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        server.runCommand("kill @e[type=!player,x=-80,y=-66,z=-15,dx=26,dy=26,dz=60]");
        server.runCommand("fill -79 -60 -14 -55 -50 44 air");
        server.runCommand("fill -79 -61 -14 -55 -61 44 grass_block");
        server.runCommand("time set 6000");

        shot = cheetahs(ctx, world, shot);
        shot = elephant(ctx, world, shot);
        shot = kangaroos(ctx, world, shot);
        shot = mantis(ctx, world, shot);
        shot = manta(ctx, world, shot);
        shot = paddock(ctx, world, shot);

        server.runCommand("kill @e[type=!player,x=-80,y=-66,z=-15,dx=26,dy=26,dz=60]");
        server.runCommand("time set 18000");
        server.runCommand("tp @a 0 -60 -8 0 12");   // back to the pen; let its chunks tick again
        ctx.waitTicks(40);
        return shot;
    }

    /** A wild cheetah runs down a rabbit and is winded after; a tamed one paces its sprinting owner. */
    static int cheetahs(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        AABB strip = new AABB(-79, -64, 33, -55, -55, 39);
        server.runCommand("summon nsvmobs:cheetah -76.5 -60 36.5 {PersistenceRequired:1b,Rotation:[-90f,0f]}");
        server.runCommand("summon minecraft:rabbit -64.5 -60 36.5 {NoAI:1b,PersistenceRequired:1b}");
        server.runCommand("tp @a -70.5 -58 27.5 0 20");   // 9 blocks off, so the shy cat doesn't mind
        ctx.waitTicks(10);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Cheetah c = only(level, NsvEntities.CHEETAH, strip, e -> true);
            c.huntNow(only(level, EntityTypes.RABBIT, strip, e -> true));
        });
        ctx.waitTicks(12);
        shoot(ctx, String.format("nsvmobs-%02d-cheetah-hunting", shot++));
        boolean caught = waitFor(ctx, server, srv -> srv.overworld().getEntities(EntityTypes.RABBIT, strip, LivingEntity::isAlive).isEmpty(), 150);
        check(caught, "a cheetah runs down a rabbit");
        ctx.waitTicks(10);
        double[] at = server.computeOnServer(srv -> {
            Cheetah c = only(srv.overworld(), NsvEntities.CHEETAH, strip, e -> true);
            check(c.isWinded() && c.mode() == Cheetah.WINDED, "a cheetah is winded after its sprint (mode " + c.mode() + ")");
            return new double[]{c.getX(), c.getY(), c.getZ()};
        });
        photo(ctx, world, at, 2.6, 18, String.format("nsvmobs-%02d-cheetah-winded", shot++));

        // a tamed cheetah bolts alongside its sprinting owner: Speed II
        AABB lane = new AABB(-79, -64, 40, -55, -55, 44);
        server.runCommand("summon nsvmobs:cheetah -76.5 -60 41.5 {PersistenceRequired:1b,Rotation:[-90f,0f]}");
        server.runCommand("tp @a -76.5 -60 42.5 -90 0");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerPlayer player = player(srv);
            Cheetah c = only(srv.overworld(), NsvEntities.CHEETAH, lane, e -> true);
            check(tame(player, c, Items.CHICKEN), "raw chicken tames a cheetah");
            c.setOrderedToSit(false);
            c.setInSittingPose(false);
            player.removeEffect(MobEffects.SPEED);
        });
        ctx.waitTicks(5);
        ctx.runOnClient(client -> {
            client.player.setYRot(-90.0F);
            client.player.setXRot(10.0F);
        });
        ctx.getInput().holdKey(o -> o.keySprint);
        ctx.getInput().holdKeyFor(o -> o.keyUp, 30);
        server.runOnServer(srv -> {
            ServerPlayer player = player(srv);
            check(player.hasEffect(MobEffects.SPEED) && player.getEffect(MobEffects.SPEED).getAmplifier() == 1,
                    "a tamed cheetah gives its sprinting owner Speed II");
        });
        ctx.getInput().releaseKey(o -> o.keySprint);
        // sit it down: left following, it would trail the camera into every later scene (and defend it)
        server.runOnServer(srv -> only(srv.overworld(), NsvEntities.CHEETAH, lane.inflate(12), e -> e.isTame()).setOrderedToSit(true));
        server.runCommand("tp @a -64 -58 37.5 160 25");
        ctx.waitTicks(8);
        shoot(ctx, String.format("nsvmobs-%02d-cheetah-sprint-partner", shot++));
        return shot;
    }

    /** An elephant with a trunkful of water hoses down a burning pig, then squares up when hurt. */
    static int elephant(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        AABB yard = around(-68.5, 4.5, 6);
        server.runCommand("summon nsvmobs:elephant -70.5 -60 4.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[-90f,0f]}");
        server.runCommand("summon nsvmobs:elephant -72.5 -60 7.5 {NoAI:1b,PersistenceRequired:1b,Age:-24000,Rotation:[-60f,0f]}");
        server.runCommand("summon minecraft:pig -66.5 -60 4.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[90f,0f]}");
        server.runCommand("tp @a -66 -59 -2.5 -20 15");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            only(level, EntityTypes.PIG, yard, e -> true).igniteForSeconds(8.0F);
            only(level, NsvEntities.ELEPHANT, yard, e -> !e.isBaby()).fillTrunk();
        });
        check(waitFor(ctx, server, srv -> only(srv.overworld(), NsvEntities.ELEPHANT, yard, e -> !e.isBaby()).isSpraying(), 30),
                "an elephant with water sprays at a burning pig");
        ctx.waitTicks(3);
        shoot(ctx, String.format("nsvmobs-%02d-elephant-spraying", shot++));
        check(waitFor(ctx, server, srv -> !only(srv.overworld(), EntityTypes.PIG, yard, e -> true).isOnFire(), 30),
                "an elephant's spray puts out a burning pig");
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Elephant e = only(level, NsvEntities.ELEPHANT, yard, x -> !x.isBaby());
            check(!e.hasWater(), "the spray empties the elephant's trunk");
            e.hurtServer(level, level.damageSources().playerAttack(player(srv)), 1.0F);
            check(e.isThreatening(), "a hurt elephant flares its ears and trumpets");
        });
        ctx.waitTicks(5);
        photo(ctx, world, new double[]{-70.5, -60, 4.5}, 6.0, 8, String.format("nsvmobs-%02d-elephant-threat", shot++));
        return shot;
    }

    /** A hurt buck boxes; a frightened doe's joey hops into her pouch. */
    static int kangaroos(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        AABB mob = around(-59, -6.5, 5);
        server.runCommand("summon nsvmobs:kangaroo -61.5 -60 -6.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[-30f,0f]}");
        server.runCommand("summon nsvmobs:kangaroo -60.3 -60 -5.2 {NoAI:1b,PersistenceRequired:1b,Age:-24000,Rotation:[-10f,0f]}");
        server.runCommand("summon nsvmobs:kangaroo -56.5 -60 -6.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[30f,0f]}");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            ServerPlayer player = player(srv);
            List<? extends Kangaroo> adults = level.getEntities(NsvEntities.KANGAROO, mob, e -> !e.isBaby());
            check(adults.size() == 2, "two grown kangaroos (" + adults.size() + ")");
            Kangaroo doe = adults.stream().min((a, b) -> Double.compare(a.getX(), b.getX())).orElseThrow();
            Kangaroo buck = adults.stream().max((a, b) -> Double.compare(a.getX(), b.getX())).orElseThrow();
            doe.setBuck(false);
            buck.setBuck(true);
            buck.hurtServer(level, level.damageSources().playerAttack(player), 1.0F);
            check(buck.isBoxing(), "a hurt buck rears up to box");
            doe.hurtServer(level, level.damageSources().playerAttack(player), 1.0F);
            check(!doe.isBoxing(), "a hurt doe doesn't box");
        });
        check(waitFor(ctx, server, srv -> {
            ServerLevel level = srv.overworld();
            Kangaroo joey = only(level, NsvEntities.KANGAROO, mob, Kangaroo::isBaby);
            return joey.getVehicle() instanceof Kangaroo mum && !mum.isBuck();
        }, 40), "a frightened doe's joey hops into her pouch");
        photo(ctx, world, new double[]{-59, -60, -6.5}, 4.6, 10, String.format("nsvmobs-%02d-kangaroo-boxing-and-pouch", shot++));
        return shot;
    }

    /** A survival player who walks up to an orchid mantis among the petals is struck and snagged. */
    static int mantis(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        AABB bed = around(-70.5, -8.5, 4);
        server.runCommand("fill -74 -60 -12 -67 -60 -5 pink_petals[flower_amount=4]");
        server.runCommand("setblock -71 -60 -9 air");
        server.runCommand("summon nsvmobs:orchid_mantis -70.5 -60 -8.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[0f,0f]}");
        server.runCommand("tp @a -69.2 -59 -12.2 25 22");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-orchid-mantis-hiding", shot++));
        server.runCommand("tp @a -70.5 -60 -6.9 180 10");
        server.runCommand("gamemode survival @a");
        ctx.waitTicks(25);
        server.runOnServer(srv -> {
            ServerPlayer player = player(srv);
            OrchidMantis m = only(srv.overworld(), NsvEntities.ORCHID_MANTIS, bed, e -> true);
            check(player.getHealth() < player.getMaxHealth(), "an orchid mantis strikes a player who walks up to it");
            check(m.action() == OrchidMantis.SNAG || m.action() == OrchidMantis.THREAT,
                    "a striking orchid mantis snags its victim, then flares its wings (action " + m.action() + ")");
        });
        server.runCommand("gamemode creative @a");
        server.runOnServer(srv -> player(srv).setHealth(player(srv).getMaxHealth()));
        waitFor(ctx, server, srv -> only(srv.overworld(), NsvEntities.ORCHID_MANTIS, bed, e -> true).action() == OrchidMantis.THREAT, 40);
        photo(ctx, world, new double[]{-70.5, -60, -8.5}, 2.4, 20, String.format("nsvmobs-%02d-orchid-mantis-threat", shot++));
        return shot;
    }

    /** A rider steers a manta ray along a pool with real key presses; an unridden one breaches. */
    static int manta(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        AABB pool = new AABB(-79, -65, 15, -55, -50, 22);
        server.runCommand("fill -78 -63 16 -56 -61 20 water");
        server.runCommand("summon nsvmobs:manta_ray -75.5 -62.3 18.5 {PersistenceRequired:1b,Rotation:[-90f,0f]}");
        server.runCommand("tp @a -75.5 -61.5 18.5 -90 0");
        ctx.waitTicks(5);
        server.runCommand("execute positioned -75.5 -62 18.5 run ride @p mount @e[type=nsvmobs:manta_ray,limit=1,sort=nearest]");
        ctx.waitTicks(10);
        double startX = server.computeOnServer(srv -> {
            MantaRay m = only(srv.overworld(), NsvEntities.MANTA_RAY, pool, e -> true);
            check(player(srv).getVehicle() == m, "the player holds on to the manta ray");
            return m.getX();
        });
        ctx.runOnClient(client -> {
            client.player.setYRot(-90.0F);
            client.player.setXRot(0.0F);
            client.options.setCameraType(CameraType.THIRD_PERSON_BACK);
        });
        ctx.getInput().holdKeyFor(o -> o.keyUp, 40);
        double ridden = server.computeOnServer(srv -> only(srv.overworld(), NsvEntities.MANTA_RAY, pool, e -> true).getX());
        check(ridden - startX > 6.0, String.format("a ridden manta ray swims where its rider looks (x %.2f -> %.2f)", startX, ridden));
        shoot(ctx, String.format("nsvmobs-%02d-manta-ray-ride", shot++));
        ctx.runOnClient(client -> client.options.setCameraType(CameraType.FIRST_PERSON));
        server.runCommand("ride @p dismount");

        // an unridden manta just under the surface leaps clear of the water
        server.runCommand("tp @a -61.5 -59 11.5 40 8");   // from the bank, looking at the leap
        server.runOnServer(srv -> {
            MantaRay m = only(srv.overworld(), NsvEntities.MANTA_RAY, pool, e -> true);
            m.teleportTo(-66.5, -61.4, 18.5);
            m.setDeltaMovement(0, 0, 0);
            m.breach();
        });
        check(waitFor(ctx, server, srv -> {
            MantaRay m = only(srv.overworld(), NsvEntities.MANTA_RAY, pool, e -> true);
            return m.isBreaching() && m.getY() > -60.0;
        }, 15), "a manta ray breaches clear of the water");
        shoot(ctx, String.format("nsvmobs-%02d-manta-ray-breach", shot++));
        ctx.waitTicks(40);
        return shot;
    }

    /**
     * All five with their AI on, two of each (a baby among them), in a fenced paddock around the
     * pool: first in creative, then in survival with full Resistance so the neutral ones react.
     * Nothing may crash, and at least one of each survives.
     */
    static int paddock(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        AABB paddock = new AABB(-79, -65, -14, -55, -40, 23);
        server.runCommand("kill @e[type=!player,x=-80,y=-66,z=-15,dx=26,dy=26,dz=60]");
        server.runCommand("kill @e[type=item,x=-80,y=-66,z=-15,dx=26,dy=26,dz=60]");   // what the killed scene mobs dropped
        server.runCommand("fill -79 -60 -14 -55 -60 22 oak_fence");
        server.runCommand("fill -78 -60 -13 -56 -60 21 air");
        String[] ids = {"cheetah", "elephant", "kangaroo", "orchid_mantis"};
        for (int i = 0; i < ids.length; i++) {
            for (int k = 0; k < 2; k++) {
                server.runCommand(String.format("summon nsvmobs:%s %.1f -60 %.1f {PersistenceRequired:1b%s}", ids[i],
                        -75.5 + i * 5.5, -10.5 + k * 9, k == 1 && i < 3 ? ",Age:-24000" : ""));
            }
        }
        server.runCommand("summon nsvmobs:manta_ray -72.5 -62.3 18.5 {PersistenceRequired:1b}");
        server.runCommand("summon nsvmobs:manta_ray -62.5 -62.3 18.5 {PersistenceRequired:1b}");
        server.runCommand("tp @a -67 -60 4 0 0");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            Cheetah c = srv.overworld().getEntities(NsvEntities.CHEETAH, paddock, e -> !e.isBaby()).getFirst();
            check(tame(player(srv), c, Items.RABBIT), "a paddock cheetah tames with raw rabbit");
            c.setOrderedToSit(false);
        });
        ctx.waitTicks(200);
        server.runCommand("effect give @a resistance infinite 4 true");
        server.runCommand("gamemode survival @a");
        server.runCommand("tp @a -60 -60 -8 90 0");
        ctx.waitTicks(100);
        server.runCommand("tp @a -74 -60 10 -90 0");
        ctx.waitTicks(100);
        server.runCommand("gamemode creative @a");
        server.runCommand("effect clear @a minecraft:resistance");
        server.runCommand("effect clear @a minecraft:speed");
        server.runCommand("effect give @a night_vision infinite 0 true");
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            for (String id : List.of("cheetah", "elephant", "kangaroo", "orchid_mantis", "manta_ray")) {
                EntityType<?> type = MobRegistry.all().stream().filter(m -> m.id.equals(id)).findFirst().orElseThrow().type;
                int alive = level.getEntities(type, paddock.inflate(16), Entity::isAlive).size();
                check(alive >= 1, "the paddock still has a " + id + " after the AI run (" + alive + ")");
            }
        });
        server.runCommand("tp @a -67 -52 -20 0 35");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-safari-paddock", shot++));
        return shot;
    }
}
