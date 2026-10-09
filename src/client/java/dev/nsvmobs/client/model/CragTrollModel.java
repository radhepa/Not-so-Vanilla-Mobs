package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A lumbering, arm-swinging walk. About to throw, it holds a boulder high over its head with both
 * hands and roars; it punches with its right fist.
 */
public class CragTrollModel extends CritterModel {
    private final ModelPart body, head, jaw, rightArm, leftArm, rightLeg, leftLeg, boulder;

    public CragTrollModel(ModelPart root) {
        super(root, "crag_troll");
        this.body = part("body");
        this.head = part("head");
        this.jaw = part("jaw");
        this.rightArm = part("right_arm");
        this.leftArm = part("left_arm");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
        this.boulder = part("boulder");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        look(this.head, s, 0.7F);
        float pos = s.walkAnimationPos * 0.6662F, speed = s.walkAnimationSpeed;
        this.rightLeg.xRot += Mth.cos(pos) * 0.8F * speed;
        this.leftLeg.xRot += Mth.cos(pos + Mth.PI) * 0.8F * speed;
        this.rightArm.xRot += Mth.cos(pos + Mth.PI) * 0.7F * speed;
        this.leftArm.xRot += Mth.cos(pos) * 0.7F * speed;
        this.body.yRot += Mth.cos(pos) * 0.06F * speed;
        this.rightArm.zRot += Mth.sin(t * 0.07F) * 0.04F;
        this.leftArm.zRot -= Mth.sin(t * 0.07F) * 0.04F;
        this.jaw.xRot += Math.max(0, Mth.sin(t * 0.05F) - 0.7F) * 0.6F;

        this.boulder.visible = s.holding;
        if (s.holding) {
            this.rightArm.xRot = -2.9F;
            this.leftArm.xRot = -2.9F;
            this.rightArm.yRot = 0.0F;
            this.leftArm.yRot = 0.0F;
            this.jaw.xRot += 0.45F;
            this.head.xRot -= 0.2F;
        }
        float punch = Mth.sin(s.swing * Mth.PI);
        this.rightArm.xRot -= punch * 1.6F;
        this.jaw.xRot += punch * 0.3F;
    }
}
