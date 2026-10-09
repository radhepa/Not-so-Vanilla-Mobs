package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * A heavy waddle on land. Swimming, it lies low with its head up, forepaws tucked, kicking with the
 * big webbed hind feet while the paddle tail sculls up and down. Gnawing, it holds on with its
 * forepaws and works its head side to side; a tail slap lifts the paddle high and smacks it down.
 */
public class BeaverModel extends CritterModel {
    private final ModelPart body, head, tail, rf, lf, rh, lh;

    public BeaverModel(ModelPart root) {
        super(root, "beaver");
        this.body = part("body");
        this.head = part("head");
        this.tail = part("tail");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        look(this.head, s, 0.6F);
        if (s.swimming) {
            this.body.xRot -= 0.12F;
            this.head.xRot -= 0.15F;
            this.rf.xRot -= 0.9F;
            this.lf.xRot -= 0.9F;
            float kick = Mth.sin(t * 0.45F);
            this.rh.xRot += 0.7F + kick * 0.6F;
            this.lh.xRot += 0.7F - kick * 0.6F;
            this.tail.xRot += 0.3F + Mth.sin(t * 0.3F) * 0.2F;
        } else {
            walk(s, 1.0F, this.rf, this.lf, this.rh, this.lh);
            float gait = Mth.sin(s.walkAnimationPos * 0.6662F) * s.walkAnimationSpeed;
            this.body.zRot += gait * 0.05F;   // a heavy waddle
            this.tail.yRot += gait * 0.15F + Mth.sin(t * 0.05F) * 0.05F;
        }
        if (s.playing) {
            // gnawing: forepaws up on the log, head working side to side, jaw going
            this.rf.xRot -= 0.7F;
            this.lf.xRot -= 0.7F;
            this.head.xRot += 0.2F + Mth.sin(t * 1.7F) * 0.07F;
            this.head.zRot += Mth.sin(t * 0.8F) * 0.12F;
        }
        if (s.warning) {
            // tail slap: up high, then smacked down
            this.tail.xRot += 0.6F + Mth.sin(t * 0.8F) * 0.65F;
            this.head.xRot += 0.1F;
        }
    }
}
