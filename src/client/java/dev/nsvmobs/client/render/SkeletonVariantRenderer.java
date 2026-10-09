package dev.nsvmobs.client.render;

import dev.nsvmobs.client.model.Geometry;
import dev.nsvmobs.client.model.GravewardenModel;
import dev.nsvmobs.client.model.SculkbonesModel;

import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.monster.skeleton.SkeletonModel;
import net.minecraft.client.renderer.entity.AbstractSkeletonRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.SkeletonRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.monster.skeleton.AbstractSkeleton;

/** Skeleton variants: vanilla skeleton animation, bow pose and armour on one of this mod's models. */
public class SkeletonVariantRenderer extends AbstractSkeletonRenderer<AbstractSkeleton, SkeletonRenderState> {
    private final Identifier texture;

    public SkeletonVariantRenderer(EntityRendererProvider.Context context, String id) {
        super(context, ModelLayers.SKELETON_ARMOR, model(context.bakeLayer(Geometry.layer(id)), id));
        this.texture = Identifier.fromNamespaceAndPath("nsvmobs", "textures/entity/" + id + ".png");
        if (GlowLayer.exists(id)) this.addLayer(new GlowLayer<>(this, id));
    }

    private static SkeletonModel<SkeletonRenderState> model(ModelPart root, String id) {
        return switch (id) {
            case "gravewarden" -> new GravewardenModel(root);
            case "sculkbones" -> new SculkbonesModel(root);
            default -> new SkeletonModel<>(root);
        };
    }

    @Override
    public Identifier getTextureLocation(SkeletonRenderState state) {
        return this.texture;
    }

    @Override
    public SkeletonRenderState createRenderState() {
        return new SkeletonRenderState();
    }
}
