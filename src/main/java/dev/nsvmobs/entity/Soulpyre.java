package dev.nsvmobs.entity;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.monster.skeleton.AbstractSkeleton;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.jspecify.annotations.Nullable;

/** A skeleton wreathed in soul fire. Fire can't hurt it, and its arrows set you alight. */
public class Soulpyre extends AbstractSkeleton {
    public Soulpyre(EntityType<? extends Soulpyre> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return AbstractSkeleton.createAttributes();
    }

    @Override
    protected AbstractArrow getArrow(ItemStack projectile, float power, @Nullable ItemStack firingWeapon) {
        AbstractArrow arrow = super.getArrow(projectile, power, firingWeapon);
        arrow.igniteForSeconds(100.0F);
        return arrow;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level().isClientSide() && this.random.nextInt(3) == 0) {
            this.level().addParticle(this.random.nextInt(4) == 0 ? ParticleTypes.SOUL : ParticleTypes.SOUL_FIRE_FLAME,
                    this.getRandomX(0.5), this.getRandomY(), this.getRandomZ(0.5), 0.0, 0.03, 0.0);
        }
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.SKELETON_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.SKELETON_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.SKELETON_DEATH; }
    @Override protected SoundEvent getStepSound() { return SoundEvents.SKELETON_STEP; }
    @Override public float getVoicePitch() { return 0.8F + this.random.nextFloat() * 0.1F; }
}
