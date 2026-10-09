package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A striped skunk. It never bites. Walk up on it without crouching and it stamps its front feet and
 * raises its tail; stay close, or hurt it, and it turns its rear and sprays everything nearby
 * (Nausea and a moment's Blindness), then trots off. It needs half a minute to reload.
 */
public class Skunk extends Animal {
    private static final EntityDataAccessor<Boolean> WARNING = SynchedEntityData.defineId(Skunk.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> SPRAYING = SynchedEntityData.defineId(Skunk.class, EntityDataSerializers.BOOLEAN);
    static final double WARN_RANGE = 3.0;
    static final double SPRAY_RANGE = 4.0;
    static final int SPRAY_COOLDOWN = 600;
    private int warnTicks;
    private int sprayTicks;
    private int sprayCooldown;
    private int fleeTicks;
    /** Who it's warning off or spraying. */
    private @Nullable LivingEntity threat;
    private @Nullable Vec3 fleeFrom;

    public Skunk(EntityType<? extends Skunk> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(WARNING, false);
        builder.define(SPRAYING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new StandGroundGoal());
        this.goalSelector.addGoal(2, new TrotOffGoal());
        this.goalSelector.addGoal(3, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(4, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(5, new TemptGoal(this, 1.1, s -> s.is(ItemTags.EGGS), false));
        this.goalSelector.addGoal(6, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
    }

    /** Stamping its front feet with its tail up. */
    public boolean isWarning() {
        return this.entityData.get(WARNING);
    }

    /** Rear turned, tail up: spraying. */
    public boolean isSpraying() {
        return this.entityData.get(SPRAYING);
    }

    /** The yaw (degrees) that points this skunk at a spot. */
    private float yawTo(double x, double z) {
        return (float) (Mth.atan2(z - this.getZ(), x - this.getX()) * Mth.RAD_TO_DEG) - 90.0F;
    }

    private void face(float yaw) {
        this.setYRot(yaw);
        this.setYBodyRot(yaw);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        if (this.sprayCooldown > 0) this.sprayCooldown--;
        if (this.fleeTicks > 0) this.fleeTicks--;
        LivingEntity t = this.threat;
        if (this.sprayTicks > 0) {
            // rear kept turned on its target, looking back over its shoulder
            if (t != null) {
                this.face(this.yawTo(t.getX(), t.getZ()) + 180.0F);
                this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            }
            if (--this.sprayTicks == 0) {
                this.entityData.set(SPRAYING, false);
                this.threat = null;
            }
        } else if (this.warnTicks > 0) {
            if (t == null || !t.isAlive() || t.isSpectator() || this.distanceToSqr(t) > 8.0 * 8.0) {
                this.warnTicks = 0;
                this.entityData.set(WARNING, false);
                this.threat = null;
                return;
            }
            this.getNavigation().stop();
            this.face(this.yawTo(t.getX(), t.getZ()));
            this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (this.warnTicks % 8 == 0) this.playSound(SoundEvents.GOAT_STEP, 0.8F, 1.8F);   // stamp, stamp
            if (--this.warnTicks == 0) {
                this.entityData.set(WARNING, false);
                if (this.distanceToSqr(t) <= WARN_RANGE * WARN_RANGE) this.spray(level);   // didn't back off
                else this.threat = null;
            }
        } else if (this.sprayCooldown == 0 && !this.isBaby() && !this.isInWater() && this.tickCount % 5 == 0) {
            Player p = level.getNearestPlayer(this.getX(), this.getY(), this.getZ(), WARN_RANGE,
                    e -> EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(e) && !e.isCrouching() && this.hasLineOfSight(e));
            if (p != null) {
                this.threat = p;
                this.warnTicks = 40;
                this.entityData.set(WARNING, true);
                this.playSound(SoundEvents.FOX_AGGRO, 0.6F, 1.7F);
            }
        }
    }

    /**
     * Sprays now: turns its rear on whoever it was warning (if anyone), gives everything within 4
     * blocks except other skunks Nausea (10 s) and Blindness (3 s), and then trots off. Ready again
     * after 30 s.
     */
    public void spray(ServerLevel level) {
        LivingEntity target = this.threat;
        this.warnTicks = 0;
        this.entityData.set(WARNING, false);
        this.entityData.set(SPRAYING, true);
        this.sprayTicks = 20;
        this.sprayCooldown = SPRAY_COOLDOWN;
        this.getNavigation().stop();
        if (target != null) this.face(this.yawTo(target.getX(), target.getZ()) + 180.0F);

        // out of the rear: a jet of green droplets and a stinking cloud
        double bx = Mth.sin(this.yBodyRot * Mth.DEG_TO_RAD), bz = -Mth.cos(this.yBodyRot * Mth.DEG_TO_RAD);
        double rx = this.getX() + bx * 0.4, ry = this.getY() + 0.35, rz = this.getZ() + bz * 0.4;
        for (int i = 0; i < 18; i++) {
            level.sendParticles(ParticleTypes.SNEEZE, rx, ry, rz, 0,
                    bx + this.random.nextGaussian() * 0.25, 0.15 + this.random.nextGaussian() * 0.1, bz + this.random.nextGaussian() * 0.25,
                    0.25 + this.random.nextFloat() * 0.3);
        }
        level.sendParticles(ParticleTypes.NOXIOUS_GAS, rx + bx * 1.5, ry + 0.3, rz + bz * 1.5, 24, 1.3, 0.5, 1.3, 0.005);
        level.sendParticles(ParticleTypes.SNEEZE, rx + bx * 1.5, ry + 0.3, rz + bz * 1.5, 20, 1.5, 0.6, 1.5, 0.01);
        this.playSound(SoundEvents.PUFFER_FISH_BLOW_OUT, 1.0F, 0.7F);
        this.playSound(SoundEvents.FIRE_EXTINGUISH, 0.4F, 1.8F);

        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(SPRAY_RANGE),
                e -> e != this && !(e instanceof Skunk) && e.isAlive() && !e.isSpectator() && this.distanceToSqr(e) <= SPRAY_RANGE * SPRAY_RANGE)) {
            e.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 200), this);
            e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60), this);
        }
        this.fleeFrom = target != null ? target.position() : this.position().add(bx, 0.0, bz);
        this.fleeTicks = 100;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive() && this.sprayCooldown == 0 && !this.isBaby()
                && source.getEntity() instanceof LivingEntity attacker && !(attacker instanceof Skunk)) {
            this.threat = attacker;
            this.spray(level);
        }
        return hurt;
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(ItemTags.EGGS); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.SKUNK.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("SprayCooldown", this.sprayCooldown);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.sprayCooldown = input.getIntOr("SprayCooldown", 0);
    }

    @Override protected SoundEvent getAmbientSound() { return this.isWarning() ? null : SoundEvents.FOX_SNIFF; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.FOX_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.FOX_DEATH; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.9F : 1.5F) + this.random.nextFloat() * 0.15F; }
    @Override protected float getSoundVolume() { return 0.5F; }

    /** Plants its feet while it warns and while it sprays. */
    final class StandGroundGoal extends Goal {
        StandGroundGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP, Flag.LOOK));
        }

        @Override public boolean canUse() { return Skunk.this.warnTicks > 0 || Skunk.this.sprayTicks > 0; }
        @Override public void start() { Skunk.this.getNavigation().stop(); }
    }

    /** After spraying it trots off, away from whoever it sprayed. */
    final class TrotOffGoal extends Goal {
        TrotOffGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override public boolean canUse() { return Skunk.this.fleeTicks > 0 && Skunk.this.fleeFrom != null; }
        @Override public boolean canContinueToUse() { return this.canUse(); }

        @Override
        public void tick() {
            Skunk s = Skunk.this;
            if (s.getNavigation().isDone() && s.fleeFrom != null) {
                Vec3 to = DefaultRandomPos.getPosAway(s, 12, 5, s.fleeFrom);
                if (to != null) s.getNavigation().moveTo(to.x, to.y, to.z, 1.3);
            }
        }

        @Override
        public void stop() {
            Skunk.this.fleeFrom = null;
            Skunk.this.getNavigation().stop();
        }
    }
}
