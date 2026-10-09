package dev.nsvmobs.client.render;

import java.util.List;

import dev.nsvmobs.client.model.CritterModel;
import dev.nsvmobs.client.model.Geometry;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;

/**
 * Draws the item a mob carries (its main hand) at one of its model parts, like a fox with something
 * in its jaws: a goose's bill, a raccoon's mouth. The part is usually an empty marker part.
 */
public class MouthItemLayer extends RenderLayer<CritterRenderState, CritterModel> {
    private final List<ModelPart> chain;

    public MouthItemLayer(RenderLayerParent<CritterRenderState, CritterModel> renderer, String id, String part) {
        super(renderer);
        this.chain = Geometry.path(renderer.getModel().root(), id, part);
    }

    @Override
    public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, CritterRenderState state, float yRot, float xRot) {
        if (state.heldItem.isEmpty()) return;
        poseStack.pushPose();
        // the parts already hold this frame's animated pose, so following them keeps the item in the mouth
        for (ModelPart p : this.chain) p.translateAndRotate(poseStack);
        poseStack.rotateDegrees(Axis.XP, 90.0F);   // lying crosswise, as foxes carry things
        state.heldItem.submit(poseStack, collector, light, OverlayTexture.NO_OVERLAY, state.outlineColor);
        poseStack.popPose();
    }
}
