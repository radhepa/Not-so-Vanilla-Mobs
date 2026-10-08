package dev.nsvmobs.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/** A zombie frozen solid. Its touch chills to the bone and it leaves snow where it walks. */
public class Frostbitten extends Zombie {
    public Frostbitten(EntityType<? extends Frostbitten> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes();
    }

    @Override public void setBaby(boolean baby) { super.setBaby(false); }
    @Override protected boolean convertsInWater() { return false; }
    @Override protected boolean isSunSensitive() { return false; }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 1), this);
            if (living.canFreeze()) {
                living.setTicksFrozen(Math.max(living.getTicksFrozen(), living.getTicksRequiredToFreeze() * 2));
            }
        }
        return hit;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level && this.tickCount % 4 == 0 && Griefing.allowed(level)) {
            BlockPos pos = BlockPos.containing(this.getX() + (this.random.nextFloat() - 0.5) * 0.6, this.getY(),
                    this.getZ() + (this.random.nextFloat() - 0.5) * 0.6);
            BlockState snow = Blocks.SNOW.defaultBlockState();
            if (level.getBlockState(pos).isAir() && snow.canSurvive(level, pos)
                    && level.getBiome(pos).value().coldEnoughToSnow(pos, level.getSeaLevel())) {
                level.setBlockAndUpdate(pos, snow);
            }
        }
        if (this.level().isClientSide() && this.random.nextInt(12) == 0) {
            // frosty breath
            this.level().addParticle(net.minecraft.core.particles.ParticleTypes.SNOWFLAKE,
                    this.getX() - Mth.sin(this.yHeadRot * Mth.DEG_TO_RAD) * 0.35, this.getEyeY() - 0.1,
                    this.getZ() + Mth.cos(this.yHeadRot * Mth.DEG_TO_RAD) * 0.35, 0, 0.01, 0);
        }
    }
}
