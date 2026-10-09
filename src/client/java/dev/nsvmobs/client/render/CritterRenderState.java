package dev.nsvmobs.client.render;

import net.minecraft.client.renderer.entity.state.HoldingEntityRenderState;

/**
 * Render state shared by the mod's non-humanoid mobs; each renderer fills the fields it uses.
 * {@code heldItem} (from HoldingEntityRenderState) is the item a mob carries in its mouth, filled
 * only by renderers made with {@link CritterRenderer#carriesItem}.
 */
public class CritterRenderState extends HoldingEntityRenderState {
    public boolean sitting;
    public boolean hiding;
    public boolean sheared;
    public boolean burrowed;
    public boolean flying = true;
    public boolean lurking;
    public boolean aggressive;
    /** Upright on its hind legs (meerkat on watch). */
    public boolean standing;
    /** Belly-down (penguin tobogganing). */
    public boolean sliding;
    public boolean swimming;
    /** On its back at the surface (otter). */
    public boolean floating;
    /** Disguised on the ceiling (dripfang). */
    public boolean hanging;
    /** A threat display: rattling, hissing, stamping, a raised alarm tail, a tail slap. */
    public boolean warning;
    /** Idling in a resting pose (a flamingo on one leg). */
    public boolean resting;
    /** Busy with something: a display dance, balancing a ball, gnawing, spraying, washing food. */
    public boolean playing;
    /** Wears its antlers or horns (grown stags, adult yaks). */
    public boolean antlers;
    public boolean saddled;
    /** ARGB colour the whole model is multiplied by (white = untinted). */
    public int tint = 0xFFFFFFFF;
    /** 0..1 progress of a tongue lash (0 = mouth closed). */
    public float lash;
    /** Which texture variant to draw (index into the renderer's texture list). */
    public int variant;
    /** Not drawn at all, shadow included (a sandmaw underground, a riftstalker inside its rift). */
    public boolean hidden;
    /** The mob's current action or phase (each mob class defines its own numbers), and how long it's been at it (ticks). */
    public int mode;
    public float modeAge;
    /** The frame's partial tick, for extract lambdas that need it. */
    public float partialTick;
    /** 0..1 progress of a melee swing (0 = not swinging). */
    public float swing;
    /** Badly hurt and furious (cinderhulk). */
    public boolean enraged;
    /** Holding something overhead (crag troll's boulder) or rearing up (broodmother about to spit). */
    public boolean holding;
}
