package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Hanging, only the stalactite disguise shows. On the ground: rippling spider legs, a swaying tail
 * spike and fangs that pinch, faster when it's hunting.
 */
public class DripfangModel extends CritterModel {
    private final ModelPart body, stalactite, rightFang, leftFang, tail;
    private final ModelPart[] rightLegs = new ModelPart[3], leftLegs = new ModelPart[3];

    public DripfangModel(ModelPart root) {
        super(root, "dripfang");
        this.body = part("body");
        this.stalactite = part("stalactite");
        this.rightFang = part("right_fang");
        this.leftFang = part("left_fang");
        this.tail = part("tail");
        for (int i = 0; i < 3; i++) {
            this.rightLegs[i] = part("right_leg" + (i + 1));
            this.leftLegs[i] = part("left_leg" + (i + 1));
        }
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        this.stalactite.visible = s.hanging;
        this.body.visible = !s.hanging;
        if (s.hanging) return;
        float pos = s.walkAnimationPos * 1.6F, speed = s.walkAnimationSpeed;
        for (int i = 0; i < 3; i++) {
            float phase = i * 2.1F;
            // a lifted leg (zRot toward its side) on the forward stroke, like vanilla spiders
            this.rightLegs[i].zRot -= Math.max(0, Mth.sin(pos + phase)) * 0.45F * speed;
            this.leftLegs[i].zRot += Math.max(0, Mth.sin(pos + phase + Mth.PI)) * 0.45F * speed;
            this.rightLegs[i].yRot += Mth.cos(pos + phase) * 0.35F * speed;
            this.leftLegs[i].yRot -= Mth.cos(pos + phase) * 0.35F * speed;
        }
        float t = s.ageInTicks;
        this.tail.yRot += Mth.sin(t * 0.07F) * 0.12F + Mth.sin(pos * 0.5F) * 0.15F * speed;
        float pinch = s.aggressive ? Math.max(0, Mth.sin(t * 0.6F)) * 0.45F : Math.max(0, Mth.sin(t * 0.05F) - 0.85F) * 2.0F;
        this.rightFang.yRot -= pinch;
        this.leftFang.yRot += pinch;
    }
}
