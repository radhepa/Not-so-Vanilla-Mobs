package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Squat toad walk, a throat that breathes, a jaw that gapes and a tongue that shoots out. */
public class BogLurkerModel extends CritterModel {
    private final ModelPart body, head, jaw, tongue, rf, lf, rh, lh;

    public BogLurkerModel(ModelPart root) {
        super(root, "bog_lurker");
        this.body = part("body");
        this.head = part("head");
        this.jaw = part("jaw");
        this.tongue = part("tongue");
        this.rf = part("right_front_leg");
        this.lf = part("left_front_leg");
        this.rh = part("right_hind_leg");
        this.lh = part("left_hind_leg");
    }

    @Override
    public void setupAnim(CritterRenderState s) {
        super.setupAnim(s);
        if (!s.lurking) look(this.head, s, 0.6F);
        walk(s, 0.9F, this.rf, this.lf, this.rh, this.lh);
        // slow breathing, slower still while it lurks
        float breath = Mth.sin(s.ageInTicks * (s.lurking ? 0.05F : 0.1F)) * 0.03F;
        this.body.yScale = 1.0F + breath;
        float open = s.lash > 0 ? 0.7F : (s.aggressive ? 0.15F + Mth.sin(s.ageInTicks * 0.3F) * 0.1F : 0.0F);
        this.jaw.xRot += open;
        this.tongue.zScale = 1.0F + s.lash * 7.0F;
        this.tongue.visible = s.lash > 0;
    }
}
