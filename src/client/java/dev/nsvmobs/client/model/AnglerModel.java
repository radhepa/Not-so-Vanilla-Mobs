package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A slow sculling tail, rowing fins and a lure that bobs on its stalk; the jaw gapes wide when it
 * lunges. Stranded on land it lies on its side.
 */
public class AnglerModel extends CritterModel {
    private final ModelPart body, jaw, lureStalk, lure, tail, tailFin, rightFin, leftFin;

    public AnglerModel(ModelPart root) {
        super(root, "angler");
        this.body = part("body");
        this.jaw = part("jaw");
        this.lureStalk = part("lure_stalk");
        this.lure = part("lure");
        this.tail = part("tail");
        this.tailFin = part("tail_fin");
        this.rightFin = part("right_fin");
        this.leftFin = part("left_fin");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float swim = 0.25F + Math.min(1.0F, s.walkAnimationSpeed) * 0.5F;
        this.body.xRot += s.xRot * Mth.DEG_TO_RAD;
        this.tail.yRot += Mth.sin(t * 0.3F) * 0.3F * swim;
        this.tailFin.yRot += Mth.sin(t * 0.3F - 0.8F) * 0.45F * swim;
        // +zRot lifts a fin on the right side; the left mirrors it
        this.rightFin.zRot += Mth.sin(t * 0.22F) * 0.35F;
        this.leftFin.zRot -= Mth.sin(t * 0.22F) * 0.35F;
        // the bulb hangs straight down: whatever the stalk sways, the lure takes back (plus a little swing)
        float sway = Mth.sin(t * 0.06F) * 0.08F;
        this.lureStalk.xRot += sway;
        this.lure.xRot += -sway + Mth.sin(t * 0.06F - 0.9F) * 0.12F;
        this.lure.zRot += Mth.cos(t * 0.05F) * 0.1F;
        // closed at rest (a small gape makes the tooth rows overlap); wide open, snapping, when it lunges
        this.jaw.xRot += s.aggressive ? 0.6F + Mth.sin(t * 0.5F) * 0.1F : 0.0F;
        if (!s.swimming) {
            this.body.zRot += Mth.HALF_PI;
            this.body.y += 1.0F;
        }
    }
}
