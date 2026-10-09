package dev.nsvmobs.test;

import java.util.List;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.entity.Dripfang;
import dev.nsvmobs.entity.Hedgehog;
import dev.nsvmobs.entity.HermitCrab;
import dev.nsvmobs.entity.Meerkat;
import dev.nsvmobs.entity.MossbackTortoise;
import dev.nsvmobs.entity.Otter;
import dev.nsvmobs.entity.Sculkbones;
import dev.nsvmobs.entity.Wyrmling;
import dev.nsvmobs.registry.MobEntry;
import dev.nsvmobs.registry.MobRegistry;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.EntityTypeTags;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Spawns every catalogued mob in a lit pen (new mobs join automatically), checks each one exists
 * and has a spawn egg, photographs the lineup and every mob up close, then checks a few behaviours
 * (shearing, hiding, taming, burrowing, a scarecrow by day, a dripfang on the ceiling, a meerkat on
 * watch). Water mobs get a little glass tank. Screenshots land in build/run/clientGameTest/screenshots.
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

    static double[] spotOf(List<MobEntry<?>> mobs, EntityType<?> type) {
        for (int i = 0; i < mobs.size(); i++) {
            if (mobs.get(i).type == type) return spot(i);
        }
        throw new AssertionError("not catalogued: " + type);
    }

    /** A screenshot without leftover toasts (advancements, recipes) in the corner. */
    static void shoot(ClientGameTestContext ctx, String name) {
        ctx.runOnClient(client -> client.gui.toastManager().clear());
        ctx.takeScreenshot(name);
    }

    /** Photograph one spot from the front-right, close up. */
    static void photo(ClientGameTestContext ctx, TestSingleplayerContext world, double[] p, double dist, int pitch, String name) {
        world.getServer().runCommand(String.format("tp @a %.2f %.2f %.2f 22 %d", p[0] + dist * 0.42, p[1], p[2] - dist, pitch));
        ctx.waitTicks(8);
        shoot(ctx, name);
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
            ctx.runOnClient(client -> {
                if (!client.gui.hud.isHidden()) client.gui.hud.toggle();   // F1: no hand, hotbar or chat in the pictures
            });
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
                if (mobs.get(i).type.builtInRegistryHolder().is(EntityTypeTags.AQUATIC)) {
                    // a 2x2 glass tank of water, two deep, for swimmers
                    int x = (int) p[0], z = (int) p[2];
                    server.runCommand(String.format("fill %d -61 %d %d -59 %d glass", x - 2, z - 2, x + 1, z + 1));
                    server.runCommand(String.format("fill %d -60 %d %d -59 %d water", x - 1, z - 1, x, z));
                }
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
            compatChecks();
            shoot(ctx, "nsvmobs-01-lineup");
            server.runCommand("tp @a 0 -56 -10 0 25");
            ctx.waitTicks(10);
            shoot(ctx, "nsvmobs-02-lineup-high");

            // close-ups from the front-right
            for (int i = 0; i < mobs.size(); i++) {
                double[] p = spot(i);
                boolean tall = mobs.get(i).type.getHeight() > 1.5F;
                double dist = Math.max(tall ? 3.6 : 2.6, Math.max(mobs.get(i).type.getHeight() * 1.45, mobs.get(i).type.getWidth() * 1.9));
                server.runCommand(String.format("tp @a %.2f %.2f %.2f 22 %d", p[0] + dist * 0.42, FLOOR, p[2] - dist, tall ? 8 : 28));
                ctx.waitTicks(8);
                shoot(ctx, String.format("nsvmobs-%02d-%s", i + 3, mobs.get(i).id));
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
            // the hermit crab ducks into its shell when hurt; the hedgehog curls up, and tames with sweet berries
            server.runOnServer(srv -> {
                ServerLevel level = srv.overworld();
                HermitCrab crab = first(level, NsvEntities.HERMIT_CRAB);
                check(crab.shell() >= 0 && crab.shell() < HermitCrab.SHELLS, "crab has a valid shell");
                crab.hurtServer(level, level.damageSources().generic(), 1.0F);
                check(crab.isHiding(), "a hurt hermit crab hides");
                Hedgehog hog = first(level, NsvEntities.HEDGEHOG);
                ServerPlayer player = srv.getPlayerList().getPlayers().getFirst();
                player.setGameMode(GameType.SURVIVAL);
                for (int i = 0; i < 60 && !hog.isTame(); i++) {
                    player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.SWEET_BERRIES, 8));
                    hog.mobInteract(player, InteractionHand.MAIN_HAND);
                }
                check(hog.isTame() && hog.isOwnedBy(player), "sweet berries tame a hedgehog");
                player.setGameMode(GameType.CREATIVE);
                hog.hurtServer(level, level.damageSources().generic(), 1.0F);
                check(hog.isCurled(), "a hurt hedgehog curls into a ball");
            });
            ctx.waitTicks(10);
            server.runOnServer(srv -> check(first(srv.overworld(), NsvEntities.DUNE_SCORPION).isBurrowed(), "scorpion burrowed"));
            server.runCommand("tp @a 0 -55 -6 0 40");
            ctx.waitTicks(10);
            shoot(ctx, String.format("nsvmobs-%02d-sheared-burrowed-tamed", mobs.size() + 3));

            int shot = mobs.size() + 4;

            // Daylight scenes, set up away from the lineup (its undead burn by day; the fire is put out after).
            // A scarecrow in a wheat field can't move by day: it stands with its arms out.
            AABB field = new AABB(-32, -62, -20, -19, -55, -8);
            server.runCommand("fill -31 -61 -19 -20 -61 -9 farmland");
            server.runCommand("fill -31 -60 -19 -20 -60 -9 wheat[age=7]");
            server.runCommand("fill -26 -61 -15 -25 -61 -14 grass_block");
            server.runCommand("fill -26 -60 -15 -25 -60 -14 air");
            server.runCommand("summon nsvmobs:scarecrow -25 -60 -14 {PersistenceRequired:1b,Rotation:[0f,0f]}");
            server.runCommand("time set 6000");
            ctx.waitTicks(25);
            server.runOnServer(srv -> {
                var crows = srv.overworld().getEntities(NsvEntities.SCARECROW, field, e -> true);
                check(crows.size() == 1 && crows.getFirst().isPosing(), "a scarecrow freezes in daylight");
            });
            server.runCommand("tp @a -25 -60 -9.6 180 4");
            ctx.waitTicks(10);
            shoot(ctx, String.format("nsvmobs-%02d-scarecrow-by-day", shot++));

            // a vulture soaring overhead
            server.runCommand("summon nsvmobs:vulture -36 -53 -10 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[90f,0f]}");
            server.runCommand("tp @a -33.5 -60 -13.5 36 -50");
            ctx.waitTicks(10);
            shoot(ctx, String.format("nsvmobs-%02d-vulture-soaring", shot++));

            // babies: a penguin chick and a striped boar piglet beside their parents
            server.runCommand("fill -30 -61 8 -18 -61 14 snow_block");
            server.runCommand("summon nsvmobs:penguin -27 -60 11 {NoAI:1b,PersistenceRequired:1b,Rotation:[160f,0f]}");
            server.runCommand("summon nsvmobs:penguin -25.8 -60 10.6 {NoAI:1b,PersistenceRequired:1b,Age:-24000,Rotation:[200f,0f]}");
            server.runCommand("summon nsvmobs:wild_boar -22 -60 11 {NoAI:1b,PersistenceRequired:1b,Rotation:[160f,0f]}");
            server.runCommand("summon nsvmobs:wild_boar -20.3 -60 10.4 {NoAI:1b,PersistenceRequired:1b,Age:-24000,Rotation:[210f,0f]}");
            server.runCommand("tp @a -23.5 -59.5 6.4 0 18");
            ctx.waitTicks(15);
            shoot(ctx, String.format("nsvmobs-%02d-chick-and-piglet", shot++));

            // an otter with nothing to do in the water floats on its back at the surface
            server.runCommand("fill -29 -62 17 -25 -61 20 water");
            server.runCommand("summon nsvmobs:otter -27 -60.45 18.5 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[150f,0f]}");
            ctx.waitTicks(15);
            server.runOnServer(srv -> {
                var floaters = srv.overworld().getEntities(NsvEntities.OTTER, new AABB(-30, -63, 16, -24, -58, 21), e -> true);
                check(floaters.size() == 1 && floaters.getFirst().isFloating(), "an idle otter floats on its back");
            });
            server.runCommand("tp @a -25.6 -60 15.6 25 40");
            ctx.waitTicks(10);
            shoot(ctx, String.format("nsvmobs-%02d-otter-floating", shot++));

            // back to night; put out the lineup's sunburnt undead
            server.runCommand("time set 18000");
            server.runCommand("execute as @e[type=!player] run data merge entity @s {Fire:0s}");
            ctx.waitTicks(25);
            server.runOnServer(srv -> {
                var crows = srv.overworld().getEntities(NsvEntities.SCARECROW, field, e -> true);
                check(!crows.getFirst().isPosing(), "a scarecrow walks again at night");
            });

            // an angler in deep water, lure lit (seen from underwater)
            server.runCommand("fill 18 -63 -18 26 -61 -10 water");
            server.runCommand("summon nsvmobs:angler 22.5 -62.4 -14.5 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[0f,0f]}");
            server.runCommand("tp @a 22.5 -63 -11.4 180 12");
            ctx.waitTicks(15);
            shoot(ctx, String.format("nsvmobs-%02d-angler-deep", shot++));

            // footsteps are what a sculkbones hears; sneaking is silent
            server.runOnServer(srv -> {
                ServerPlayer player = srv.getPlayerList().getPlayers().getFirst();
                Vec3 before = player.position().add(1.0, 0.0, 0.0);
                check(Sculkbones.noisy(player, before), "sculkbones hears footsteps");
                player.setShiftKeyDown(true);
                check(!Sculkbones.noisy(player, before), "sculkbones can't hear a sneaking player");
                player.setShiftKeyDown(false);
            });

            // a dripfang hangs from a dripstone ceiling among real pointed dripstone, and drops when hit
            AABB cave = new AABB(-38, -60, -6, -28, -54, 6);
            server.runCommand("fill -38 -55 -6 -28 -55 6 dripstone_block");
            for (String cmd : List.of("setblock -35 -56 1 pointed_dripstone[vertical_direction=down,thickness=frustum]",
                    "setblock -35 -57 1 pointed_dripstone[vertical_direction=down,thickness=tip]",
                    "setblock -32 -56 -1 pointed_dripstone[vertical_direction=down,thickness=tip]",
                    "setblock -31 -56 2 pointed_dripstone[vertical_direction=down,thickness=frustum]",
                    "setblock -31 -57 2 pointed_dripstone[vertical_direction=down,thickness=tip]")) {
                server.runCommand(cmd);
            }
            server.runCommand("summon nsvmobs:dripfang -33.5 -55.55 0.5 {Hanging:1b,PersistenceRequired:1b}");
            ctx.waitTicks(10);
            server.runOnServer(srv -> {
                var hanging = srv.overworld().getEntities(NsvEntities.DRIPFANG, cave, e -> true);
                check(hanging.size() == 1 && hanging.getFirst().isHanging(), "a dripfang hangs from the ceiling");
            });
            server.runCommand("tp @a -33.5 -60 -2.6 0 -42");
            ctx.waitTicks(10);
            shoot(ctx, String.format("nsvmobs-%02d-dripfang-hanging", shot++));
            server.runOnServer(srv -> {
                ServerLevel level = srv.overworld();
                Dripfang d = level.getEntities(NsvEntities.DRIPFANG, cave, e -> true).getFirst();
                d.hurtServer(level, level.damageSources().generic(), 1.0F);
                check(!d.isHanging(), "a hurt dripfang drops from the ceiling");
            });

            // an otter tames with raw cod
            server.runOnServer(srv -> {
                ServerLevel level = srv.overworld();
                Otter otter = first(level, NsvEntities.OTTER);
                ServerPlayer player = srv.getPlayerList().getPlayers().getFirst();
                player.setGameMode(GameType.SURVIVAL);
                for (int i = 0; i < 60 && !otter.isTame(); i++) {
                    player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.COD, 8));
                    otter.mobInteract(player, InteractionHand.MAIN_HAND);
                }
                check(otter.isTame() && otter.isOwnedBy(player), "raw cod tames an otter");
                player.setGameMode(GameType.CREATIVE);
            });

            // a meerkat on watch stands up, and every monster in sight starts glowing
            server.runOnServer(srv -> first(srv.overworld(), NsvEntities.MEERKAT).setSentry(true));
            ctx.waitTicks(30);
            server.runOnServer(srv -> {
                ServerLevel level = srv.overworld();
                Meerkat m = first(level, NsvEntities.MEERKAT);
                check(m.isSentry(), "the meerkat stands watch");
                var near = level.getEntitiesOfClass(net.minecraft.world.entity.Mob.class, m.getBoundingBox().inflate(12.0),
                        e -> e instanceof net.minecraft.world.entity.monster.Enemy);
                check(!near.isEmpty() && near.stream().allMatch(e -> e.hasEffect(MobEffects.GLOWING)), "a meerkat on watch makes nearby monsters glow");
            });
            photo(ctx, world, spotOf(mobs, NsvEntities.MEERKAT), 2.2, 20, String.format("nsvmobs-%02d-meerkat-on-watch", shot++));

            // a lost miner walled in with stone digs through to reach a villager 5 blocks away
            for (String cmd : List.of("fill 30 -61 -2 38 -57 2 stone", "fill 31 -60 0 31 -59 0 air", "fill 36 -60 0 36 -59 0 air",
                    "summon nsvmobs:lost_miner 31.5 -60 0.5 {PersistenceRequired:1b}",
                    "summon minecraft:villager 36.5 -60 0.5 {NoAI:1b,PersistenceRequired:1b}")) {
                server.runCommand(cmd);
            }
            ctx.waitTicks(5);
            // it spotted the villager before the wall went up (zombies forget unseen targets; miners don't)
            server.runOnServer(srv -> {
                ServerLevel level = srv.overworld();
                AABB cell = new AABB(29, -62, -3, 39, -55, 3);
                var miner = level.getEntities(NsvEntities.LOST_MINER, cell, e -> true).getFirst();
                var villager = level.getEntities(net.minecraft.world.entity.EntityTypes.VILLAGER, cell, e -> true).getFirst();
                miner.setTarget(villager);
            });
            ctx.waitTicks(500);
            boolean dug = server.computeOnServer(srv -> {
                ServerLevel level = srv.overworld();
                int open = 0;
                for (int x = 32; x <= 35; x++) {
                    if (level.getBlockState(new BlockPos(x, -60, 0)).isAir() || level.getBlockState(new BlockPos(x, -59, 0)).isAir()) open++;
                }
                return open >= 2;
            });
            check(dug, "a walled-in lost miner tunnels toward its target");
            server.runCommand("fill 30 -58 -2 38 -57 2 air");   // lift the lid to show the tunnel
            server.runCommand("tp @a 33.5 -54 0.5 90 90");   // straight down onto the dug row
            ctx.waitTicks(10);
            shoot(ctx, String.format("nsvmobs-%02d-lost-miner-tunnel", shot++));

            ChallengerScenes.run(ctx, world, shot);
        }
    }

    /**
     * Only in a modpack run (-PcompatMods=...): with the Village Friends RPG add-on loaded, its
     * Bestiary must file each mob under the family the catalogue gives it, and nothing else.
     */
    static void compatChecks() {
        var loader = net.fabricmc.loader.api.FabricLoader.getInstance();
        System.out.println("[nsvmobs-test] villagefriends loaded: " + loader.isModLoaded("villagefriends")
                + ", villagefriends_rpg loaded: " + loader.isModLoaded("villagefriends_rpg"));
        if (!loader.isModLoaded("villagefriends_rpg")) return;
        try {
            var ofMob = Class.forName("dev.villagefriends.rpg.Bestiary").getMethod("ofMob", String.class);
            for (MobEntry<?> m : MobRegistry.all()) {
                Object family = ofMob.invoke(null, m.id);
                String id = family == null ? null : (String) family.getClass().getMethod("id").invoke(family);
                check(java.util.Objects.equals(id, m.rpgFamily()), "RPG Bestiary files " + m.id + " under " + id + ", expected " + m.rpgFamily());
            }
            Object zombie = ofMob.invoke(null, "zombie");
            check(zombie != null && "zombie".equals(zombie.getClass().getMethod("id").invoke(zombie)), "vanilla zombies still map to Zombies");
            System.out.println("[nsvmobs-test] RPG Bestiary compat OK for " + MobRegistry.all().size() + " mobs");
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("couldn't query the RPG Bestiary", e);
        }
    }

    static <T extends Entity> T first(ServerLevel level, EntityType<T> type) {
        List<? extends T> all = level.getEntities(type, PEN, e -> true);
        check(!all.isEmpty(), "no " + type);
        return all.getFirst();
    }
}
