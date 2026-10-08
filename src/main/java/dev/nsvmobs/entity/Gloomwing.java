package dev.nsvmobs.entity;

import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
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
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** A cave bat-thing that circles, then swoops. Its bite brings the Darkness. Lives only underground. */
public class Gloomwing extends Monster {
    public Gloomwing(EntityType<? extends Gloomwing> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 20, true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.FLYING_SPEED, 0.6)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    /** Underground only: below y 40, no sky overhead, and dark like any monster. */
    public static boolean checkSpawnRules(EntityType<Gloomwing> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        if (EntitySpawnReason.isSpawner(reason)) return Monster.checkMonsterSpawnRules(type, level, reason, pos, random);
        return pos.getY() < 40 && !level.canSeeSky(pos) && Monster.checkMonsterSpawnRules(type, level, reason, pos, random);
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
        this.goalSelector.addGoal(8, new WaterAvoidingRandomFlyingGoal(this, 1.0));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 80), this);
        }
        return hit;
    }

    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override public boolean isFlapping() { return true; }
    @Override public float getVoicePitch() { return 0.5F + this.random.nextFloat() * 0.15F; }
    @Override protected SoundEvent getAmbientSound() { return this.random.nextInt(3) == 0 ? SoundEvents.BAT_AMBIENT : null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.BAT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.BAT_DEATH; }

    /** Circle the target a few blocks up, then dive in for a bite and climb away again. */
    final class SwoopGoal extends Goal {
        private int cooldown;
        private float orbit;

        SwoopGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Gloomwing.this.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public void start() {
            this.cooldown = 20 + Gloomwing.this.random.nextInt(20);
            this.orbit = Gloomwing.this.random.nextFloat() * Mth.TWO_PI;
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = Gloomwing.this.getTarget();
            if (t == null) return;
            Gloomwing.this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (this.cooldown > 0) {
                this.cooldown--;
                this.orbit += 0.08F;
                double r = 3.5;
                Vec3 aim = new Vec3(t.getX() + Mth.cos(this.orbit) * r, t.getY() + 2.6 + Mth.sin(this.orbit * 2.3F) * 0.6,
                        t.getZ() + Mth.sin(this.orbit) * r);
                Gloomwing.this.getMoveControl().setWantedPosition(aim.x, aim.y, aim.z, 1.0);
                return;
            }
            Gloomwing.this.getMoveControl().setWantedPosition(t.getX(), t.getY() + t.getBbHeight() * 0.6, t.getZ(), 1.7);
            if (Gloomwing.this.distanceToSqr(t) < 1.6 && Gloomwing.this.level() instanceof ServerLevel level) {
                Gloomwing.this.doHurtTarget(level, t);
                this.cooldown = 30 + Gloomwing.this.random.nextInt(30);
            }
        }
    }
}
