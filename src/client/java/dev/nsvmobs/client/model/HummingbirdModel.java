package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Hovering: the wings beat so fast they blur (about 13 beats a second, faster than the frame rate
 * can follow), the body bobs and the tail flicks for balance. Perched, the body levels out and the
 * wings fold back along the sides.
 */
public class HummingbirdModel extends CritterModel {
    private final ModelPart body, head, rightWing, leftWing, tail;

    public HummingbirdModel(ModelPart root) {
        super(root, "hummingbird");
        this.body = part("body");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.tail = part("tail");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        look(this.head, s, 0.5F);
        if (s.flying) {
            float beat = t * 4.1F;
            // +zRot lifts the right wing (it reaches toward -x); a little fore-aft sweep makes the
            // stroke a flat figure of eight
            this.rightWing.zRot += Mth.cos(beat) * 0.95F;
            this.leftWing.zRot -= Mth.cos(beat) * 0.95F;
            this.rightWing.yRot += Mth.sin(beat) * 0.35F;
            this.leftWing.yRot -= Mth.sin(beat) * 0.35F;
            this.body.y += Mth.sin(t * 0.25F) * 0.5F;
            this.body.xRot += Mth.sin(t * 0.2F) * 0.06F;
            this.tail.xRot += Mth.sin(t * 0.5F) * 0.12F;
            return;
        }
        // perched: body nearly level and down on the perch, wings folded back along the sides
        this.body.xRot += 0.35F;
        this.head.xRot -= 0.35F;
        this.body.y += 2.0F;
        this.rightWing.xRot = 0.15F;
        this.rightWing.yRot = 1.35F;
        this.rightWing.zRot = -0.2F;
        this.leftWing.xRot = 0.15F;
        this.leftWing.yRot = -1.35F;
        this.leftWing.zRot = 0.2F;
        this.tail.xRot += Mth.sin(t * 0.1F) * 0.05F;
    }
}
