package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Sandmaw;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * The worm bursts up out of the ground (the whole column slides up from below), sways, opens its
 * four jaws wide to roar and to bite, and slides back down when it dives.
 */
public class SandmawModel extends CritterModel {
    /** How far (px) the column has to drop to be completely underground. */
    static final float SINK = 56.0F;
    private final ModelPart segment1, segment2, segment3, head, jawTop, jawBottom, jawLeft, jawRight;

    public SandmawModel(ModelPart root) {
        super(root, "sandmaw");
        this.segment1 = part("segment1");
        this.segment2 = part("segment2");
        this.segment3 = part("segment3");
        this.head = part("head");
        this.jawTop = part("jaw_top");
        this.jawBottom = part("jaw_bottom");
        this.jawLeft = part("jaw_left");
        this.jawRight = part("jaw_right");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        if (s.hidden) return;
        float t = s.ageInTicks;
        float sink = 0.0F;
        if (s.mode == Sandmaw.SURFACED) sink = 1.0F - Math.min(1.0F, s.modeAge / Sandmaw.RISE_TICKS);
        else if (s.mode == Sandmaw.DIVING) sink = Math.min(1.0F, s.modeAge / Sandmaw.DIVE_TICKS);
        this.segment1.y += sink * sink * SINK;

        float sway = Mth.sin(t * 0.09F);
        this.segment1.zRot += sway * 0.04F;
        this.segment2.zRot += Mth.sin(t * 0.09F + 1.0F) * 0.07F;
        this.segment3.zRot -= Mth.sin(t * 0.09F + 2.0F) * 0.07F;
        this.segment2.xRot += Mth.sin(t * 0.06F) * 0.05F;
        this.segment3.xRot += Mth.sin(t * 0.06F + 1.2F) * 0.06F;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.4F;

        // jaws: a slow working at rest, wide open on surfacing (the roar) and on every bite
        float open = 0.12F + Math.max(0, Mth.sin(t * 0.12F)) * 0.12F;
        if (s.mode == Sandmaw.SURFACED && s.modeAge < 16) open = Math.max(open, Mth.sin(Math.min(1.0F, s.modeAge / 16.0F) * Mth.PI) * 1.0F);
        open = Math.max(open, Mth.sin(s.swing * Mth.PI) * 0.95F);
        this.jawTop.xRot -= open;
        this.jawBottom.xRot += open;
        this.jawLeft.yRot -= open;
        this.jawRight.yRot += open;
    }
}
