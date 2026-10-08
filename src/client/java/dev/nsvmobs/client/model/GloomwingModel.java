package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Ragged, never-resting wingbeats with a lagging tip and a bob of the body. */
public class GloomwingModel extends CritterModel {
    private final ModelPart body, head, rightWing, leftWing, rightTip, leftTip;

    public GloomwingModel(ModelPart root) {
        super(root, "gloomwing");
        this.body = part("body");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightTip = part("right_wing_tip");
        this.leftTip = part("left_wing_tip");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        look(this.head, s, 0.5F);
        float t = s.ageInTicks * 1.15F;
        float beat = Mth.cos(t) * 0.85F;
        float tip = Mth.cos(t - 0.7F) * 0.55F;
        // +zRot raises the right wing (it reaches toward -x); the left mirrors it
        this.rightWing.zRot += beat;
        this.leftWing.zRot -= beat;
        this.rightTip.zRot += tip;
        this.leftTip.zRot -= tip;
        this.body.y += Mth.sin(t) * 1.2F;
        this.body.xRot += 0.15F + s.walkAnimationSpeed * 0.3F;
    }
}
