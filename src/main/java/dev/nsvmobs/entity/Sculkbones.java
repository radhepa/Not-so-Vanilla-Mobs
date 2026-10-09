package dev.nsvmobs.entity;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.animal.wolf.Wolf;
import net.minecraft.world.entity.monster.skeleton.AbstractSkeleton;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A skeleton swallowed by the sculk. It's blind and hunts by sound: walk, run or jump near it and it
 * hears you; sneak or stand still and it never knows you're there. Its arrows mark you (Glowing),
 * and while marked it can hear you even when you sneak.
 */
public class Sculkbones extends AbstractSkeleton {
    static final double HEARING = 16.0;
    private static final int LISTEN_EVERY = 5;
    /** Where each nearby player was the last time it listened, and when they last made a noise. */
    private final Map<UUID, Vec3> lastPos = new HashMap<>();
    private final Map<UUID, Integer> lastNoise = new HashMap<>();

    public Sculkbones(EntityType<? extends Sculkbones> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return AbstractSkeleton.createAttributes().add(Attributes.FOLLOW_RANGE, HEARING).add(Attributes.MAX_HEALTH, 24.0);
    }

    @Override
    protected void registerGoals() {
        // a skeleton's goals without the eyesight: no fleeing the sun it can't see, no staring at players
        this.goalSelector.addGoal(3, new AvoidEntityGoal<>(this, Wolf.class, 6.0F, 1.0, 1.2));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(6, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 5, false, false, (t, l) -> this.hears(t)));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, 5, false, false, (t, l) -> this.hears(t)));
    }

    /** Heard a noise from it within the last 3 s (or it's marked by one of its arrows). */
    public boolean hears(LivingEntity target) {
        if (target.hasEffect(MobEffects.GLOWING)) return true;
        Integer when = this.lastNoise.get(target.getUUID());
        return when != null && this.tickCount - when < 60 && this.distanceToSqr(target) < HEARING * HEARING;
    }

    /** Footsteps: anyone who moved since it last listened and wasn't sneaking. */
    public static boolean noisy(LivingEntity e, @Nullable Vec3 before) {
        if (before == null || e.isShiftKeyDown() || e.isSpectator()) return false;
        return e.position().distanceToSqr(before) > 0.3 * 0.3 || e.isSprinting();
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level) {
            if (this.tickCount % LISTEN_EVERY == 0) listen(level);
            LivingEntity target = this.getTarget();
            if (target != null && !this.hears(target) && this.getLastHurtByMob() != target) {
                this.setTarget(null);   // the footsteps stopped
            }
        } else if (this.random.nextInt(10) == 0) {
            this.level().addParticle(ParticleTypes.SCULK_SOUL, this.getRandomX(0.4), this.getY(0.9), this.getRandomZ(0.4), 0, 0.02, 0);
        }
    }

    private void listen(ServerLevel level) {
        Map<UUID, Vec3> seen = new HashMap<>();
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(HEARING),
                e -> e instanceof Player || e instanceof IronGolem)) {
            UUID id = e.getUUID();
            boolean first = !this.lastNoise.containsKey(id) || this.tickCount - this.lastNoise.get(id) >= 60;
            if (noisy(e, this.lastPos.get(id))) {
                this.lastNoise.put(id, this.tickCount);
                if (first && this.getTarget() == null && e instanceof Player) {
                    this.playSound(SoundEvents.SCULK_CLICKING, 1.0F, 0.8F + this.random.nextFloat() * 0.2F);
                }
            }
            seen.put(id, e.position());
        }
        this.lastPos.clear();
        this.lastPos.putAll(seen);
        this.lastNoise.keySet().retainAll(seen.keySet());
    }

    @Override
    protected AbstractArrow getArrow(ItemStack projectile, float power, @Nullable ItemStack firingWeapon) {
        AbstractArrow arrow = super.getArrow(projectile, power, firingWeapon);
        if (arrow instanceof Arrow tipped) {
            tipped.addEffect(new MobEffectInstance(MobEffects.GLOWING, 120));
        }
        return arrow;
    }

    @Override protected SoundEvent getAmbientSound() { return this.random.nextInt(3) == 0 ? SoundEvents.WARDEN_TENDRIL_CLICKS : SoundEvents.SKELETON_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.SKELETON_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.SKELETON_DEATH; }
    @Override protected SoundEvent getStepSound() { return SoundEvents.SCULK_BLOCK_STEP; }
    @Override public float getVoicePitch() { return 0.65F + this.random.nextFloat() * 0.1F; }
}
