package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A hunched, shuffling walk with a swaying ringed tail. Sitting, it settles back on its haunches;
 * washing its food, it sits up the same way and rubs its little hands together under its chin.
 */
public class RaccoonModel extends CritterModel {
    private final ModelPart body, head, tail, tailTip, rf, lf, rh, lh;

    public RaccoonModel(ModelPart root) {
        super(root, "raccoon");
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
        if (s.sitting || s.playing) {
            // on its haunches: the body drops 3 px and tips back about the hips, which lifts the chest
            // onto the straight front legs (the neck comes back 3.5 px, so the head follows); the
            // hind legs fold forward under it and the tail lies along the ground
            this.body.y += 3.0F;
            this.body.xRot -= 0.7F;
            this.head.y -= 1.0F;
            this.head.z += 3.5F;
            this.rh.y += 3.0F;
            this.lh.y += 3.0F;
            this.rh.xRot -= 1.4F;
            this.lh.xRot -= 1.4F;
            this.tail.xRot += 1.0F;
            this.tailTip.xRot -= 0.1F;
            this.tail.yRot += Mth.sin(t * 0.05F) * 0.15F;
            if (s.playing) {
                // washing: hands up under the chin, scrubbing in turn, head bowed over them
                float scrub = Mth.sin(t * 0.9F) * 0.18F;
                this.rf.y -= 2.0F;
                this.lf.y -= 2.0F;
                this.rf.z -= 0.5F;
                this.lf.z -= 0.5F;
                this.rf.xRot -= 0.8F + scrub;
                this.lf.xRot -= 0.8F - scrub;
                this.rf.zRot -= 0.3F;
                this.lf.zRot += 0.3F;
                this.head.xRot += 0.3F + Mth.sin(t * 0.45F) * 0.05F;
            } else {
                look(this.head, s, 0.6F);
                this.head.xRot -= 0.15F;
            }
            return;
        }
        look(this.head, s, 0.6F);
        walk(s, 1.1F, this.rf, this.lf, this.rh, this.lh);
        float gait = Mth.sin(s.walkAnimationPos * 0.6662F) * s.walkAnimationSpeed;
        this.body.zRot += gait * 0.04F;   // a waddle in the hips
        this.tail.yRot += Mth.sin(t * 0.08F) * 0.12F + gait * 0.2F;
        this.tailTip.yRot += Mth.sin(t * 0.08F - 0.7F) * 0.15F;
    }
}
