package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A slow, heavy amble: the pillar legs swing stiffly one after another, the body rolls and sinks
 * with each step, the head nods and the trunk swings like a pendulum a beat behind. Standing, it fans
 * its ears now and then and lets its trunk sway and curl (the tip curled up when it holds water).
 * Trumpeting (`warning`) it throws its head up, flares its ears wide, opens its mouth and raises its
 * trunk in a curl; charging (`aggressive`) it drops its head with the ears out and the trunk tucked
 * under; spraying (`playing`) it lifts the trunk high and aims it forward over its head, sweeping it
 * a little. Calves have no tusks.
 */
public class ElephantModel extends CritterModel {
    private final ModelPart body, head, tail, trunk1, trunk2, trunk3, rightEar, leftEar, rightTusk, leftTusk;
    private final ModelPart rf, lf, rh, lh;
    private final ModelPart jaw;

    public ElephantModel(ModelPart root) {
        super(root, "elephant");
        this.body = part("body");
        this.head = part("head");
        this.tail = part("tail");
        this.trunk1 = part("trunk1");
        this.trunk2 = part("trunk2");
        this.trunk3 = part("trunk3");
        this.rightEar = part("right_ear");
        this.leftEar = part("left_ear");
        this.rightTusk = part("right_tusk");
        this.leftTusk = part("left_tusk");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
        this.jaw = optional("jaw");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        this.rightTusk.visible = !s.isBaby;
        this.leftTusk.visible = !s.isBaby;

        // a heavy head turns only so far; the ear on the inside of the turn swings out to stay clear
        // of the shoulder
        float yaw = Mth.clamp(s.yRot, -40.0F, 40.0F) * Mth.DEG_TO_RAD * 0.55F;
        this.head.yRot += yaw;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.35F;
        this.rightEar.yRot -= Math.max(0.0F, yaw);
        this.leftEar.yRot -= Math.min(0.0F, yaw);

        // the amble: a lateral walk, each leg a quarter of a stride after the last
        // (left hind, left fore, right hind, right fore)
        float p = s.walkAnimationPos * 0.45F, speed = Math.min(1.0F, s.walkAnimationSpeed);
        float a = 0.42F * speed;
        this.lh.xRot += Mth.sin(p) * a;
        this.lf.xRot += Mth.sin(p - Mth.HALF_PI) * a;
        this.rh.xRot += Mth.sin(p - Mth.PI) * a;
        this.rf.xRot += Mth.sin(p - Mth.PI * 1.5F) * a;
        this.body.zRot += Mth.sin(p) * 0.03F * speed;              // the body rolls over each hind foot
        this.body.y += (1.0F - Mth.cos(p * 2.0F)) * 0.3F * speed;   // and sinks a little with each step
        this.head.xRot += Mth.sin(p * 2.0F + 0.5F) * 0.04F * speed;
        // the trunk swings like a pendulum, each joint a beat behind the one above
        this.trunk1.zRot += Mth.sin(p - 0.6F) * 0.1F * speed;
        this.trunk2.zRot += Mth.sin(p - 1.2F) * 0.1F * speed;
        this.trunk3.zRot += Mth.sin(p - 1.8F) * 0.14F * speed;
        this.trunk1.xRot += Mth.cos(p * 2.0F) * 0.04F * speed;
        this.tail.zRot += Mth.sin(p) * 0.18F * speed;

        // standing about: the trunk sways and curls, the tail swishes
        float still = Math.max(0.0F, 1.0F - speed * 3.0F);
        this.trunk1.zRot += Mth.sin(t * 0.05F) * 0.07F * still;
        this.trunk2.zRot += Mth.sin(t * 0.05F - 0.7F) * 0.09F * still;
        this.trunk3.zRot += Mth.sin(t * 0.05F - 1.4F) * 0.12F * still;
        this.trunk2.xRot -= (0.06F + Mth.sin(t * 0.031F) * 0.06F) * still;
        this.trunk3.xRot -= (0.12F + Mth.sin(t * 0.031F - 0.8F) * 0.14F) * still;
        if (s.holding) this.trunk3.xRot -= 0.25F;                   // a trunkful of water: tip curled up
        this.tail.zRot += Mth.sin(t * 0.08F) * 0.14F;
        this.tail.xRot += Mth.sin(t * 0.05F) * 0.05F;

        // ear fanning: a couple of slow flaps every few seconds, a faint flutter in between
        float c = t % 140.0F;
        float flap = c < 50.0F ? (1.0F - Mth.cos(c / 50.0F * Mth.TWO_PI * 2.0F)) * 0.5F * 0.5F : 0.0F;
        flap += Mth.sin(t * 0.11F) * 0.04F;
        this.rightEar.yRot -= flap;
        this.leftEar.yRot += flap;

        if (s.warning) {
            // the trumpet: head thrown up, ears flared wide and trembling, mouth open, trunk raised
            // and curled back over the forehead
            float shake = Mth.sin(t * 0.9F) * 0.05F;
            this.head.xRot -= 0.45F;
            this.rightEar.yRot -= 0.95F + shake - flap;
            this.leftEar.yRot += 0.95F + shake - flap;
            this.rightEar.zRot += 0.12F;
            this.leftEar.zRot -= 0.12F;
            this.trunk1.xRot -= 2.0F;
            this.trunk2.xRot -= 0.7F;
            this.trunk3.xRot -= 0.9F;
            if (this.jaw != null) this.jaw.xRot += 0.5F;
            this.body.xRot -= 0.04F;
        } else if (s.aggressive) {
            // the charge: head down, ears out, trunk curled in under the chin out of harm's way; a
            // toss of the tusks with each blow
            float toss = Mth.sin(s.swing * Mth.PI);
            this.head.xRot += 0.3F - toss * 0.6F;
            this.rightEar.yRot -= 0.7F - flap;
            this.leftEar.yRot += 0.7F - flap;
            this.trunk1.xRot += 0.35F;
            this.trunk2.xRot += 0.8F;
            this.trunk3.xRot += 1.0F;
        } else if (s.playing) {
            // spraying (water, or dust over its back): trunk lifted high and aimed forward over the
            // head, sweeping the jet from side to side
            this.head.xRot -= 0.15F;
            this.rightEar.yRot -= 0.2F;
            this.leftEar.yRot += 0.2F;
            this.trunk1.xRot -= 2.3F;
            this.trunk1.zRot += Mth.sin(t * 0.35F) * 0.12F;
            this.trunk2.xRot += 0.55F;
            this.trunk3.xRot += 0.4F;
        }
    }
}
