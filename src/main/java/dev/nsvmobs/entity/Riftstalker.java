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
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
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
import net.minecraft.world.entity.monster.Endermite;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A gaunt void predator of the outer End. Every few seconds it vanishes and a rift opens behind
 * you, swirling for most of a second; then it steps out and slashes. Turn round and hit it before
 * the slash lands and it staggers, helpless and taking extra damage, for a couple of seconds.
 * Arrows and other projectiles never touch it: it blinks away from them. Water burns it.
 */
public class Riftstalker extends Monster {
    public static final byte HUNTING = 0, PHASED = 1, EMERGED = 2, STAGGERED = 3;
    private static final EntityDataAccessor<Byte> PHASE = SynchedEntityData.defineId(Riftstalker.class, EntityDataSerializers.BYTE);
    /** Rift open (phased) before it steps out; then the window to hit it before it slashes. */
    public static final int RIFT_TICKS = 16, COUNTER_TICKS = 10, STAGGER_TICKS = 50;
    static final float SLASH_DAMAGE = 10.0F;
    private int phaseStart;
    private @Nullable Vec3 rift;

    public Riftstalker(EntityType<? extends Riftstalker> type, Level level) {
        super(type, level);
        this.xpReward = 25;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.4)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(PHASE, HUNTING);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new BlinkGoal());
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 12.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Endermite.class, true));
    }

    public byte phase() { return this.entityData.get(PHASE); }

    public void setPhase(byte phase) {
        this.entityData.set(PHASE, phase);
        this.phaseStart = this.tickCount;
    }

    public float phaseAge(float partialTick) {
        return this.tickCount - this.phaseStart + partialTick;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (PHASE.equals(key)) this.phaseStart = this.tickCount;
    }

    public boolean isPhased() { return this.phase() == PHASED; }
    public boolean isStaggered() { return this.phase() == STAGGERED; }
    /** Out of the rift and winding up its slash: the moment to hit it. */
    public boolean isExposed() { return this.phase() == EMERGED && this.tickCount - this.phaseStart < COUNTER_TICKS; }

    @Override public boolean isSensitiveToWater() { return true; }

    @Override
    public boolean isInvulnerableTo(ServerLevel level, DamageSource source) {
        return this.isPhased() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) || super.isInvulnerableTo(level, source);
    }

    @Override public boolean isPickable() { return !this.isPhased() && super.isPickable(); }
    @Override public boolean isPushable() { return !this.isPhased() && super.isPushable(); }
    @Override public boolean canBeCollidedWith(@Nullable Entity other) { return !this.isPhased() && super.canBeCollidedWith(other); }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (this.isInvulnerableTo(level, source)) return false;
        if (source.is(DamageTypeTags.IS_PROJECTILE) && !this.isStaggered()) {
            this.blinkAway(level);
            return false;
        }
        if (this.isExposed() && source.getDirectEntity() instanceof LivingEntity) {
            this.stagger(level);   // caught as it stepped out
        }
        return super.hurtServer(level, source, this.isStaggered() ? damage * 1.5F : damage);
    }

    void stagger(ServerLevel level) {
        this.setPhase(STAGGERED);
        this.getNavigation().stop();
        this.playSound(SoundEvents.ENDERMAN_HURT, 1.5F, 0.5F);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, this.getX(), this.getY() + 1.6, this.getZ(), 30, 0.4, 0.8, 0.4, 0.05);
    }

    /** A short hop away (from an arrow, or out of water). */
    boolean blinkAway(ServerLevel level) {
        for (int i = 0; i < 16; i++) {
            double x = this.getX() + (this.random.nextDouble() - 0.5) * 16.0;
            double y = this.getY() + this.random.nextInt(8) - 4;
            double z = this.getZ() + (this.random.nextDouble() - 0.5) * 16.0;
            Vec3 from = this.position();
            if (this.randomTeleport(x, y, z, true, BlockTags.ENDERMAN_DOES_NOT_TELEPORT_TO)) {
                level.playSound(null, from.x, from.y, from.z, SoundEvents.ENDERMAN_TELEPORT, this.getSoundSource(), 1.0F, 0.6F);
                return true;
            }
        }
        return false;
    }

    @Override
    protected boolean isImmobile() {
        return super.isImmobile() || this.isStaggered() || this.isPhased();
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) {
            if (this.random.nextInt(this.isStaggered() ? 1 : 4) == 0 && !this.isPhased()) {
                this.level().addParticle(ParticleTypes.PORTAL, this.getRandomX(0.5), this.getRandomY() - 0.25, this.getRandomZ(0.5),
                        (this.random.nextDouble() - 0.5) * 2.0, -this.random.nextDouble(), (this.random.nextDouble() - 0.5) * 2.0);
            }
            return;
        }
        if (this.phase() == HUNTING && this.tickCount % 20 == 0 && this.isInWaterOrRain()) this.blinkAway(level);
        // the blink runs here, not in a goal, so nothing can interrupt it halfway
        int age = this.tickCount - this.phaseStart;
        switch (this.phase()) {
            case PHASED -> {
                if (this.rift != null) {
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, this.rift.x, this.rift.y + 1.2, this.rift.z, 8, 0.25, 0.9, 0.25, 0.02);
                    level.sendParticles(ParticleTypes.PORTAL, this.rift.x, this.rift.y + 1.2, this.rift.z, 6, 0.1, 0.9, 0.1, 0.4);
                }
                if (age >= RIFT_TICKS) this.emerge(level);
            }
            case EMERGED -> {
                LivingEntity t = this.getTarget();
                if (age == COUNTER_TICKS && t != null && t.isAlive()) {
                    this.swingForAttack(InteractionHand.MAIN_HAND);
                    if (this.distanceToSqr(t) < 12.25) {
                        t.hurtServer(level, this.damageSources().mobAttack(this), SLASH_DAMAGE);
                    } else {
                        // it came out too far away: lunge
                        Vec3 to = t.position().subtract(this.position()).normalize();
                        this.setDeltaMovement(to.x * 0.9, 0.3, to.z * 0.9);
                    }
                }
                if (age >= COUNTER_TICKS + 10) this.setPhase(HUNTING);
            }
            case STAGGERED -> {
                if (age >= STAGGER_TICKS) this.setPhase(HUNTING);
            }
            default -> {}
        }
    }

    /** Vanish, and open a rift two blocks behind the target (behind where it's looking). */
    public boolean openRift(ServerLevel level, LivingEntity target) {
        Vec3 look = Vec3.directionFromRotation(0.0F, target.getYHeadRot());
        for (double[] off : new double[][]{{-2.0, 0.0}, {-1.5, 1.5}, {-1.5, -1.5}, {0.0, 2.0}, {0.0, -2.0}}) {
            // behind, then behind-left/right, then the sides
            Vec3 side = new Vec3(-look.z, 0, look.x);
            Vec3 p = target.position().add(look.scale(off[0])).add(side.scale(off[1]));
            Vec3 ground = this.standingSpot(level, p);
            if (ground != null) {
                this.rift = ground;
                this.setPhase(PHASED);
                this.getNavigation().stop();
                level.sendParticles(ParticleTypes.PORTAL, this.getX(), this.getY() + 1.3, this.getZ(), 40, 0.3, 1.0, 0.3, 0.6);
                level.playSound(null, this.getX(), this.getY(), this.getZ(), SoundEvents.ENDERMAN_TELEPORT, this.getSoundSource(), 1.0F, 0.5F);
                level.playSound(null, ground.x, ground.y, ground.z, SoundEvents.PORTAL_AMBIENT, this.getSoundSource(), 0.6F, 1.8F);
                return true;
            }
        }
        return false;
    }

    private @Nullable Vec3 standingSpot(ServerLevel level, Vec3 p) {
        BlockPos.MutableBlockPos b = BlockPos.containing(p.x, p.y + 1, p.z).mutable();
        for (int i = 0; i < 4; i++, b.move(0, -1, 0)) {
            if (level.getBlockState(b.below()).isFaceSturdy(level, b.below(), net.minecraft.core.Direction.UP)) {
                Vec3 at = new Vec3(p.x, b.getY(), p.z);
                if (level.noCollision(this, this.getDimensions(this.getPose()).makeBoundingBox(at)) && !level.containsAnyLiquid(this.getDimensions(this.getPose()).makeBoundingBox(at))) {
                    return at;
                }
            }
        }
        return null;
    }

    void emerge(ServerLevel level) {
        Vec3 at = this.rift != null ? this.rift : this.position();
        this.rift = null;
        LivingEntity t = this.getTarget();
        float yaw = t != null ? (float) (Mth.atan2(t.getZ() - at.z, t.getX() - at.x) * Mth.RAD_TO_DEG) - 90.0F : this.getYRot();
        this.snapTo(at.x, at.y, at.z, yaw, 0.0F);
        this.yHeadRot = yaw;
        this.yBodyRot = yaw;
        this.setPhase(EMERGED);
        this.playSound(SoundEvents.ENDERMAN_SCREAM, 1.2F, 0.6F);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, at.x, at.y + 1.2, at.z, 40, 0.3, 1.0, 0.3, 0.1);
    }

    @Override public float getVoicePitch() { return 0.6F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return this.isPhased() ? null : SoundEvents.ENDERMAN_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.ENDERMAN_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.ENDERMAN_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) {}

    /** Every few seconds, when the target is within 24 blocks: blink behind it. */
    final class BlinkGoal extends Goal {
        private int next;

        BlinkGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            Riftstalker r = Riftstalker.this;
            LivingEntity t = r.getTarget();
            if (t == null || !t.isAlive() || r.phase() != HUNTING || r.tickCount < this.next) return false;
            if (t instanceof Player p && (p.isCreative() || p.isSpectator())) return false;
            return r.distanceToSqr(t) < 576.0 && r.distanceToSqr(t) > 4.0;
        }

        @Override public boolean canContinueToUse() { return false; }

        @Override
        public void start() {
            Riftstalker r = Riftstalker.this;
            LivingEntity t = r.getTarget();
            this.next = r.tickCount + 90 + r.random.nextInt(50);
            if (t != null) r.openRift((ServerLevel) r.level(), t);
        }
    }
}
