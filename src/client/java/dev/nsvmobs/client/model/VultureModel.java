package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Mostly gliding on spread wings that rock in the air, with a burst of slow wingbeats every few
 * seconds; diving, it sweeps its wings back.
 */
public class VultureModel extends CritterModel {
    private final ModelPart body, neck, head, rightWing, leftWing, rightTip, leftTip, tail, rightLeg, leftLeg;

    public VultureModel(ModelPart root) {
        super(root, "vulture");
        this.body = part("body");
        this.neck = part("neck");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightTip = part("right_wing_tip");
        this.leftTip = part("left_wing_tip");
        this.tail = part("tail");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        // the head sits on a tilted neck: turn the neck to look around, tip the head to look up and down
        this.neck.yRot += s.yRot * Mth.DEG_TO_RAD * 0.5F;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.5F;
        float t = s.ageInTicks;
        // +zRot raises a right-side wing (it reaches toward -x); the left side mirrors it
        float rock = Mth.sin(t * 0.05F) * 0.08F;
        float cycle = t % 60.0F;
        float flap = cycle < 12.0F ? Mth.sin(cycle / 12.0F * Mth.TWO_PI) * 0.55F : 0.0F;
        float tipFlap = cycle < 12.0F ? Mth.sin(cycle / 12.0F * Mth.TWO_PI - 0.7F) * 0.35F : 0.0F;
        this.rightWing.zRot += flap + rock;
        this.leftWing.zRot -= flap - rock;
        this.rightTip.zRot += tipFlap;
        this.leftTip.zRot -= tipFlap;
        // banking into the turn while soaring
        this.body.zRot += Mth.sin(t * 0.025F) * 0.12F;
        this.body.y += Mth.sin(t * 0.08F) * 0.6F;
        this.tail.xRot += Mth.sin(t * 0.1F) * 0.06F;
        if (s.aggressive) {
            // diving: wings swept back, tips folded in
            this.rightWing.yRot += 0.75F;
            this.leftWing.yRot -= 0.75F;
            this.rightTip.yRot += 0.6F;
            this.leftTip.yRot -= 0.6F;
            this.body.xRot += 0.25F;
            // talons forward for the strike
            this.rightLeg.xRot -= 1.1F;
            this.leftLeg.xRot -= 1.1F;
        }
    }
}
