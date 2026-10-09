package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A low, rolling trot with the plume of a tail flowing behind. Warning, it raises the tail straight
 * up and stamps its front feet in turn, head down; spraying, it braces its hind legs and curls the
 * tail right over its back (the entity has already turned its rear on the target).
 */
public class SkunkModel extends CritterModel {
    private final ModelPart body, head, tail, tailTip, rf, lf, rh, lh;

    public SkunkModel(ModelPart root) {
        super(root, "skunk");
        this.body = part("body");
        this.head = part("head");
        this.tail = part("tail");
        this.tailTip = part("tail_tip");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        if (s.playing) {
            look(this.head, s, 0.8F);   // over its shoulder at whoever it's spraying
            this.body.xRot += 0.08F;
            this.tail.xRot += 1.25F;
            this.tailTip.xRot += 0.9F + Mth.sin(t * 0.9F) * 0.06F;   // quivering
            this.rh.xRot += 0.3F;
            this.lh.xRot += 0.3F;
            this.rh.zRot += 0.2F;
            this.lh.zRot -= 0.2F;
            return;
        }
        if (s.warning) {
            look(this.head, s, 0.5F);
            this.head.xRot += 0.25F;
            // stamp, stamp: each forefoot snaps up and slams down in turn
            float a = Mth.sin(t * 0.7F);
            float right = Math.max(0.0F, a), left = Math.max(0.0F, -a);
            this.rf.xRot -= right * right * 0.9F;
            this.lf.xRot -= left * left * 0.9F;
            this.body.xRot += (right + left) * 0.03F;
            this.tail.xRot += 0.95F;
            this.tailTip.xRot += 0.35F + Mth.sin(t * 0.5F) * 0.05F;
            this.tail.zRot += Mth.sin(t * 0.35F) * 0.05F;
            return;
        }
        look(this.head, s, 0.6F);
        walk(s, 1.3F, this.rf, this.lf, this.rh, this.lh);
        float gait = Mth.sin(s.walkAnimationPos * 0.6662F) * s.walkAnimationSpeed;
        this.body.zRot += gait * 0.03F;
        this.tail.xRot += gait * 0.06F;
        this.tail.yRot += Mth.sin(t * 0.09F) * 0.08F + gait * 0.12F;
        this.tailTip.yRot += Mth.sin(t * 0.09F - 0.8F) * 0.12F;
        this.tailTip.xRot += Mth.sin(t * 0.07F) * 0.04F;
    }
}
