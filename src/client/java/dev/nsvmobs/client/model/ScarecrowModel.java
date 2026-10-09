package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.ScarecrowRenderer;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.monster.zombie.ZombieModel;
import net.minecraft.util.Mth;

/** Vanilla zombie animation, except by day: arms straight out, legs together, head lolled to one side. */
public class ScarecrowModel extends ZombieModel<ScarecrowRenderer.State> {
    public ScarecrowModel(ModelPart root) {
        super(root);
    }

    @Override
    public void setupAnim(ScarecrowRenderer.State state) {
        super.setupAnim(state);
        if (!state.posing) return;
        // +zRot swings the right arm (hanging down at -x) out to the right; the left arm mirrors it
        this.rightArm.xRot = 0.0F;
        this.rightArm.yRot = 0.0F;
        this.rightArm.zRot = Mth.HALF_PI;
        this.leftArm.xRot = 0.0F;
        this.leftArm.yRot = 0.0F;
        this.leftArm.zRot = -Mth.HALF_PI;
        this.rightLeg.xRot = this.leftLeg.xRot = 0.0F;
        this.rightLeg.yRot = this.leftLeg.yRot = 0.0F;
        this.head.xRot = 0.15F;
        this.head.yRot = 0.0F;
        this.head.zRot = 0.2F;
        this.body.xRot = this.body.yRot = 0.0F;
    }
}
