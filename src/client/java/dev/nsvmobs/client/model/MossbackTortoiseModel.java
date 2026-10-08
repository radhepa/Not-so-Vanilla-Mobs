package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Slow plod, a bobbing head, a garden that vanishes when sheared, and a pull-into-the-shell pose. */
public class MossbackTortoiseModel extends CritterModel {
    /** How far the shell drops when the tortoise tucks in (model pixels). */
    private static final float HIDE_DROP = 4.0F;
    private final ModelPart body, garden, head, rf, lf, rh, lh, tail;

    public MossbackTortoiseModel(ModelPart root) {
        super(root, "mossback_tortoise");
        this.body = part("body");
        this.garden = part("garden");
        this.head = part("head");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
        this.tail = optional("tail");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        this.garden.visible = !s.sheared;
        if (s.hiding) {
            // shell down on the ground; legs end up inside it, head and tail tuck in under the rim
            this.body.y += HIDE_DROP;
            this.head.y += HIDE_DROP;
            this.head.z += 7.5F;
            if (this.tail != null) {
                this.tail.y += HIDE_DROP;
                this.tail.z -= 3.0F;
            }
            return;
        }
        look(this.head, s, 0.7F);
        walk(s, 0.7F, this.rf, this.lf, this.rh, this.lh);
        this.head.y += Mth.sin(s.walkAnimationPos * 0.6662F * 2.0F) * 0.4F * s.walkAnimationSpeed;
        if (this.tail != null) this.tail.yRot += Mth.sin(s.ageInTicks * 0.1F) * 0.15F;
    }
}
