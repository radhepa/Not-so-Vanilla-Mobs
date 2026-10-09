package dev.nsvmobs.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A field scarecrow that walks at night. Under the open sky by day it can't move at all, so it just
 * stands there with its arms out like any other scarecrow. Straw burns twice as well as flesh.
 */
public class Scarecrow extends Zombie {
    private static final EntityDataAccessor<Boolean> POSING = SynchedEntityData.defineId(Scarecrow.class, EntityDataSerializers.BOOLEAN);

    public Scarecrow(EntityType<? extends Scarecrow> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes().add(Attributes.MAX_HEALTH, 18.0).add(Attributes.MOVEMENT_SPEED, 0.25);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(POSING, false);
    }

    @Override public void setBaby(boolean baby) { super.setBaby(false); }
    @Override protected boolean convertsInWater() { return false; }
    @Override protected boolean isSunSensitive() { return false; }
    /** Calls no other scarecrows for help. */
    @Override protected void randomizeReinforcementsChance() { this.getAttribute(Attributes.SPAWN_REINFORCEMENTS_CHANCE).setBaseValue(0.0); }

    /** Standing stock-still in the daylight, arms out. */
    public boolean isPosing() {
        return this.entityData.get(POSING);
    }

    /** While posing it runs no AI at all: no walking, turning or attacking. */
    @Override
    protected boolean isImmobile() {
        return super.isImmobile() || this.isPosing();
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level && (this.tickCount % 10 == 0 || this.tickCount < 2)) {
            boolean day = level.isBrightOutside() && !level.isRainingAt(this.blockPosition())
                    && level.canSeeSky(BlockPos.containing(this.getX(), this.getEyeY(), this.getZ()));
            if (day != this.isPosing()) {
                this.entityData.set(POSING, day);
                if (day) {
                    this.getNavigation().stop();
                    this.setTarget(null);
                    this.setAggressive(false);
                } else {
                    this.playSound(SoundEvents.CROP_BREAK, 1.0F, 0.6F);
                }
            }
        }
        if (this.isPosing()) {
            this.setDeltaMovement(this.getDeltaMovement().multiply(0, 1, 0));
            this.yHeadRot = this.yBodyRot = this.getYRot();
            this.setXRot(0.0F);
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            // a face full of straw
            living.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30), this);
        }
        return hit;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (source.is(DamageTypeTags.IS_FIRE)) damage *= 2.0F;
        return super.hurtServer(level, source, damage);
    }

    @Override public boolean isPushable() { return !this.isPosing() && super.isPushable(); }
    @Override protected SoundEvent getAmbientSound() { return this.isPosing() ? null : SoundEvents.ZOMBIE_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.GRASS_HIT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.GRASS_BREAK; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.CROP_BREAK, 0.25F, 1.3F); }
    @Override public float getVoicePitch() { return 0.55F + this.random.nextFloat() * 0.1F; }
}
