package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;
import dev.nsvmobs.entity.Rimewraith;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * It bobs as it floats, its robe streaming back as it drifts and its long arms swaying. Casting,
 * it lifts its right hand toward you, then flings the shards.
 */
public class RimewraithModel extends CritterModel {
    private final ModelPart body, head, rightArm, leftArm, robe;
    private final ModelPart robeTail;

    public RimewraithModel(ModelPart root) {
        super(root, "rimewraith");
        this.body = part("body");
        this.head = part("head");
        this.rightArm = part("right_arm");
        this.leftArm = part("left_arm");
        this.robe = part("robe");
        this.robeTail = optional("robe_tail");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        look(this.head, s, 0.8F);
        this.body.y += Mth.sin(t * 0.1F) * 1.0F;
        float drift = Math.min(1.0F, s.walkAnimationSpeed * 2.0F);
        this.robe.xRot += 0.08F + drift * 0.35F + Mth.sin(t * 0.08F) * 0.06F;
        this.robe.zRot += Mth.sin(t * 0.06F) * 0.05F;
        if (this.robeTail != null) this.robeTail.xRot += drift * 0.25F + Mth.sin(t * 0.08F - 1.0F) * 0.1F;
        this.rightArm.zRot += Mth.sin(t * 0.09F) * 0.07F;
        this.leftArm.zRot -= Mth.sin(t * 0.09F + 0.5F) * 0.07F;
        this.rightArm.xRot += Mth.sin(t * 0.07F) * 0.05F - (s.aggressive ? 0.3F : 0.0F);
        this.leftArm.xRot += Mth.sin(t * 0.07F + 1.0F) * 0.05F - (s.aggressive ? 0.3F : 0.0F);
        if (s.mode == Rimewraith.CASTING) {
            float p = Math.min(1.0F, s.modeAge / 8.0F);
            this.rightArm.xRot -= 1.6F * p;
            this.leftArm.xRot -= 0.4F * p;
        }
        float swipe = Mth.sin(s.swing * Mth.PI);
        this.rightArm.xRot -= swipe * 1.4F;
    }
}
