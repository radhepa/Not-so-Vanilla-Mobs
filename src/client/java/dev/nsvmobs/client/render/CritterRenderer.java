package dev.nsvmobs.client.render;

import java.util.List;
import java.util.function.BiConsumer;
import java.util.function.Function;

import dev.nsvmobs.client.model.CritterModel;
import dev.nsvmobs.client.model.Geometry;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

/** Renderer for the non-humanoid mobs: one baked model, one texture, an optional glow layer. */
public class CritterRenderer<T extends Mob> extends MobRenderer<T, CritterRenderState, CritterModel> {
    private final List<Identifier> textures;
    private final BiConsumer<T, CritterRenderState> extract;

    public CritterRenderer(EntityRendererProvider.Context context, String id, Function<ModelPart, CritterModel> model,
                           float shadow, BiConsumer<T, CritterRenderState> extract) {
        this(context, id, model, shadow, extract, List.of(id));
    }

    /**
     * With texture variants: {@code textureIds} are names under textures/entity/, picked by
     * {@link CritterRenderState#variant} (the extract lambda sets it).
     */
    public CritterRenderer(EntityRendererProvider.Context context, String id, Function<ModelPart, CritterModel> model,
                           float shadow, BiConsumer<T, CritterRenderState> extract, List<String> textureIds) {
        super(context, model.apply(context.bakeLayer(Geometry.layer(id))), shadow);
        this.textures = textureIds.stream().map(t -> Identifier.fromNamespaceAndPath("nsvmobs", "textures/entity/" + t + ".png")).toList();
        this.extract = extract;
        if (GlowLayer.exists(id)) this.addLayer(new GlowLayer<>(this, id));
    }

    @Override
    public Identifier getTextureLocation(CritterRenderState state) {
        return this.textures.get(Math.floorMod(state.variant, this.textures.size()));
    }

    /** 26.3 doesn't shrink babies itself (vanilla swaps in separate baby models), so scale by the age scale here. */
    @Override
    protected void scale(CritterRenderState state, PoseStack poseStack) {
        if (state.ageScale != 1.0F) poseStack.scale(state.ageScale, state.ageScale, state.ageScale);
    }

    @Override
    public CritterRenderState createRenderState() {
        return new CritterRenderState();
    }

    @Override
    public void extractRenderState(T entity, CritterRenderState state, float partialTicks) {
        super.extractRenderState(entity, state, partialTicks);
        state.aggressive = entity.isAggressive();
        state.swing = entity.getSwingAnimation(partialTicks);
        state.partialTick = partialTicks;
        this.extract.accept(entity, state);
    }

    @Override
    protected float getShadowRadius(CritterRenderState state) {
        return state.hidden ? 0.0F : super.getShadowRadius(state);
    }
}
