package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * In the water the great wings rise and fall in slow, deep beats, the tips lagging behind each
 * stroke and twisting through it, while the body lifts a little on every downstroke, pitches with
 * the swim like a dolphin's and trails its whip tail in a lazy wave; the beats quicken and deepen
 * with its speed. Breaching, it flaps hard and fast with its cephalic fins flared. Stranded on land
 * it lies flat with its wings drooped to the ground, twitching now and then.
 */
public class MantaRayModel extends CritterModel {
    /** How far the wings and the tips sag onto the ground out of the water (radians). */
    private static final float DROOP = 0.08F, TIP_DROOP = 0.09F;
    private final ModelPart body, rightWing, leftWing, rightTip, leftTip, rightLobe, leftLobe, tail, tailTip;

    public MantaRayModel(ModelPart root) {
        super(root, "manta_ray");
        this.body = part("body");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightTip = part("right_wing_tip");
        this.leftTip = part("left_wing_tip");
        this.rightLobe = part("right_lobe");
        this.leftLobe = part("left_lobe");
        this.tail = part("tail");
        this.tailTip = part("tail_tip");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float pitch = Mth.clamp(s.xRot, -60.0F, 60.0F) * Mth.DEG_TO_RAD;

        if (s.playing) {
            // breaching: hard, fast, full strokes; the fins flare and the tail streams out straight
            float phase = t * 0.65F;
            this.flap(Mth.sin(phase) * 0.6F, Mth.sin(phase - 0.8F) * 0.5F);
            this.body.xRot += pitch;
            this.body.y += Mth.cos(phase) * 0.8F;
            this.rightLobe.yRot += 0.3F;
            this.leftLobe.yRot -= 0.3F;
            this.rightLobe.xRot -= 0.15F;
            this.leftLobe.xRot -= 0.15F;
            this.tail.xRot += Mth.sin(phase - 1.5F) * 0.06F;
            this.tailTip.xRot += Mth.sin(phase - 2.3F) * 0.1F;
            return;
        }

        if (s.swimming) {
            // slow, deep wing beats that quicken and deepen with speed (walkAnimationPos keeps the
            // phase smooth as the speed changes); the tips trail each stroke and twist through it
            float speed = Mth.clamp(s.walkAnimationSpeed, 0.0F, 1.0F);
            float phase = t * 0.11F + s.walkAnimationPos * 0.2F;
            float amp = 0.3F + 0.18F * speed;
            this.flap(Mth.sin(phase) * amp, Mth.sin(phase - 0.9F) * amp * 0.85F);
            float twist = Mth.cos(phase - 0.9F) * 0.07F;
            this.rightTip.xRot += twist;
            this.leftTip.xRot += twist;
            // the body lifts on each downstroke and pitches with the dive or climb
            this.body.y += Mth.cos(phase) * 0.5F;
            this.body.xRot += pitch + Mth.sin(phase + 0.6F) * 0.025F;
            // the whip tail trails in a lazy wave behind the beat, swaying from side to side
            this.tail.xRot += Mth.sin(phase - 1.8F) * 0.08F;
            this.tailTip.xRot += Mth.sin(phase - 2.6F) * 0.16F;
            this.tail.yRot += Mth.sin(t * 0.05F) * 0.1F;
            this.tailTip.yRot += Mth.sin(t * 0.05F - 0.9F) * 0.2F;
            // the curled fins at the mouth work slowly
            this.rightLobe.xRot += Mth.sin(t * 0.07F) * 0.06F;
            this.leftLobe.xRot += Mth.sin(t * 0.07F + 1.1F) * 0.06F;
            return;
        }

        // stranded: lying flat, the wings drooped onto the ground, a twitch of the wingtips and the
        // tail now and then
        float twitch = Math.max(0.0F, Mth.sin(t * 0.13F) - 0.88F) * 3.0F;
        float flick = Math.max(0.0F, Mth.sin(t * 0.09F + 2.0F) - 0.9F) * 3.0F;
        this.flap(-DROOP + twitch * 0.25F, -TIP_DROOP + twitch);
        this.tail.xRot -= 0.1F;
        this.tailTip.xRot -= 0.05F;
        this.tailTip.yRot += Mth.sin(t * 0.6F) * flick;
    }

    /** Raises both wings by {@code beat} and the tips by {@code tip} (radians; negative lowers them). */
    private void flap(float beat, float tip) {
        this.rightWing.zRot += beat;
        this.leftWing.zRot -= beat;
        this.rightTip.zRot += tip;
        this.leftTip.zRot -= tip;
    }
}
