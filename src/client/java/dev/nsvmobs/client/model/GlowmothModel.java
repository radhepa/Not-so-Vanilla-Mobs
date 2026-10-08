package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Soft, fast wingbeats (hindwings a beat behind), drifting antennae and a gentle bob. */
public class GlowmothModel extends CritterModel {
    private final ModelPart body, head, rightWing, leftWing, rightHind, leftHind, rightAntenna, leftAntenna;

    public GlowmothModel(ModelPart root) {
        super(root, "glowmoth");
        this.body = part("body");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightHind = part("right_hindwing");
        this.leftHind = part("left_hindwing");
        this.rightAntenna = part("right_antenna");
        this.leftAntenna = part("left_antenna");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        look(this.head, s, 0.4F);
        float t = s.ageInTicks * 0.9F;
        float fore = Mth.cos(t) * 0.75F;
        float hind = Mth.cos(t - 0.5F) * 0.6F;
        // +zRot raises a right-side wing (it reaches toward -x); the left side mirrors it
        this.rightWing.zRot += fore;
        this.leftWing.zRot -= fore;
        this.rightHind.zRot += hind;
        this.leftHind.zRot -= hind;
        this.rightAntenna.xRot += Mth.sin(t * 0.21F) * 0.12F;
        this.leftAntenna.xRot += Mth.sin(t * 0.21F + 1.3F) * 0.12F;
        this.body.y += Mth.sin(t) * 0.8F;
    }
}
