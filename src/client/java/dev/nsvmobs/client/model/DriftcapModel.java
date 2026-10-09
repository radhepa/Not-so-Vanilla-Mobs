package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** The cap pulses like a jellyfish bell while the tendrils sway, trailing back as it drifts along. */
public class DriftcapModel extends CritterModel {
    private final ModelPart cap;
    private final ModelPart[] tendrils = new ModelPart[6];

    public DriftcapModel(ModelPart root) {
        super(root, "driftcap");
        this.cap = part("cap");
        for (int i = 0; i < 6; i++) this.tendrils[i] = part("tendril" + (i + 1));
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float pulse = Mth.sin(t * 0.15F);
        this.cap.yScale = 1.0F - pulse * 0.07F;
        this.cap.xScale = this.cap.zScale = 1.0F + pulse * 0.05F;
        this.cap.y += Mth.sin(t * 0.08F) * 0.8F;
        float trail = Math.min(0.6F, s.walkAnimationSpeed * 0.8F);
        for (int i = 0; i < 6; i++) {
            ModelPart tendril = this.tendrils[i];
            // +xRot swings a hanging tendril back (+z), so it trails behind when the cap moves forward
            tendril.xRot += Mth.sin(t * 0.1F + i * 1.1F) * 0.14F + trail;
            tendril.zRot += Mth.cos(t * 0.09F + i * 1.7F) * 0.14F;
        }
    }
}
