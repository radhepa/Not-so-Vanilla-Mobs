package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Prowler;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A big cat's walk, a slow tail swish. Stalking it slinks low with its legs bent; gathering for a
 * pounce it sinks lower still and lashes its tail; mid-leap it stretches out full length with its
 * jaws open; mauling, it's all jaws and front paws. Dazed, its head lolls.
 */
public class ProwlerModel extends CritterModel {
    private final ModelPart body, head, jaw, tail, tailTip, rightFront, leftFront, rightHind, leftHind;

    public ProwlerModel(ModelPart root) {
        super(root, "prowler");
        this.body = part("body");
        this.head = part("head");
        this.jaw = part("jaw");
        this.tail = part("tail");
        this.tailTip = part("tail_tip");
        this.rightFront = part("right_front_leg");
        this.leftFront = part("left_front_leg");
        this.rightHind = part("right_hind_leg");
        this.leftHind = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        look(this.head, s, 1.0F);
        walk(s, 1.0F, this.rightFront, this.leftFront, this.rightHind, this.leftHind);
        this.tail.yRot += Mth.sin(t * 0.08F) * 0.25F;
        this.tailTip.yRot += Mth.sin(t * 0.08F - 0.8F) * 0.3F;

        float crouch = switch (s.mode) {
            case Prowler.STALKING -> 0.6F;
            case Prowler.CROUCHING -> Math.min(1.0F, 0.6F + s.modeAge / 8.0F);
            default -> 0.0F;
        };
        if (crouch > 0) {
            float drop = 3.5F * crouch;
            this.body.y += drop;
            this.head.y += drop;
            for (ModelPart leg : new ModelPart[]{this.rightFront, this.leftFront, this.rightHind, this.leftHind}) leg.y += drop;
            this.rightFront.xRot -= 0.85F * crouch;
            this.leftFront.xRot -= 0.85F * crouch;
            this.rightHind.xRot += 0.85F * crouch;
            this.leftHind.xRot += 0.85F * crouch;
            this.tail.xRot -= 0.3F * crouch;
        }
        switch (s.mode) {
            case Prowler.CROUCHING -> {
                this.tail.yRot += Mth.sin(t * 0.9F) * 0.5F;
                this.tailTip.yRot += Mth.sin(t * 0.9F - 1.0F) * 0.6F;
                this.body.zRot += Mth.sin(t * 1.3F) * 0.03F;   // the rump wiggle
                this.jaw.xRot += 0.25F;
            }
            case Prowler.LEAPING -> {
                this.rightFront.xRot -= 0.95F;
                this.leftFront.xRot -= 0.95F;
                this.rightHind.xRot += 0.85F;
                this.leftHind.xRot += 0.85F;
                this.body.xRot -= 0.1F;
                this.head.xRot -= 0.15F;
                this.jaw.xRot += 0.6F;
                this.tail.xRot += 0.4F;
            }
            case Prowler.MAULING -> {
                this.head.xRot += 0.45F;
                this.jaw.xRot += 0.35F + Math.max(0, Mth.sin(t * 1.3F)) * 0.45F;
                float rake = Mth.sin(t * 0.9F);
                this.rightFront.xRot -= 0.9F + rake * 0.4F;
                this.leftFront.xRot -= 0.9F - rake * 0.4F;
            }
            case Prowler.DAZED -> {
                this.head.zRot += Mth.sin(t * 0.25F) * 0.3F;
                this.head.xRot += 0.3F;
                this.jaw.xRot += 0.2F;
            }
            default -> {}
        }
        float swipe = Mth.sin(s.swing * Mth.PI);
        this.rightFront.xRot -= swipe * 1.2F;
        this.jaw.xRot += swipe * 0.5F;
    }
}
