package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A slow, heavy plod with a nodding head and a swishing tail. Shearing hides the long coat (the
 * `fringe`) to show the undercoat; calves have no horns. Standing about, it now and then drops its
 * head to graze.
 */
public class YakModel extends CritterModel {
    private final ModelPart body, fringe, tail, head, rightHorn, leftHorn, rf, lf, rh, lh;
    private final ModelPart rightEar, leftEar;

    public YakModel(ModelPart root) {
        super(root, "yak");
        this.body = part("body");
        this.fringe = part("fringe");
        this.tail = part("tail");
        this.head = part("head");
        this.rightHorn = part("right_horn");
        this.leftHorn = part("left_horn");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
        this.rightEar = optional("right_ear");
        this.leftEar = optional("left_ear");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        this.fringe.visible = !s.sheared;
        this.rightHorn.visible = s.antlers;
        this.leftHorn.visible = s.antlers;
        look(this.head, s, 0.5F);
        walk(s, 0.8F, this.rf, this.lf, this.rh, this.lh);
        float pos = s.walkAnimationPos * 0.6662F, speed = s.walkAnimationSpeed;
        // the big body rolls a little and the head nods with each heavy step
        this.body.zRot += Mth.sin(pos) * 0.025F * speed;
        this.head.xRot += Mth.cos(pos * 2.0F) * 0.06F * speed;
        this.head.y += Math.abs(Mth.sin(pos)) * 0.4F * speed;
        // grazing now and then while it stands
        float still = Math.max(0.0F, 1.0F - speed * 4.0F);
        float graze = Math.max(0.0F, Mth.sin(t * 0.015F + 1.3F) - 0.5F) * 2.0F * still;
        this.head.xRot += graze * 0.8F + graze * Mth.sin(t * 0.5F) * 0.04F;   // and chewing
        this.head.y += graze * 1.5F;
        // a lazy swish of the tail, ear flicks
        this.tail.zRot += Mth.sin(t * 0.07F) * 0.12F;
        this.tail.xRot += Mth.sin(t * 0.05F) * 0.05F + 0.2F * speed;
        float flick = (t % 80.0F) < 6.0F ? Mth.sin((t % 80.0F) / 6.0F * Mth.PI) * 0.4F : 0.0F;
        if (this.rightEar != null) this.rightEar.zRot += flick;
        if (this.leftEar != null) this.leftEar.zRot -= flick * 0.6F;
    }
}
