package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Oregorger;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A heavy plodding walk. Curled up it's a ball, spinning faster and faster as it revs and then
 * tumbling as it rolls. Stunned it slumps sideways, legs splayed, head lolling. Eating, it chomps.
 */
public class OregorgerModel extends CritterModel {
    private final ModelPart body, head, jaw, tail, ball, rightFront, leftFront, rightHind, leftHind;

    public OregorgerModel(ModelPart root) {
        super(root, "oregorger");
        this.body = part("body");
        this.head = part("head");
        this.jaw = part("jaw");
        this.tail = part("tail");
        this.ball = part("ball");
        this.rightFront = part("right_front_leg");
        this.leftFront = part("left_front_leg");
        this.rightHind = part("right_hind_leg");
        this.leftHind = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        boolean balled = s.mode == Oregorger.ROLLING || s.mode == Oregorger.CURLING && s.modeAge > Oregorger.CURL_TICKS / 2.0F;
        this.ball.visible = balled;
        this.body.visible = !balled;
        for (ModelPart leg : new ModelPart[]{this.rightFront, this.leftFront, this.rightHind, this.leftHind}) leg.visible = !balled;
        if (balled) {
            // revving: spin up while curled; rolling: tumble forward at about the speed it moves
            float spin = s.mode == Oregorger.CURLING ? (s.modeAge - Oregorger.CURL_TICKS / 2.0F) * (s.modeAge - Oregorger.CURL_TICKS / 2.0F) * 0.03F
                    : s.modeAge * 0.87F + 3.0F;   // 16/11 rad per block at 0.6 blocks a tick
            this.ball.xRot += spin;
            return;
        }
        look(this.head, s, 0.5F);
        walk(s, 0.8F, this.rightFront, this.leftFront, this.rightHind, this.leftHind);
        this.tail.yRot += Mth.sin(t * 0.06F) * 0.15F + Mth.cos(s.walkAnimationPos * 0.6662F) * 0.2F * s.walkAnimationSpeed;
        if (s.mode == Oregorger.CURLING) {
            // tucking in: head down, back rounding
            float p = Math.min(1.0F, s.modeAge / (Oregorger.CURL_TICKS / 2.0F));
            this.head.xRot += 0.8F * p;
            this.body.xRot += 0.25F * p;
            this.tail.xRot -= 0.6F * p;
        } else if (s.mode == Oregorger.STUNNED) {
            this.body.zRot += 0.22F;
            this.head.xRot += 0.4F;
            this.head.zRot += Mth.sin(t * 0.2F) * 0.35F;
            this.jaw.xRot += 0.35F;
            this.rightFront.zRot += 0.5F;
            this.leftFront.zRot -= 0.5F;
            this.rightHind.zRot += 0.4F;
            this.leftHind.zRot -= 0.4F;
        } else if (s.mode == Oregorger.EATING) {
            this.head.xRot += 0.35F;
            this.jaw.xRot += Math.max(0, Mth.sin(t * 0.8F)) * 0.5F;
        }
        this.jaw.xRot += Mth.sin(s.swing * Mth.PI) * 0.6F;
    }
}
