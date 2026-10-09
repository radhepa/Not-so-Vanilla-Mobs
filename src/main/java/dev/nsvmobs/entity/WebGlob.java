package dev.nsvmobs.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/**
 * A Broodmother's spat web. Whatever it hits is stuck in a cobweb for a few seconds (the web melts
 * away again on its own); with mobGriefing off it just slows them down.
 */
public class WebGlob extends MobMissile {
    /** How long a spat web lasts. */
    static final int WEB_TICKS = 160;

    public WebGlob(EntityType<? extends WebGlob> type, Level level) {
        super(type, level);
    }

    public WebGlob(EntityType<? extends WebGlob> type, LivingEntity thrower) {
        super(type, thrower, new ItemStack(Items.COBWEB));
    }

    @Override
    protected Item getDefaultItem() {
        return Items.COBWEB;
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        super.onHitEntity(hit);
        if (!(this.level() instanceof ServerLevel level) || !(hit.getEntity() instanceof LivingEntity target)) return;
        target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2), this.getOwner());
        if (Griefing.allowed(level)) TemporaryBlocks.place(level, target.blockPosition(), Blocks.COBWEB, WEB_TICKS);
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        super.onHitBlock(hit);
        if (this.level() instanceof ServerLevel level && Griefing.allowed(level)) {
            TemporaryBlocks.place(level, hit.getBlockPos().relative(hit.getDirection()), Blocks.COBWEB, WEB_TICKS);
        }
    }

    @Override
    protected void onHit(HitResult hit) {
        if (!this.level().isClientSide()) {
            this.level().playSound(null, this.getX(), this.getY(), this.getZ(), SoundEvents.SLIME_SQUISH_SMALL, SoundSource.HOSTILE, 0.8F, 0.6F);
        }
        super.onHit(hit);
    }
}
