package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * A mountain troll. It rips boulders out of the ground and hurls them, and its punches throw you
 * clean off a cliff. It heals itself all the time (a heart every two seconds) unless it's been
 * burned: fire stops the healing for ten seconds. It collects tolls, so it carries emeralds.
 */
public class CragTroll extends Monster {
    private static final EntityDataAccessor<Boolean> HOLDING = SynchedEntityData.defineId(CragTroll.class, EntityDataSerializers.BOOLEAN);
    public static final int THROW_WINDUP = 26;
    /** How long a burn stops its healing. */
    static final int SCORCH_TICKS = 200;
    private int scorched;

    public CragTroll(EntityType<? extends CragTroll> type, Level level) {
        super(type, level);
        this.xpReward = 25;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 80.0)
                .add(Attributes.ATTACK_DAMAGE, 10.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.ATTACK_KNOCKBACK, 2.2)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(HOLDING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new ThrowBoulderGoal());
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.0, false));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.7));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 10.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, true));
    }

    /** Holding a boulder over its head, about to throw. */
    public boolean isHolding() { return this.entityData.get(HOLDING); }
    public void setHolding(boolean holding) { this.entityData.set(HOLDING, holding); }
    /** Burned recently, so it can't heal. */
    public boolean isScorched() { return this.scorched > 0 || this.isOnFire(); }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            target.push(0, 0.45, 0);   // a punch that lifts you off your feet
            target.needsSync = true;
        }
        return hit;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && source.is(DamageTypeTags.IS_FIRE)) this.scorched = SCORCH_TICKS;
        return hurt;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level) {
            if (this.scorched > 0) this.scorched--;
            if (this.isAlive() && this.tickCount % 40 == 0 && this.getHealth() < this.getMaxHealth()) {
                if (this.isScorched()) {
                    level.sendParticles(ParticleTypes.LARGE_SMOKE, this.getX(), this.getY() + 2.0, this.getZ(), 4, 0.4, 0.4, 0.4, 0.01);
                } else {
                    this.heal(2.0F);
                    level.sendParticles(ParticleTypes.COMPOSTER, this.getX(), this.getY() + 1.6, this.getZ(), 6, 0.5, 0.6, 0.5, 0.0);
                }
            }
        }
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Scorched", this.scorched);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.scorched = input.getIntOr("Scorched", 0);
    }

    @Override protected float getSoundVolume() { return 1.2F; }
    @Override public float getVoicePitch() { return 0.75F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.RAVAGER_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.RAVAGER_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.RAVAGER_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.RAVAGER_STEP, 0.6F, 0.8F); }

    /** From 6 to 28 blocks away: rip a boulder out of the ground, lift it overhead, and throw. */
    final class ThrowBoulderGoal extends Goal {
        private int ticks, next;

        ThrowBoulderGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = CragTroll.this.getTarget();
            if (t == null || !t.isAlive() || CragTroll.this.tickCount < this.next || !CragTroll.this.onGround()) return false;
            double d = CragTroll.this.distanceToSqr(t);
            return d > 36.0 && d < 784.0 && CragTroll.this.hasLineOfSight(t);
        }

        @Override public boolean canContinueToUse() { return this.ticks < THROW_WINDUP + 6 && CragTroll.this.getTarget() != null; }

        @Override
        public void start() {
            this.ticks = 0;
            CragTroll.this.getNavigation().stop();
            CragTroll.this.entityData.set(HOLDING, true);
            CragTroll.this.playSound(SoundEvents.RAVAGER_ROAR, 1.2F, 0.9F);
            if (CragTroll.this.level() instanceof ServerLevel level) {
                BlockState ground = level.getBlockState(CragTroll.this.getBlockPosBelowThatAffectsMyMovement());
                if (ground.isAir()) ground = Blocks.STONE.defaultBlockState();
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), CragTroll.this.getX(), CragTroll.this.getY() + 0.2,
                        CragTroll.this.getZ(), 30, 0.6, 0.2, 0.6, 0.15);
                CragTroll.this.playSound(SoundEvents.STONE_BREAK, 1.5F, 0.6F);
            }
        }

        @Override
        public void stop() {
            CragTroll.this.entityData.set(HOLDING, false);
            this.next = CragTroll.this.tickCount + 100 + CragTroll.this.random.nextInt(40);
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = CragTroll.this.getTarget();
            if (t == null) return;
            CragTroll.this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (++this.ticks == THROW_WINDUP) {
                CragTroll.this.entityData.set(HOLDING, false);
                Boulder rock = new Boulder(NsvEntities.BOULDER, CragTroll.this, false);
                rock.setPos(CragTroll.this.getX(), CragTroll.this.getY() + 3.0, CragTroll.this.getZ());
                rock.aimAt(t, 1.4F, 2.5F);
                CragTroll.this.level().addFreshEntity(rock);
                CragTroll.this.playSound(SoundEvents.GOAT_RAM_IMPACT, 1.2F, 0.5F);
            }
        }
    }
}
