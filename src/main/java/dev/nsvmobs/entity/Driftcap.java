package dev.nsvmobs.entity;

import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/**
 * A floating jellyfish of warped fungus from the Warped Forest. It drifts slowly toward anyone
 * nearby; its trailing tendrils sting, and the sting warps you a few blocks away like chorus fruit.
 * Hit it and it may warp away itself.
 */
public class Driftcap extends Monster {
    public Driftcap(EntityType<? extends Driftcap> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 10, true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.FLYING_SPEED, 0.12)
                .add(Attributes.MOVEMENT_SPEED, 0.12)
                .add(Attributes.FOLLOW_RANGE, 12.0);
    }

    /** Ordinary monster rules, but only half as often (the Warped Forest has few other monsters to share with). */
    public static boolean checkSpawnRules(EntityType<Driftcap> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        return (EntitySpawnReason.isSpawner(reason) || random.nextBoolean()) && Monster.checkMonsterSpawnRules(type, level, reason, pos, random);
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
        this.goalSelector.addGoal(2, new DriftTowardGoal());
        this.goalSelector.addGoal(8, new DriftGoal());
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level) {
            if (this.isAlive() && this.tickCount % 10 == 0) stingTouching(level);
        } else if (this.random.nextInt(4) == 0) {
            this.level().addParticle(ParticleTypes.WARPED_SPORE, this.getRandomX(0.6), this.getY() + this.random.nextDouble() * 0.6,
                    this.getRandomZ(0.6), 0, -0.02, 0);
        }
    }

    /** Anything caught in the tendrils (the lower half of the hitbox and a little around it) is stung. */
    private void stingTouching(ServerLevel level) {
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(0.15, 0.3, 0.15),
                e -> e != this && e.isAlive() && !(e instanceof Driftcap) && !(e instanceof Player p && (p.isCreative() || p.isSpectator())))) {
            if (e.hurtServer(level, this.damageSources().mobAttack(this), (float) this.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                e.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 80), this);
                warp(level, e);
            }
        }
    }

    /** Teleport a few blocks in a random direction, the way chorus fruit does. */
    static boolean warp(ServerLevel level, LivingEntity e) {
        Vec3 from = e.position();
        for (int i = 0; i < 16; i++) {
            double x = e.getX() + (e.getRandom().nextDouble() - 0.5) * 16.0;
            double y = Mth.clamp(e.getY() + (e.getRandom().nextInt(16) - 8), level.getMinY(), level.getMinY() + level.getLogicalHeight() - 1);
            double z = e.getZ() + (e.getRandom().nextDouble() - 0.5) * 16.0;
            if (e.isPassenger()) e.stopRiding();
            if (e.randomTeleport(x, y, z, true, BlockTags.CONSUMABLE_DOES_NOT_TELEPORT_TO)) {
                level.playSound(null, from.x, from.y, from.z, SoundEvents.CHORUS_FRUIT_TELEPORT, SoundSource.HOSTILE, 1.0F, 1.0F);
                e.playSound(SoundEvents.CHORUS_FRUIT_TELEPORT, 1.0F, 1.0F);
                e.resetFallDistance();
                return true;
            }
        }
        return false;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive() && this.random.nextInt(5) < 2) warp(level, this);
        return hurt;
    }

    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override public boolean isFlapping() { return false; }
    @Override public float getVoicePitch() { return 1.3F + this.random.nextFloat() * 0.2F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.GLOW_SQUID_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.SLIME_SQUISH; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.SLIME_DEATH; }
    @Override protected float getSoundVolume() { return 0.6F; }

    /** Ground height under x, z, searching down from the mob (the Nether has a roof). */
    private double floorBelow(double x, double z) {
        BlockPos.MutableBlockPos p = BlockPos.containing(x, this.getY(), z).mutable();
        for (int i = 0; i < 12 && p.getY() > this.level().getMinY(); i++, p.move(0, -1, 0)) {
            if (!this.level().getBlockState(p).getCollisionShape(this.level(), p).isEmpty()) return p.getY() + 1;
        }
        return this.level().dimensionType().hasCeiling() ? this.getY() - 2 : this.level().getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(x), Mth.floor(z));
    }

    /** Drift about a few blocks at a time, bobbing 1-3 blocks above the ground. */
    final class DriftGoal extends Goal {
        private Vec3 to;
        private int ticks;

        DriftGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return Driftcap.this.getTarget() == null && Driftcap.this.random.nextInt(20) == 0;
        }

        @Override
        public void start() {
            double x = Driftcap.this.getX() + Driftcap.this.random.nextInt(13) - 6;
            double z = Driftcap.this.getZ() + Driftcap.this.random.nextInt(13) - 6;
            this.to = new Vec3(x, floorBelow(x, z) + 1.0 + Driftcap.this.random.nextDouble() * 2.0, z);
            this.ticks = 100 + Driftcap.this.random.nextInt(100);
        }

        @Override public boolean canContinueToUse() { return --this.ticks > 0 && Driftcap.this.getTarget() == null; }

        @Override
        public void tick() {
            double bob = Mth.sin(Driftcap.this.tickCount * 0.08F) * 0.4;
            Driftcap.this.getMoveControl().setWantedPosition(this.to.x, this.to.y + bob, this.to.z, 1.0);
        }
    }

    /** Drift slowly at the target so its tendrils trail over them. */
    final class DriftTowardGoal extends Goal {
        DriftTowardGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Driftcap.this.getTarget();
            return t != null && t.isAlive();
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = Driftcap.this.getTarget();
            if (t == null) return;
            Driftcap.this.getLookControl().setLookAt(t, 10.0F, 10.0F);
            // aim to hang with the tendrils at the target's head
            Driftcap.this.getMoveControl().setWantedPosition(t.getX(), t.getY() + t.getBbHeight() * 0.6, t.getZ(), 1.3);
        }
    }
}
