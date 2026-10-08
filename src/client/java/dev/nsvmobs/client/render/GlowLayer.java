package dev.nsvmobs.client.render;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;

/** Draws a mob's {@code <id>_glow.png} at full brightness (glowing eyes, embers). */
public class GlowLayer<S extends EntityRenderState, M extends EntityModel<S>> extends EyesLayer<S, M> {
    private final RenderType type;

    public GlowLayer(RenderLayerParent<S, M> renderer, String textureId) {
        super(renderer);
        this.type = RenderTypes.eyes(Identifier.fromNamespaceAndPath("nsvmobs", "textures/entity/" + textureId + "_glow.png"));
    }

    @Override
    public RenderType renderType() {
        return this.type;
    }

    /** Whether a mob ships a glow texture; the art tool writes one only when something glows. */
    public static boolean exists(String textureId) {
        return GlowLayer.class.getResource("/assets/nsvmobs/textures/entity/" + textureId + "_glow.png") != null;
    }
}
