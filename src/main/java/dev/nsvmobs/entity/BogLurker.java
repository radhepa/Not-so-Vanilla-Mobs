package dev.nsvmobs.entity;

import java.util.EnumSet;

import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.AmphibiousPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;

/**
 * A huge mossy toad. It sits still until prey wanders close, then leaps; from further away it lashes
 * its tongue and drags the target in.
 */
public class BogLurker extends Monster {
    /** Ticks left of the current tongue lash (counts down from {@link #LASH_TICKS}). */
    private static final EntityDataAccessor<Integer> LASH = SynchedEntityData.defineId(BogLurker.class, EntityDataSerializers.INT);
    public static final int LASH_TICKS = 12;
    private static final double AMBUSH_RANGE = 6.0;
    private int idleTicks;

    public BogLurker(EntityType<? extends BogLurker> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.FOLLOW_RANGE, 20.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.3);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(LASH, 0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new AmphibiousPathNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(2, new TongueLashGoal());
        this.goalSelector.addGoal(3, new LeapAtTargetGoal(this, 0.5F));
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.2, false));
        this.goalSelector.addGoal(7, new RandomStrollGoal(this, 0.8, 240) {
            @Override public boolean canUse() { return !BogLurker.this.isLurking() && super.canUse(); }
        });
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        // While lurking it only notices players who come right up to it.
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (target, level) -> !this.isLurking() || target.distanceToSqr(this) < AMBUSH_RANGE * AMBUSH_RANGE));
    }

    /** Lurking: no target for a while, so it sits perfectly still and waits. */
    public boolean isLurking() {
        return this.idleTicks > 60;
    }

    public int lashTicks() {
        return this.entityData.get(LASH);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!this.level().isClientSide()) {
            this.idleTicks = this.getTarget() == null ? this.idleTicks + 1 : 0;
            int lash = this.entityData.get(LASH);
            if (lash > 0) this.entityData.set(LASH, lash - 1);
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) this.playSound(SoundEvents.FROG_EAT, 1.0F, 0.6F);
        return hit;
    }

    @Override public boolean canBreatheUnderwater() { return true; }
    @Override public boolean isPushedByFluid() { return false; }
    @Override public float getVoicePitch() { return 0.55F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.FROG_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.FROG_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.FROG_DEATH; }

    /** From 3 to 8 blocks away: lash the tongue and yank the target toward the mouth. */
    final class TongueLashGoal extends Goal {
        private int cooldown;
        private int windup;

        TongueLashGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (this.cooldown > 0) {
                this.cooldown--;
                return false;
            }
            LivingEntity target = BogLurker.this.getTarget();
            if (target == null || !target.isAlive()) return false;
            double d = BogLurker.this.distanceToSqr(target);
            return d > 9.0 && d < 64.0 && BogLurker.this.hasLineOfSight(target);
        }

        @Override
        public void start() {
            this.windup = 6;
            BogLurker.this.getNavigation().stop();
            BogLurker.this.entityData.set(LASH, LASH_TICKS);
            BogLurker.this.playSound(SoundEvents.FROG_TONGUE, 1.2F, 0.6F);
        }

        @Override public boolean canContinueToUse() { return this.windup > 0; }

        @Override
        public void tick() {
            LivingEntity target = BogLurker.this.getTarget();
            if (target == null) {
                this.windup = 0;
                return;
            }
            BogLurker.this.getLookControl().setLookAt(target, 30.0F, 30.0F);
            if (--this.windup == 0 && BogLurker.this.hasLineOfSight(target)) {
                Vec3 pull = BogLurker.this.position().subtract(target.position());
                double dist = pull.length();
                Vec3 v = pull.normalize().scale(Math.min(1.6, 0.35 + dist * 0.16)).add(0, 0.35, 0);
                target.setDeltaMovement(target.getDeltaMovement().add(v));
                target.needsSync = true;
            }
        }

        @Override
        public void stop() {
            this.cooldown = 80;
        }
    }
}
