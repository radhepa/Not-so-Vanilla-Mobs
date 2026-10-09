package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A light-footed walk on long legs with a nodding neck and flicking ears; antlers only on grown
 * stags. Alarmed, it flags its white tail straight up, lifts its head and lays its ears back as it
 * bounds away.
 */
public class DeerModel extends CritterModel {
    private final ModelPart body, neck, head, antlers, tail, rightEar, leftEar, rf, lf, rh, lh;

    public DeerModel(ModelPart root) {
        super(root, "deer");
        this.body = part("body");
        this.neck = part("neck");
        this.head = part("head");
        this.antlers = part("antlers");
        this.tail = part("tail");
        this.rightEar = part("right_ear");
        this.leftEar = part("left_ear");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        this.antlers.visible = s.antlers;
        // the head sits on a forward-leaning neck: turn the neck to look around, tip the head to look
        // up and down
        this.neck.yRot += s.yRot * Mth.DEG_TO_RAD * 0.6F;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.6F;
        float pos = s.walkAnimationPos * 0.6662F, speed = s.walkAnimationSpeed;
        walk(s, 1.0F, this.rf, this.lf, this.rh, this.lh);
        this.neck.xRot += Mth.cos(pos * 2.0F) * 0.05F * speed;   // a nod with each stride

        if (s.warning) {
            // bounding away: white flag up, head high, ears laid back, a rocking gait
            this.tail.xRot += 2.05F + Mth.sin(t * 0.6F) * 0.08F;
            this.neck.xRot -= 0.3F;
            this.head.xRot += 0.15F;
            this.rightEar.yRot += 0.5F;
            this.leftEar.yRot -= 0.5F;
            this.body.xRot += Mth.sin(pos) * 0.06F * speed;
            return;
        }
        // tail flicks and ear twitches now and then
        float c1 = t % 70.0F, c2 = (t + 23.0F) % 110.0F, c3 = (t + 51.0F) % 90.0F;
        this.tail.xRot += c1 < 8.0F ? Mth.sin(c1 / 8.0F * Mth.PI) * 0.5F : 0.0F;
        this.tail.zRot += Mth.sin(t * 0.25F) * 0.06F;
        if (c2 < 6.0F) this.rightEar.zRot += Mth.sin(c2 / 6.0F * Mth.PI) * 0.45F;
        if (c3 < 6.0F) this.leftEar.zRot -= Mth.sin(c3 / 6.0F * Mth.PI) * 0.45F;
        // standing still, it now and then lowers its head to browse
        float still = Math.max(0.0F, 1.0F - speed * 4.0F);
        float browse = Math.max(0.0F, Mth.sin(t * 0.017F) - 0.55F) * 2.2F * still;
        this.neck.xRot += browse * 0.9F;
        this.head.xRot += browse * 0.5F;
    }
}
