package dev.nsvmobs.client.model;

import dev.nsvmobs.client.render.CritterRenderState;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Base for the non-humanoid models: named part lookup plus the usual head-look and leg swing. */
public abstract class CritterModel extends EntityModel<CritterRenderState> {
    protected final String id;

    protected CritterModel(ModelPart root, String id) {
        super(root);
        this.id = id;
    }

    protected ModelPart part(String name) {
        return Geometry.part(this.root(), this.id, name);
    }

    protected ModelPart optional(String name) {
        return Geometry.optional(this.root(), this.id, name);
    }

    /** Turn a head toward where the mob is looking (degrees from the render state). */
    protected static void look(ModelPart head, CritterRenderState s, float weight) {
        head.yRot += s.yRot * Mth.DEG_TO_RAD * weight;
        head.xRot += s.xRot * Mth.DEG_TO_RAD * weight;
    }

    /** Classic quadruped walk: diagonal pairs swing together. */
    protected static void walk(CritterRenderState s, float amount, ModelPart rf, ModelPart lf, ModelPart rh, ModelPart lh) {
        float swing = Mth.cos(s.walkAnimationPos * 0.6662F) * amount * s.walkAnimationSpeed;
        rh.xRot += swing;
        lf.xRot += swing;
        lh.xRot -= swing;
        rf.xRot -= swing;
    }
}
