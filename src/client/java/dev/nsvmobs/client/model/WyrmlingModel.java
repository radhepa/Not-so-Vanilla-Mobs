package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Wings fold on the ground and beat in the air; tail sways; it settles down on its haunches to sit. */
public class WyrmlingModel extends CritterModel {
    private final ModelPart body, neck, head, jaw, rightWing, leftWing, rightTip, leftTip, tail, tailTip, rf, lf, rh, lh;

    public WyrmlingModel(ModelPart root) {
        super(root, "wyrmling");
        this.body = part("body");
        this.neck = part("neck");
        this.head = part("head");
        this.jaw = part("jaw");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightTip = part("right_wing_tip");
        this.leftTip = part("left_wing_tip");
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
        look(this.head, s, 0.6F);
        float t = s.ageInTicks;
        this.tail.yRot += Mth.sin(t * 0.12F) * 0.25F;
        this.tailTip.yRot += Mth.sin(t * 0.12F - 0.8F) * 0.3F;
        this.jaw.xRot += s.aggressive ? 0.35F + Mth.sin(t * 0.5F) * 0.1F : Math.max(0, Mth.sin(t * 0.03F) - 0.92F) * 3.0F;

        if (s.flying && !s.sitting) {
            // spread from the folded rest pose, then beat
            float beat = Mth.cos(t * 0.9F) * 0.7F;
            float tip = Mth.cos(t * 0.9F - 0.6F) * 0.35F;
            this.rightWing.yRot = 0.25F;
            this.rightWing.zRot = 0.35F + beat;
            this.leftWing.yRot = -0.25F;
            this.leftWing.zRot = -0.35F - beat;
            this.rightTip.yRot = 0.35F;
            this.rightTip.zRot = -0.15F + tip;
            this.leftTip.yRot = -0.35F;
            this.leftTip.zRot = 0.15F - tip;
            // legs tucked back, body bobbing with each beat
            this.rf.xRot += 0.9F;
            this.lf.xRot += 0.9F;
            this.rh.xRot += 1.1F;
            this.lh.xRot += 1.1F;
            this.body.y += Mth.cos(t * 0.9F) * 0.8F;
            return;
        }
        if (s.sitting) {
            this.body.xRot -= 0.35F;
            this.body.y += 1.5F;
            this.rh.xRot -= 1.2F;
            this.lh.xRot -= 1.2F;
            this.rf.xRot += 0.35F;
            this.lf.xRot += 0.35F;
            this.neck.xRot += 0.35F;
            this.tail.xRot += 0.3F;
            return;
        }
        walk(s, 1.0F, this.rf, this.lf, this.rh, this.lh);
        // folded wings shiver a little now and then
        this.rightWing.zRot += Mth.sin(t * 0.07F) * 0.04F;
        this.leftWing.zRot -= Mth.sin(t * 0.07F) * 0.04F;
    }
}
