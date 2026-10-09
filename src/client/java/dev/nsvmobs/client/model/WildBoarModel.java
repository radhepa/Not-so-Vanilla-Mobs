package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** A heavy trot; charging, it drops its head to lead with the tusks. The tail flicks. */
public class WildBoarModel extends CritterModel {
    private final ModelPart head, rf, lf, rh, lh, tail;

    public WildBoarModel(ModelPart root) {
        super(root, "wild_boar");
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
        look(this.head, s, 0.6F);
        walk(s, 1.2F, this.rf, this.lf, this.rh, this.lh);
        float t = s.ageInTicks;
        if (s.aggressive) {
            this.head.xRot += 0.4F;
            this.head.y += 0.5F;
        } else {
            // snuffling about now and then
            this.head.xRot += Math.max(0, Mth.sin(t * 0.04F) - 0.6F) * 1.2F;
        }
        this.tail.zRot += Mth.sin(t * 0.3F) * 0.25F;
    }
}
