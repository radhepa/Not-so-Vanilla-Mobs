package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Sits back on its feet and tail at rest, ears flicking. On the move it bounds: both legs push off
 * together with the feet planted, swing through in the air and reach forward to land, the body
 * pitched forward and the tail streaming out behind as a counterweight. A boxing buck rears up on
 * its tail with its fists raised, jabs right and left, and rocks back for a two-footed kick.
 * Lounging, it lies on its side propped on one elbow. A joey riding in the pouch shows only its head
 * and paws over the rim (its body isn't drawn).
 */
public class KangarooModel extends CritterModel {
    /** Rest pose numbers from the art script (tools/mobs/kangaroo.py). */
    private static final float LEAN = 0.38F;
    private static final float THIGH_REST = -0.95F, SHIN_REST = 1.95F, FOOT_REST = -1.0F, HIP_Y = 15.5F;
    private static final float THIGH_LEN = 6.0F, SHIN_LEN = 7.0F, FOOT_DROP = 1.2276F, TOE_Z = -10.0F, HEEL_Z = 1.0F;
    /** Lounging: how far it rolls onto its side, how far the chest is propped back up, and the head's
     * rotation that keeps it upright and level on that body (worked out offline). */
    private static final float LOUNGE_ROLL = 1.3F, LOUNGE_PROP = 0.6F;
    private static final float LOUNGE_HEAD_X = -1.2716F, LOUNGE_HEAD_Y = -0.6282F, LOUNGE_HEAD_Z = -0.1793F;
    private final ModelPart body, head, rightEar, leftEar, rightArm, leftArm, pouch, tail, tailTip;
    private final ModelPart rightLeg, leftLeg, rightShin, leftShin, rightFoot, leftFoot;

    public KangarooModel(ModelPart root) {
        super(root, "kangaroo");
        this.body = part("body");
        this.head = part("head");
        this.rightEar = part("right_ear");
        this.leftEar = part("left_ear");
        this.rightArm = part("right_arm");
        this.leftArm = part("left_arm");
        this.pouch = part("pouch");
        this.tail = part("tail");
        this.tailTip = part("tail_tip");
        this.rightLeg = part("right_leg");
        this.leftLeg = part("left_leg");
        this.rightShin = part("right_shin");
        this.leftShin = part("left_shin");
        this.rightFoot = part("right_foot");
        this.leftFoot = part("left_foot");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        // visibility isn't part of the pose reset (and the model is shared), so set it every frame
        this.body.skipDraw = false;
        this.tail.visible = true;
        this.rightLeg.visible = true;
        this.leftLeg.visible = true;
        this.pouch.visible = s.variant == 1;   // only does have a pouch
        if (s.isBaby) {
            // a joey's head is big for its size, its ears bigger still
            this.head.xScale = this.head.yScale = this.head.zScale = 1.25F;
            this.rightEar.xScale = this.rightEar.yScale = this.rightEar.zScale = 1.25F;
            this.leftEar.xScale = this.leftEar.yScale = this.leftEar.zScale = 1.25F;
        }
        this.earFlicks(t);

        float speed = Math.min(1.0F, s.walkAnimationSpeed * 1.3F);
        if (s.sitting) {
            this.inPouch(s, t);
        } else if (s.resting) {
            this.lounge(s, t);
        } else if (s.standing && (s.mode != 0 || speed < 0.25F)) {
            // squared up (closing in on its opponent it bounds like any other time)
            this.box(s, t);
        } else {
            float breathe = Mth.sin(t * 0.08F) * 0.015F;
            this.body.xRot += breathe;
            this.head.xRot -= breathe;
            look(this.head, s, 0.8F);
            this.tailTip.yRot += Mth.sin(t * 0.05F) * 0.1F * (1.0F - speed);
            this.rightArm.xRot += Mth.sin(t * 0.07F) * 0.04F;
            this.leftArm.xRot += Mth.sin(t * 0.07F + 1.0F) * 0.04F;
            // a doe with a joey aboard bounds gently, so the joey stays in the pouch
            if (speed > 0.01F) this.hop(s.walkAnimationPos, s.holding ? speed * 0.35F : speed);
        }
    }

    /** Ears turn about on their own now and then. */
    private void earFlicks(float t) {
        float r = Math.max(0.0F, Mth.sin(t * 0.043F) - 0.85F) * 3.0F;
        float l = Math.max(0.0F, Mth.sin(t * 0.037F + 2.0F) - 0.85F) * 3.0F;
        this.rightEar.yRot += r * Mth.sin(t * 0.9F) * 0.6F;
        this.leftEar.yRot -= l * Mth.sin(t * 0.8F) * 0.6F;
        this.rightEar.xRot += Mth.sin(t * 0.06F) * 0.04F;
        this.leftEar.xRot += Mth.sin(t * 0.06F + 1.3F) * 0.04F;
    }

    // -- the bound ------------------------------------------------------------------------------------
    // One bound per 2 pi of walk animation: push-off at phase 0 (legs kicked back, heels up, toes
    // planted), flight until pi (the legs swing through), landing at pi, then a crouch.

    private static float thighAt(float ph) {
        return Mth.cos(ph) * 0.55F - Math.max(0.0F, -Mth.sin(ph)) * 0.15F;
    }

    private static float shinAt(float ph) {
        float s = Mth.sin(ph), c = Mth.cos(ph);
        return -Math.max(0.0F, c) * 0.75F + Math.max(0.0F, -c) * 0.2F + Math.max(0.0F, -s) * 0.45F;
    }

    private static float footAt(float ph) {
        float s = Mth.sin(ph), c = Mth.cos(ph);
        return Math.max(0.0F, c) * 0.95F - Math.max(0.0F, -c) * 0.15F - Math.max(0.0F, -s) * 0.25F;
    }

    /** How far below the ground the long foot would reach with the legs at this phase (negative: above it). */
    private static float reach(float ph, float amount) {
        float a1 = THIGH_REST + thighAt(ph) * amount;
        float a2 = a1 + SHIN_REST + shinAt(ph) * amount;
        float a3 = a2 + FOOT_REST + footAt(ph) * amount;
        float heel = HIP_Y + THIGH_LEN * Mth.cos(a1) + SHIN_LEN * Mth.cos(a2);
        float toeY = heel + FOOT_DROP * Mth.cos(a3) - TOE_Z * Mth.sin(a3);
        float heelY = heel + FOOT_DROP * Mth.cos(a3) - HEEL_Z * Mth.sin(a3);
        return Math.max(toeY, heelY) - 24.0F;
    }

    private void hop(float pos, float amount) {
        float ph = Mth.positiveModulo(pos, Mth.TWO_PI);
        float s = Mth.sin(ph), c = Mth.cos(ph);
        float thigh = thighAt(ph) * amount, shin = shinAt(ph) * amount, foot = footAt(ph) * amount;
        this.rightLeg.xRot += thigh;
        this.leftLeg.xRot += thigh;
        this.rightShin.xRot += shin;
        this.leftShin.xRot += shin;
        this.rightFoot.xRot += foot;
        this.leftFoot.xRot += foot;
        // on the ground the feet stay planted and the body rides up and down on the legs; in the air
        // it arcs from the push-off height to the landing height
        float lift;
        if (ph < Mth.PI) {
            float k = ph / Mth.PI;
            lift = reach(0.0F, amount) * (1.0F - k) + reach(Mth.PI, amount) * k + s * 3.0F * amount;
        } else {
            lift = reach(ph, amount);
        }
        this.body.y -= lift;
        this.tail.y -= lift;
        this.rightLeg.y -= lift;
        this.leftLeg.y -= lift;
        // the body pitches forward into the bound, the head stays level
        float pitch = (0.7F + s * 0.15F - c * 0.1F) * amount;
        this.body.xRot += pitch;
        this.head.xRot -= pitch * 0.85F;
        // arms tucked to the chest, ears back, the tail out straight behind and swinging against the body
        this.rightArm.xRot += 0.6F * amount;
        this.leftArm.xRot += 0.6F * amount;
        this.tail.xRot += (0.62F + s * 0.18F) * amount;
        this.tailTip.xRot -= (0.45F + c * 0.1F) * amount;
        this.rightEar.xRot += 0.35F * amount;
        this.leftEar.xRot += 0.35F * amount;
    }

    // -- boxing ---------------------------------------------------------------------------------------

    /** Reared up on its tail, fists raised; jabs and the two-footed kick play out by modeAge. */
    private void box(CritterRenderState s, float t) {
        float sway = Mth.sin(t * 0.25F);
        // upright on the tail, leaning back a little, bobbing on its toes
        float rise = 3.0F + sway * 0.4F;
        float back = LEAN + 0.12F;
        this.body.xRot -= back;
        this.body.y -= rise;
        this.head.xRot += back;
        look(this.head, s, 0.6F);
        this.tail.y -= rise;
        this.tail.xRot -= 0.32F;
        this.tailTip.xRot += 0.3F;
        this.rightLeg.y -= rise;
        this.leftLeg.y -= rise;
        this.rightLeg.xRot += 0.35F;
        this.leftLeg.xRot += 0.35F;
        this.rightShin.xRot -= 0.64F;
        this.leftShin.xRot -= 0.64F;
        this.rightFoot.xRot += 0.29F;
        this.leftFoot.xRot += 0.29F;
        // ears laid back, fists up in front of the chin
        this.rightEar.xRot += 0.45F;
        this.leftEar.xRot += 0.45F;
        this.rightArm.xRot -= 0.68F + sway * 0.06F;
        this.leftArm.xRot -= 0.68F - sway * 0.06F;
        this.rightArm.zRot += 0.25F;
        this.leftArm.zRot -= 0.25F;

        float a = s.modeAge;
        switch (s.mode) {
            case 1 -> this.jab(this.rightArm, -1.0F, a);
            case 2 -> this.jab(this.leftArm, 1.0F, a);
            case 3 -> this.kick(a);
            default -> {}
        }
    }

    /** A quick straight punch: out in 3 ticks, back by 8, the shoulder turning into it. */
    private void jab(ModelPart arm, float side, float age) {
        float k = Mth.clamp(age < 3.0F ? age / 3.0F : 1.0F - (age - 4.0F) / 4.0F, 0.0F, 1.0F);
        arm.xRot += 0.15F * k;
        arm.zRot += 0.25F * side * k;
        arm.z -= 3.5F * k;
        arm.y += 0.5F * k;
        this.body.yRot += 0.3F * side * k;
        this.head.yRot -= 0.2F * side * k;
    }

    /**
     * The kick: rocks back onto the tail (0-6 ticks), both feet shoot forward together (6-9), then it
     * drops back down onto them (9-16).
     */
    private void kick(float age) {
        float wind = Mth.clamp(age / 6.0F, 0.0F, 1.0F);
        float strike = age < 6.0F ? 0.0F : age < 9.0F ? (age - 6.0F) / 3.0F : Math.max(0.0F, 1.0F - (age - 9.0F) / 7.0F);
        float back = Math.max(wind, strike) * (age < 9.0F ? 1.0F : strike);
        this.body.xRot -= 0.45F * back;
        this.head.xRot += 0.45F * back;
        this.body.y -= 1.5F * back;
        this.tail.xRot -= 0.12F * back;
        float legLift = 1.5F * back + 3.0F * strike;
        float legSwing = 0.4F * wind * (1.0F - strike) + 1.35F * strike;
        float shinBend = 0.4F * wind * (1.0F - strike) - 1.25F * strike;
        this.rightLeg.y -= legLift;
        this.leftLeg.y -= legLift;
        this.rightLeg.z += strike;
        this.leftLeg.z += strike;
        this.rightLeg.xRot -= legSwing;
        this.leftLeg.xRot -= legSwing;
        this.rightShin.xRot += shinBend;
        this.leftShin.xRot += shinBend;
        this.rightFoot.xRot -= 0.3F * strike;
        this.leftFoot.xRot -= 0.3F * strike;
        // arms thrown up and out for balance
        this.rightArm.xRot -= 0.3F * strike;
        this.leftArm.xRot -= 0.3F * strike;
        this.rightArm.zRot += 0.35F * strike;
        this.leftArm.zRot -= 0.35F * strike;
    }

    // -- resting --------------------------------------------------------------------------------------

    /**
     * Lying on its left side, propped on that elbow. First it's laid out flat (body tipped forward,
     * legs stretched ahead, tail straight back), then everything hung off the root rolls over onto the
     * left side about a line along the ground, and the chest is propped back up a little. The head
     * keeps upright and level.
     */
    private void lounge(CritterRenderState s, float t) {
        this.body.xRot += 0.95F;
        for (ModelPart leg : new ModelPart[]{this.rightLeg, this.leftLeg}) leg.xRot -= 0.3F;
        this.rightShin.xRot -= 1.0F;
        this.leftShin.xRot -= 1.0F;
        this.rightFoot.xRot += 1.5F;
        this.leftFoot.xRot += 1.5F;
        this.tail.xRot += 0.7F;
        this.tailTip.xRot -= 0.62F - Mth.sin(t * 0.04F) * 0.05F;
        for (ModelPart p : new ModelPart[]{this.body, this.tail, this.rightLeg, this.leftLeg}) {
            roll(p, LOUNGE_ROLL);
            p.x -= 5.0F;
            p.y -= 3.0F;
        }
        this.body.zRot -= LOUNGE_PROP;
        this.leftLeg.xRot -= 0.12F;
        this.head.xRot = LOUNGE_HEAD_X;
        this.head.yRot = LOUNGE_HEAD_Y;
        this.head.zRot = LOUNGE_HEAD_Z;
        look(this.head, s, 0.5F);
        this.head.xRot += Mth.sin(t * 0.05F) * 0.03F;
        // the lower (left) arm props it up; the upper arm rests on the flank
        this.leftArm.xRot += 0.55F;
        this.leftArm.zRot -= 0.6F;
        this.rightArm.xRot += 0.9F;
        this.rightArm.zRot += 0.1F;
    }

    /** Rolls a root-level part by {@code angle} about the line along z through (0, 22). */
    private static void roll(ModelPart p, float angle) {
        float dx = p.x, dy = p.y - 22.0F;
        float c = Mth.cos(angle), sn = Mth.sin(angle);
        p.x = dx * c - dy * sn;
        p.y = 22.0F + dx * sn + dy * c;
        p.zRot += angle;
    }

    /**
     * A joey in its mother's pouch: the body upright and undrawn, legs and tail hidden, so only the
     * head and the paws resting on the rim show. The entity sits low enough that the rest is inside her.
     */
    private void inPouch(CritterRenderState s, float t) {
        this.body.skipDraw = true;
        this.tail.visible = false;
        this.rightLeg.visible = false;
        this.leftLeg.visible = false;
        this.pouch.visible = false;
        this.body.xRot -= LEAN;
        this.head.xRot += LEAN;
        look(this.head, s, 0.7F);
        this.head.xRot += Mth.sin(t * 0.06F) * 0.05F;
        this.rightArm.xRot -= 0.95F;
        this.leftArm.xRot -= 0.95F;
        this.rightArm.zRot += 0.3F;
        this.leftArm.zRot -= 0.3F;
    }
}
