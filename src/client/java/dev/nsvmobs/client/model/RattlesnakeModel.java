package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Slithers with a wave that travels from head to tail, flicks its forked tongue, and to warn you
 * off rears its neck into an S with the head held level, curls its tail beside it and shakes the
 * raised rattle into a blur. Chasing, it bites with the jaw open wide.
 */
public class RattlesnakeModel extends CritterModel {
    private final ModelPart head, jaw, tongue, rattle;
    private final ModelPart[] body = new ModelPart[5];

    public RattlesnakeModel(ModelPart root) {
        super(root, "rattlesnake");
        for (int i = 0; i < 5; i++) this.body[i] = part("body" + (i + 1));
        this.head = part("head");
        this.jaw = part("jaw");
        this.tongue = part("tongue");
        this.rattle = part("rattle");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;

        // the tongue slides out and back for a moment every couple of seconds (more often when uneasy)
        float period = s.warning || s.aggressive ? 22.0F : 46.0F;
        float cycle = (t + 17.0F) % period;
        float flick = cycle < 7.0F ? Mth.sin(cycle / 7.0F * Mth.PI) : 0.0F;
        this.tongue.z -= 5.5F * flick;
        this.tongue.yRot += Mth.sin(t * 2.3F) * 0.12F * flick;

        if (s.warning) {
            // rearing: body1 tips its front end up off a raised joint, body2 slopes back down to the
            // ground and body3 levels out, so the neck makes an S and the head stays level
            this.body[0].y -= 2.5F;
            this.body[0].xRot -= 0.95F;
            this.body[1].xRot += 0.43F;
            this.body[1].yRot -= 0.3F;
            this.body[2].xRot += 0.52F;
            this.body[2].yRot += 0.45F;
            this.head.xRot += 0.95F;
            look(this.head, s, 0.7F);
            // the tail curls round beside it with the rattle stood up and buzzing
            float sway = Mth.sin(t * 0.15F) * 0.06F;
            this.body[3].yRot += 1.5F + sway;
            this.body[4].yRot += 1.6F - sway;
            this.rattle.xRot += 1.2F + Mth.cos(t * 3.1F) * 0.08F;
            this.rattle.yRot += Mth.sin(t * 3.1F) * 0.35F;
            // the raised neck sways a little, ready to strike
            this.body[0].yRot += Mth.sin(t * 0.09F) * 0.08F;
            this.head.yRot -= Mth.sin(t * 0.09F) * 0.08F;
            return;
        }

        // slither: a wave runs down the chain. Each joint bends by the difference between the
        // wave's angle at its segment and at the one before, so the absolute angles travel along.
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.6F);
        float pos = s.walkAnimationPos * 0.9F;
        float before = 0.0F;
        for (int i = 0; i < 5; i++) {
            float angle = Mth.sin(pos - i * 1.15F) * 0.45F * amount;
            this.body[i].yRot += angle - before;
            before = angle;
        }
        this.rattle.yRot += Mth.sin(pos - 5 * 1.15F) * 0.3F * amount - before * 0.5F;
        // the head keeps pointing where it's going while the neck swings
        this.head.yRot -= Mth.sin(pos) * 0.45F * amount * 0.8F;
        look(this.head, s, 0.5F);

        if (s.aggressive) {
            // closing in to bite: head lifted off the ground, mouth gaping in time with the lunges
            this.body[0].xRot -= 0.3F;
            this.body[1].xRot += 0.3F;
            this.head.xRot += 0.3F;
            this.jaw.xRot += 0.45F + Math.max(0.0F, Mth.sin(t * 0.5F)) * 0.35F;
        } else {
            // basking: just the odd lazy twitch of the tail
            this.rattle.yRot += Math.max(0.0F, Mth.sin(t * 0.05F) - 0.9F) * 2.0F;
        }
    }
}
