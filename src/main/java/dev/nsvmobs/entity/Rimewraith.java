package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * A spectre of ice and snow from the frozen peaks. It floats a little above the ground and freezes
 * its prey (any player) within six blocks, the way powder snow does (leather armour keeps you warm, just like
 * in powder snow); once you're frozen through, its cold bites harder. It hurls fans of ice shards and
 * rakes with icicle claws. Water freezes over under it. Fire hurts it twice as much, and it wastes
 * away in warm places.
 */
public class Rimewraith extends Monster {
    public static final byte IDLE = 0, CASTING = 1;
    private static final EntityDataAccessor<Byte> ACTION = SynchedEntityData.defineId(Rimewraith.class, EntityDataSerializers.BYTE);
    static final double AURA = 6.0;
    /** Freezing added every 5 ticks in the aura (powder snow adds 5; the cold wears off at 10). */
    static final int AURA_CHILL = 25;
    public static final int VOLLEY_WINDUP = 14;
    private int actionStart;

    public Rimewraith(EntityType<? extends Rimewraith> type, Level level) {
        super(type, level);
        this.xpReward = 20;
        this.moveControl = new FlyingMoveControl(this, 10, true);
        this.setNoGravity(true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.FLYING_SPEED, 0.35)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ACTION, IDLE);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(2, new VolleyGoal());
        this.goalSelector.addGoal(3, new HauntGoal());
        this.goalSelector.addGoal(8, new HoverGoal());
        this.goalSelector.addGoal(9, new LookAtPlayerGoal(this, Player.class, 12.0F));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    public byte action() { return this.entityData.get(ACTION); }

    public void setAction(byte action) {
        this.entityData.set(ACTION, action);
        this.actionStart = this.tickCount;
    }

    public float actionAge(float partialTick) {
        return this.tickCount - this.actionStart + partialTick;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (ACTION.equals(key)) this.actionStart = this.tickCount;
    }

    /** Freeze something a little more, like powder snow does (nothing happens to a leather-clad player). */
    public static void chill(LivingEntity e, int ticks) {
        if (!e.canFreeze()) return;
        e.setTicksFrozen(Math.min(e.getTicksRequiredToFreeze() + 40, e.getTicksFrozen() + ticks));
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level) {
            if (this.isAlive() && this.tickCount % 5 == 0) this.freezeAround(level);
            if (this.tickCount % 10 == 0 && Griefing.allowed(level)) this.frostWater(level);
            if (this.tickCount % 40 == 0 && level.getBiome(this.blockPosition()).value().getBaseTemperature() > 1.0F) {
                this.hurtServer(level, this.damageSources().onFire(), 1.0F);   // it wastes away somewhere warm
            }
        } else {
            for (int i = 0; i < 2; i++) {
                double a = this.random.nextDouble() * Mth.TWO_PI, r = 0.5 + this.random.nextDouble() * 3.0;
                this.level().addParticle(ParticleTypes.SNOWFLAKE, this.getX() + Math.cos(a) * r, this.getY() + this.random.nextDouble() * 2.2,
                        this.getZ() + Math.sin(a) * r, 0, -0.02, 0);
            }
        }
    }

    private void freezeAround(ServerLevel level) {
        boolean bite = this.tickCount % 20 == 0;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(AURA),
                e -> e != this && e.isAlive() && !(e instanceof Rimewraith) && e.distanceToSqr(this) < AURA * AURA)) {
            // the cold is for players and whatever it's hunting
            if (e instanceof Player p ? p.isCreative() || p.isSpectator() : e != this.getTarget()) continue;
            chill(e, AURA_CHILL);
            // frozen through, close to it: the cold bites
            if (bite && e.isFullyFrozen() && e.canFreeze()) e.hurtServer(level, this.damageSources().freeze(), 2.0F);
        }
    }

    /** Still water just below it freezes over (frosted ice, which melts back on its own). */
    private void frostWater(ServerLevel level) {
        BlockPos base = this.blockPosition();
        for (int dy = 1; dy <= 3; dy++) {
            BlockPos center = base.below(dy);
            if (!level.getFluidState(center).is(FluidTags.WATER)) continue;
            for (BlockPos p : BlockPos.betweenClosed(center.offset(-2, 0, -2), center.offset(2, 0, 2))) {
                if (p.distSqr(center) > 5) continue;
                BlockState s = level.getBlockState(p);
                if (s.is(Blocks.WATER) && s.getFluidState().isSource() && level.getBlockState(p.above()).isAir()) {
                    level.setBlockAndUpdate(p, Blocks.FROSTED_ICE.defaultBlockState());
                    level.scheduleTick(p, Blocks.FROSTED_ICE, Mth.nextInt(this.random, 60, 120));
                }
            }
            return;
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity l) chill(l, 60);
        return hit;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        return super.hurtServer(level, source, source.is(DamageTypeTags.IS_FIRE) ? damage * 2.0F : damage);
    }

    /** Throw three ice shards in a fan. */
    void volley(LivingEntity target) {
        for (int i = -1; i <= 1; i++) {
            IceShard shard = new IceShard(NsvEntities.ICE_SHARD, this);
            shard.setPos(this.getX(), this.getEyeY() - 0.3, this.getZ());
            double dx = target.getX() - this.getX(), dz = target.getZ() - this.getZ();
            double dy = target.getY(0.5) - shard.getY();
            float spread = i * 12.0F * Mth.DEG_TO_RAD;
            double rx = dx * Mth.cos(spread) - dz * Mth.sin(spread), rz = dx * Mth.sin(spread) + dz * Mth.cos(spread);
            shard.shoot(rx, dy + Math.sqrt(rx * rx + rz * rz) * 0.02, rz, 1.5F, 1.0F);
            this.level().addFreshEntity(shard);
        }
        this.playSound(SoundEvents.SNOW_GOLEM_SHOOT, 1.2F, 0.6F);
    }

    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override public boolean isFlapping() { return false; }
    @Override public float getVoicePitch() { return 0.7F + this.random.nextFloat() * 0.15F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.STRAY_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.STRAY_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.STRAY_DEATH; }

    /** Ground height under x, z, searching down from the wraith. */
    private double floorBelow(double x, double y, double z) {
        BlockPos.MutableBlockPos p = BlockPos.containing(x, y, z).mutable();
        for (int i = 0; i < 10 && p.getY() > this.level().getMinY(); i++, p.move(0, -1, 0)) {
            BlockState s = this.level().getBlockState(p);
            if (!s.getCollisionShape(this.level(), p).isEmpty() || !s.getFluidState().isEmpty()) return p.getY() + 1;
        }
        return y - 3;
    }

    /** From 4 to 20 blocks away: raise a hand, then a fan of three ice shards. */
    final class VolleyGoal extends Goal {
        private int ticks, next;

        VolleyGoal() {
            this.setFlags(EnumSet.of(Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Rimewraith.this.getTarget();
            if (t == null || !t.isAlive() || Rimewraith.this.tickCount < this.next) return false;
            double d = Rimewraith.this.distanceToSqr(t);
            return d > 9.0 && d < 400.0 && Rimewraith.this.hasLineOfSight(t);
        }

        @Override public boolean canContinueToUse() { return this.ticks < VOLLEY_WINDUP + 4 && Rimewraith.this.getTarget() != null; }

        @Override
        public void start() {
            this.ticks = 0;
            Rimewraith.this.setAction(CASTING);
            Rimewraith.this.playSound(SoundEvents.STRAY_AMBIENT, 1.0F, 1.6F);
        }

        @Override
        public void stop() {
            Rimewraith.this.setAction(IDLE);
            int base = Rimewraith.this.level().getDifficulty() == Difficulty.HARD ? 40 : 55;
            this.next = Rimewraith.this.tickCount + base + Rimewraith.this.random.nextInt(20);
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = Rimewraith.this.getTarget();
            if (t == null) return;
            Rimewraith.this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (++this.ticks == VOLLEY_WINDUP) {
                Rimewraith.this.swingForAttack(InteractionHand.MAIN_HAND);
                Rimewraith.this.volley(t);
            }
        }
    }

    /** Drift in close (its cold reaches six blocks) and claw anything within reach. */
    final class HauntGoal extends Goal {
        private int clawCooldown;

        HauntGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Rimewraith.this.getTarget();
            return t != null && t.isAlive();
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            Rimewraith w = Rimewraith.this;
            LivingEntity t = w.getTarget();
            if (t == null) return;
            if (this.clawCooldown > 0) this.clawCooldown--;
            double d = w.distanceToSqr(t);
            if (d < 4.0) {
                if (this.clawCooldown == 0) {
                    w.swingForAttack(InteractionHand.MAIN_HAND);
                    w.doHurtTarget((ServerLevel) w.level(), t);
                    this.clawCooldown = 25;
                }
                w.getMoveControl().setWantedPosition(t.getX(), t.getY() + 0.5, t.getZ(), 0.6);
            } else {
                // hang 3 blocks off, a little above its prey, circling slowly
                double a = w.tickCount * 0.03;
                double x = t.getX() + Math.cos(a) * 3.0, z = t.getZ() + Math.sin(a) * 3.0;
                double y = Math.max(t.getY() + 0.8, w.floorBelow(x, w.getY(), z) + 0.6);
                w.getMoveControl().setWantedPosition(x, y, z, 1.0);
            }
        }
    }

    /** With nothing to haunt it drifts about, hovering a block or two above the snow. */
    final class HoverGoal extends Goal {
        private Vec3 to;
        private int ticks;

        HoverGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return Rimewraith.this.getTarget() == null && Rimewraith.this.random.nextInt(20) == 0;
        }

        @Override
        public void start() {
            Rimewraith w = Rimewraith.this;
            double x = w.getX() + w.random.nextInt(13) - 6, z = w.getZ() + w.random.nextInt(13) - 6;
            this.to = new Vec3(x, w.floorBelow(x, w.getY() + 3, z) + 1.0 + w.random.nextDouble(), z);
            this.ticks = 100 + w.random.nextInt(100);
        }

        @Override public boolean canContinueToUse() { return --this.ticks > 0 && Rimewraith.this.getTarget() == null; }

        @Override
        public void tick() {
            double bob = Mth.sin(Rimewraith.this.tickCount * 0.07F) * 0.3;
            Rimewraith.this.getMoveControl().setWantedPosition(this.to.x, this.to.y + bob, this.to.z, 0.6);
        }
    }
}
