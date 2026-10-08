package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Six-legged scuttle, snapping pincers, a swaying tail that cocks to strike, and a burrowed pose. */
public class DuneScorpionModel extends CritterModel {
    private final ModelPart body, head, rightClaw, leftClaw, rightPincer, leftPincer;
    private final ModelPart[] tail = new ModelPart[4];
    private final ModelPart[] rightLegs = new ModelPart[3], leftLegs = new ModelPart[3];

    public DuneScorpionModel(ModelPart root) {
        super(root, "dune_scorpion");
        this.body = part("body");
        this.head = part("head");
        this.rightClaw = part("right_claw");
        this.leftClaw = part("left_claw");
        this.rightPincer = part("right_pincer");
        this.leftPincer = part("left_pincer");
        for (int i = 0; i < 4; i++) this.tail[i] = part("tail" + (i + 1));
        for (int i = 0; i < 3; i++) {
            this.rightLegs[i] = part("right_leg" + (i + 1));
            this.leftLegs[i] = part("left_leg" + (i + 1));
        }
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        if (s.burrowed) {
            // sunk into the sand: only the curled tail tip sticks out
            this.body.y += 9.0F;
            this.tail[0].xRot -= 0.25F;
            return;
        }
        look(this.head, s, 0.3F);
        float pos = s.walkAnimationPos * 1.3F, speed = s.walkAnimationSpeed;
        for (int i = 0; i < 3; i++) {
            float phase = i * 2.1F;
            float swing = Mth.cos(pos + phase) * 0.45F * speed;
            float lift = Math.max(0, Mth.sin(pos + phase)) * 0.4F * speed;
            this.rightLegs[i].yRot += swing;
            this.leftLegs[i].yRot += swing;
            this.rightLegs[i].zRot -= lift;
            this.leftLegs[i].zRot += lift;
        }
        float idle = s.ageInTicks * 0.08F;
        for (int i = 0; i < 4; i++) {
            this.tail[i].xRot += Mth.sin(idle - i * 0.5F) * 0.04F;
            this.tail[i].yRot += Mth.sin(idle * 0.7F - i * 0.4F) * 0.05F;
        }
        float snap = s.aggressive ? Math.abs(Mth.sin(s.ageInTicks * 0.35F)) * 0.45F : Math.abs(Mth.sin(idle)) * 0.08F;
        this.rightPincer.yRot += snap;
        this.leftPincer.yRot -= snap;
        if (s.aggressive) {
            // cocked to strike, claws raised
            this.tail[1].xRot -= 0.15F;
            this.tail[3].xRot -= 0.25F + Mth.sin(s.ageInTicks * 0.25F) * 0.1F;
            this.rightClaw.xRot -= 0.2F;
            this.leftClaw.xRot -= 0.2F;
        }
    }
}
