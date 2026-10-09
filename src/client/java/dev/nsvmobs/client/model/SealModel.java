package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * On land it galumphs: the body rocks and humps along with the front flippers pushing. In water it
 * pitches with its dives and sculls with its joined hind flippers. Balancing, it points its nose to
 * the sky with the snowball wobbling on the tip and claps its flippers in front of its chest.
 */
public class SealModel extends CritterModel {
    private final ModelPart body, head, ball, rightFlipper, leftFlipper, tail;

    public SealModel(ModelPart root) {
        super(root, "seal");
        this.body = part("body");
        this.head = part("head");
        this.ball = part("ball");
        this.rightFlipper = part("right_flipper");
        this.leftFlipper = part("left_flipper");
        this.tail = part("tail");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        this.ball.visible = s.playing;

        if (s.playing) {
            // chest up, nose to the sky; the ball (hidden inside the head at rest) moves out onto
            // the tip of the nose and wobbles there
            this.body.xRot -= 0.2F;
            this.head.xRot = -1.0F;
            this.head.yRot += Mth.sin(t * 0.3F) * 0.08F;
            this.ball.y -= 0.4F;
            this.ball.z -= 5.4F;
            this.ball.x += Mth.sin(t * 0.45F) * 0.35F;
            this.ball.zRot += Mth.sin(t * 0.45F) * 0.3F;
            // flippers brought up in front of the chest in a V, clapping together at the tips
            float clap = Math.abs(Mth.sin(t * 0.7F));
            this.rightFlipper.x += 0.5F;
            this.leftFlipper.x -= 0.5F;
            this.rightFlipper.y -= 1.0F;
            this.leftFlipper.y -= 1.0F;
            this.rightFlipper.z -= 2.5F;
            this.leftFlipper.z -= 2.5F;
            this.rightFlipper.xRot = 0.6F;
            this.leftFlipper.xRot = 0.6F;
            this.rightFlipper.yRot = -2.0F - clap * 0.55F;
            this.leftFlipper.yRot = 2.0F + clap * 0.55F;
            this.rightFlipper.zRot = 0.0F;
            this.leftFlipper.zRot = 0.0F;
            this.tail.xRot += 0.3F;
            return;
        }

        if (s.swimming) {
            // pitch with the dive, scull with the hind flippers, front flippers tucked back
            this.body.xRot += s.xRot * Mth.DEG_TO_RAD * 0.8F;
            float scull = Mth.sin(t * 0.35F);
            this.tail.yRot += scull * 0.45F;
            this.body.yRot += Mth.sin(t * 0.35F - 1.2F) * 0.06F;
            this.rightFlipper.yRot += 0.6F;
            this.leftFlipper.yRot -= 0.6F;
            this.rightFlipper.zRot += 0.15F;
            this.leftFlipper.zRot -= 0.15F;
            look(this.head, s, 0.4F);
            this.head.xRot -= s.xRot * Mth.DEG_TO_RAD * 0.4F;   // the body already carries most of the pitch
            return;
        }

        look(this.head, s, 0.6F);
        // galumphing: each hump lifts the chest, then the hips; the flippers push off
        float hump = Mth.sin(s.walkAnimationPos * 0.6F) * s.walkAnimationSpeed;
        this.body.xRot += hump * 0.12F;
        this.body.y -= Math.abs(hump) * 0.7F;
        this.head.xRot -= hump * 0.12F;
        this.rightFlipper.yRot += hump * 0.45F;
        this.leftFlipper.yRot -= hump * 0.45F;
        this.tail.xRot -= hump * 0.2F;
        // idle: the hind flippers wave lazily now and then
        this.tail.yRot += Math.max(0.0F, Mth.sin(t * 0.06F) - 0.6F) * Mth.sin(t * 0.5F) * 0.5F;
    }
}
