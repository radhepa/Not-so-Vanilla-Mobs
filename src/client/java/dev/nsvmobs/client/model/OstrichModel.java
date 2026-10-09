package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A long-legged stride with flexing heels and a pumping neck, wings held a little out for balance
 * as it speeds up; with a rider in the air it spreads its wings wide and beats them slowly, legs
 * tucked back. The saddle shows only when it wears one.
 */
public class OstrichModel extends CritterModel {
    private final ModelPart body, neck, head, rightWing, leftWing, tail, saddle, rightLeg, leftLeg, rightShin, leftShin;

    public OstrichModel(ModelPart root) {
        super(root, "ostrich");
        this.body = part("body");
        this.neck = part("neck");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.tail = part("tail");
        this.saddle = part("saddle");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
        this.rightShin = part("right_shin");
        this.leftShin = part("left_shin");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        this.saddle.visible = s.saddled;
        // the neck swings round to look, the head tips up and down
        this.neck.yRot += s.yRot * Mth.DEG_TO_RAD * 0.5F;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.6F;
        this.tail.yRot += Mth.sin(t * 0.1F) * 0.05F;

        if (s.flying) {
            // gliding: the wings are folded by their rest rotation; open them wide and beat slowly
            float beat = Mth.sin(t * 0.6F) * 0.35F;
            this.rightWing.xRot = 0.0F;
            this.rightWing.yRot = 0.15F;
            this.rightWing.zRot = 0.2F + beat;
            this.leftWing.xRot = 0.0F;
            this.leftWing.yRot = -0.15F;
            this.leftWing.zRot = -0.2F - beat;
            this.neck.xRot += 0.6F;
            this.head.xRot -= 0.6F;
            this.rightLeg.xRot += 0.9F;
            this.leftLeg.xRot += 0.9F;
            this.rightShin.xRot += 0.7F;
            this.leftShin.xRot += 0.7F;
            this.tail.xRot += 0.3F;
            return;
        }

        float pos = s.walkAnimationPos * 0.6662F * 0.9F, speed = Math.min(1.0F, s.walkAnimationSpeed * 1.4F);
        float swing = Mth.cos(pos) * 0.8F * speed;
        this.rightLeg.xRot += swing;
        this.leftLeg.xRot -= swing;
        // the heel folds the foot back as each leg swings forward
        this.rightShin.xRot += Math.max(0.0F, Mth.sin(pos)) * 1.0F * speed;
        this.leftShin.xRot += Math.max(0.0F, -Mth.sin(pos)) * 1.0F * speed;
        this.body.y -= Math.abs(Mth.sin(pos)) * 0.6F * speed;
        this.neck.xRot += (0.1F + Mth.sin(pos * 2.0F) * 0.08F) * speed;
        this.head.xRot -= 0.1F * speed;
        // wings eased out from the flanks for balance at speed
        this.rightWing.zRot += 0.35F * speed;
        this.leftWing.zRot -= 0.35F * speed;
    }
}
