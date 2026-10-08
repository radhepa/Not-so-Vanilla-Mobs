package dev.nsvmobs.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.monster.skeleton.AbstractSkeleton;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.jspecify.annotations.Nullable;

/** A skeleton strangled by jungle growth: poisoned arrows, and thorns for anyone who hits it up close. */
public class Briarbones extends AbstractSkeleton {
    public Briarbones(EntityType<? extends Briarbones> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return AbstractSkeleton.createAttributes();
    }

    @Override
    protected AbstractArrow getArrow(ItemStack projectile, float power, @Nullable ItemStack firingWeapon) {
        AbstractArrow arrow = super.getArrow(projectile, power, firingWeapon);
        if (arrow instanceof Arrow tipped) {
            tipped.addEffect(new MobEffectInstance(MobEffects.POISON, 100));
        }
        return arrow;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && source.getDirectEntity() instanceof LivingEntity attacker && source.getEntity() == attacker
                && !(attacker instanceof Briarbones)) {
            attacker.hurtServer(level, this.damageSources().thorns(this), 1.0F);
        }
        return hurt;
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.BOGGED_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.BOGGED_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.BOGGED_DEATH; }
    @Override protected SoundEvent getStepSound() { return SoundEvents.BOGGED_STEP; }
}
