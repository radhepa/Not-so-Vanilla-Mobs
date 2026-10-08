package dev.nsvmobs.client.model;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.monster.skeleton.SkeletonModel;
import net.minecraft.client.renderer.entity.state.SkeletonRenderState;
import net.minecraft.util.Mth;

/** Skeleton animation plus a cape that billows out behind the legs as the knight walks. */
public class GravewardenModel extends SkeletonModel<SkeletonRenderState> {
    private final ModelPart cape;

    public GravewardenModel(ModelPart root) {
        super(root);
        this.cape = Geometry.part(root, "gravewarden", "cape");
    }

    @Override
    public void setupAnim(SkeletonRenderState state) {
        super.setupAnim(state);
        float sway = Mth.cos(state.walkAnimationPos * 0.6662F * 2.0F) * 0.08F * state.walkAnimationSpeed;
        this.cape.xRot += Math.min(0.9F, state.walkAnimationSpeed * 0.75F) + sway;
    }
}
