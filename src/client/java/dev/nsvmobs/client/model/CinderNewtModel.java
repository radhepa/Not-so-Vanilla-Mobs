package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A lizard walk: the splayed legs sweep forward and back in diagonal pairs, lifting as they swing,
 * while the spine wiggles side to side and the flat tail swishes after it. At rest the throat pumps
 * and the tail tip idles; when it means to bite, it lifts its head and gapes.
 */
public class CinderNewtModel extends CritterModel {
    private final ModelPart body, head, jaw, tail, tailTip, rf, lf, rh, lh;

    public CinderNewtModel(ModelPart root) {
        super(root, "cinder_newt");
        this.body = part("body");
        this.head = part("head");
        this.jaw = part("jaw");
        this.tail = part("tail");
        this.tailTip = part("tail_tip");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.4F);
        float p = s.walkAnimationPos * 0.9F;

        // diagonal pairs: right front with left hind, left front with right hind. The legs stick out
        // sideways, so a yaw sweeps a foot forward or back and a roll lifts it; each foot lifts
        // while it swings forward.
        float swing = Mth.sin(p) * 0.6F * amount;
        float liftA = Math.max(0.0F, Mth.cos(p)) * 0.45F * amount;
        float liftB = Math.max(0.0F, -Mth.cos(p)) * 0.45F * amount;
        this.rf.yRot -= swing;
        this.lh.yRot += swing;
        this.lf.yRot -= swing;
        this.rh.yRot += swing;
        this.rf.zRot += liftA;
        this.lh.zRot -= liftA;
        this.lf.zRot -= liftB;
        this.rh.zRot += liftB;

        // the spine wiggles with the stride; head steadies itself, the tail follows a beat behind
        float wiggle = Mth.sin(p) * 0.15F * amount;
        this.body.yRot += wiggle;
        this.head.yRot -= wiggle * 1.5F;
        this.tail.yRot -= wiggle * 2.0F + Mth.sin(t * 0.05F) * 0.08F;
        this.tailTip.yRot -= Mth.sin(p - 1.2F) * 0.3F * amount + Mth.sin(t * 0.05F - 0.8F) * 0.14F;
        look(this.head, s, 0.6F);

        if (s.aggressive) {
            this.head.xRot -= 0.15F;
            this.jaw.xRot += 0.35F + Math.max(0.0F, Mth.sin(t * 0.5F)) * 0.3F;
        } else {
            // the throat pumps gently
            this.jaw.y += Math.max(0.0F, Mth.sin(t * 0.3F)) * 0.18F;
        }
    }
}
