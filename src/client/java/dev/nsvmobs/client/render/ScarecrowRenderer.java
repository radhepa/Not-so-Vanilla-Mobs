package dev.nsvmobs.client.render;

import dev.nsvmobs.client.model.Geometry;
import dev.nsvmobs.client.model.ScarecrowModel;
import dev.nsvmobs.entity.Scarecrow;

import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.AbstractZombieRenderer;
import net.minecraft.client.renderer.entity.ArmorModelSet;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.ZombieRenderState;
import net.minecraft.resources.Identifier;

/** Zombie animation by night; by day the scarecrow T-pose (see {@link ScarecrowModel}). */
public class ScarecrowRenderer extends AbstractZombieRenderer<Scarecrow, ScarecrowRenderer.State, ScarecrowModel> {
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath("nsvmobs", "textures/entity/scarecrow.png");

    public static class State extends ZombieRenderState {
        public boolean posing;
    }

    public ScarecrowRenderer(EntityRendererProvider.Context context) {
        this(context, new ScarecrowModel(context.bakeLayer(Geometry.layer("scarecrow"))),
                ArmorModelSet.bake(ModelLayers.ZOMBIE_ARMOR, context.getModelSet(), ScarecrowModel::new));
    }

    private ScarecrowRenderer(EntityRendererProvider.Context context, ScarecrowModel model, ArmorModelSet<ScarecrowModel> armor) {
        super(context, model, model, armor, armor);
        if (GlowLayer.exists("scarecrow")) this.addLayer(new GlowLayer<>(this, "scarecrow"));
    }

    @Override
    public Identifier getTextureLocation(State state) {
        return TEXTURE;
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(Scarecrow entity, State state, float partialTicks) {
        super.extractRenderState(entity, state, partialTicks);
        state.posing = entity.isPosing();
    }
}
