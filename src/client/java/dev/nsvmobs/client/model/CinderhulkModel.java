package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Cinderhulk;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A knuckle-walk with heavy swinging arms. The slam: both fists climb overhead (shaking with the
 * effort), then come down on the ground with the whole body behind them. The hurl: the right arm
 * cocks back and whips over. Enraged, it trembles.
 */
public class CinderhulkModel extends CritterModel {
    private final ModelPart body, head, rightArm, leftArm, rightLeg, leftLeg;

    public CinderhulkModel(ModelPart root) {
        super(root, "cinderhulk");
        this.body = part("body");
        this.head = part("head");
        this.rightArm = part("right_arm");
        this.leftArm = part("left_arm");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        look(this.head, s, 0.6F);
        float pos = s.walkAnimationPos * 0.6662F, speed = s.walkAnimationSpeed;
        this.rightLeg.xRot += Mth.cos(pos) * 0.9F * speed;
        this.leftLeg.xRot += Mth.cos(pos + Mth.PI) * 0.9F * speed;
        this.rightArm.xRot += Mth.cos(pos + Mth.PI) * 0.6F * speed;
        this.leftArm.xRot += Mth.cos(pos) * 0.6F * speed;
        this.body.zRot += Mth.cos(pos) * 0.04F * speed;
        if (s.enraged) {
            this.body.xRot += Mth.sin(t * 2.1F) * 0.015F;
            this.head.yRot += Mth.sin(t * 1.7F) * 0.04F;
        }
        switch (s.mode) {
            case Cinderhulk.SLAM_WINDUP -> {
                float p = Math.min(1.0F, s.modeAge / 10.0F);
                float strain = Mth.sin(t * 2.4F) * 0.04F * p;
                this.rightArm.xRot += -2.9F * p + strain;
                this.leftArm.xRot += -2.9F * p - strain;
                this.rightArm.zRot += 0.15F * p;
                this.leftArm.zRot -= 0.15F * p;
                this.body.xRot -= 0.22F * p;
            }
            case Cinderhulk.SLAMMING -> {
                float q = Math.min(1.0F, s.modeAge / 3.0F);
                this.rightArm.xRot += -2.9F * (1.0F - q) - 0.35F * q;
                this.leftArm.xRot += -2.9F * (1.0F - q) - 0.35F * q;
                this.body.xRot += 0.4F * q - 0.22F * (1.0F - q);
                this.head.xRot += 0.2F * q;
            }
            case Cinderhulk.HURLING -> {
                float wind = Math.min(1.0F, s.modeAge / 12.0F);
                float release = Mth.clamp((s.modeAge - Cinderhulk.HURL_WINDUP_TICKS) / 4.0F, 0.0F, 1.0F);
                this.rightArm.xRot += -2.7F * wind + 2.2F * release;
                this.rightArm.zRot += 0.3F * wind * (1.0F - release);
                this.body.yRot += 0.3F * wind - 0.6F * release;
            }
            default -> {}
        }
        float punch = Mth.sin(s.swing * Mth.PI);
        this.rightArm.xRot -= punch * 1.5F;
        this.body.yRot -= punch * 0.25F;
    }
}
