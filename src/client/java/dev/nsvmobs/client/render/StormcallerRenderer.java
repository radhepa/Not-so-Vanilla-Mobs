package dev.nsvmobs.client.render;

import dev.nsvmobs.client.model.Geometry;
import dev.nsvmobs.entity.Stormcaller;

import net.minecraft.client.model.monster.illager.IllagerModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.IllagerRenderer;
import net.minecraft.client.renderer.entity.state.EvokerRenderState;
import net.minecraft.resources.Identifier;

/** The Stormcaller: vanilla illager model and animation (crossed arms, both arms up to cast) on this mod's geometry. */
public class StormcallerRenderer extends IllagerRenderer<Stormcaller, EvokerRenderState> {
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath("nsvmobs", "textures/entity/stormcaller.png");

    public StormcallerRenderer(EntityRendererProvider.Context context) {
        super(context, new IllagerModel<>(context.bakeLayer(Geometry.layer("stormcaller"))), 0.5F);
        if (GlowLayer.exists("stormcaller")) this.addLayer(new GlowLayer<>(this, "stormcaller"));
    }

    @Override
    public Identifier getTextureLocation(EvokerRenderState state) {
        return TEXTURE;
    }

    @Override
    public EvokerRenderState createRenderState() {
        return new EvokerRenderState();
    }

    @Override
    public void extractRenderState(Stormcaller entity, EvokerRenderState state, float partialTicks) {
        super.extractRenderState(entity, state, partialTicks);
        state.isCastingSpell = entity.isCastingSpell();
    }
}
