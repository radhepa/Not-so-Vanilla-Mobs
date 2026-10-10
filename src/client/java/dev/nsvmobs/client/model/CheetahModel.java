package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Cheetah;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A light, long-striding walk with the head carried low and level and the long tail swaying.
 * Stalking, it sinks low on bent legs, shoulder blades high and head stretched out level, and steps
 * slowly. Sprinting, it's a full double-suspension gallop: the spine bunches and stretches, the legs
 * reach far out in front and behind, the head stays dead level and the tail streams out as a
 * rudder. It pounces forelegs first, pants with its tongue out and its flanks heaving when winded,
 * sits up tall (tamed, or on watch) and lounges stretched out in the grass with its head up.
 */
public class CheetahModel extends CritterModel {
    private final ModelPart body, hips, neck, head, jaw, tongue, rightEar, leftEar, tail, tailMid, tailTip;
    private final ModelPart rf, rfLower, lf, lfLower, rh, rhLower, rhFoot, lh, lhLower, lhFoot;

    public CheetahModel(ModelPart root) {
        super(root, "cheetah");
        this.body = part("body");
        this.hips = part("hips");
        this.neck = part("neck");
        this.head = part("head");
        this.jaw = part("jaw");
        this.tongue = part("tongue");
        this.rightEar = part("right_ear");
        this.leftEar = part("left_ear");
        this.tail = part("tail");
        this.tailMid = part("tail_mid");
        this.tailTip = part("tail_tip");
        this.rf = part("right_front_leg");
        this.rfLower = part("right_front_leg_lower");
        this.lf = part("left_front_leg");
        this.lfLower = part("left_front_leg_lower");
        this.rh = part("right_hind_leg");
        this.rhLower = part("right_hind_leg_lower");
        this.rhFoot = part("right_hind_foot");
        this.lh = part("left_hind_leg");
        this.lhLower = part("left_hind_leg_lower");
        this.lhFoot = part("left_hind_foot");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float yaw = s.yRot * Mth.DEG_TO_RAD, pitch = s.xRot * Mth.DEG_TO_RAD;
        this.tongue.visible = s.mode == Cheetah.WINDED;
        if (s.resting) {
            this.lounge(t, yaw, pitch);
        } else if (s.sitting) {
            this.sit(t, yaw, pitch);
        } else if (s.mode == Cheetah.SPRINT) {
            this.gallop(s, t, yaw);
        } else if (s.mode == Cheetah.POUNCE) {
            this.pounce(s, pitch);
        } else {
            this.stride(s, t, yaw, pitch);
        }
        if (s.mode == Cheetah.WINDED) {
            // panting: jaw open, tongue out, the flanks heaving fast
            float b = 0.5F + 0.5F * Mth.sin(t * 1.1F);
            this.jaw.xRot += 0.4F + 0.12F * b;
            this.tongue.z -= 1.2F;
            this.tongue.y += 0.25F;
            this.tongue.xRot += 0.35F + 0.1F * b;
            this.hips.xScale = 1.0F + 0.07F * b;
            if (!s.sitting && !s.resting) {
                this.neck.xRot += 0.3F;
                this.head.xRot -= 0.1F;
            }
        }
        // a bite
        float bite = Mth.sin(s.swing * Mth.PI);
        this.neck.xRot += bite * 0.3F;
        this.jaw.xRot += bite * 0.6F;
    }

    /** Walking (also stalking and winded): long diagonal strides, the lower legs folding as they swing through. */
    private void stride(CritterRenderState s, float t, float yaw, float pitch) {
        boolean stalk = s.mode == Cheetah.STALK;
        float pos = s.walkAnimationPos * 0.6662F * (s.isBaby ? 0.5F : 1.0F), sp = s.walkAnimationSpeed;
        float swing = Mth.cos(pos) * (stalk ? 0.45F : 0.7F) * sp;
        this.rh.xRot += swing;
        this.lf.xRot += swing;
        this.lh.xRot -= swing;
        this.rf.xRot -= swing;
        float fold = Mth.sin(pos) * sp;
        this.rfLower.xRot += Math.max(0.0F, -fold) * 0.8F;
        this.lfLower.xRot += Math.max(0.0F, fold) * 0.8F;
        this.rhLower.xRot += Math.max(0.0F, fold) * 0.5F;
        this.rhFoot.xRot -= Math.max(0.0F, fold) * 0.5F;
        this.lhLower.xRot += Math.max(0.0F, -fold) * 0.5F;
        this.lhFoot.xRot -= Math.max(0.0F, -fold) * 0.5F;
        this.neck.xRot += Mth.cos(pos * 2.0F) * 0.04F * sp;
        this.neck.yRot += yaw * 0.8F;
        this.head.xRot += pitch * 0.6F;
        this.tail.yRot += Mth.sin(t * 0.07F) * 0.12F + Mth.sin(pos) * 0.1F * sp;
        this.tailMid.yRot += Mth.sin(t * 0.07F - 0.6F) * 0.14F;
        this.tailTip.xRot += Mth.sin(t * 0.11F) * 0.12F;
        if (stalk) {
            // body 3 px lower; the legs fold to keep the paws on the ground (elbows back, wrists forward;
            // the hind legs crouch deeper at stifle and hock); head low and level, the tail tip twitching
            this.body.y += 3.0F;
            this.rf.xRot += 0.68F;
            this.lf.xRot += 0.68F;
            this.rfLower.xRot -= 1.54F;
            this.lfLower.xRot -= 1.54F;
            this.rh.xRot -= 0.55F;
            this.lh.xRot -= 0.55F;
            this.rhLower.xRot += 1.1F;
            this.lhLower.xRot += 1.1F;
            this.rhFoot.xRot -= 0.6F;
            this.lhFoot.xRot -= 0.6F;
            this.neck.xRot += 0.4F;
            this.head.xRot -= 0.4F;
            this.tail.xRot -= 0.15F;
            this.tailTip.xRot += Mth.sin(t * 0.3F) * 0.2F;
            this.rightEar.xRot -= 0.25F;
            this.leftEar.xRot -= 0.25F;
        } else if (sp < 0.1F) {
            // standing about: now and then an ear flicks
            float c1 = (t + 23.0F) % 110.0F, c2 = (t + 61.0F) % 90.0F;
            if (c1 < 6.0F) this.rightEar.zRot -= Mth.sin(c1 / 6.0F * Mth.PI) * 0.4F;
            if (c2 < 6.0F) this.leftEar.zRot += Mth.sin(c2 / 6.0F * Mth.PI) * 0.4F;
        }
    }

    /**
     * The double-suspension gallop. g = +1 is the gathered suspension (spine arched, the hind legs
     * swung forward past the front ones), g = -1 the stretched-out one (front legs reaching far ahead,
     * hind legs far behind). The right legs lead. Scaled by how fast it's moving.
     */
    private void gallop(CritterRenderState s, float t, float yaw) {
        float ph = s.walkAnimationPos * (s.isBaby ? 0.45F : 0.9F);
        float a = Math.min(1.0F, s.walkAnimationSpeed * 1.25F);
        float g = Mth.sin(ph);
        float lead = 0.4F;
        float flex = -0.38F * g * a;
        this.hips.xRot += flex;
        this.body.xRot += 0.1F * g * a;
        this.body.y += Math.abs(Mth.cos(ph)) * 0.5F * a;
        this.frontLeg(this.rf, this.rfLower, ph + lead, a);
        this.frontLeg(this.lf, this.lfLower, ph, a);
        this.hindLeg(this.rh, this.rhLower, this.rhFoot, ph + lead, a);
        this.hindLeg(this.lh, this.lhLower, this.lhFoot, ph, a);
        // the head stays level and steady, stretched forward, ears laid back
        this.neck.xRot += 0.3F * a;
        this.neck.yRot += yaw * 0.3F;
        this.head.xRot -= 0.3F * a + 0.1F * g * a;
        this.rightEar.xRot -= 0.7F * a;
        this.leftEar.xRot -= 0.7F * a;
        // the tail streams out straight behind, steering
        this.tail.xRot += 1.15F * a - flex * 0.6F;
        this.tailMid.xRot -= 0.45F * a;
        this.tailTip.xRot -= 0.8F * a;
        this.tail.yRot += Mth.sin(t * 0.45F) * 0.14F * a;
        this.tailTip.yRot += Mth.sin(t * 0.45F - 1.0F) * 0.2F * a;
    }

    /** Back under the body when gathered, reaching far forward when stretched out; the wrist folds on the swing forward. */
    private void frontLeg(ModelPart leg, ModelPart lower, float ph, float a) {
        leg.xRot += a * (-0.2F + 1.1F * Mth.sin(ph));
        lower.xRot += a * 1.4F * Math.max(0.0F, -Mth.cos(ph));
    }

    /** Forward under the body when gathered, far back when stretched out; the hock folds on the swing forward and straightens on the push. */
    private void hindLeg(ModelPart thigh, ModelPart gaskin, ModelPart foot, float ph, float a) {
        float h = Mth.sin(ph), c = Mth.cos(ph);
        thigh.xRot += a * (0.1F - 1.05F * h);
        gaskin.xRot += a * (0.9F * Math.max(0.0F, c) - 0.35F * Math.max(0.0F, -h));
        foot.xRot += a * (-0.7F * Math.max(0.0F, c) + 0.6F * Math.max(0.0F, -h));
    }

    /** Airborne: forelegs reaching for the prey, hind legs stretched out behind, jaws open. */
    private void pounce(CritterRenderState s, float pitch) {
        float k = Math.min(1.0F, s.modeAge / 2.0F);
        this.rf.xRot -= 1.05F * k;
        this.lf.xRot -= 0.9F * k;
        this.rfLower.xRot -= 0.2F * k;
        this.lfLower.xRot -= 0.05F * k;
        this.rh.xRot += 0.95F * k;
        this.lh.xRot += 0.85F * k;
        this.rhLower.xRot -= 0.45F * k;
        this.lhLower.xRot -= 0.45F * k;
        this.rhFoot.xRot += 0.7F * k;
        this.lhFoot.xRot += 0.7F * k;
        this.body.xRot -= 0.15F * k;
        this.hips.xRot += 0.2F * k;
        this.neck.xRot += 0.15F * k;
        this.head.xRot -= 0.15F * k - pitch * 0.4F;
        this.jaw.xRot += 0.5F * k;
        this.rightEar.xRot -= 0.6F * k;
        this.leftEar.xRot -= 0.6F * k;
        this.tail.xRot += 1.1F * k;
        this.tailMid.xRot -= 0.4F * k;
        this.tailTip.xRot -= 0.7F * k;
    }

    /**
     * Upright on its haunches: the body tips back about the mid-back and drops onto the rump, the
     * front legs stand straight, the hind legs fold flat beside it and the tail curls round on the
     * ground. The head stays level and watches.
     */
    private void sit(float t, float yaw, float pitch) {
        float tilt = -0.72F;
        this.body.xRot += tilt;
        this.body.y += 2.8F;
        this.body.z += 1.5F;
        this.rf.xRot -= tilt;
        this.lf.xRot -= tilt;
        this.rf.y += 2.0F;
        this.lf.y += 2.0F;
        for (ModelPart thigh : new ModelPart[]{this.rh, this.lh}) thigh.xRot -= 0.9F;
        this.rhLower.xRot += 1.6F;
        this.lhLower.xRot += 1.6F;
        this.rhFoot.xRot -= 1.3F;
        this.lhFoot.xRot -= 1.3F;
        this.neck.xRot -= 0.25F;
        this.head.xRot -= tilt - 0.25F;
        this.neck.yRot += yaw * 0.8F;
        this.head.xRot += pitch * 0.6F;
        this.tail.xRot += 1.65F;
        this.tailMid.xRot -= 0.23F;
        this.tailMid.yRot += 0.7F;
        this.tailTip.xRot -= 0.85F;
        this.tailTip.yRot += 0.8F + Mth.sin(t * 0.08F) * 0.15F;
    }

    /**
     * Lying stretched out on its belly, forelegs straight out in front, hind legs folded under, the
     * tail lying along the ground with the tip curled, head up and looking about.
     */
    private void lounge(float t, float yaw, float pitch) {
        this.body.y += 6.5F;
        this.hips.xRot -= 0.15F;
        this.rf.xRot -= 1.45F;
        this.lf.xRot -= 1.45F;
        this.rf.y += 1.6F;
        this.lf.y += 1.6F;
        this.rfLower.xRot += 0.1F;
        this.lfLower.xRot += 0.1F;
        this.rh.xRot -= 1.2F;
        this.lh.xRot -= 1.2F;
        this.rh.zRot -= 0.25F;
        this.lh.zRot += 0.25F;
        this.rhLower.xRot += 2.2F;
        this.lhLower.xRot += 2.2F;
        this.rhFoot.xRot -= 1.15F;
        this.lhFoot.xRot -= 1.15F;
        this.neck.xRot -= 0.45F;
        this.head.xRot += 0.45F;
        this.neck.yRot += yaw * 0.8F;
        this.head.xRot += pitch * 0.6F;
        this.tail.xRot += 0.55F;
        this.tail.yRot += 0.3F;
        this.tailMid.xRot += 0.3F;
        this.tailMid.yRot += 0.4F;
        this.tailTip.xRot -= 0.85F;
        this.tailTip.yRot += 0.5F + Mth.sin(t * 0.06F) * 0.15F;
    }
}
