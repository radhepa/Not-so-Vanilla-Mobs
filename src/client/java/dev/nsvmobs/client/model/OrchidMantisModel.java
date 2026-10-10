package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.OrchidMantis;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * In its disguise the orchid mantis sways like a blossom in the breeze, forelegs folded, while its
 * head swivels a long way round to follow whatever moves. It walks on its four petal-lobed legs in
 * two alternating pairs. The strike shoots the forelegs out and snaps the hooks shut in a few ticks;
 * the snag clutches the victim close; the threat display rears up, raises the forelegs wide and
 * flares the wings so the eye-spots on the hindwings face you. A fluttering hop spreads and beats
 * the wings fast.
 */
public class OrchidMantisModel extends CritterModel {
    /** The head's seat on the prothorax, in prothorax space (PRO_TIP in tools/mobs/orchid_mantis.py). */
    private static final float TIP_Y = -0.5F, TIP_Z = -5.0F;
    private static final float MAX_HEAD_YAW = 110.0F;
    private final ModelPart body, prothorax, head, rightAntenna, leftAntenna, abdomen, abdomenTip;
    private final ModelPart rightArm, leftArm, rightClaw, leftClaw, rightHook, leftHook;
    private final ModelPart rightWing, leftWing, rightHind, leftHind;
    private final ModelPart rl1, rl2, ll1, ll2;

    public OrchidMantisModel(ModelPart root) {
        super(root, "orchid_mantis");
        this.body = part("body");
        this.prothorax = part("prothorax");
        this.head = part("head");
        this.rightAntenna = part("right_antenna");
        this.leftAntenna = part("left_antenna");
        this.abdomen = part("abdomen");
        this.abdomenTip = part("abdomen_tip");
        this.rightArm = part("right_arm");
        this.leftArm = part("left_arm");
        this.rightClaw = part("right_claw");
        this.leftClaw = part("left_claw");
        this.rightHook = part("right_hook");
        this.leftHook = part("left_hook");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightHind = part("right_hindwing");
        this.leftHind = part("left_hindwing");
        this.rl1 = part("right_leg1");
        this.rl2 = part("right_leg2");
        this.ll1 = part("left_leg1");
        this.ll2 = part("left_leg2");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;

        this.rightAntenna.xRot += Mth.sin(t * 0.09F) * 0.08F;
        this.leftAntenna.xRot += Mth.sin(t * 0.09F + 1.7F) * 0.08F;
        this.abdomen.xRot += Mth.sin(t * 0.07F) * 0.025F;

        if (s.flying) {
            this.flutter(t);
        } else {
            this.walk(s);
            if (s.lurking && s.mode == OrchidMantis.NONE) this.sway(t);
        }
        if (s.aggressive && s.mode == OrchidMantis.NONE) {
            // a fighting stance: reared a little, forelegs half raised and cocked
            this.prothorax.xRot -= 0.15F;
            this.forelegs(-0.5F, 0.0F, 0.3F, 0.0F);
        }
        switch (s.mode) {
            case OrchidMantis.STRIKE -> this.strike(s.modeAge);
            case OrchidMantis.SNAG -> this.snag(s.modeAge);
            case OrchidMantis.THREAT -> this.threat(s.modeAge);
            default -> {}
        }

        // the head sits on the prothorax tip wherever the prothorax has reared to, and turns a long
        // way round about the vertical (it's a child of body, not of the prothorax)
        float a = this.prothorax.xRot;
        this.head.y = this.prothorax.y + TIP_Y * Mth.cos(a) - TIP_Z * Mth.sin(a);
        this.head.z = this.prothorax.z + TIP_Y * Mth.sin(a) + TIP_Z * Mth.cos(a);
        this.head.yRot += Mth.clamp(s.yRot, -MAX_HEAD_YAW, MAX_HEAD_YAW) * Mth.DEG_TO_RAD;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.6F;
    }

    /** Two alternating pairs (right front with left hind): each leg swings forward lifted, back planted. */
    private void walk(CritterRenderState s) {
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.6F);
        if (amount < 0.01F) return;
        float ph = s.walkAnimationPos * 0.9F;
        float swingA = Mth.sin(ph) * 0.35F * amount, liftA = Math.max(0.0F, Mth.cos(ph)) * 0.3F * amount;
        float swingB = -swingA, liftB = Math.max(0.0F, -Mth.cos(ph)) * 0.3F * amount;
        // a right leg reaches forward with -yRot and lifts with +zRot; a left leg mirrors both
        this.rl1.yRot -= swingA;
        this.rl1.zRot += liftA;
        this.ll2.yRot += swingA;
        this.ll2.zRot -= liftA;
        this.ll1.yRot += swingB;
        this.ll1.zRot -= liftB;
        this.rl2.yRot -= swingB;
        this.rl2.zRot += liftB;
        this.body.y -= Math.abs(Mth.sin(ph)) * 0.25F * amount;
        this.prothorax.xRot += Mth.sin(ph * 2.0F) * 0.03F * amount;
    }

    /** The disguise: rocking gently on planted feet like a bloom in the breeze, forelegs folded. */
    private void sway(float t) {
        float roll = Mth.sin(t * 0.07F) * 0.06F + Mth.sin(t * 0.023F + 0.8F) * 0.035F;
        float pitch = Mth.sin(t * 0.05F + 2.0F) * 0.025F;
        this.body.zRot += roll;
        this.body.xRot += pitch;
        // the feet stay put while the body rocks over them
        this.rl1.zRot -= roll;
        this.rl2.zRot -= roll;
        this.ll1.zRot -= roll;
        this.ll2.zRot -= roll;
        this.prothorax.xRot += Mth.sin(t * 0.06F + 1.0F) * 0.035F;
        this.abdomenTip.xRot += Mth.sin(t * 0.05F + 0.5F) * 0.04F;
        this.forelegs(Mth.sin(t * 0.08F) * 0.04F, 0.0F, 0.0F, 0.0F);
    }

    /** Wings spread out sideways and beating fast, legs dangling, forelegs tucked. */
    private void flutter(float t) {
        float beat = Mth.sin(t * 2.6F) * 0.6F;
        this.rightWing.xRot -= 0.2F;
        this.rightWing.yRot -= 1.3F;
        this.rightWing.zRot += 0.4F + beat;
        this.leftWing.xRot -= 0.2F;
        this.leftWing.yRot += 1.3F;
        this.leftWing.zRot -= 0.4F + beat;
        this.rightHind.yRot += 0.4F;
        this.leftHind.yRot -= 0.4F;
        this.rightHind.zRot += Mth.sin(t * 2.6F - 0.7F) * 0.2F;
        this.leftHind.zRot -= Mth.sin(t * 2.6F - 0.7F) * 0.2F;
        this.rl1.zRot -= 0.25F;
        this.rl2.zRot -= 0.25F;
        this.ll1.zRot += 0.25F;
        this.ll2.zRot += 0.25F;
        this.forelegs(0.15F, 0.0F, -0.1F, 0.0F);
    }

    /** The forelegs shoot out (in under two ticks), then the hooks snap shut. */
    private void strike(float age) {
        float out = smooth(age / 1.6F);
        float shut = smooth((age - 1.6F) / 1.2F);
        this.prothorax.xRot += 0.2F * out;
        this.forelegs(-1.5F * out, -0.1F * out, 2.2F * out, -1.0F * out + 1.2F * shut);
    }

    /** Clutching the victim close, hooks shut, tugging, the head working at it. */
    private void snag(float age) {
        float in = smooth(age / 4.0F);
        float tug = Mth.sin(age * 0.6F) * 0.08F;
        this.prothorax.xRot += Mth.lerp(in, 0.2F, 0.1F);
        this.forelegs(Mth.lerp(in, -1.5F, -1.0F) + tug, Mth.lerp(in, -0.1F, -0.15F), Mth.lerp(in, 2.2F, 0.9F), 0.2F);
        this.head.xRot += Mth.sin(age * 0.9F) * 0.06F;
    }

    /** Reared up, forelegs raised wide, wings flared up and out with the eye-spots facing forward. */
    private void threat(float age) {
        float f = smooth(age / 5.0F);
        this.prothorax.xRot -= 0.35F * f;
        this.head.xRot -= 0.1F * f;
        this.abdomen.xRot += 0.1F * f;
        this.abdomenTip.xRot += 0.15F * f;
        float quiver = Mth.sin(age * 1.7F) * 0.04F * f;
        this.rightWing.xRot += 1.3F * f;
        this.rightWing.zRot -= 0.6F * f + quiver;
        this.leftWing.xRot += 1.3F * f;
        this.leftWing.zRot += 0.6F * f + quiver;
        // fanned within the wing's own plane, so the eye-spot keeps facing forward
        this.rightHind.yRot -= 0.9F * f;
        this.leftHind.yRot += 0.9F * f;
        this.forelegs(-1.4F * f, 0.9F * f, -0.4F * f, -0.6F * f);
        // real mantises rock from side to side in the display
        this.body.zRot += Mth.sin(age * 0.45F) * 0.05F * f;
    }

    /**
     * Adds to both forelegs: coxa pitch (negative swings it forward and up), outward spread, femur
     * unfold (positive straightens it out from the coxa) and hook (negative opens the tibia).
     */
    private void forelegs(float coxa, float spread, float femur, float hook) {
        this.rightArm.xRot += coxa;
        this.leftArm.xRot += coxa;
        this.rightArm.zRot += spread;
        this.leftArm.zRot -= spread;
        this.rightClaw.xRot += femur;
        this.leftClaw.xRot += femur;
        this.rightHook.xRot += hook;
        this.leftHook.xRot += hook;
    }

    private static float smooth(float x) {
        float c = Mth.clamp(x, 0.0F, 1.0F);
        return c * c * (3.0F - 2.0F * c);
    }
}
