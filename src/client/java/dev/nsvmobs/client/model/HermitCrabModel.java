package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Fast scuttling legs, claws that open and close, twitchy eye stalks; only the shell while hiding. */
public class HermitCrabModel extends CritterModel {
    private final ModelPart body, rightClaw, leftClaw, rightEye, leftEye;
    private final ModelPart[] rightLegs = new ModelPart[3], leftLegs = new ModelPart[3];

    public HermitCrabModel(ModelPart root) {
        super(root, "hermit_crab");
        this.body = part("body");
        this.rightClaw = part("right_claw");
        this.leftClaw = part("left_claw");
        this.rightEye = part("right_eye");
        this.leftEye = part("left_eye");
        for (int i = 0; i < 3; i++) {
            this.rightLegs[i] = part("right_leg" + (i + 1));
            this.leftLegs[i] = part("left_leg" + (i + 1));
        }
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        this.body.visible = !s.hiding;
        if (s.hiding) return;
        float pos = s.walkAnimationPos * 2.2F, speed = s.walkAnimationSpeed;
        for (int i = 0; i < 3; i++) {
            float phase = i * 2.1F;
            this.rightLegs[i].zRot -= Math.max(0, Mth.sin(pos + phase)) * 0.5F * speed;
            this.leftLegs[i].zRot += Math.max(0, Mth.sin(pos + phase + Mth.PI)) * 0.5F * speed;
            this.rightLegs[i].yRot += Mth.cos(pos + phase) * 0.3F * speed;
            this.leftLegs[i].yRot -= Mth.cos(pos + phase) * 0.3F * speed;
        }
        float t = s.ageInTicks;
        this.rightClaw.xRot += Mth.sin(t * 0.08F) * 0.08F;
        this.leftClaw.xRot += Mth.sin(t * 0.08F + 1.0F) * 0.08F;
        // a quick claw snap every few seconds
        float snap = (t % 70.0F) < 5.0F ? Mth.sin((t % 70.0F) / 5.0F * Mth.PI) * 0.35F : 0.0F;
        this.rightClaw.yRot -= snap;   // snaps inward (toward +x)
        this.rightEye.zRot += Mth.sin(t * 0.13F) * 0.1F;
        this.leftEye.zRot += Mth.sin(t * 0.11F + 2.0F) * 0.1F;
    }
}
