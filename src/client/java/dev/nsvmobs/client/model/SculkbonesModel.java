package dev.nsvmobs.client.model;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.monster.skeleton.SkeletonModel;
import net.minecraft.client.renderer.entity.state.SkeletonRenderState;
import net.minecraft.util.Mth;

/** Skeleton animation plus two sensor tendrils that twitch as it listens, faster when it's hunting. */
public class SculkbonesModel extends SkeletonModel<SkeletonRenderState> {
    private final ModelPart rightTendril, leftTendril;

    public SculkbonesModel(ModelPart root) {
        super(root);
        this.rightTendril = Geometry.part(root, "sculkbones", "right_tendril");
        this.leftTendril = Geometry.part(root, "sculkbones", "left_tendril");
    }

    @Override
    public void setupAnim(SkeletonRenderState state) {
        super.setupAnim(state);
        float t = state.ageInTicks * (state.isAggressive ? 0.9F : 0.25F);
        float amp = state.isAggressive ? 0.35F : 0.15F;
        this.rightTendril.zRot += Mth.sin(t) * amp;
        this.rightTendril.xRot += Mth.cos(t * 0.7F) * amp * 0.5F;
        this.leftTendril.zRot -= Mth.sin(t + 1.3F) * amp;
        this.leftTendril.xRot += Mth.cos(t * 0.7F + 1.3F) * amp * 0.5F;
    }
}
