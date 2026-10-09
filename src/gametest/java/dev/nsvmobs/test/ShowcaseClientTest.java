package dev.nsvmobs.test;

import java.util.List;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.entity.Beaver;
import dev.nsvmobs.entity.Chameleon;
import dev.nsvmobs.entity.Dripfang;
import dev.nsvmobs.entity.Goose;
import dev.nsvmobs.entity.Griffin;
import dev.nsvmobs.entity.Hedgehog;
import dev.nsvmobs.entity.HermitCrab;
import dev.nsvmobs.entity.Meerkat;
import dev.nsvmobs.entity.MossbackTortoise;
import dev.nsvmobs.entity.Ostrich;
import dev.nsvmobs.entity.Otter;
import dev.nsvmobs.entity.Sculkbones;
import dev.nsvmobs.entity.Seal;
import dev.nsvmobs.entity.Wyrmling;
import dev.nsvmobs.entity.Yak;
import dev.nsvmobs.registry.MobEntry;
import dev.nsvmobs.registry.MobRegistry;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.EntityTypeTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.MapColor;
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
                double dist = tall ? 3.6 : 2.6;
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

            shot = newcomers(ctx, world, mobs, shot);

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
            shoot(ctx, String.format("nsvmobs-%02d-lost-miner-tunnel", shot));
        }
    }

    /** Feed a wild pet its taming food (as a survival player) until it's tamed; false if it never took. */
    static boolean tame(ServerPlayer player, TamableAnimal pet, Item food) {
        player.setGameMode(GameType.SURVIVAL);
        for (int i = 0; i < 80 && !pet.isTame(); i++) {
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(food, 8));
            pet.mobInteract(player, InteractionHand.MAIN_HAND);
        }
        player.setGameMode(GameType.CREATIVE);
        return pet.isTame() && pet.isOwnedBy(player);
    }

    static ServerPlayer player(net.minecraft.server.MinecraftServer srv) {
        return srv.getPlayerList().getPlayers().getFirst();
    }

    /** Stand the player a little in front of a lineup mob. */
    static void standBy(TestSingleplayerContext world, double[] p, double dx, double dz) {
        world.getServer().runCommand(String.format("tp @a %.2f %.2f %.2f 0 0", p[0] + dx, FLOOR, p[2] + dz));
    }

    /**
     * The 1.4 friendly, neutral and tamable mobs: a yak's warm coat and shearing, a hummingbird's
     * pollen, a seal's snowball, a beaver's gnawing, a skunk's spray, a rattlesnake's warning, a cinder
     * newt on lava, the tamable pets and their gifts, a saddled ostrich, carried items, and a
     * nursery of babies. Returns the next screenshot number.
     */
    static int newcomers(ClientGameTestContext ctx, TestSingleplayerContext world, List<MobEntry<?>> mobs, int shot) {
        var server = world.getServer();

        // a yak's long coat keeps a player beside it from freezing; shearing takes the coat off
        standBy(world, spotOf(mobs, NsvEntities.YAK), 1.6, -1.0);
        ctx.waitTicks(2);
        server.runOnServer(srv -> player(srv).setTicksFrozen(140));
        ctx.waitTicks(3);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            int frozen = player(srv).getTicksFrozen();
            check(frozen < 20, "a yak's coat keeps the player beside it warm (frozen ticks " + frozen + ")");
            Yak yak = first(level, NsvEntities.YAK);
            check(yak.readyForShearing(), "a yak starts with its long coat");
            yak.shear(level, SoundSource.PLAYERS, new ItemStack(Items.SHEARS));
            check(yak.isSheared() && !yak.readyForShearing(), "shearing takes the yak's coat");
        });
        photo(ctx, world, spotOf(mobs, NsvEntities.YAK), 3.2, 15, String.format("nsvmobs-%02d-yak-sheared", shot++));

        // a hummingbird over a wheat patch grows the wheat around it
        for (String cmd : List.of("fill 20 -61 24 24 -61 28 farmland", "fill 20 -60 24 24 -60 28 wheat[age=0]",
                "setblock 22 -60 26 air", "summon nsvmobs:hummingbird 22.5 -59.4 26.5 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[160f,0f]}")) {
            server.runCommand(cmd);
        }
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            var birds = level.getEntities(NsvEntities.HUMMINGBIRD, new AABB(19, -62, 23, 26, -56, 30), e -> true);
            check(birds.size() == 1, "the wheat-patch hummingbird is there");
            check(birds.getFirst().pollinateAround(level), "a hummingbird pollinates the crops around it");
            int grown = 0;
            for (BlockPos pos : BlockPos.betweenClosed(20, -60, 24, 24, -60, 28)) {
                BlockState st = level.getBlockState(pos);
                if (st.getBlock() instanceof CropBlock crop && crop.getAge(st) > 0) grown++;
            }
            check(grown > 0, "pollination grows the wheat around a hummingbird");
        });
        server.runCommand("tp @a 23.4 -60 23.4 25 30");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-hummingbird-wheat", shot++));

        // a seal catches a snowball on its nose
        server.runOnServer(srv -> {
            Seal seal = first(srv.overworld(), NsvEntities.SEAL);
            seal.catchSnowball(player(srv));
            check(seal.isBalancing(), "a seal catches a snowball on its nose");
        });
        photo(ctx, world, spotOf(mobs, NsvEntities.SEAL), 2.4, 18, String.format("nsvmobs-%02d-seal-snowball", shot++));

        // a beaver gnaws the log beside it into a stripped log
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Beaver beaver = first(level, NsvEntities.BEAVER);
            BlockPos log = BlockPos.containing(beaver.getX(), FLOOR, beaver.getZ()).east();
            level.setBlockAndUpdate(log, Blocks.OAK_LOG.defaultBlockState());
            check(beaver.gnawNearbyLog(level), "a beaver gnaws a log beside it");
            check(level.getBlockState(log).is(Blocks.STRIPPED_OAK_LOG), "a gnawed log is stripped");
        });
        photo(ctx, world, spotOf(mobs, NsvEntities.BEAVER), 2.4, 22, String.format("nsvmobs-%02d-beaver-gnawing", shot++));
        server.runOnServer(srv -> {
            Beaver beaver = first(srv.overworld(), NsvEntities.BEAVER);
            srv.overworld().setBlockAndUpdate(BlockPos.containing(beaver.getX(), FLOOR, beaver.getZ()).east(), Blocks.AIR.defaultBlockState());
        });

        // a skunk's spray: Nausea for everyone close by
        standBy(world, spotOf(mobs, NsvEntities.SKUNK), 1.0, -1.5);
        ctx.waitTicks(2);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            first(level, NsvEntities.SKUNK).spray(level);
            check(player(srv).hasEffect(MobEffects.NAUSEA), "a skunk's spray brings Nausea");
        });
        server.runCommand("effect clear @a minecraft:nausea");
        server.runCommand("effect clear @a minecraft:blindness");
        photo(ctx, world, spotOf(mobs, NsvEntities.SKUNK), 2.4, 22, String.format("nsvmobs-%02d-skunk-spraying", shot++));

        // a rattlesnake rattles at a survival player 3 blocks away
        standBy(world, spotOf(mobs, NsvEntities.RATTLESNAKE), 1.0, -3.0);
        server.runCommand("gamemode survival @a");
        ctx.waitTicks(25);
        server.runOnServer(srv -> check(first(srv.overworld(), NsvEntities.RATTLESNAKE).isRattling(), "a rattlesnake rattles at a nearby player"));
        photo(ctx, world, spotOf(mobs, NsvEntities.RATTLESNAKE), 2.2, 22, String.format("nsvmobs-%02d-rattlesnake-warning", shot++));
        server.runCommand("gamemode creative @a");

        // a cinder newt stands on a lava pool instead of sinking
        for (String cmd : List.of("fill 25 -62 -6 31 -60 0 glass", "fill 26 -61 -5 30 -60 -1 air", "fill 26 -61 -5 30 -61 -1 lava",
                "summon nsvmobs:cinder_newt 28.5 -59.8 -2.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[200f,0f]}")) {
            server.runCommand(cmd);
        }
        ctx.waitTicks(40);
        server.runOnServer(srv -> {
            var newts = srv.overworld().getEntities(NsvEntities.CINDER_NEWT, new AABB(24, -64, -7, 32, -55, 1), e -> true);
            check(newts.size() == 1 && newts.getFirst().isAlive(), "a cinder newt survives on lava");
            check(newts.getFirst().getY() > -60.6, "a cinder newt stands on lava (y " + newts.getFirst().getY() + ")");
        });
        server.runCommand("tp @a 29.4 -60 -5.6 330 35");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-cinder-newt-on-lava", shot++));

        // the pets: an owl (raw rabbit), a raccoon (cookie), a chameleon (spider eye)
        standBy(world, spotOf(mobs, NsvEntities.OWL), 1.0, -1.5);
        ctx.waitTicks(2);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            ServerPlayer player = player(srv);
            check(tame(player, first(level, NsvEntities.OWL), Items.RABBIT), "raw rabbit tames an owl");
            check(tame(player, first(level, NsvEntities.RACCOON), Items.COOKIE), "a cookie tames a raccoon");
            check(tame(player, first(level, NsvEntities.CHAMELEON), Items.SPIDER_EYE), "a spider eye tames a chameleon");
            player.removeEffect(MobEffects.NIGHT_VISION);
        });
        // at night an owl lends its owner its eyes
        ctx.waitTicks(110);
        server.runOnServer(srv -> check(player(srv).hasEffect(MobEffects.NIGHT_VISION), "a tamed owl gives its owner Night Vision at night"));
        server.runCommand("effect give @a night_vision infinite 0 true");

        // a chameleon on red wool turns red
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Chameleon c = first(level, NsvEntities.CHAMELEON);
            level.setBlockAndUpdate(BlockPos.containing(c.getX(), FLOOR, c.getZ()).below(), Blocks.WOOL.red().defaultBlockState());
        });
        ctx.waitTicks(100);
        server.runOnServer(srv -> {
            int skin = first(srv.overworld(), NsvEntities.CHAMELEON).skinColour();
            check(skin == (MapColor.COLOR_RED.col | 0xFF000000), String.format("a chameleon on red wool turns red (skin %08x)", skin));
        });
        photo(ctx, world, spotOf(mobs, NsvEntities.CHAMELEON), 2.0, 25, String.format("nsvmobs-%02d-chameleon-red", shot++));

        // a tamed ostrich takes a saddle
        server.runOnServer(srv -> {
            Ostrich ostrich = first(srv.overworld(), NsvEntities.OSTRICH);
            ostrich.tameWithName(player(srv));
            ostrich.setItemSlot(EquipmentSlot.SADDLE, new ItemStack(Items.SADDLE));
            check(ostrich.isTamed() && ostrich.isSaddled(), "a tamed ostrich takes a saddle");
        });
        photo(ctx, world, spotOf(mobs, NsvEntities.OSTRICH), 3.8, 10, String.format("nsvmobs-%02d-ostrich-saddled", shot++));

        shot = griffinFlight(ctx, world, shot);

        // carried items: a goose with stolen bread, a raccoon with an apple; a hurt goose drops its loot
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            first(level, NsvEntities.GOOSE).setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.BREAD));
            first(level, NsvEntities.RACCOON).setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.APPLE));
        });
        photo(ctx, world, spotOf(mobs, NsvEntities.GOOSE), 2.4, 15, String.format("nsvmobs-%02d-goose-bread", shot++));
        photo(ctx, world, spotOf(mobs, NsvEntities.RACCOON), 2.2, 20, String.format("nsvmobs-%02d-raccoon-apple", shot++));
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Goose goose = first(level, NsvEntities.GOOSE);
            goose.hurtServer(level, level.damageSources().generic(), 1.0F);
            check(goose.getMainHandItem().isEmpty(), "a hurt goose drops what it carried");
        });

        // a nursery of the new babies (outside the pen) with a parent or two
        server.runCommand("fill 42 -61 4 62 -61 16 grass_block");
        String[] babies = {"deer", "goose", "yak", "flamingo", "seal", "beaver", "skunk", "owl", "raccoon", "ostrich"};
        for (int i = 0; i < babies.length; i++) {
            server.runCommand(String.format("summon nsvmobs:%s %.1f -60 %.1f {NoAI:1b,PersistenceRequired:1b,Age:-24000,Rotation:[%df,0f]}",
                    babies[i], 44.0 + (i % 6) * 3.2, 9.0 + (i / 6) * 3.4, 170 + (i % 3) * 15));
        }
        server.runCommand("summon nsvmobs:deer 60.5 -60 14 {NoAI:1b,PersistenceRequired:1b,Rotation:[200f,0f]}");
        server.runCommand("tp @a 52 -57.5 3.2 0 22");
        ctx.waitTicks(15);
        shoot(ctx, String.format("nsvmobs-%02d-nursery", shot++));
        server.runCommand("kill @e[type=item]");
        return soak(ctx, world, shot);
    }

    /**
     * A tamed, saddled griffin flown with real key presses: a charged jump launches it, holding
     * forward flies it where the rider looks (here: up and away), letting go hovers it, and a rider
     * who hops off mid-air leaves it to glide down unhurt.
     */
    static int griffinFlight(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        var server = world.getServer();
        AABB sky = new AABB(30, -64, -60, 130, 120, 260);
        server.runCommand("summon nsvmobs:griffin 80.5 -60 -30.5 {PersistenceRequired:1b,Rotation:[0f,0f]}");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            Griffin g = srv.overworld().getEntities(NsvEntities.GRIFFIN, sky, e -> true).getFirst();
            g.tameWithName(player(srv));
            g.setItemSlot(EquipmentSlot.SADDLE, new ItemStack(Items.SADDLE));
            check(g.isTamed() && g.isSaddled(), "a tamed griffin takes a saddle");
        });
        server.runCommand("tp @a 80.5 -60 -32.5 0 0");
        server.runCommand("execute positioned 80.5 -60 -30.5 run ride @p mount @e[type=nsvmobs:griffin,limit=1,sort=nearest]");
        ctx.waitTicks(10);
        double[] start = server.computeOnServer(srv -> {
            Griffin g = srv.overworld().getEntities(NsvEntities.GRIFFIN, sky, e -> true).getFirst();
            check(player(srv).getVehicle() == g, "the player rides the griffin");
            return new double[]{g.getY(), g.getZ()};
        });

        // a charged jump: up it goes
        ctx.getInput().holdKeyFor(o -> o.keyJump, 12);
        ctx.waitTicks(15);
        double launched = server.computeOnServer(srv -> {
            Griffin g = srv.overworld().getEntities(NsvEntities.GRIFFIN, sky, e -> true).getFirst();
            check(g.isFlying(), "a griffin takes off on a charged jump");
            check(g.getY() > start[0] + 1.5, String.format("a griffin launches upward (%.2f -> %.2f)", start[0], g.getY()));
            return g.getY();
        });

        // look up a little and hold forward: it climbs away where the rider looks
        ctx.runOnClient(client -> {
            client.player.setYRot(0.0F);
            client.player.setXRot(-20.0F);
            client.options.setCameraType(CameraType.THIRD_PERSON_BACK);
        });
        ctx.getInput().holdKeyFor(o -> o.keyUp, 50);
        double[] flown = server.computeOnServer(srv -> {
            Griffin g = srv.overworld().getEntities(NsvEntities.GRIFFIN, sky, e -> true).getFirst();
            check(g.isFlying() && g.getY() > launched, String.format("a griffin climbs where its rider looks (%.2f -> %.2f)", launched, g.getY()));
            check(g.getZ() - start[1] > 10.0, String.format("a griffin flies forward (z %.2f -> %.2f)", start[1], g.getZ()));
            return new double[]{g.getY(), g.getZ()};
        });
        shoot(ctx, String.format("nsvmobs-%02d-griffin-flight", shot++));

        // let go: it hovers, sinking only slowly
        ctx.waitTicks(40);
        server.runOnServer(srv -> {
            Griffin g = srv.overworld().getEntities(NsvEntities.GRIFFIN, sky, e -> true).getFirst();
            check(g.isFlying() && g.getY() > flown[0] - 4.0, String.format("a riderless-input griffin hovers (%.2f -> %.2f)", flown[0], g.getY()));
        });

        // hop off mid-air: it glides down and lands unhurt
        ctx.runOnClient(client -> client.options.setCameraType(CameraType.FIRST_PERSON));
        server.runCommand("ride @p dismount");
        server.runCommand(String.format("tp @a 80.5 %.1f %.1f 180 30", flown[0] + 2.0, flown[1] + 6.0));
        ctx.runOnClient(client -> client.player.getAbilities().flying = true);   // the camera hovers to watch
        ctx.waitTicks(30);
        shoot(ctx, String.format("nsvmobs-%02d-griffin-gliding", shot++));
        ctx.waitTicks(400);
        server.runOnServer(srv -> {
            Griffin g = srv.overworld().getEntities(NsvEntities.GRIFFIN, sky, e -> true).getFirst();
            check(g.onGround() && !g.isFlying(), String.format("a riderless griffin glides down and lands (y %.2f)", g.getY()));
            check(g.getHealth() >= g.getMaxHealth(), "a griffin takes no fall damage");
        });
        ctx.runOnClient(client -> client.player.getAbilities().flying = false);
        server.runCommand("tp @a 80.5 -60 -40 0 0");
        return shot;
    }

    /**
     * Every 1.4 mob with its AI switched on, in a fenced meadow with a pond, a log, flowers, wheat and
     * loose items, around the player: first in creative, then in survival (with full Resistance) so
     * the neutral ones react. Tamed pets follow and fetch. Nothing may crash, and everyone survives.
     */
    static int soak(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        var server = world.getServer();
        for (String cmd : List.of("fill 43 -60 -41 65 -60 -19 oak_fence", "fill 44 -60 -40 64 -55 -20 air",
                "fill 46 -61 -38 51 -62 -34 water", "setblock 60 -60 -24 oak_log", "setblock 60 -59 -24 oak_log",
                "fill 56 -60 -38 58 -60 -36 poppy", "fill 56 -61 -30 58 -61 -28 farmland", "fill 56 -60 -30 58 -60 -28 wheat[age=2]",
                "summon item 52 -60 -26 {Item:{id:\"minecraft:apple\",count:3}}", "summon item 62 -60 -36 {Item:{id:\"minecraft:bone\",count:2}}")) {
            server.runCommand(cmd);
        }
        String[] ids = {"deer", "goose", "yak", "flamingo", "hummingbird", "seal", "beaver", "skunk", "rattlesnake", "cinder_newt",
                "owl", "raccoon", "chameleon", "ostrich", "griffin"};
        for (int i = 0; i < ids.length; i++) {
            for (int k = 0; k < 2; k++) {
                server.runCommand(String.format("summon nsvmobs:%s %.1f -60 %.1f {PersistenceRequired:1b%s}", ids[i],
                        45.5 + (i % 5) * 4 + k * 1.5, -39.0 + (i / 5) * 6 + k * 2, k == 1 && i % 3 == 0 ? ",Age:-24000" : ""));
            }
        }
        AABB meadow = new AABB(43, -64, -41, 66, -40, -18);
        server.runCommand("tp @a 54.5 -60 -30.5 0 0");
        ctx.waitTicks(5);
        // tame one of each pet and leave it free to follow and fetch
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            ServerPlayer player = player(srv);
            for (var type : List.of(NsvEntities.OWL, NsvEntities.RACCOON, NsvEntities.CHAMELEON)) {
                TamableAnimal pet = level.getEntities(type, meadow, e -> !e.isBaby()).getFirst();
                check(tame(player, pet, type == NsvEntities.OWL ? Items.CHICKEN : type == NsvEntities.RACCOON ? Items.APPLE : Items.SPIDER_EYE),
                        "a meadow " + type.getDescription().getString() + " tames");
                pet.setOrderedToSit(false);
            }
        });
        ctx.waitTicks(200);
        server.runCommand("effect give @a resistance infinite 4 true");
        server.runCommand("gamemode survival @a");
        server.runCommand("tp @a 54.5 -60 -35.5 0 0");
        ctx.waitTicks(100);
        server.runCommand("tp @a 47.5 -60 -24.5 90 0");
        ctx.waitTicks(100);
        server.runCommand("gamemode creative @a");
        server.runCommand("effect clear @a minecraft:resistance");
        server.runCommand("effect clear @a minecraft:nausea");
        server.runCommand("effect clear @a minecraft:blindness");
        server.runCommand("effect clear @a minecraft:poison");
        server.runCommand("effect give @a night_vision infinite 0 true");
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            for (String id : ids) {
                EntityType<?> type = MobRegistry.all().stream().filter(m -> m.id.equals(id)).findFirst().orElseThrow().type;
                int alive = level.getEntities(type, meadow.inflate(16), e -> e.isAlive()).size();
                check(alive >= 1, "the meadow still has a " + id + " after the AI run (" + alive + ")");
            }
        });
        server.runCommand("tp @a 54.5 -55 -44 0 30");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-meadow", shot++));
        return shot;
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
