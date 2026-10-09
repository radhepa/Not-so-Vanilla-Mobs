package dev.nsvmobs.client;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.client.model.AnglerModel;
import dev.nsvmobs.client.model.BogLurkerModel;
import dev.nsvmobs.client.model.CapybaraModel;
import dev.nsvmobs.client.model.DriftcapModel;
import dev.nsvmobs.client.model.DripfangModel;
import dev.nsvmobs.client.model.DuneScorpionModel;
import dev.nsvmobs.client.model.Geometry;
import dev.nsvmobs.client.model.GloomwingModel;
import dev.nsvmobs.client.model.GlowmothModel;
import dev.nsvmobs.client.model.HedgehogModel;
import dev.nsvmobs.client.model.HermitCrabModel;
import dev.nsvmobs.client.model.MeerkatModel;
import dev.nsvmobs.client.model.MossbackTortoiseModel;
import dev.nsvmobs.client.model.OtterModel;
import dev.nsvmobs.client.model.PenguinModel;
import dev.nsvmobs.client.model.VultureModel;
import dev.nsvmobs.client.model.WildBoarModel;
import dev.nsvmobs.client.model.WyrmlingModel;
import dev.nsvmobs.client.render.CritterRenderer;
import dev.nsvmobs.client.render.ScarecrowRenderer;
import dev.nsvmobs.client.render.SkeletonVariantRenderer;
import dev.nsvmobs.client.render.ZombieVariantRenderer;
import dev.nsvmobs.entity.BogLurker;
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
        renderer(NsvEntities.WYRMLING, ctx -> new CritterRenderer<>(ctx, "wyrmling", WyrmlingModel::new, 0.4F, (e, s) -> {
            s.sitting = e.isInSittingPose();
            s.flying = e.isFlying();
        }));
        renderer(NsvEntities.WYRMLING_EMBER, ctx -> new ThrownItemRenderer<>(ctx, 0.5F, true));

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
