package dev.nsvmobs.entity;

import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
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
 * A desert vulture. It soars in wide circles high over open country and leaves healthy players alone,
 * but anyone below half health draws every vulture around: they circle overhead, then swoop to peck.
 */
public class Vulture extends Monster {
    /** Players at or below this share of their health are fair game. */
    static final float WOUNDED = 0.5F;
    private Vec3 soarCentre;

    public Vulture(EntityType<? extends Vulture> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 10, true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.FLYING_SPEED, 0.55)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 40.0);
    }

    /** Out in the open (any light: it's a day bird), on the surface. */
    public static boolean checkSpawnRules(EntityType<Vulture> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                         BlockPos pos, RandomSource random) {
        if (EntitySpawnReason.isSpawner(reason)) return Monster.checkAnyLightMonsterSpawnRules(type, level, reason, pos, random);
        return level.canSeeSky(pos) && pos.getY() >= level.getSeaLevel() && Monster.checkAnyLightMonsterSpawnRules(type, level, reason, pos, random);
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
        this.goalSelector.addGoal(2, new SwoopGoal());
        this.goalSelector.addGoal(8, new SoarGoal());
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, false, false, (t, l) -> wounded(t)));
    }

    static boolean wounded(LivingEntity e) {
        return e.getHealth() <= e.getMaxHealth() * WOUNDED;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        // a player who heals up is no longer carrion (unless they started the fight)
        if (!this.level().isClientSide() && this.getTarget() instanceof Player p && p.getHealth() > p.getMaxHealth() * 0.7F
                && this.getLastHurtByMob() != p) {
            this.setTarget(null);
        }
    }

    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override public boolean isFlapping() { return this.tickCount % 60 < 12; }
    @Override public float getVoicePitch() { return 0.55F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.PARROT_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.PARROT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PARROT_DEATH; }
    @Override public int getAmbientSoundInterval() { return 200; }

    /** Height of the ground (top solid block) under x, z. */
    private int groundY(double x, double z) {
        return this.level().getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(x), Mth.floor(z));
    }

    /** No target: ride the thermals in wide slow circles 14-22 blocks above the ground, drifting about. */
    final class SoarGoal extends Goal {
        private float angle, radius;
        private int ticks;
        private double altitude;

        SoarGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override public boolean canUse() { return Vulture.this.getTarget() == null; }

        @Override
        public void start() {
            RandomSource r = Vulture.this.random;
            if (Vulture.this.soarCentre == null || Vulture.this.soarCentre.distanceToSqr(Vulture.this.position()) > 48 * 48 || r.nextInt(4) == 0) {
                Vulture.this.soarCentre = Vulture.this.position().add(r.nextInt(17) - 8, 0, r.nextInt(17) - 8);
            }
            this.radius = 7.0F + r.nextFloat() * 6.0F;
            this.altitude = 14 + r.nextInt(9);
            this.ticks = 300 + r.nextInt(300);
            Vec3 off = Vulture.this.position().subtract(Vulture.this.soarCentre);
            this.angle = (float) Mth.atan2(off.z, off.x);
        }

        @Override public boolean canContinueToUse() { return this.ticks > 0 && Vulture.this.getTarget() == null; }

        @Override
        public void tick() {
            this.ticks--;
            this.angle += 0.025F;
            Vec3 c = Vulture.this.soarCentre;
            double x = c.x + Mth.cos(this.angle) * this.radius, z = c.z + Mth.sin(this.angle) * this.radius;
            double y = Math.max(groundY(x, z), groundY(c.x, c.z)) + this.altitude + Mth.sin(this.angle * 0.5F) * 1.5;
            Vulture.this.getMoveControl().setWantedPosition(x, y, z, 0.7);
        }
    }

    /** Circle a few blocks over the target, then dive in to peck and climb away again. */
    final class SwoopGoal extends Goal {
        private int cooldown;
        private float orbit;

        SwoopGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Vulture.this.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public void start() {
            this.cooldown = 40 + Vulture.this.random.nextInt(40);
            this.orbit = Vulture.this.random.nextFloat() * Mth.TWO_PI;
            Vulture.this.playSound(SoundEvents.PHANTOM_SWOOP, 0.6F, 1.4F);
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = Vulture.this.getTarget();
            if (t == null) return;
            if (this.cooldown > 0) {
                this.cooldown--;
                this.orbit += 0.06F;
                double r = 5.0;
                Vulture.this.getMoveControl().setWantedPosition(t.getX() + Mth.cos(this.orbit) * r, t.getY() + 6.5 + Mth.sin(this.orbit * 1.7F),
                        t.getZ() + Mth.sin(this.orbit) * r, 0.9);
                return;
            }
            Vulture.this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            Vulture.this.getMoveControl().setWantedPosition(t.getX(), t.getY() + t.getBbHeight() * 0.6, t.getZ(), 1.8);
            if (Vulture.this.distanceToSqr(t) < 2.2 && Vulture.this.level() instanceof ServerLevel level) {
                Vulture.this.doHurtTarget(level, t);
                Vulture.this.playSound(SoundEvents.PHANTOM_BITE, 0.8F, 1.3F);
                this.cooldown = 50 + Vulture.this.random.nextInt(50);
            }
        }
    }
}
