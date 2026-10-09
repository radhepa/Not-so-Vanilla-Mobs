package dev.nsvmobs.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.TryFindLiquidGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraft.world.entity.animal.fish.AbstractFish;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A deep-sea anglerfish. It hangs in the dark deep water with only its lure lit, snaps up any fish
 * that swims close, and rushes divers. Out of water it flops about and suffocates like any fish.
 */
public class Angler extends Monster {
    public Angler(EntityType<? extends Angler> type, Level level) {
        super(type, level);
        this.moveControl = new SmoothSwimmingMoveControl<>(this, 85, 10, 0.02F, 0.1F, true);
        this.lookControl = new SmoothSwimmingLookControl(this, 10);
        this.setPathfindingMalus(net.minecraft.world.level.pathfinder.PathType.WATER, 0.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 1.1)
                .add(Attributes.FOLLOW_RANGE, 16.0);
    }

    /** Deep, dark ocean water only: at least 12 blocks under the surface. */
    public static boolean checkSpawnRules(EntityType<Angler> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                         BlockPos pos, RandomSource random) {
        if (level.getDifficulty() == Difficulty.PEACEFUL) return false;
        if (EntitySpawnReason.isSpawner(reason)) return true;
        return level.getFluidState(pos).is(FluidTags.WATER) && level.getFluidState(pos.below()).is(FluidTags.WATER)
                && pos.getY() <= level.getSeaLevel() - 12 && Monster.isDarkEnoughToSpawn(level, pos, random);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WaterBoundPathNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new TryFindLiquidGoal(this, FluidTags.WATER));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.6, true));
        this.goalSelector.addGoal(5, new RandomSwimmingGoal(this, 0.7, 60));
        this.goalSelector.addGoal(6, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false, (t, l) -> t.isInWater()));
        // the lure brings fish to it: it eats any that come close
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, AbstractFish.class, 40, true, false,
                (t, l) -> t.distanceToSqr(this) < 8 * 8));
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            this.playSound(SoundEvents.DOLPHIN_ATTACK, 1.0F, 0.5F);
            if (target instanceof AbstractFish fish && !fish.isAlive()) this.heal(4.0F);
        }
        return hit;
    }

    @Override
    public void baseTick() {
        int air = this.getAirSupply();
        super.baseTick();
        if (this.level() instanceof ServerLevel level && this.isAlive()) {
            if (this.isInWater()) {
                this.setAirSupply(300);
            } else {
                this.setAirSupply(air - 1);
                if (this.getAirSupply() <= -20) {
                    this.setAirSupply(0);
                    this.hurtServer(level, this.damageSources().drown(), 2.0F);
                }
            }
        }
    }

    @Override
    public void aiStep() {
        if (!this.isInWater() && this.onGround() && this.verticalCollision) {
            // flop
            this.setDeltaMovement(this.getDeltaMovement().add((this.random.nextFloat() * 2.0F - 1.0F) * 0.05F, 0.4F,
                    (this.random.nextFloat() * 2.0F - 1.0F) * 0.05F));
            this.setOnGround(false);
            this.needsSync = true;
            this.playSound(SoundEvents.GUARDIAN_FLOP, 0.8F, 0.7F);
        }
        super.aiStep();
    }

    public boolean isFlopping() {
        return !this.isInWater();
    }

    @Override public boolean canBreatheUnderwater() { return true; }
    @Override public boolean isPushedByFluid() { return false; }
    @Override public boolean canBeLeashed() { return false; }
    @Override public int getMaxHeadXRot() { return 1; }
    @Override public int getMaxHeadYRot() { return 1; }
    @Override public float getWalkTargetValue(BlockPos pos, LevelReader level) {
        return level.getFluidState(pos).is(FluidTags.WATER) ? 10.0F - level.getPathfindingCostFromLightLevels(pos) : -10.0F;
    }
    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override protected SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.COD_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.COD_DEATH; }
    @Override protected SoundEvent getSwimSound() { return SoundEvents.FISH_SWIM; }
    @Override public float getVoicePitch() { return 0.5F + this.random.nextFloat() * 0.1F; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) {}
}
