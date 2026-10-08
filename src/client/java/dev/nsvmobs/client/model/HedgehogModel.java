package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** A busy little trot, a snuffling nose, a loaf when sitting, and a spiky ball when it curls up. */
public class HedgehogModel extends CritterModel {
    private final ModelPart body, head, snout, ball, rf, lf, rh, lh;

    public HedgehogModel(ModelPart root) {
        super(root, "hedgehog");
        this.body = part("body");
        this.head = part("head");
        this.snout = part("snout");
        this.ball = part("ball");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        boolean curled = s.hiding;
        this.ball.visible = curled;
        for (ModelPart p : new ModelPart[]{this.body, this.head, this.rf, this.lf, this.rh, this.lh}) p.visible = !curled;
        if (curled) {
            // a tiny wobble now and then, as if peeking
            this.ball.zRot += Mth.sin(s.ageInTicks * 0.25F) * 0.04F;
            return;
        }
        look(this.head, s, 0.7F);
        this.snout.yRot += Mth.sin(s.ageInTicks * 0.6F) * 0.06F;   // sniff sniff
        if (s.sitting) {
            // legs are only 2 px tall: settle 1 px onto the belly with the hind legs tucked forward
            this.body.y += 1.0F;
            this.head.y += 1.0F;
            this.rh.xRot -= 0.4F;
            this.lh.xRot -= 0.4F;
            this.rh.y -= 0.5F;
            this.lh.y -= 0.5F;
            return;
        }
        walk(s, 0.9F, this.rf, this.lf, this.rh, this.lh);
        this.body.y += Math.abs(Mth.sin(s.walkAnimationPos * 0.6662F)) * -0.5F * s.walkAnimationSpeed;
    }
}
