package dev.nsvmobs.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.skeleton.AbstractSkeleton;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** A dead knight in rusted plate. Sword and shield; arrows from the front glance off. */
public class Gravewarden extends AbstractSkeleton {
    public Gravewarden(EntityType<? extends Gravewarden> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return AbstractSkeleton.createAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.MOVEMENT_SPEED, 0.21)
                .add(Attributes.SCALE, 1.15);
    }

    @Override
    protected void populateDefaultEquipmentSlots(RandomSource random, DifficultyInstance difficulty) {
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.IRON_SWORD));
        this.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(Items.SHIELD));
        this.setDropChance(EquipmentSlot.MAINHAND, 0.05F);
        this.setDropChance(EquipmentSlot.OFFHAND, 0.0F);
    }

    @Override public boolean canPickUpLoot() { return false; }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (source.is(DamageTypeTags.IS_PROJECTILE) && fromTheFront(source)) {
            this.playSound(SoundEvents.SHIELD_BLOCK.value(), 1.0F, 0.8F + this.random.nextFloat() * 0.4F);
            return false;
        }
        return super.hurtServer(level, source, damage);
    }

    private boolean fromTheFront(DamageSource source) {
        Vec3 from = source.getSourcePosition();
        if (from == null || !this.getOffhandItem().is(Items.SHIELD)) return false;
        Vec3 view = this.calculateViewVector(0.0F, this.yBodyRot);
        Vec3 toSource = from.subtract(this.position()).multiply(1, 0, 1).normalize();
        return toSource.dot(view) > 0.3;
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.WITHER_SKELETON_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.WITHER_SKELETON_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.WITHER_SKELETON_DEATH; }
    @Override protected SoundEvent getStepSound() { return SoundEvents.WITHER_SKELETON_STEP; }
}
