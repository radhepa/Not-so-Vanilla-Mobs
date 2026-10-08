package dev.nsvmobs.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/** A zombie overgrown by fungus. Its hits sicken, and it dies in a cloud of spores that plants mushrooms. */
public class Sporeling extends Zombie {
    public Sporeling(EntityType<? extends Sporeling> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes();
    }

    @Override public void setBaby(boolean baby) { super.setBaby(false); }
    @Override protected boolean convertsInWater() { return false; }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 120), this);
            living.addEffect(new MobEffectInstance(MobEffects.POISON, 60), this);
        }
        return hit;
    }

    @Override
    public void die(DamageSource source) {
        boolean first = !this.isRemoved() && !this.dead;
        super.die(source);
        if (first && this.level() instanceof ServerLevel level) {
            sporeBurst(level);
        }
    }

    private void sporeBurst(ServerLevel level) {
        AreaEffectCloud cloud = new AreaEffectCloud(level, this.getX(), this.getY() + 0.5, this.getZ());
        cloud.setOwner(this);
        cloud.setRadius(2.5F);
        cloud.setRadiusOnUse(-0.4F);
        cloud.setWaitTime(10);
        cloud.setDuration(100);
        cloud.setRadiusPerTick(-cloud.getRadius() / cloud.getDuration());
        cloud.addEffect(new MobEffectInstance(MobEffects.POISON, 80));
        level.addFreshEntity(cloud);

        if (!Griefing.allowed(level)) return;
        int planted = 0;
        for (int i = 0; i < 16 && planted < 3; i++) {
            BlockPos pos = this.blockPosition().offset(this.random.nextInt(7) - 3, this.random.nextInt(3) - 1, this.random.nextInt(7) - 3);
            BlockState mushroom = (this.random.nextBoolean() ? Blocks.RED_MUSHROOM : Blocks.BROWN_MUSHROOM).defaultBlockState();
            if (level.isEmptyBlock(pos) && mushroom.canSurvive(level, pos)) {
                level.setBlock(pos, mushroom, 3);
                planted++;
            }
        }
    }
}
