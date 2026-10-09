package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A stately stalk with the heels flexing on each step; resting, one leg folds up into the belly
 * feathers; fluttering, the wings open wide and beat while the neck stretches out and the legs
 * trail behind; in the flock display it marches with the neck tall, flagging its head side to side.
 */
public class FlamingoModel extends CritterModel {
    private final ModelPart body, neck, neckUpper, head, rightWing, leftWing, tail, rightLeg, leftLeg, rightShin, leftShin;

    public FlamingoModel(ModelPart root) {
        super(root, "flamingo");
        this.body = part("body");
        this.neck = part("neck");
        this.neckUpper = part("neck_upper");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.tail = part("tail");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
        this.rightShin = part("right_shin");
        this.leftShin = part("left_shin");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        // the neck swings round to look, the head tips up and down
        this.neck.yRot += s.yRot * Mth.DEG_TO_RAD * 0.5F;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.5F;
        this.tail.yRot += Mth.sin(t * 0.09F) * 0.05F;

        if (s.flying) {
            // the wings are folded by their rest rotation; open them flat and beat them
            float beat = Mth.sin(t * 1.1F) * 0.7F;
            this.rightWing.xRot = 0.0F;
            this.rightWing.yRot = 0.12F;
            this.rightWing.zRot = 0.15F + beat;
            this.leftWing.xRot = 0.0F;
            this.leftWing.yRot = -0.12F;
            this.leftWing.zRot = -0.15F - beat;
            // neck stretched out ahead, head level; legs trailing straight behind
            this.neck.xRot += 0.6F;
            this.neckUpper.xRot += 0.9F;
            this.head.xRot -= 1.5F;
            this.rightLeg.xRot += 1.25F;
            this.leftLeg.xRot += 1.25F;
            this.body.xRot += Mth.sin(t * 1.1F + 0.6F) * 0.04F;
            return;
        }

        if (s.swimming) {
            // wading or bobbing: slow alternate strides, heels flexing
            float stride = Mth.sin(t * 0.18F);
            this.rightLeg.xRot += stride * 0.35F;
            this.leftLeg.xRot -= stride * 0.35F;
            this.rightShin.xRot += Math.max(0.0F, stride) * 0.6F;
            this.leftShin.xRot += Math.max(0.0F, -stride) * 0.6F;
        } else {
            float pos = s.walkAnimationPos * 0.6662F, speed = Math.min(1.0F, s.walkAnimationSpeed * 1.5F);
            float swing = Mth.cos(pos) * 0.7F * speed;
            this.rightLeg.xRot += swing;
            this.leftLeg.xRot -= swing;
            // the heel folds the foot back while the leg swings forward
            this.rightShin.xRot += Math.max(0.0F, Mth.sin(pos)) * 0.9F * speed;
            this.leftShin.xRot += Math.max(0.0F, -Mth.sin(pos)) * 0.9F * speed;
            this.neck.xRot += Mth.sin(pos * 2.0F) * 0.06F * speed;
            this.body.y += Math.abs(Mth.cos(pos)) * 0.4F * speed;
        }

        if (s.resting) {
            // one leg drawn up into the belly feathers, heel forward and foot folded back
            this.rightLeg.y -= 4.0F;
            this.rightLeg.xRot -= 0.9F;
            this.rightShin.xRot += 2.6F;
            this.leftLeg.x -= 0.6F;
            this.neck.xRot -= 0.12F;
            this.head.xRot += 0.12F;
        }

        if (s.playing) {
            // display march: neck drawn up tall and straight, head flagging from side to side
            float flag = Mth.sin(t * 0.45F);
            this.neck.xRot -= 0.35F;
            this.neckUpper.xRot += 0.65F;
            this.head.xRot -= 0.3F;
            this.neck.yRot += flag * 0.5F;
            this.head.yRot += flag * 0.35F;
        }
    }
}
