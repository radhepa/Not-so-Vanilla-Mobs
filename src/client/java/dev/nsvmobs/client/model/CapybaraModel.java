package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** An unhurried waddle, a lazy head and ears that flick now and then. */
public class CapybaraModel extends CritterModel {
    private final ModelPart head, rf, lf, rh, lh, rightEar, leftEar;

    public CapybaraModel(ModelPart root) {
        super(root, "capybara");
        this.head = part("head");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
        this.rightEar = optional("right_ear");
        this.leftEar = optional("left_ear");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        look(this.head, s, 0.5F);
        walk(s, 0.9F, this.rf, this.lf, this.rh, this.lh);
        this.head.xRot += Mth.sin(s.ageInTicks * 0.04F) * 0.03F;
        // a quick flick every few seconds
        float flick = (s.ageInTicks % 90.0F) < 6.0F ? Mth.sin((s.ageInTicks % 90.0F) / 6.0F * Mth.PI) * 0.5F : 0.0F;
        if (this.rightEar != null) this.rightEar.zRot -= flick;
        if (this.leftEar != null) this.leftEar.zRot += flick * 0.6F;
    }
}
