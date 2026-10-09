package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A waddle with a bobbing neck; hissing (or charging), the neck drops forward low and level, the
 * wings come half out and the tail cocks up; afloat, it rides high with its feet paddling below.
 */
public class GooseModel extends CritterModel {
    private final ModelPart body, neck, head, rightWing, leftWing, tail, rightLeg, leftLeg;

    public GooseModel(ModelPart root) {
        super(root, "goose");
        this.body = part("body");
        this.neck = part("neck");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.tail = part("tail");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        // the neck turns to look around, the head tips up and down
        this.neck.yRot += s.yRot * Mth.DEG_TO_RAD * 0.6F;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.6F;
        this.tail.yRot += Mth.sin(t * 0.12F) * 0.06F;

        if (s.swimming) {
            // feet paddle slowly under the surface, folded back
            float paddle = Mth.sin(t * 0.25F) * 0.45F;
            this.rightLeg.xRot += 0.9F + paddle;
            this.leftLeg.xRot += 0.9F - paddle;
            this.rightLeg.y -= 1.0F;
            this.leftLeg.y -= 1.0F;
            this.body.y += Mth.sin(t * 0.1F) * 0.25F;
            this.neck.xRot += Mth.sin(t * 0.07F) * 0.05F;
        } else {
            float pos = s.walkAnimationPos * 0.6662F * 1.4F, speed = Math.min(1.0F, s.walkAnimationSpeed * 1.5F);
            this.rightLeg.xRot += Mth.cos(pos) * 0.9F * speed;
            this.leftLeg.xRot -= Mth.cos(pos) * 0.9F * speed;
            this.body.zRot += Mth.sin(pos) * 0.09F * speed;     // the waddle
            this.neck.xRot += (0.06F + Mth.sin(pos * 2.0F) * 0.07F) * speed;   // head bobs with each step
        }

        if (s.warning || s.aggressive) {
            // neck stretched forward and low with the bill level, wings half out, tail up; a tremble
            float shake = Mth.sin(t * 1.3F) * 0.04F;
            this.body.xRot += 0.12F;
            this.neck.xRot += 1.0F + shake;
            this.head.xRot -= 1.1F + shake;
            this.rightWing.zRot += 0.5F;
            this.rightWing.yRot -= 0.25F;
            this.leftWing.zRot -= 0.5F;
            this.leftWing.yRot += 0.25F;
            this.tail.xRot += 0.3F;
        }
    }
}
