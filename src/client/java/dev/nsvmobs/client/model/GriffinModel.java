package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * On the ground a horse-like walk and gallop with the wings folded along the flanks (eased out a
 * little at speed) and a swishing tail. In the air the wings open and beat in big slow strokes, faster
 * while climbing, the tips trailing each stroke (an unsaddled glide barely moves them); the legs tuck
 * back, the tail streams out and the body pitches with the climb or dive. The saddle shows only when
 * it wears one.
 */
public class GriffinModel extends CritterModel {
    private final ModelPart body, neck, head, rightWing, leftWing, rightTip, leftTip, tail, tuft, saddle, rf, lf, rh, lh;

    public GriffinModel(ModelPart root) {
        super(root, "griffin");
        this.body = part("body");
        this.neck = part("neck");
        this.head = part("head");
        this.rightWing = part("right_wing");
        this.leftWing = part("left_wing");
        this.rightTip = part("right_wing_tip");
        this.leftTip = part("left_wing_tip");
        this.tail = part("tail");
        this.tuft = part("tail_tuft");
        this.saddle = part("saddle");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        this.saddle.visible = s.saddled;
        // the neck swings round to look, the head tips up and down
        this.neck.yRot += s.yRot * Mth.DEG_TO_RAD * 0.5F;
        this.head.yRot += s.yRot * Mth.DEG_TO_RAD * 0.15F;
        this.head.xRot += s.xRot * Mth.DEG_TO_RAD * 0.5F;

        if (s.flying) {
            // the wings are folded by their rest rotation: open them flat and beat them. Looking up
            // (negative pitch) means climbing, which takes quicker strokes. Without a saddle it's a
            // glide (a wild one, or sinking down riderless): wings held out, only easing up and down.
            float climb = Mth.clamp(-s.xRot / 25.0F, 0.0F, 1.0F);
            float stroke = s.saddled ? 1.0F : 0.35F;
            float phase = t * (s.saddled ? 0.3F + 0.25F * climb : 0.15F);
            float beat = Mth.sin(phase) * stroke;
            float tipBeat = Mth.sin(phase - 0.7F) * stroke;
            this.rightWing.xRot = 0.0F;
            this.rightWing.yRot = 0.1F;
            this.rightWing.zRot = 0.1F + beat * 0.65F;
            this.leftWing.xRot = 0.0F;
            this.leftWing.yRot = -0.1F;
            this.leftWing.zRot = -0.1F - beat * 0.65F;
            this.rightTip.xRot = 0.0F;
            this.rightTip.yRot = 0.15F;
            this.rightTip.zRot = tipBeat * 0.4F;
            this.leftTip.xRot = 0.0F;
            this.leftTip.yRot = -0.15F;
            this.leftTip.zRot = -tipBeat * 0.4F;
            // the body lifts on each down-stroke and pitches with the climb or dive
            this.body.y += Mth.cos(phase) * 0.7F * stroke;
            this.body.xRot += s.xRot * Mth.DEG_TO_RAD * 0.35F;
            this.neck.xRot += 0.35F;
            this.head.xRot -= 0.35F;
            // eagle forelegs folded back under the breast, lion hind legs stretched out behind
            this.rf.xRot += 1.1F;
            this.lf.xRot += 1.1F;
            this.rh.xRot += 1.2F;
            this.lh.xRot += 1.2F;
            this.tail.xRot += 0.7F + Mth.sin(t * 0.2F) * 0.05F;
            this.tuft.xRot -= 0.3F;
            return;
        }

        float pos = s.walkAnimationPos * 0.6662F, speed = Math.min(1.0F, s.walkAnimationSpeed * 1.4F);
        walk(s, 0.9F, this.rf, this.lf, this.rh, this.lh);
        this.body.y -= Math.abs(Mth.sin(pos)) * 0.6F * speed;
        this.neck.xRot += Mth.sin(pos * 2.0F) * 0.05F * speed;
        // folded wings eased out from the flanks at a gallop, settling with each breath at rest
        float out = 0.12F * speed + Mth.sin(t * 0.06F) * 0.015F;
        this.rightWing.zRot += out;
        this.leftWing.zRot -= out;
        // a lion's tail: swishing, lifted behind at speed
        this.tail.xRot += 0.35F * speed;
        this.tail.yRot += Mth.sin(t * 0.08F) * 0.15F;
        this.tuft.yRot += Mth.sin(t * 0.08F - 0.8F) * 0.25F;
    }
}
