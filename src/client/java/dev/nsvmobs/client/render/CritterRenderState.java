package dev.nsvmobs.client.render;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** Render state shared by the mod's non-humanoid mobs; each renderer fills the fields it uses. */
public class CritterRenderState extends LivingEntityRenderState {
    public boolean sitting;
    public boolean hiding;
    public boolean sheared;
    public boolean burrowed;
    public boolean flying = true;
    public boolean lurking;
    public boolean aggressive;
    /** 0..1 progress of a tongue lash (0 = mouth closed). */
    public float lash;
    /** Which texture variant to draw (index into the renderer's texture list). */
    public int variant;
}
