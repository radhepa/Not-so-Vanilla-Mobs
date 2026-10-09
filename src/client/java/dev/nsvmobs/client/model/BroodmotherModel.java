package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Eight rippling legs (diagonal pairs together, like a real spider), a slowly heaving abdomen and
 * pinching fangs. About to spit, she rears up on her back legs with her front legs raised.
 */
public class BroodmotherModel extends CritterModel {
    private final ModelPart body, head, abdomen, rightFang, leftFang;
    private final ModelPart[] rightLegs = new ModelPart[4], leftLegs = new ModelPart[4];

    public BroodmotherModel(ModelPart root) {
        super(root, "broodmother");
        this.body = part("body");
        this.head = part("head");
        this.abdomen = part("abdomen");
        this.rightFang = part("right_fang");
        this.leftFang = part("left_fang");
        for (int i = 0; i < 4; i++) {
            this.rightLegs[i] = part("right_leg" + (i + 1));
            this.leftLegs[i] = part("left_leg" + (i + 1));
        }
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        look(this.head, s, 0.4F);
        float pos = s.walkAnimationPos * 1.4F, speed = Math.min(1.0F, s.walkAnimationSpeed * 1.3F);
        for (int i = 0; i < 4; i++) {
            // legs 1 & 3 move with the opposite side's 2 & 4
            float phase = (i % 2 == 0 ? 0.0F : Mth.PI) + i * 0.4F;
            // +zRot lifts a right leg, -zRot a left one
            this.rightLegs[i].zRot += Math.max(0, Mth.sin(pos + phase)) * 0.4F * speed;
            this.leftLegs[i].zRot -= Math.max(0, Mth.sin(pos + phase + Mth.PI)) * 0.4F * speed;
            this.rightLegs[i].yRot += Mth.cos(pos + phase) * 0.3F * speed;
            this.leftLegs[i].yRot -= Mth.cos(pos + phase) * 0.3F * speed;
        }
        float breathe = Mth.sin(t * 0.08F);
        this.abdomen.xRot += breathe * 0.04F;
        this.abdomen.xScale = this.abdomen.zScale = 1.0F + breathe * 0.025F;
        this.abdomen.yScale = 1.0F - breathe * 0.02F;

        if (s.holding) {
            // rear up: front of the body lifted, front legs pawing the air
            this.body.xRot -= 0.32F;
            this.abdomen.xRot += 0.32F;
            this.head.xRot -= 0.15F;
            float paw = Mth.sin(t * 0.5F) * 0.15F;
            this.rightLegs[0].zRot += 0.7F + paw;
            this.leftLegs[0].zRot -= 0.7F + paw;
            this.rightLegs[1].zRot += 0.35F - paw;
            this.leftLegs[1].zRot -= 0.35F - paw;
        }
        float bite = Mth.sin(s.swing * Mth.PI);
        float pinch = s.aggressive ? Math.max(0, Mth.sin(t * 0.5F)) * 0.35F : Math.max(0, Mth.sin(t * 0.04F) - 0.85F) * 2.0F;
        this.rightFang.yRot -= pinch;
        this.leftFang.yRot += pinch;
        this.rightFang.xRot -= bite * 0.6F;
        this.leftFang.xRot -= bite * 0.6F;
    }
}
