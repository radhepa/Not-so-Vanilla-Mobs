package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A slow, jerky walk: each step hangs at the end of its swing and then snaps through, while the body
 * rocks back and forth like a leaf in the wind. The turret eyes dart about on their own, each one
 * holding a gaze and then flicking somewhere new. Sitting, it settles low on splayed legs.
 */
public class ChameleonModel extends CritterModel {
    private final ModelPart body, head, rightEye, leftEye, tail, tailCurl, rf, lf, rh, lh;

    public ChameleonModel(ModelPart root) {
        super(root, "chameleon");
        this.body = part("body");
        this.head = part("head");
        this.rightEye = part("right_eye");
        this.leftEye = part("left_eye");
        this.tail = part("tail");
        this.tailCurl = part("tail_curl");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;

        // each eye picks a new direction every second or two and flicks to it
        this.rightEye.yRot += dart(t, 37.0F, 1) * 0.6F;
        this.rightEye.xRot += dart(t, 37.0F, 2) * 0.3F;
        this.leftEye.yRot += dart(t, 29.0F, 3) * 0.6F;
        this.leftEye.xRot += dart(t, 29.0F, 4) * 0.3F;
        this.tail.xRot += Mth.sin(t * 0.05F) * 0.04F;
        this.tailCurl.xRot += Mth.sin(t * 0.05F - 0.6F) * 0.05F;

        if (s.sitting) {
            // low on its belly, legs splayed wide
            this.body.y += 1.0F;
            this.tail.xRot += 0.2F;          // lifts the curl clear of the ground
            this.rf.zRot += 0.6F;
            this.rh.zRot += 0.6F;
            this.lf.zRot -= 0.6F;
            this.lh.zRot -= 0.6F;
            look(this.head, s, 0.5F);
            return;
        }

        // the stride hangs at each end and snaps through the middle: stepped is the walk phase
        // with a smooth pause at every whole step
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.8F);
        float g = s.walkAnimationPos * 0.45F;
        float whole = Mth.floor(g);
        float f = g - whole;
        float stepped = whole + f * f * f * (f * (f * 6.0F - 15.0F) + 10.0F);
        float swing = Mth.cos(stepped * Mth.PI) * 0.5F * amount;
        this.rh.xRot += swing;
        this.lf.xRot += swing;
        this.lh.xRot -= swing;
        this.rf.xRot -= swing;
        // rocking: the body sways forward and back and rolls as the weight shifts
        float rock = Mth.sin(stepped * Mth.PI) * amount;
        this.body.z += rock * 0.45F;
        this.body.zRot += rock * 0.07F;
        this.head.zRot -= rock * 0.05F;
        look(this.head, s, 0.5F);
    }

    /** A gaze angle in -1..1 that holds for {@code period} ticks, then flicks to a new one. */
    private static float dart(float t, float period, int seed) {
        float k = Mth.floor(t / period);
        float f = Math.min(1.0F, (t - k * period) / 4.0F);   // the flick takes four ticks
        float from = noise(k - 1.0F, seed), to = noise(k, seed);
        return from + (to - from) * f * f * (3.0F - 2.0F * f);
    }

    private static float noise(float n, int seed) {
        float x = Mth.sin(n * 12.9898F + seed * 78.233F) * 43758.547F;
        return (x - Mth.floor(x)) * 2.0F - 1.0F;
    }
}
