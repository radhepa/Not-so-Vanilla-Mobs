package dev.nsvmobs.entity;

import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A black jungle panther. It stalks you crouched and silent (all you see at night are its green
 * eyes), then gathers itself for a moment, growls, and pounces from up to ten blocks away. If the
 * pounce lands it pins you and mauls you, then melts back into the undergrowth to stalk again. Block
 * the pounce with a shield and it's left dazed, taking extra damage, for three seconds.
 */
public class Prowler extends Monster {
    public static final byte PROWLING = 0, STALKING = 1, CROUCHING = 2, LEAPING = 3, MAULING = 4, DAZED = 5, RETREATING = 6;
    private static final EntityDataAccessor<Byte> MODE = SynchedEntityData.defineId(Prowler.class, EntityDataSerializers.BYTE);
    public static final int CROUCH_TICKS = 16, MAUL_TICKS = 30, DAZE_TICKS = 60;
    static final float POUNCE_DAMAGE = 8.0F, MAUL_DAMAGE = 3.0F;
    private int modeStart;
    /** Set while a pounce lands, if a shield caught it. */
    private boolean blocked;

    public Prowler(EntityType<? extends Prowler> type, Level level) {
        super(type, level);
        this.xpReward = 20;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.MOVEMENT_SPEED, 0.34)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(MODE, PROWLING);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new HuntGoal());
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 10.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    public byte mode() { return this.entityData.get(MODE); }

    public void setMode(byte mode) {
        this.entityData.set(MODE, mode);
        this.modeStart = this.tickCount;
    }

    /** Ticks (with partial) since the current mode began (either side). */
    public float modeAge(float partialTick) {
        return this.tickCount - this.modeStart + partialTick;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (MODE.equals(key)) this.modeStart = this.tickCount;
    }

    public boolean isCrouched() {
        byte m = this.mode();
        return m == STALKING || m == CROUCHING;
    }

    /** A shield caught the pounce (called by the target's blocking code). */
    @Override
    protected void blockedByItem(LivingEntity defender, DamageSource source, float damage, boolean fullyBlocked) {
        super.blockedByItem(defender, source, damage, fullyBlocked);
        if (this.mode() == LEAPING) this.blocked = true;
    }

    /** The pounce connects: pinned and mauled, or (against a raised shield) dazed. */
    public void pounceHit(ServerLevel level, LivingEntity target) {
        this.blocked = false;
        boolean hurt = target.hurtServer(level, this.damageSources().mobAttack(this), POUNCE_DAMAGE);
        this.swingForAttack(InteractionHand.MAIN_HAND);
        if (this.blocked) {
            this.daze();
        } else if (hurt) {
            this.setMode(MAULING);
            target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, MAUL_TICKS + 5, 5), this);
            this.playSound(SoundEvents.POLAR_BEAR_WARNING, 1.2F, 1.3F);
        } else {
            this.setMode(RETREATING);
        }
    }

    void daze() {
        this.setMode(DAZED);
        this.setDeltaMovement(this.getDeltaMovement().multiply(-0.4, 0.0, -0.4).add(0, 0.25, 0));
        this.playSound(SoundEvents.OCELOT_HURT, 1.2F, 0.5F);
    }

    public boolean isDazed() { return this.mode() == DAZED; }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean dazed = this.isDazed();
        boolean hurt = super.hurtServer(level, source, dazed ? damage * 1.5F : damage);
        // hitting it hard while it's mauling you throws it off
        if (hurt && this.mode() == MAULING && damage >= 3.0F) this.setMode(RETREATING);
        return hurt;
    }

    @Override
    protected boolean isImmobile() {
        return super.isImmobile() || this.isDazed();
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level) {
            // the daze wears off whether or not its AI is running
            if (this.isDazed() && this.tickCount - this.modeStart >= DAZE_TICKS) this.setMode(RETREATING);
        } else if (this.isDazed() && this.tickCount % 4 == 0) {
            this.level().addParticle(ParticleTypes.CRIT, this.getX(), this.getY() + 1.1, this.getZ(),
                    (this.random.nextDouble() - 0.5) * 0.3, 0.1, (this.random.nextDouble() - 0.5) * 0.3);
        }
    }

    @Override public float getVoicePitch() { return 0.5F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return this.isCrouched() ? null : SoundEvents.OCELOT_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.OCELOT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.OCELOT_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) {}

    /** The whole hunt: stalk, crouch, pounce, maul, slink away, stalk again. */
    final class HuntGoal extends Goal {
        private int nextPounce, swipeCooldown, retreatUntil;
        private @Nullable Vec3 hideAt;

        HuntGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        private @Nullable LivingEntity target() {
            LivingEntity t = Prowler.this.getTarget();
            return t != null && t.isAlive() && !(t instanceof Player p && (p.isCreative() || p.isSpectator())) ? t : null;
        }

        @Override public boolean canUse() { return this.target() != null; }
        @Override public boolean canContinueToUse() { return this.target() != null || Prowler.this.mode() == MAULING; }

        @Override
        public void start() {
            Prowler.this.setMode(STALKING);
        }

        @Override
        public void stop() {
            if (!Prowler.this.isDazed()) Prowler.this.setMode(PROWLING);
            Prowler.this.getNavigation().stop();
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            Prowler p = Prowler.this;
            LivingEntity t = this.target();
            if (this.swipeCooldown > 0) this.swipeCooldown--;
            int age = p.tickCount - p.modeStart;
            ServerLevel level = (ServerLevel) p.level();
            switch (p.mode()) {
                case STALKING, PROWLING -> {
                    if (t == null) return;
                    if (p.mode() == PROWLING) p.setMode(STALKING);
                    p.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    double d = p.distanceToSqr(t);
                    if (d < 9.0) {
                        // too close for a pounce: swipe
                        p.getNavigation().moveTo(t, 1.0);
                        if (this.swipeCooldown == 0 && d < 5.0) {
                            p.swingForAttack(InteractionHand.MAIN_HAND);
                            p.doHurtTarget(level, t);
                            this.swipeCooldown = 20;
                        }
                    } else if (d < 100.0 && p.tickCount >= this.nextPounce && p.onGround() && p.hasLineOfSight(t)) {
                        p.getNavigation().stop();
                        p.setMode(CROUCHING);
                        p.playSound(SoundEvents.PANDA_AGGRESSIVE_AMBIENT, 1.0F, 0.5F);
                    } else {
                        p.getNavigation().moveTo(t, 0.75);
                    }
                }
                case CROUCHING -> {
                    if (t == null) return;
                    p.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    p.getNavigation().stop();
                    if (age >= CROUCH_TICKS) this.leap(t);
                }
                case LEAPING -> {
                    if (t != null && p.getBoundingBox().inflate(0.4).intersects(t.getBoundingBox())) {
                        p.pounceHit(level, t);
                        this.nextPounce = p.tickCount + 100;
                    } else if (age > 3 && p.onGround()) {
                        // missed
                        p.setMode(STALKING);
                        this.nextPounce = p.tickCount + 40;
                    }
                }
                case MAULING -> {
                    if (t == null || age >= MAUL_TICKS) {
                        this.retreat(t);
                        return;
                    }
                    p.getNavigation().stop();
                    p.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    // stay on top of it
                    Vec3 to = t.position().subtract(p.position());
                    if (to.horizontalDistanceSqr() > 0.5) p.setDeltaMovement(to.x * 0.3, p.getDeltaMovement().y, to.z * 0.3);
                    if (age % 10 == 9) {
                        p.swingForAttack(InteractionHand.MAIN_HAND);
                        t.hurtServer(level, p.damageSources().mobAttack(p), MAUL_DAMAGE);
                        p.playSound(SoundEvents.PANDA_BITE, 1.0F, 0.6F);
                    }
                }
                case RETREATING -> {
                    if (this.hideAt == null) this.retreat(t);
                    if (p.tickCount >= this.retreatUntil || p.getNavigation().isDone() && age > 20) {
                        this.hideAt = null;
                        p.setMode(STALKING);
                    }
                }
                default -> {}
            }
        }

        private void leap(LivingEntity t) {
            Prowler p = Prowler.this;
            // aim a little ahead of where the target is heading
            Vec3 aim = t.position().add(t.getDeltaMovement().multiply(4.0, 0.0, 4.0));
            Vec3 to = aim.subtract(p.position());
            double flat = Math.sqrt(to.x * to.x + to.z * to.z);
            double speed = Mth.clamp(flat * 0.16, 0.6, 1.6);
            p.setDeltaMovement(to.x / Math.max(flat, 0.1) * speed, 0.42 + Math.min(flat, 10.0) * 0.02 + Math.max(0.0, to.y) * 0.1,
                    to.z / Math.max(flat, 0.1) * speed);
            p.setYRot((float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90.0F);
            p.yBodyRot = p.getYRot();
            p.setMode(LEAPING);
            p.playSound(SoundEvents.POLAR_BEAR_WARNING, 1.3F, 1.25F);
        }

        private void retreat(@Nullable LivingEntity t) {
            Prowler p = Prowler.this;
            p.setMode(RETREATING);
            Vec3 from = t != null ? t.position() : p.position();
            this.hideAt = DefaultRandomPos.getPosAway(p, 14, 6, from);
            if (this.hideAt != null) p.getNavigation().moveTo(this.hideAt.x, this.hideAt.y, this.hideAt.z, 1.3);
            this.retreatUntil = p.tickCount + 60 + p.random.nextInt(40);
        }
    }
}
