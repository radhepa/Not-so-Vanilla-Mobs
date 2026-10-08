package dev.nsvmobs.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** A desert scorpion that hides under the sand and bursts out when someone walks too close. */
public class DuneScorpion extends Monster {
    private static final EntityDataAccessor<Boolean> BURROWED = SynchedEntityData.defineId(DuneScorpion.class, EntityDataSerializers.BOOLEAN);
    private static final double SENSE_RANGE = 5.0;
    private int idleTicks;

    public DuneScorpion(EntityType<? extends DuneScorpion> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    /** Sand underfoot; any light, but daylight spawns are rare so deserts don't fill up with them. */
    public static boolean checkSpawnRules(EntityType<DuneScorpion> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        if (!level.getBlockState(pos.below()).is(BlockTags.SAND)) return false;
        if (EntitySpawnReason.isSpawner(reason) || level.getRawBrightness(pos, 0) <= 7) {
            return Monster.checkAnyLightMonsterSpawnRules(type, level, reason, pos, random);
        }
        return random.nextInt(10) == 0 && Monster.checkAnyLightMonsterSpawnRules(type, level, reason, pos, random);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(BURROWED, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.15, true) {
            @Override public boolean canUse() { return !DuneScorpion.this.isBurrowed() && super.canUse(); }
        });
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8) {
            @Override public boolean canUse() { return !DuneScorpion.this.isBurrowed() && super.canUse(); }
        });
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F) {
            @Override public boolean canUse() { return !DuneScorpion.this.isBurrowed() && super.canUse(); }
        });
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this) {
            @Override public boolean canUse() { return !DuneScorpion.this.isBurrowed() && super.canUse(); }
        });
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        // Buried, it only senses footsteps right next to it.
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (target, level) -> !this.isBurrowed() || target.distanceToSqr(this) < SENSE_RANGE * SENSE_RANGE));
    }

    public boolean isBurrowed() {
        return this.entityData.get(BURROWED);
    }

    private void setBurrowed(boolean burrowed) {
        if (burrowed == this.isBurrowed()) return;
        this.entityData.set(BURROWED, burrowed);
        this.playSound(burrowed ? SoundEvents.SAND_BREAK : SoundEvents.SAND_HIT, 1.0F, burrowed ? 0.8F : 0.6F);
        if (this.level() instanceof ServerLevel level) {
            BlockState below = level.getBlockState(this.blockPosition().below());
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, below), this.getX(), this.getY() + 0.3, this.getZ(),
                    burrowed ? 20 : 40, 0.5, 0.2, 0.5, 0.1);
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level().isClientSide()) return;
        if (this.isBurrowed()) {
            this.getNavigation().stop();
            this.setDeltaMovement(this.getDeltaMovement().multiply(0, 1, 0));
            if (this.getTarget() != null) this.setBurrowed(false);
            return;
        }
        this.idleTicks = this.getTarget() == null && this.getNavigation().isDone() ? this.idleTicks + 1 : 0;
        if (this.idleTicks > 200 && this.onGround() && this.level().getBlockState(this.blockPosition().below()).is(BlockTags.SAND)) {
            this.idleTicks = 0;
            this.setBurrowed(true);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt) this.setBurrowed(false);
        return hurt;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living && this.random.nextFloat() < 0.3F) {
            living.addEffect(new MobEffectInstance(MobEffects.POISON, 100), this);
            this.playSound(SoundEvents.BEE_STING, 1.0F, 0.7F);
        }
        return hit;
    }

    @Override public boolean isPushable() { return !this.isBurrowed() && super.isPushable(); }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Burrowed", this.isBurrowed());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(BURROWED, input.getBooleanOr("Burrowed", false));
    }

    @Override public float getVoicePitch() { return 0.75F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return this.isBurrowed() ? null : SoundEvents.SPIDER_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.SPIDER_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.SPIDER_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.SPIDER_STEP, 0.12F, 1.2F); }
}
