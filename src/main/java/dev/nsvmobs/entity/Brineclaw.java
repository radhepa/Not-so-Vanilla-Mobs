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
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.BodyRotationControl;
import net.minecraft.world.entity.ai.control.LookControl;
import net.minecraft.world.entity.ai.control.MoveControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A giant armoured shore crab. Its thick front shell shrugs off three quarters of any blow that
 * comes from in front of it, arrows included, but it turns slowly: get round to its side or back
 * and it takes full damage. Its huge crusher claw rises (that's your warning), snaps shut on whatever
 * is in front of it, holds it, and flings it aside.
 */
public class Brineclaw extends Monster {
    public static final byte IDLE = 0, WINDUP = 1, CLAMPING = 2;
    private static final EntityDataAccessor<Byte> ACTION = SynchedEntityData.defineId(Brineclaw.class, EntityDataSerializers.BYTE);
    /** Degrees per tick it can turn; a sprinting player circling it close outpaces this. */
    static final float TURN = 5.0F;
    /** Blows from within this many degrees of straight ahead hit the shell. */
    static final double GUARD_ARC = 70.0;
    static final float GUARD_FACTOR = 0.25F, CLAMP_DAMAGE = 9.0F;
    public static final int WINDUP_TICKS = 12, CLAMP_TICKS = 20;
    static final double REACH = 2.9;
    private int actionStart;

    public Brineclaw(EntityType<? extends Brineclaw> type, Level level) {
        super(type, level);
        this.xpReward = 20;
        this.moveControl = new SlowTurnMoveControl(this);
        this.lookControl = new SlowLookControl(this);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.ATTACK_DAMAGE, CLAMP_DAMAGE)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FOLLOW_RANGE, 20.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.7)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ACTION, IDLE);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new ClampGoal());
        this.goalSelector.addGoal(6, new RandomStrollGoal(this, 0.7));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected BodyRotationControl createBodyControl() {
        return new SlowBodyControl(this);
    }

    public byte action() { return this.entityData.get(ACTION); }

    public void setAction(byte action) {
        this.entityData.set(ACTION, action);
        this.actionStart = this.tickCount;
    }

    /** Ticks (with partial) since the current action began. */
    public float actionAge(float partialTick) {
        return this.tickCount - this.actionStart + partialTick;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (ACTION.equals(key)) this.actionStart = this.tickCount;
    }

    /** Degrees between where it faces and the direction of a point (0 = dead ahead). */
    double angleTo(Vec3 p) {
        Vec3 view = Vec3.directionFromRotation(0.0F, this.yBodyRot);
        Vec3 to = new Vec3(p.x - this.getX(), 0.0, p.z - this.getZ());
        if (to.lengthSqr() < 1.0E-6) return 0.0;
        return Math.toDegrees(Math.acos(Mth.clamp(to.normalize().dot(view), -1.0, 1.0)));
    }

    /** Whether a blow from this source lands on the front shell. */
    public boolean guards(DamageSource source) {
        if (source.is(DamageTypeTags.BYPASSES_ARMOR) || source.is(DamageTypeTags.IS_FIRE) || source.is(DamageTypeTags.IS_FALL)) return false;
        Vec3 from = source.getSourcePosition();
        return from != null && this.angleTo(from) < GUARD_ARC;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (this.guards(source)) {
            damage *= GUARD_FACTOR;
            this.playSound(SoundEvents.SHIELD_BLOCK.value(), 1.0F, 0.6F + this.random.nextFloat() * 0.2F);
            level.sendParticles(ParticleTypes.CRIT, this.getX(), this.getY() + 0.7, this.getZ(), 6, 0.5, 0.3, 0.5, 0.1);
        }
        return super.hurtServer(level, source, damage);
    }

    @Override public float getVoicePitch() { return 0.55F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.TURTLE_AMBIENT_LAND; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.TURTLE_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.TURTLE_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.SPIDER_STEP, 0.25F, 0.5F); }

    /** Movement turns the body no faster than {@link #TURN} degrees a tick. */
    static final class SlowTurnMoveControl extends MoveControl<Brineclaw> {
        SlowTurnMoveControl(Brineclaw mob) {
            super(mob);
        }

        @Override
        public void tick() {
            float before = this.mob.getYRot();
            super.tick();
            this.mob.setYRot(Mth.approachDegrees(before, this.mob.getYRot(), TURN));
        }
    }

    /** It has no neck: its eyes turn with its body. */
    static final class SlowLookControl extends LookControl {
        SlowLookControl(Brineclaw mob) {
            super(mob);
        }

        @Override
        public void tick() {
            float before = this.mob.yHeadRot;
            super.tick();
            this.mob.yHeadRot = Mth.approachDegrees(before, this.mob.yHeadRot, TURN);
        }
    }

    static final class SlowBodyControl extends BodyRotationControl {
        private final Brineclaw mob;

        SlowBodyControl(Brineclaw mob) {
            super(mob);
            this.mob = mob;
        }

        @Override
        public void clientTick() {
            double dx = this.mob.getX() - this.mob.xo, dz = this.mob.getZ() - this.mob.zo;
            float want = dx * dx + dz * dz > 2.5E-7 ? this.mob.getYRot() : this.mob.yHeadRot;
            this.mob.yBodyRot = Mth.approachDegrees(this.mob.yBodyRot, want, TURN);
        }
    }

    /** Close in, raise the claw, snap it shut on whatever is in front, hold it, fling it aside. */
    final class ClampGoal extends Goal {
        private int cooldown;
        private @Nullable LivingEntity held;

        ClampGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        private @Nullable LivingEntity target() {
            LivingEntity t = Brineclaw.this.getTarget();
            return t != null && t.isAlive() && !(t instanceof Player p && (p.isCreative() || p.isSpectator())) ? t : null;
        }

        @Override public boolean canUse() { return this.target() != null; }
        @Override public boolean canContinueToUse() { return this.target() != null || Brineclaw.this.action() != IDLE; }

        @Override
        public void stop() {
            Brineclaw.this.setAction(IDLE);
            Brineclaw.this.getNavigation().stop();
            this.held = null;
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        private boolean inReach(LivingEntity t, double arc) {
            return Brineclaw.this.distanceToSqr(t) < REACH * REACH && Brineclaw.this.angleTo(t.position()) < arc;
        }

        @Override
        public void tick() {
            Brineclaw c = Brineclaw.this;
            LivingEntity t = this.target();
            if (this.cooldown > 0) this.cooldown--;
            int age = c.tickCount - c.actionStart;
            ServerLevel level = (ServerLevel) c.level();
            switch (c.action()) {
                case IDLE -> {
                    if (t == null) return;
                    c.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    if (this.cooldown == 0 && this.inReach(t, 50.0)) {
                        c.getNavigation().stop();
                        c.setAction(WINDUP);
                        c.playSound(SoundEvents.ARMADILLO_SCUTE_DROP, 1.2F, 0.5F);
                    } else {
                        c.getNavigation().moveTo(t, 1.0);
                    }
                }
                case WINDUP -> {
                    if (t != null) c.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    if (age < WINDUP_TICKS) return;
                    if (t != null && this.inReach(t, 60.0)) {
                        c.swingForAttack(InteractionHand.MAIN_HAND);
                        if (c.doHurtTarget(level, t)) {
                            t.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, CLAMP_TICKS + 5, 5), c);
                            this.held = t;
                            c.setAction(CLAMPING);
                            c.playSound(SoundEvents.ZOMBIE_ATTACK_IRON_DOOR, 0.8F, 1.4F);
                            return;
                        }
                    }
                    c.setAction(IDLE);   // missed: it snapped at empty water
                    this.cooldown = 30;
                }
                case CLAMPING -> {
                    if (age < CLAMP_TICKS && this.held != null && this.held.isAlive()) return;
                    if (this.held != null && this.held.isAlive()) {
                        // fling it out to the side the big claw is on
                        Vec3 side = Vec3.directionFromRotation(0.0F, c.yBodyRot - 90.0F);
                        this.held.push(side.x * 1.1, 0.5, side.z * 1.1);
                        this.held.needsSync = true;
                    }
                    this.held = null;
                    c.setAction(IDLE);
                    this.cooldown = 50;
                }
                default -> {}
            }
        }
    }
}
