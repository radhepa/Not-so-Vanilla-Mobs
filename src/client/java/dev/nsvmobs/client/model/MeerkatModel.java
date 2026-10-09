package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** A quick scurry on all fours; on watch it sits bolt upright on its haunches and turns its head about. */
public class MeerkatModel extends CritterModel {
    private final ModelPart body, head, rf, lf, rh, lh, tail;

    public MeerkatModel(ModelPart root) {
        super(root, "meerkat");
        this.body = part("body");
        this.head = part("head");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
        this.tail = part("tail");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        if (s.standing) {
            // body points straight up from the hips and the head turns back level. In that upright
            // frame the head's zRot is the turn left/right (its yRot would roll it), so the look and
            // a slow scan of the horizon go there.
            this.body.xRot -= Mth.HALF_PI - Mth.sin(t * 0.1F) * 0.03F;
            this.head.xRot += Mth.HALF_PI + s.xRot * Mth.DEG_TO_RAD * 0.5F;
            this.head.zRot += s.yRot * Mth.DEG_TO_RAD * 0.5F + Mth.sin(t * 0.045F) * 0.8F;
            this.rf.xRot += 1.0F;   // forepaws held in front of the chest
            this.lf.xRot += 1.0F;
            this.tail.xRot += 1.49F;   // down to the ground behind it, a prop
            return;
        }
        look(this.head, s, 0.8F);
        walk(s, 1.3F, this.rf, this.lf, this.rh, this.lh);
        this.tail.yRot += Mth.sin(t * 0.12F) * 0.15F;
        this.tail.xRot += Mth.sin(s.walkAnimationPos * 0.6662F) * 0.1F * s.walkAnimationSpeed;
    }
}
