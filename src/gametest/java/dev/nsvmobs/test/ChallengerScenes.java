package dev.nsvmobs.test;

import java.util.List;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.entity.Brineclaw;
import dev.nsvmobs.entity.Broodmother;
import dev.nsvmobs.entity.Cinderhulk;
import dev.nsvmobs.entity.CragTroll;
import dev.nsvmobs.entity.Oregorger;
import dev.nsvmobs.entity.Prowler;
import dev.nsvmobs.entity.Riftstalker;
import dev.nsvmobs.entity.Rimewraith;
import dev.nsvmobs.entity.Sandmaw;
import dev.nsvmobs.entity.Stormcaller;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import static dev.nsvmobs.test.ShowcaseClientTest.check;
import static dev.nsvmobs.test.ShowcaseClientTest.shoot;

/**
 * The challengers in action, in an arena east of the lineup (x 54 to 100): each one's signature
 * attack is triggered, checked and photographed. Every plot is 16 blocks apart so they don't meet.
 */
@SuppressWarnings("UnstableApiUsage")
final class ChallengerScenes {
    private ChallengerScenes() {}

    static final AABB ARENA = new AABB(50, -70, -20, 110, -40, 60);

    static <T extends Entity> T only(ServerLevel level, EntityType<T> type, AABB box) {
        List<? extends T> all = level.getEntities(type, box, e -> true);
        check(all.size() == 1, "expected one " + type + " in " + box + ", found " + all.size());
        return all.getFirst();
    }

    static AABB around(double x, double z, double r) {
        return new AABB(x - r, -64, z - r, x + r, -50, z + r);
    }

    static void run(ClientGameTestContext ctx, TestSingleplayerContext world, int shot) {
        TestServerContext server = world.getServer();
        server.runCommand("kill @e[type=minecraft:villager]");
        server.runCommand("tp @a 76 -50 14 0 60");
        ctx.waitTicks(30);

        // ---- checks on the lineup's statues (NoAI) ----
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            // a sandmaw underground can't be hurt; surfaced it can
            Sandmaw maw = ShowcaseClientTest.first(level, NsvEntities.SANDMAW);
            maw.setPhase(Sandmaw.BURROWED);
            check(!maw.hurtServer(level, level.damageSources().generic(), 5.0F), "a burrowed sandmaw can't be hurt");
            maw.setPhase(Sandmaw.SURFACED);
            check(maw.hurtServer(level, level.damageSources().generic(), 5.0F), "a surfaced sandmaw can be hurt");
            // a riftstalker blinks away from projectiles
            Riftstalker rift = ShowcaseClientTest.first(level, NsvEntities.RIFTSTALKER);
            float before = rift.getHealth();
            check(!rift.hurtServer(level, level.damageSources().thrown(rift, null), 5.0F) && rift.getHealth() == before,
                    "projectiles never touch a riftstalker");
            // the broodmother's first brood comes when she's down to two thirds
            Broodmother brood = ShowcaseClientTest.first(level, NsvEntities.BROODMOTHER);
            brood.hurtServer(level, level.damageSources().generic(), 26.0F);
            int spiders = level.getEntities(EntityTypes.CAVE_SPIDER, brood.getBoundingBox().inflate(4.0), e -> true).size();
            check(brood.broodsReleased() == 1 && spiders >= 3,
                    "a hurt broodmother releases a brood (" + spiders + " cave spiders)");
        });
        server.runCommand("kill @e[type=minecraft:cave_spider]");

        // the crag troll heals itself, unless it has been burned
        server.runOnServer(srv -> ShowcaseClientTest.first(srv.overworld(), NsvEntities.CRAG_TROLL)
                .hurtServer(srv.overworld(), srv.overworld().damageSources().generic(), 30.0F));
        float hurt = server.computeOnServer(srv -> ShowcaseClientTest.first(srv.overworld(), NsvEntities.CRAG_TROLL).getHealth());
        ctx.waitTicks(85);
        float healed = server.computeOnServer(srv -> ShowcaseClientTest.first(srv.overworld(), NsvEntities.CRAG_TROLL).getHealth());
        check(healed > hurt, "a crag troll regenerates (" + hurt + " -> " + healed + ")");
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            CragTroll troll = ShowcaseClientTest.first(level, NsvEntities.CRAG_TROLL);
            troll.setInvulnerableTime(0);
            troll.hurtServer(level, level.damageSources().inFire(), 2.0F);
            check(troll.isScorched(), "fire scorches a crag troll");
        });
        float scorched = server.computeOnServer(srv -> ShowcaseClientTest.first(srv.overworld(), NsvEntities.CRAG_TROLL).getHealth());
        ctx.waitTicks(85);
        float after = server.computeOnServer(srv -> ShowcaseClientTest.first(srv.overworld(), NsvEntities.CRAG_TROLL).getHealth());
        check(after <= scorched, "a scorched crag troll can't heal (" + scorched + " -> " + after + ")");

        // ---- plot 1: a sandmaw hunts a villager across the sand and bursts up under it ----
        server.runCommand("fill 52 -61 -8 68 -61 8 sand");
        server.runCommand("summon minecraft:villager 64.5 -60 0.5 {NoAI:1b,OnGround:1b,PersistenceRequired:1b,Rotation:[90f,0f]}");
        server.runCommand("summon nsvmobs:sandmaw 55.5 -60 0.5 {PersistenceRequired:1b}");
        server.runCommand("tp @a 59.0 -60 -5.0 facing 63.5 -60.02 0.5");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Sandmaw maw = only(level, NsvEntities.SANDMAW, around(60, 0, 10));
            maw.setPhase(Sandmaw.BURROWED);
            maw.setTarget(only(level, EntityTypes.VILLAGER, around(60, 0, 10)));
        });
        boolean surfaced = false;
        for (int i = 0; i < 80 && !surfaced; i++) {
            ctx.waitTicks(2);
            surfaced = server.computeOnServer(srv -> only(srv.overworld(), NsvEntities.SANDMAW, around(60, 0, 10)).phase() == Sandmaw.SURFACED);
        }
        check(surfaced, "a burrowed sandmaw tunnels to its prey and surfaces");
        ctx.waitTicks(4);
        shoot(ctx, String.format("nsvmobs-%02d-sandmaw-erupting", shot++));
        server.runOnServer(srv -> {
            LivingEntity villager = only(srv.overworld(), EntityTypes.VILLAGER, around(60, 0, 10));
            check(villager.getHealth() < villager.getMaxHealth() || !villager.isAlive(), "the sandmaw's eruption hurt the villager");
        });

        // ---- plot 2: a cinderhulk slams the ground; the shockwave burns the grounded, not the airborne ----
        server.runCommand("summon nsvmobs:cinderhulk 76.5 -60 0.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}");
        server.runCommand("summon minecraft:villager 76.5 -60 -3.5 {NoAI:1b,OnGround:1b,PersistenceRequired:1b}");
        server.runCommand("summon minecraft:villager 80.5 -58.6 0.5 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b}");
        server.runCommand("tp @a 81.0 -58.5 -6.5 facing 76.5 -61.22 0.0");
        ctx.waitTicks(15);
        server.runOnServer(srv -> {
            Cinderhulk hulk = only(srv.overworld(), NsvEntities.CINDERHULK, around(76, 0, 8));
            hulk.setAction(Cinderhulk.SLAMMING);
            hulk.slam(srv.overworld());
        });
        ctx.waitTicks(6);
        shoot(ctx, String.format("nsvmobs-%02d-cinderhulk-slam", shot++));
        ctx.waitTicks(20);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            List<? extends LivingEntity> villagers = level.getEntities(EntityTypes.VILLAGER, around(76, 0, 8), e -> true);
            LivingEntity grounded = villagers.stream().filter(v -> v.getY() < -59.5).findFirst().orElseThrow();
            LivingEntity floating = villagers.stream().filter(v -> v.getY() > -59.5).findFirst().orElseThrow();
            check(grounded.getHealth() < grounded.getMaxHealth(), "the slam's shockwave hurts what stands on the ground");
            check(floating.getHealth() == floating.getMaxHealth(), "jumping the shockwave (being off the ground) avoids it");
        });

        // ---- plot 3: a crag troll with a boulder over its head ----
        server.runCommand("summon nsvmobs:crag_troll 92.5 -60 0.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[200f,0f]}");
        ctx.waitTicks(5);
        server.runOnServer(srv -> only(srv.overworld(), NsvEntities.CRAG_TROLL, around(92, 0, 6)).setHolding(true));
        server.runCommand("tp @a 96.0 -59.5 -5.5 facing 92.5 -58.82 0.5");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-crag-troll-boulder", shot++));

        // ---- plot 4: a prowler pounces; a raised shield leaves it dazed, an open target is pinned ----
        server.runCommand("summon minecraft:zombie 60.5 -60 20.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}");
        server.runCommand("summon nsvmobs:prowler 60.5 -60 18.0 {NoAI:1b,PersistenceRequired:1b,Rotation:[0f,0f]}");
        server.runCommand("summon minecraft:villager 64.5 -60 18.5 {NoAI:1b,PersistenceRequired:1b}");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            var zombie = only(srv.overworld(), EntityTypes.ZOMBIE, around(60, 20, 4));
            zombie.setYRot(180.0F);
            zombie.setYHeadRot(180.0F);
            zombie.yBodyRot = 180.0F;
            zombie.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(Items.SHIELD));
            zombie.startUsingItem(InteractionHand.OFF_HAND);
        });
        ctx.waitTicks(12);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Prowler cat = only(level, NsvEntities.PROWLER, around(60, 18, 4));
            var zombie = only(level, EntityTypes.ZOMBIE, around(60, 20, 4));
            check(zombie.isBlocking(), "the zombie has its shield up");
            cat.setMode(Prowler.LEAPING);
            cat.pounceHit(level, zombie);
            check(cat.isDazed(), "a shield-blocked pounce dazes the prowler");
            LivingEntity villager = only(level, EntityTypes.VILLAGER, around(64, 18, 2));
            cat.setMode(Prowler.LEAPING);
            cat.pounceHit(level, villager);
            check(cat.mode() == Prowler.MAULING, "a pounce that lands pins and mauls");
        });
        server.runCommand("kill @e[type=minecraft:villager,x=64,y=-60,z=18,distance=..3]");
        server.runCommand("tp @e[type=nsvmobs:prowler,x=60,y=-60,z=18,distance=..3] 60.5 -300 18");
        ctx.waitTicks(5);
        // the photo: mid-leap at the shield-bearer
        server.runCommand("summon nsvmobs:prowler 60.5 -59.1 17.0 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[0f,0f]}");
        ctx.waitTicks(3);
        server.runOnServer(srv -> {
            for (Prowler p : srv.overworld().getEntities(NsvEntities.PROWLER, around(60, 17, 4), e -> e.getY() > -59.5)) p.setMode(Prowler.LEAPING);
        });
        server.runCommand("tp @a 56.0 -59.6 16.0 facing 60.5 -60.62 18.6");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-prowler-pounce", shot++));

        // ---- plot 5: a stormcaller marks the ground around a villager, then the lightning falls ----
        server.runCommand("summon nsvmobs:stormcaller 76.5 -60 22.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}");
        server.runCommand("summon minecraft:villager 76.5 -60 16.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[0f,0f]}");
        server.runCommand("tp @a 82.0 -59.0 15.0 facing 76.5 -61.22 19.0");
        ctx.waitTicks(10);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Stormcaller caller = only(level, NsvEntities.STORMCALLER, around(76, 22, 3));
            caller.raiseArms();
            caller.callLightning(level, only(level, EntityTypes.VILLAGER, around(76, 16, 3)));
            check(caller.pendingStrikes() >= 3, "a stormcaller marks at least three spots for lightning");
        });
        ctx.waitTicks(14);
        shoot(ctx, String.format("nsvmobs-%02d-stormcaller-marks", shot++));
        ctx.waitTicks(17);
        shoot(ctx, String.format("nsvmobs-%02d-stormcaller-strike", shot++));
        ctx.waitTicks(15);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            check(only(level, NsvEntities.STORMCALLER, around(76, 22, 3)).pendingStrikes() == 0, "every marked spot was struck");
            var villagers = level.getEntities(EntityTypes.VILLAGER, around(76, 16, 3), e -> true);
            check(villagers.isEmpty() || villagers.getFirst().getHealth() < villagers.getFirst().getMaxHealth(), "the lightning hurt the villager standing on its mark");
        });

        // ---- plot 6: a brineclaw's front shell turns blows; its sides don't ----
        server.runCommand("summon nsvmobs:brineclaw 92.5 -60 18.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}");
        server.runCommand("summon minecraft:zombie 92.5 -60 15.5 {NoAI:1b,PersistenceRequired:1b,Silent:1b}");
        server.runCommand("summon minecraft:zombie 95.5 -60 18.5 {NoAI:1b,PersistenceRequired:1b,Silent:1b}");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Brineclaw crab = only(level, NsvEntities.BRINECLAW, around(92, 18, 2));
            crab.setYRot(180.0F);
            crab.yBodyRot = 180.0F;
            crab.setYHeadRot(180.0F);
            var zombies = level.getEntities(EntityTypes.ZOMBIE, around(93, 17, 4), e -> true);
            var front = zombies.stream().filter(z -> z.getZ() < 17).findFirst().orElseThrow();
            var side = zombies.stream().filter(z -> z.getX() > 94).findFirst().orElseThrow();
            float h0 = crab.getHealth();
            crab.hurtServer(level, level.damageSources().mobAttack(front), 8.0F);
            float frontLoss = h0 - crab.getHealth();
            crab.setInvulnerableTime(0);
            float h1 = crab.getHealth();
            crab.hurtServer(level, level.damageSources().mobAttack(side), 8.0F);
            float sideLoss = h1 - crab.getHealth();
            check(frontLoss > 0 && sideLoss > frontLoss * 2.5F, "a brineclaw's shell turns blows from the front (front " + frontLoss + ", side " + sideLoss + ")");
            crab.setAction(Brineclaw.WINDUP);
        });
        server.runCommand("tp @e[type=minecraft:zombie,x=93,y=-60,z=17,distance=..5] 93 -300 17");
        server.runCommand("tp @a 95.5 -59.4 14.0 facing 92.5 -61.22 18.5");
        ctx.waitTicks(22);
        shoot(ctx, String.format("nsvmobs-%02d-brineclaw-claw-raised", shot++));

        // ---- plot 7: a rimewraith freezes its prey, unless the prey wears leather ----
        server.runCommand("summon nsvmobs:rimewraith 60.5 -59 36.5 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[180f,0f]}");
        server.runCommand("summon minecraft:villager 63.5 -60 34.5 {NoAI:1b,PersistenceRequired:1b}");
        server.runCommand("summon minecraft:villager 57.5 -60 34.5 {NoAI:1b,PersistenceRequired:1b}");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            var villagers = level.getEntities(EntityTypes.VILLAGER, around(60, 34, 5), e -> true);
            check(villagers.size() == 2, "two villagers by the wraith");
            villagers.stream().filter(v -> v.getX() < 60).forEach(v -> v.setItemSlot(EquipmentSlot.FEET, new ItemStack(Items.LEATHER_BOOTS)));
        });
        // it only chills its prey: first the bare one, then the one in leather boots
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            only(level, NsvEntities.RIMEWRAITH, around(60, 36, 3)).setTarget(
                    level.getEntities(EntityTypes.VILLAGER, around(60, 34, 5), v -> v.getX() > 60).getFirst());
        });
        ctx.waitTicks(30);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Rimewraith wraith = only(level, NsvEntities.RIMEWRAITH, around(60, 36, 3));
            var bare = level.getEntities(EntityTypes.VILLAGER, around(60, 34, 5), v -> v.getX() > 60).getFirst();
            check(bare.getTicksFrozen() > 60, "a rimewraith freezes its prey (" + bare.getTicksFrozen() + ")");
            var booted = level.getEntities(EntityTypes.VILLAGER, around(60, 34, 5), v -> v.getX() < 60).getFirst();
            wraith.setTarget(booted);
        });
        ctx.waitTicks(30);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            var booted = level.getEntities(EntityTypes.VILLAGER, around(60, 34, 5), v -> v.getX() < 60).getFirst();
            check(booted.getTicksFrozen() == 0, "leather keeps the rimewraith's cold out (" + booted.getTicksFrozen() + ")");
            only(level, NsvEntities.RIMEWRAITH, around(60, 36, 3)).setAction(Rimewraith.CASTING);
        });
        server.runCommand("tp @e[type=minecraft:villager,x=60,y=-60,z=34,distance=..5] 60 -300 34");
        server.runCommand("tp @a 62.5 -59.6 31.5 facing 60.5 -59.62 36.5");
        ctx.waitTicks(12);
        shoot(ctx, String.format("nsvmobs-%02d-rimewraith-casting", shot++));

        // ---- plot 8: a riftstalker opens a rift behind a villager; hit as it steps out, it staggers ----
        server.runCommand("summon minecraft:villager 76.5 -60 34.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[0f,0f]}");
        server.runCommand("summon nsvmobs:riftstalker 76.5 -60 44.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}");
        server.runCommand("tp @a 81.0 -59.5 30.0 facing 76.5 -60.82 33.5");
        ctx.waitTicks(10);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Riftstalker r = only(level, NsvEntities.RIFTSTALKER, around(76, 40, 8));
            LivingEntity v = only(level, EntityTypes.VILLAGER, around(76, 34, 3));
            v.setYHeadRot(0.0F);
            r.setTarget(v);
            check(r.openRift(level, v) && r.isPhased(), "a riftstalker vanishes into a rift");
        });
        ctx.waitTicks(8);
        shoot(ctx, String.format("nsvmobs-%02d-riftstalker-rift", shot++));
        boolean out = false;
        for (int i = 0; i < 20 && !out; i++) {
            ctx.waitTicks(1);
            out = server.computeOnServer(srv -> only(srv.overworld(), NsvEntities.RIFTSTALKER, around(76, 38, 10)).isExposed());
        }
        check(out, "the riftstalker steps out of its rift");
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Riftstalker r = only(level, NsvEntities.RIFTSTALKER, around(76, 38, 10));
            check(r.getZ() < 34.5, "the rift opened behind the villager (z " + r.getZ() + ")");
            LivingEntity v = only(level, EntityTypes.VILLAGER, around(76, 34, 3));
            r.hurtServer(level, level.damageSources().mobAttack(v), 2.0F);
            check(r.isStaggered(), "hit as it steps out, a riftstalker staggers");
        });
        ctx.waitTicks(12);
        shoot(ctx, String.format("nsvmobs-%02d-riftstalker-staggered", shot++));

        // ---- plot 9: an oregorger eats an ore vein, then bowls itself into a wall and is stunned ----
        server.runCommand("setblock 96 -60 38 iron_ore");
        server.runCommand("fill 101 -61 32 101 -57 40 stone");
        server.runCommand("summon nsvmobs:oregorger 88.5 -60 36.5 {PersistenceRequired:1b,Rotation:[270f,0f]}");
        ctx.waitTicks(5);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            Oregorger g = only(level, NsvEntities.OREGORGER, around(92, 36, 8));
            check(g.eat(level, new BlockPos(96, -60, 38)), "an oregorger eats an iron ore block");
            check(level.getBlockState(new BlockPos(96, -60, 38)).is(Blocks.DEEPSLATE) && g.gut().getFirst().is(Items.RAW_IRON),
                    "the ore becomes bare rock and the raw iron goes in its gut");
            g.curl(new Vec3(1, 0, 0));
        });
        server.runCommand("tp @a 91.0 -59.5 30.5 facing 91.5 -61.12 36.5");
        ctx.waitTicks(Oregorger.CURL_TICKS + 5);
        shoot(ctx, String.format("nsvmobs-%02d-oregorger-rolling", shot++));
        boolean stunned = false;
        for (int i = 0; i < 40 && !stunned; i++) {
            ctx.waitTicks(2);
            stunned = server.computeOnServer(srv -> only(srv.overworld(), NsvEntities.OREGORGER, around(94, 36, 10)).isStunned());
        }
        check(stunned, "a rolling oregorger that hits a wall is stunned");
        server.runOnServer(srv -> check(only(srv.overworld(), NsvEntities.OREGORGER, around(94, 36, 10)).getArmorValue() == 0,
                "a stunned oregorger's armour is useless"));
        server.runCommand("tp @a 97.0 -59.5 31.0 facing 99.0 -61.12 36.5");
        ctx.waitTicks(6);
        shoot(ctx, String.format("nsvmobs-%02d-oregorger-stunned", shot++));

        // ---- plot 10: a broodmother rears up to spit; a spat web sticks where it lands, then melts away ----
        server.runCommand("summon nsvmobs:broodmother 60.5 -60 52.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[160f,0f]}");
        server.runCommand("summon nsvmobs:web_glob 64.5 -57 50.5 {Motion:[0.0,-0.6,0.0]}");
        ctx.waitTicks(10);
        server.runOnServer(srv -> {
            ServerLevel level = srv.overworld();
            only(level, NsvEntities.BROODMOTHER, around(60, 52, 3)).setSpitting(true);
            check(level.getBlockState(new BlockPos(64, -60, 50)).is(Blocks.COBWEB), "a web glob leaves a cobweb where it lands");
        });
        server.runCommand("tp @a 64.0 -59.5 47.0 facing 61.5 -61.02 51.5");
        ctx.waitTicks(10);
        shoot(ctx, String.format("nsvmobs-%02d-broodmother-spitting", shot++));
        ctx.waitTicks(170);
        server.runOnServer(srv -> check(srv.overworld().getBlockState(new BlockPos(64, -60, 50)).isAir(), "a spat web melts away after a while"));

        // ---- portraits: each challenger alone, 12 blocks apart along z = 80 ----
        String[][] portraits = {
                {"broodmother", "0", "4.4", "0.6"}, {"sandmaw", "0", "5.6", "1.6"}, {"cinderhulk", "0", "5.4", "1.5"},
                {"crag_troll", "0", "5.4", "1.5"}, {"prowler", "0", "3.6", "0.5"}, {"stormcaller", "0", "3.6", "1.2"},
                {"brineclaw", "0", "4.0", "0.5"}, {"rimewraith", "0.8", "4.2", "1.9"}, {"riftstalker", "0", "5.0", "1.6"},
                {"oregorger", "0", "4.2", "0.6"}};
        for (int i = 0; i < portraits.length; i++) {
            String[] p = portraits[i];
            double x = 56.5 + i * 12, z = 80.5, lift = Double.parseDouble(p[1]), dist = Double.parseDouble(p[2]), aim = Double.parseDouble(p[3]);
            server.runCommand(String.format("summon nsvmobs:%s %.1f %.1f %.1f {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[200f,0f]}",
                    p[0], x, -60 + lift, z));
            server.runCommand(String.format("tp @a %.2f -60 %.2f facing %.2f %.2f %.2f",
                    x + dist * 0.55, z - dist * 0.85, x, -60 + aim - 1.62, z));   // tp facing aims from the feet, not the eyes
            ctx.waitTicks(12);
            shoot(ctx, String.format("nsvmobs-%02d-portrait-%s", shot++, p[0]));
            server.runCommand(String.format("tp @e[type=nsvmobs:%s,x=%.1f,y=-60,z=%.1f,distance=..3] %.1f -300 %.1f", p[0], x, z, x, z));
        }
    }
}
