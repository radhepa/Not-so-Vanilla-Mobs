package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Wings fold down the sides at rest and open into slow, deep beats in flight (the primaries swing
 * out to finish each wing); a little waddle on foot, a fluffed-down crouch when sitting, and every
 * so often the head swivels almost all the way round and back.
 */
public class OwlModel extends CritterModel {
    /** Ticks between head swivels, and how long one takes. */
    private static final float SWIVEL_EVERY = 320.0F, SWIVEL_TIME = 60.0F;
    private final ModelPart body, head, rightWing, leftWing, rightTip, leftTip, tail, rightLeg, leftLeg;

    public OwlModel(ModelPart root) {
        super(root, "owl");
        this.body = part("body");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightTip = part("right_wing_tip");
        this.leftTip = part("left_wing_tip");
        this.tail = part("tail");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;

        if (s.flying && !s.sitting) {
            // lean into the flight, head level; slow deep wingbeats (+zRot lifts the right wing out,
            // -zRot the left), the primaries swung out to the side to finish the wing
            this.body.xRot += 0.45F;
            this.head.xRot -= 0.45F;
            look(this.head, s, 0.5F);
            float beat = Mth.cos(t * 0.45F);
            this.rightWing.zRot = 1.35F + beat * 0.55F;
            this.leftWing.zRot = -1.35F - beat * 0.55F;
            this.rightTip.xRot = -1.45F;
            this.leftTip.xRot = -1.45F;
            this.rightTip.zRot = beat * 0.15F;
            this.leftTip.zRot = -beat * 0.15F;
            this.rightLeg.xRot += 1.0F;           // talons tucked back
            this.leftLeg.xRot += 1.0F;
            this.tail.xRot += 0.45F;              // tail held out level
            this.body.y -= beat * 0.6F;           // lifted a little on each downstroke
            return;
        }

        look(this.head, s, 0.6F);
        this.head.yRot += swivel(t);
        if (s.sitting) {
            // settle down over the feet, fluffed out a little
            this.body.y += 1.0F;
            this.rightLeg.y -= 1.0F;
            this.leftLeg.y -= 1.0F;
            this.rightWing.zRot += 0.06F;
            this.leftWing.zRot -= 0.06F;
            this.tail.xRot -= 0.2F;
            return;
        }
        // a rolling waddle on foot
        float step = Mth.cos(s.walkAnimationPos * 0.9F) * s.walkAnimationSpeed;
        this.rightLeg.xRot += step * 1.1F;
        this.leftLeg.xRot -= step * 1.1F;
        this.body.zRot += step * 0.09F;
        this.body.y -= Math.abs(step) * 0.4F;
        // folded wings shuffle now and then
        this.rightWing.zRot += Math.max(0.0F, Mth.sin(t * 0.05F) - 0.9F) * 0.6F;
        this.leftWing.zRot -= Math.max(0.0F, Mth.sin(t * 0.05F) - 0.9F) * 0.6F;
    }

    /**
     * The head swivel: every SWIVEL_EVERY ticks it turns smoothly to about 155 degrees, holds there,
     * and turns back, alternating sides. Owls hatch at different times, so they don't swivel together.
     */
    private static float swivel(float t) {
        float phase = t % SWIVEL_EVERY;
        if (phase >= SWIVEL_TIME) return 0.0F;
        float k = phase / SWIVEL_TIME;
        float amount;
        if (k < 0.3F) amount = smooth(k / 0.3F);
        else if (k < 0.7F) amount = 1.0F;
        else amount = smooth((1.0F - k) / 0.3F);
        float side = ((int) (t / SWIVEL_EVERY) & 1) == 0 ? 1.0F : -1.0F;
        return side * 2.7F * amount;
    }

    private static float smooth(float x) {
        return x * x * (3.0F - 2.0F * x);
    }
}
