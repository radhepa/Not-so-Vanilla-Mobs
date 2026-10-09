package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Bounds along on land; in water it paddles with a sculling tail, and when idle it rolls onto its
 * back and floats, paws up. Sitting, it settles back on its haunches.
 */
public class OtterModel extends CritterModel {
    private final ModelPart body, head, tail, tailTip, rf, lf, rh, lh;

    public OtterModel(ModelPart root) {
        super(root, "otter");
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
        if (s.floating) {
            // belly up: everything hangs off the body, so one roll turns the whole otter over
            this.body.zRot += Mth.PI;
            this.body.y -= 1.0F;
            this.head.xRot += 0.35F + Mth.sin(t * 0.05F) * 0.08F;
            float paddle = Mth.sin(t * 0.08F) * 0.25F;
            this.rf.xRot += -0.6F + paddle;
            this.lf.xRot += -0.6F - paddle;
            this.rh.xRot += 0.3F;
            this.lh.xRot += 0.3F;
            this.tail.xRot += 0.3F;   // its resting droop points up once it's belly up; level it
            this.tail.yRot += Mth.sin(t * 0.06F) * 0.2F;
            return;
        }
        if (s.swimming) {
            look(this.head, s, 0.5F);
            float stroke = Mth.sin(t * 0.5F);
            this.rf.xRot += 0.9F + stroke * 0.5F;
            this.lf.xRot += 0.9F - stroke * 0.5F;
            this.rh.xRot += 1.1F - stroke * 0.6F;
            this.lh.xRot += 1.1F + stroke * 0.6F;
            this.tail.yRot += Mth.sin(t * 0.35F) * 0.3F;
            this.tailTip.yRot += Mth.sin(t * 0.35F - 0.7F) * 0.35F;
            return;
        }
        if (s.sitting) {
            this.body.xRot -= 0.45F;
            this.body.y += 1.0F;
            this.head.xRot += 0.45F;
            this.rh.xRot -= 0.9F;
            this.lh.xRot -= 0.9F;
            this.rf.xRot += 0.45F;
            this.lf.xRot += 0.45F;
            this.tail.xRot += 0.45F;
            look(this.head, s, 0.6F);
            return;
        }
        look(this.head, s, 0.6F);
        walk(s, 1.1F, this.rf, this.lf, this.rh, this.lh);
        // a little bounding arch in the back as it runs
        this.body.xRot += Mth.sin(s.walkAnimationPos * 0.6662F) * 0.05F * s.walkAnimationSpeed;
        this.tail.yRot += Mth.sin(t * 0.1F) * 0.12F;
        this.tailTip.yRot += Mth.sin(t * 0.1F - 0.6F) * 0.15F;
    }
}
