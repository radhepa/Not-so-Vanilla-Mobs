package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Brineclaw;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Eight scuttling legs, twitching eye stalks and idly clicking pincers. Winding up, the big claw
 * rises with its pincer gaping; clamping, it snaps shut and pulls in.
 */
public class BrineclawModel extends CritterModel {
    private final ModelPart rightEye, leftEye, rightClaw, leftClaw, rightPincer, leftPincer;
    private final ModelPart[] rightLegs = new ModelPart[4], leftLegs = new ModelPart[4];

    public BrineclawModel(ModelPart root) {
        super(root, "brineclaw");
        this.rightEye = part("right_eye");
        this.leftEye = part("left_eye");
        this.rightClaw = part("right_claw");
        this.leftClaw = part("left_claw");
        this.rightPincer = part("right_pincer");
        this.leftPincer = part("left_pincer");
        for (int i = 0; i < 4; i++) {
            this.rightLegs[i] = part("right_leg" + (i + 1));
            this.leftLegs[i] = part("left_leg" + (i + 1));
        }
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float pos = s.walkAnimationPos * 1.5F, speed = Math.min(1.0F, s.walkAnimationSpeed * 1.4F);
        for (int i = 0; i < 4; i++) {
            float phase = (i % 2 == 0 ? 0.0F : Mth.PI) + i * 0.3F;
            this.rightLegs[i].zRot -= Math.max(0, Mth.sin(pos + phase)) * 0.4F * speed;
            this.leftLegs[i].zRot += Math.max(0, Mth.sin(pos + phase + Mth.PI)) * 0.4F * speed;
            this.rightLegs[i].yRot += Mth.cos(pos + phase) * 0.25F * speed;
            this.leftLegs[i].yRot -= Mth.cos(pos + phase) * 0.25F * speed;
        }
        this.rightEye.xRot += Mth.sin(t * 0.21F) * 0.08F;
        this.leftEye.xRot += Mth.sin(t * 0.17F + 2.0F) * 0.08F;
        this.rightEye.zRot += Math.max(0, Mth.sin(t * 0.05F) - 0.9F) * 2.0F;

        float click = Math.max(0, Mth.sin(t * 0.09F) - 0.6F) * 1.2F;
        float rightOpen = click, leftOpen = Math.max(0, Mth.sin(t * 0.11F + 1.5F) - 0.6F) * 1.2F;
        if (s.mode == Brineclaw.WINDUP) {
            float p = Math.min(1.0F, s.modeAge / 6.0F);
            this.rightClaw.xRot -= 0.9F * p;
            rightOpen = 0.7F * p;
        } else if (s.mode == Brineclaw.CLAMPING) {
            this.rightClaw.xRot -= 0.35F;
            this.rightClaw.yRot -= 0.25F;
            rightOpen = 0.0F;
        }
        float swipe = Mth.sin(s.swing * Mth.PI);
        this.rightClaw.xRot += swipe * 0.5F;
        // the fingers hinge around z inside each claw: negative opens the right one, positive the left
        this.rightPincer.zRot -= rightOpen;
        this.leftPincer.zRot += leftOpen;
    }
}
