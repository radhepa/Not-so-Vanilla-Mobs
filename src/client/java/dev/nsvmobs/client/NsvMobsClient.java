package dev.nsvmobs.client;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.client.model.AnglerModel;
import dev.nsvmobs.client.model.BeaverModel;
import dev.nsvmobs.client.model.BogLurkerModel;
import dev.nsvmobs.client.model.BrineclawModel;
import dev.nsvmobs.client.model.BroodmotherModel;
import dev.nsvmobs.client.model.CapybaraModel;
import dev.nsvmobs.client.model.ChameleonModel;
import dev.nsvmobs.client.model.CheetahModel;
import dev.nsvmobs.client.model.CinderNewtModel;
import dev.nsvmobs.client.model.CinderhulkModel;
import dev.nsvmobs.client.model.CragTrollModel;
import dev.nsvmobs.client.model.DeerModel;
import dev.nsvmobs.client.model.DriftcapModel;
import dev.nsvmobs.client.model.DripfangModel;
import dev.nsvmobs.client.model.DuneScorpionModel;
import dev.nsvmobs.client.model.ElephantModel;
import dev.nsvmobs.client.model.FlamingoModel;
import dev.nsvmobs.client.model.Geometry;
import dev.nsvmobs.client.model.GloomwingModel;
import dev.nsvmobs.client.model.GlowmothModel;
import dev.nsvmobs.client.model.GooseModel;
import dev.nsvmobs.client.model.GriffinModel;
import dev.nsvmobs.client.model.HedgehogModel;
import dev.nsvmobs.client.model.HermitCrabModel;
import dev.nsvmobs.client.model.HummingbirdModel;
import dev.nsvmobs.client.model.KangarooModel;
import dev.nsvmobs.client.model.MantaRayModel;
import dev.nsvmobs.client.model.MeerkatModel;
import dev.nsvmobs.client.model.MossbackTortoiseModel;
import dev.nsvmobs.client.model.OrchidMantisModel;
import dev.nsvmobs.client.model.OregorgerModel;
import dev.nsvmobs.client.model.OstrichModel;
import dev.nsvmobs.client.model.OtterModel;
import dev.nsvmobs.client.model.OwlModel;
import dev.nsvmobs.client.model.PenguinModel;
import dev.nsvmobs.client.model.ProwlerModel;
import dev.nsvmobs.client.model.RaccoonModel;
import dev.nsvmobs.client.model.RattlesnakeModel;
import dev.nsvmobs.client.model.RiftstalkerModel;
import dev.nsvmobs.client.model.RimewraithModel;
import dev.nsvmobs.client.model.SandmawModel;
import dev.nsvmobs.client.model.SealModel;
import dev.nsvmobs.client.model.SkunkModel;
import dev.nsvmobs.client.model.VultureModel;
import dev.nsvmobs.client.model.WildBoarModel;
import dev.nsvmobs.client.model.WyrmlingModel;
import dev.nsvmobs.client.model.YakModel;
import dev.nsvmobs.client.render.CritterRenderer;
import dev.nsvmobs.client.render.ScarecrowRenderer;
import dev.nsvmobs.client.render.SkeletonVariantRenderer;
import dev.nsvmobs.client.render.StormcallerRenderer;
import dev.nsvmobs.client.render.ZombieVariantRenderer;
import dev.nsvmobs.entity.BogLurker;
import dev.nsvmobs.entity.Goose;
import dev.nsvmobs.entity.Raccoon;
import dev.nsvmobs.entity.Riftstalker;
import dev.nsvmobs.registry.MobEntry;
import dev.nsvmobs.registry.MobRegistry;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;

/**
 * Client wiring: a model layer for every catalogued mob (from its geometry JSON) and one renderer
 * line per mob below. Startup fails loudly if a catalogued mob has no renderer.
 */
public final class NsvMobsClient implements ClientModInitializer {
    private final Set<EntityType<?>> rendered = new HashSet<>();

    @Override
    public void onInitializeClient() {
        for (MobEntry<?> e : MobRegistry.all()) {
            ModelLayerRegistry.registerModelLayer(Geometry.layer(e.id), () -> Geometry.load(e.id));
        }

        // Humanoid variants reuse vanilla zombie/skeleton animation; everything else uses CritterRenderer
        // with its own model class. The lambda copies whatever entity state the model animates from.
        renderer(NsvEntities.SPORELING, ctx -> new ZombieVariantRenderer(ctx, "sporeling"));
        renderer(NsvEntities.FROSTBITTEN, ctx -> new ZombieVariantRenderer(ctx, "frostbitten"));
        renderer(NsvEntities.LOST_MINER, ctx -> new ZombieVariantRenderer(ctx, "lost_miner"));
        renderer(NsvEntities.SCARECROW, ScarecrowRenderer::new);
        renderer(NsvEntities.BRIARBONES, ctx -> new SkeletonVariantRenderer(ctx, "briarbones"));
        renderer(NsvEntities.GRAVEWARDEN, ctx -> new SkeletonVariantRenderer(ctx, "gravewarden"));
        renderer(NsvEntities.SOULPYRE, ctx -> new SkeletonVariantRenderer(ctx, "soulpyre"));
        renderer(NsvEntities.SCULKBONES, ctx -> new SkeletonVariantRenderer(ctx, "sculkbones"));
        renderer(NsvEntities.BOG_LURKER, ctx -> new CritterRenderer<>(ctx, "bog_lurker", BogLurkerModel::new, 0.8F, (e, s) -> {
            s.lurking = e.isLurking();
            int lash = e.lashTicks();
            s.lash = lash > 0 ? Mth.sin(Mth.PI * (BogLurker.LASH_TICKS - lash) / BogLurker.LASH_TICKS) : 0.0F;
        }));
        renderer(NsvEntities.GLOOMWING, ctx -> new CritterRenderer<>(ctx, "gloomwing", GloomwingModel::new, 0.4F, (e, s) -> {}));
        renderer(NsvEntities.DUNE_SCORPION, ctx -> new CritterRenderer<>(ctx, "dune_scorpion", DuneScorpionModel::new, 0.8F,
                (e, s) -> s.burrowed = e.isBurrowed()));
        renderer(NsvEntities.VULTURE, ctx -> new CritterRenderer<>(ctx, "vulture", VultureModel::new, 0.5F, (e, s) -> {}));
        renderer(NsvEntities.DRIPFANG, ctx -> new CritterRenderer<>(ctx, "dripfang", DripfangModel::new, 0.6F,
                (e, s) -> s.hanging = e.isHanging()));
        renderer(NsvEntities.ANGLER, ctx -> new CritterRenderer<>(ctx, "angler", AnglerModel::new, 0.5F,
                (e, s) -> s.swimming = e.isInWater()));
        renderer(NsvEntities.DRIFTCAP, ctx -> new CritterRenderer<>(ctx, "driftcap", DriftcapModel::new, 0.4F, (e, s) -> {}));
        // challengers
        renderer(NsvEntities.BROODMOTHER, ctx -> new CritterRenderer<>(ctx, "broodmother", BroodmotherModel::new, 1.3F,
                (e, s) -> s.holding = e.isSpitting()));
        renderer(NsvEntities.SANDMAW, ctx -> new CritterRenderer<>(ctx, "sandmaw", SandmawModel::new, 0.9F, (e, s) -> {
            s.hidden = e.isUnderground();
            s.mode = e.phase();
            s.modeAge = e.phaseAge(s.partialTick);
        }));
        renderer(NsvEntities.CINDERHULK, ctx -> new CritterRenderer<>(ctx, "cinderhulk", CinderhulkModel::new, 1.1F, (e, s) -> {
            s.mode = e.action();
            s.modeAge = e.actionAge(s.partialTick);
            s.enraged = e.isEnraged();
        }));
        renderer(NsvEntities.CRAG_TROLL, ctx -> new CritterRenderer<>(ctx, "crag_troll", CragTrollModel::new, 1.0F,
                (e, s) -> s.holding = e.isHolding()));
        renderer(NsvEntities.PROWLER, ctx -> new CritterRenderer<>(ctx, "prowler", ProwlerModel::new, 0.6F, (e, s) -> {
            s.mode = e.mode();
            s.modeAge = e.modeAge(s.partialTick);
        }));
        renderer(NsvEntities.STORMCALLER, StormcallerRenderer::new);
        renderer(NsvEntities.BRINECLAW, ctx -> new CritterRenderer<>(ctx, "brineclaw", BrineclawModel::new, 1.0F, (e, s) -> {
            s.mode = e.action();
            s.modeAge = e.actionAge(s.partialTick);
        }));
        renderer(NsvEntities.RIMEWRAITH, ctx -> new CritterRenderer<>(ctx, "rimewraith", RimewraithModel::new, 0.4F, (e, s) -> {
            s.mode = e.action();
            s.modeAge = e.actionAge(s.partialTick);
        }));
        renderer(NsvEntities.RIFTSTALKER, ctx -> new CritterRenderer<>(ctx, "riftstalker", RiftstalkerModel::new, 0.5F, (e, s) -> {
            s.hidden = e.phase() == Riftstalker.PHASED;
            s.mode = e.phase();
            s.modeAge = e.phaseAge(s.partialTick);
        }));
        renderer(NsvEntities.OREGORGER, ctx -> new CritterRenderer<>(ctx, "oregorger", OregorgerModel::new, 1.0F, (e, s) -> {
            s.mode = e.mode();
            s.modeAge = e.modeAge(s.partialTick);
        }));
        renderer(NsvEntities.MOSSBACK_TORTOISE, ctx -> new CritterRenderer<>(ctx, "mossback_tortoise", MossbackTortoiseModel::new, 0.9F, (e, s) -> {
            s.sheared = e.isSheared();
            s.hiding = e.isHiding();
        }));
        renderer(NsvEntities.CAPYBARA, ctx -> new CritterRenderer<>(ctx, "capybara", CapybaraModel::new, 0.6F, (e, s) -> {}));
        renderer(NsvEntities.GLOWMOTH, ctx -> new CritterRenderer<>(ctx, "glowmoth", GlowmothModel::new, 0.3F, (e, s) -> {}));
        renderer(NsvEntities.HERMIT_CRAB, ctx -> new CritterRenderer<>(ctx, "hermit_crab", HermitCrabModel::new, 0.3F, (e, s) -> {
            s.variant = e.shell();
            s.hiding = e.isHiding();
        }, List.of("hermit_crab", "hermit_crab_whelk", "hermit_crab_snail")));
        renderer(NsvEntities.HEDGEHOG, ctx -> new CritterRenderer<>(ctx, "hedgehog", HedgehogModel::new, 0.25F, (e, s) -> {
            s.hiding = e.isCurled();
            s.sitting = e.isInSittingPose();
        }));
        renderer(NsvEntities.MEERKAT, ctx -> new CritterRenderer<>(ctx, "meerkat", MeerkatModel::new, 0.25F,
                (e, s) -> s.standing = e.isSentry()));
        renderer(NsvEntities.PENGUIN, ctx -> new CritterRenderer<>(ctx, "penguin", PenguinModel::new, 0.35F, (e, s) -> {
            s.sliding = e.isSliding();
            s.swimming = e.isInWater();
            s.variant = e.isBaby() ? 1 : 0;
        }, List.of("penguin", "penguin_chick")));
        renderer(NsvEntities.WILD_BOAR, ctx -> new CritterRenderer<>(ctx, "wild_boar", WildBoarModel::new, 0.7F,
                (e, s) -> s.variant = e.isBaby() ? 1 : 0, List.of("wild_boar", "wild_boar_piglet")));
        renderer(NsvEntities.OTTER, ctx -> new CritterRenderer<>(ctx, "otter", OtterModel::new, 0.35F, (e, s) -> {
            s.floating = e.isFloating();
            s.swimming = e.isInWater();
            s.sitting = e.isInSittingPose();
        }));
        renderer(NsvEntities.DEER, ctx -> new CritterRenderer<>(ctx, "deer", DeerModel::new, 0.5F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.antlers = e.isStag() && !e.isBaby();
            s.warning = e.isAlarmed();
        }, List.of("deer", "deer_fawn")));
        renderer(NsvEntities.GOOSE, ctx -> new CritterRenderer<Goose>(ctx, "goose", GooseModel::new, 0.35F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.warning = e.isHissing();
            s.swimming = e.isInWater();
        }, List.of("goose", "goose_gosling")).carriesItem("mouth"));
        renderer(NsvEntities.YAK, ctx -> new CritterRenderer<>(ctx, "yak", YakModel::new, 0.9F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.sheared = e.isSheared();
            s.antlers = !e.isBaby();
        }, List.of("yak", "yak_calf")));
        renderer(NsvEntities.FLAMINGO, ctx -> new CritterRenderer<>(ctx, "flamingo", FlamingoModel::new, 0.35F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.resting = e.isResting();
            s.flying = e.isFluttering();
            s.playing = e.isDancing();
            s.swimming = e.isInWater();
        }, List.of("flamingo", "flamingo_chick")));
        renderer(NsvEntities.HUMMINGBIRD, ctx -> new CritterRenderer<>(ctx, "hummingbird", HummingbirdModel::new, 0.15F, (e, s) -> {
            s.variant = e.variant();
            s.flying = e.isFlying();
        }, List.of("hummingbird", "hummingbird_violet", "hummingbird_rufous")));
        renderer(NsvEntities.SEAL, ctx -> new CritterRenderer<>(ctx, "seal", SealModel::new, 0.5F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.swimming = e.isInWater();
            s.playing = e.isBalancing();
        }, List.of("seal", "seal_pup")));
        renderer(NsvEntities.BEAVER, ctx -> new CritterRenderer<>(ctx, "beaver", BeaverModel::new, 0.4F, (e, s) -> {
            s.swimming = e.isInWater();
            s.warning = e.isSlapping();
            s.playing = e.isGnawing();
        }));
        renderer(NsvEntities.SKUNK, ctx -> new CritterRenderer<>(ctx, "skunk", SkunkModel::new, 0.35F, (e, s) -> {
            s.warning = e.isWarning();
            s.playing = e.isSpraying();
        }));
        renderer(NsvEntities.RATTLESNAKE, ctx -> new CritterRenderer<>(ctx, "rattlesnake", RattlesnakeModel::new, 0.35F,
                (e, s) -> s.warning = e.isRattling()));
        renderer(NsvEntities.CINDER_NEWT, ctx -> new CritterRenderer<>(ctx, "cinder_newt", CinderNewtModel::new, 0.4F, (e, s) -> {}));
        renderer(NsvEntities.OWL, ctx -> new CritterRenderer<>(ctx, "owl", OwlModel::new, 0.3F, (e, s) -> {
            s.variant = e.variant();
            s.sitting = e.isInSittingPose();
            s.flying = e.isFlying();
        }, List.of("owl", "owl_snowy")));
        renderer(NsvEntities.RACCOON, ctx -> new CritterRenderer<Raccoon>(ctx, "raccoon", RaccoonModel::new, 0.35F, (e, s) -> {
            s.sitting = e.isInSittingPose();
            s.playing = e.isWashing();
        }).carriesItem("mouth"));
        renderer(NsvEntities.CHAMELEON, ctx -> new CritterRenderer<>(ctx, "chameleon", ChameleonModel::new, 0.25F, (e, s) -> {
            s.sitting = e.isInSittingPose();
            s.tint = e.tint();
        }));
        renderer(NsvEntities.OSTRICH, ctx -> new CritterRenderer<>(ctx, "ostrich", OstrichModel::new, 0.6F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.saddled = e.isSaddled();
            s.flying = e.isGliding();
        }, List.of("ostrich", "ostrich_chick")));
        renderer(NsvEntities.GRIFFIN, ctx -> new CritterRenderer<>(ctx, "griffin", GriffinModel::new, 0.9F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.saddled = e.isSaddled();
            s.flying = e.isFlying();
        }, List.of("griffin", "griffin_chick")));
        renderer(NsvEntities.WYRMLING, ctx -> new CritterRenderer<>(ctx, "wyrmling", WyrmlingModel::new, 0.4F, (e, s) -> {
            s.sitting = e.isInSittingPose();
            s.flying = e.isFlying();
        }));
        renderer(NsvEntities.CHEETAH, ctx -> new CritterRenderer<>(ctx, "cheetah", CheetahModel::new, 0.45F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.sitting = e.isInSittingPose() || e.isLookout();
            s.resting = e.isLounging();
            s.mode = e.mode();
            s.modeAge = e.modeAge(s.partialTick);
        }, List.of("cheetah", "cheetah_cub")));
        renderer(NsvEntities.ELEPHANT, ctx -> new CritterRenderer<>(ctx, "elephant", ElephantModel::new, 1.3F, (e, s) -> {
            s.variant = e.isBaby() ? 1 : 0;
            s.warning = e.isThreatening();
            s.playing = e.isSpraying();
            s.holding = e.hasWater();
        }, List.of("elephant", "elephant_calf")));
        renderer(NsvEntities.KANGAROO, ctx -> new CritterRenderer<>(ctx, "kangaroo", KangarooModel::new, 0.5F, (e, s) -> {
            s.variant = e.isBaby() ? 2 : e.isBuck() ? 0 : 1;
            s.standing = e.isBoxing();
            s.resting = e.isLounging();
            s.sitting = e.isPassenger();
            s.holding = e.isVehicle();   // a doe with her joey aboard hops gently
            s.mode = e.action();
            s.modeAge = e.actionAge(s.partialTick);
        }, List.of("kangaroo", "kangaroo_doe", "kangaroo_joey")));
        renderer(NsvEntities.ORCHID_MANTIS, ctx -> new CritterRenderer<>(ctx, "orchid_mantis", OrchidMantisModel::new, 0.4F, (e, s) -> {
            s.lurking = e.isStill();
            s.flying = e.isFluttering();
            s.mode = e.action();
            s.modeAge = e.actionAge(s.partialTick);
        }));
        renderer(NsvEntities.MANTA_RAY, ctx -> new CritterRenderer<>(ctx, "manta_ray", MantaRayModel::new, 0.8F, (e, s) -> {
            s.swimming = e.isInWater();
            s.playing = e.isBreaching();
        }));
        renderer(NsvEntities.WYRMLING_EMBER, ctx -> new ThrownItemRenderer<>(ctx, 0.5F, true));
        renderer(NsvEntities.BOULDER, ctx -> new ThrownItemRenderer<>(ctx, 3.0F, false));
        renderer(NsvEntities.ICE_SHARD, ctx -> new ThrownItemRenderer<>(ctx, 0.6F, true));
        renderer(NsvEntities.WEB_GLOB, ctx -> new ThrownItemRenderer<>(ctx, 1.2F, false));

        for (MobEntry<?> e : MobRegistry.all()) {
            if (!this.rendered.contains(e.type)) {
                throw new IllegalStateException("No renderer for " + e.id + ": add one in NsvMobsClient");
            }
        }
    }

    private <T extends Entity> void renderer(EntityType<? extends T> type, EntityRendererProvider<T> provider) {
        EntityRendererRegistry.register(type, provider);
        this.rendered.add(type);
    }
}
