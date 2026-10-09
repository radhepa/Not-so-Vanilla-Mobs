package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** A side-to-side waddle with flippers held out; belly-down to slide or swim, flippers beating. */
public class PenguinModel extends CritterModel {
    private final ModelPart body, head, rightFlipper, leftFlipper, rightFoot, leftFoot, tail;

    public PenguinModel(ModelPart root) {
        super(root, "penguin");
        this.body = part("body");
        this.head = part("head");
        this.rightFlipper = part("right_flipper");
        this.leftFlipper = part("left_flipper");
        this.rightFoot = part("right_foot");
        this.leftFoot = part("left_foot");
        this.tail = optional("tail");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        if (s.sliding || s.swimming) {
            // the body pivots at its base, so tipping it forward a quarter turn lays it on its belly;
            // lifted 2 px so the belly rests on the ground
            this.body.xRot += Mth.HALF_PI;
            this.body.y -= 2.0F;
            look(this.head, s, 0.3F);
            this.head.xRot -= 1.4F;   // chin up, looking ahead
            if (this.tail != null) this.tail.xRot -= 0.9F;   // trailing straight back
            float beat = s.swimming ? Mth.sin(t * 0.45F) * 0.6F : 0.0F;
            this.rightFlipper.zRot += 0.5F + beat;
            this.leftFlipper.zRot -= 0.5F + beat;
            this.rightFoot.z += 4.0F;
            this.leftFoot.z += 4.0F;
            this.rightFoot.y -= 1.0F;
            this.leftFoot.y -= 1.0F;
            return;
        }
        look(this.head, s, 0.8F);
        float pos = s.walkAnimationPos * 0.6662F * 1.6F, speed = Math.min(1.0F, s.walkAnimationSpeed * 1.5F);
        this.body.zRot += Mth.sin(pos) * 0.18F * speed;
        this.rightFoot.y -= Math.max(0, Mth.sin(pos)) * 1.2F * speed;
        this.leftFoot.y -= Math.max(0, -Mth.sin(pos)) * 1.2F * speed;
        float out = 0.12F + speed * 0.35F + Mth.sin(t * 0.06F) * 0.04F;
        this.rightFlipper.zRot += out;
        this.leftFlipper.zRot -= out;
    }
}
