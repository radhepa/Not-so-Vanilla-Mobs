package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Riftstalker;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A long-legged, swaying stalk with the tail whipping behind. Stepping out of a rift it raises its
 * blade arm high, then slashes down. Staggered, it doubles over with its arms hanging.
 */
public class RiftstalkerModel extends CritterModel {
    private final ModelPart body, head, rightArm, leftArm, rightForearm, leftForearm, tail, tailTip, rightLeg, leftLeg, rightShin, leftShin;

    public RiftstalkerModel(ModelPart root) {
        super(root, "riftstalker");
        this.body = part("body");
        this.head = part("head");
        this.rightArm = part("right_arm");
        this.leftArm = part("left_arm");
        this.rightForearm = part("right_forearm");
        this.leftForearm = part("left_forearm");
        this.tail = part("tail");
        this.tailTip = part("tail_tip");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
        this.rightShin = part("right_shin");
        this.leftShin = part("left_shin");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        if (s.hidden) return;
        float t = s.ageInTicks;
        look(this.head, s, 0.8F);
        float pos = s.walkAnimationPos * 0.5F, speed = s.walkAnimationSpeed;
        float stride = Mth.cos(pos);
        this.rightLeg.xRot += stride * 0.7F * speed;
        this.leftLeg.xRot -= stride * 0.7F * speed;
        this.rightShin.xRot += Math.max(0, -stride) * 0.6F * speed;
        this.leftShin.xRot += Math.max(0, stride) * 0.6F * speed;
        this.rightArm.xRot -= stride * 0.5F * speed;
        this.leftArm.xRot += stride * 0.5F * speed;
        this.body.zRot += Mth.sin(pos) * 0.05F * speed;
        this.tail.yRot += Mth.sin(t * 0.1F) * 0.25F;
        this.tailTip.yRot += Mth.sin(t * 0.1F - 0.9F) * 0.35F;
        this.tail.xRot += Mth.sin(t * 0.07F) * 0.06F;
        this.rightForearm.xRot += Mth.sin(t * 0.06F) * 0.05F;
        this.leftForearm.xRot += Mth.sin(t * 0.06F + 1.0F) * 0.05F;

        if (s.mode == Riftstalker.EMERGED) {
            float raise = Math.min(1.0F, s.modeAge / (Riftstalker.COUNTER_TICKS - 2.0F));
            float slash = Mth.clamp((s.modeAge - Riftstalker.COUNTER_TICKS) / 3.0F, 0.0F, 1.0F);
            this.rightArm.xRot += -2.6F * raise * (1.0F - slash) + 0.5F * slash;
            this.rightForearm.xRot -= 0.4F * raise * (1.0F - slash);
            this.body.xRot -= 0.15F * raise * (1.0F - slash) - 0.3F * slash;
            this.leftArm.xRot -= 0.6F * raise;
        } else if (s.mode == Riftstalker.STAGGERED) {
            this.body.xRot += 0.45F;
            this.head.xRot += 0.4F;
            this.head.zRot += Mth.sin(t * 0.3F) * 0.25F;
            this.rightArm.xRot += 0.3F;
            this.leftArm.xRot += 0.3F;
            this.tail.xRot += 0.4F;
        }
        float swipe = Mth.sin(s.swing * Mth.PI);
        this.rightArm.xRot -= swipe * 1.8F;
    }
}
