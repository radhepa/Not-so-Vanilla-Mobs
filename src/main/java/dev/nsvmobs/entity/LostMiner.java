package dev.nsvmobs.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A miner who never came back up. Lives below y 0, tires you out with every hit, and when it can't
 * reach you it digs its way through stone.
 */
public class LostMiner extends Zombie {
    private BlockPos digging;
    private int digTicks, digNeeded;
    /** Whoever it was last hunting; it keeps digging toward them for a while after losing sight. */
    private LivingEntity quarry;
    private int quarryTicks;

    public LostMiner(EntityType<? extends LostMiner> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes();
    }

    /** Deep underground only. */
    public static boolean checkSpawnRules(EntityType<LostMiner> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        return (EntitySpawnReason.isSpawner(reason) || pos.getY() < 0) && Monster.checkMonsterSpawnRules(type, level, reason, pos, random);
    }

    @Override public void setBaby(boolean baby) { super.setBaby(false); }
    @Override protected boolean convertsInWater() { return false; }

    @Override
    protected void populateDefaultEquipmentSlots(RandomSource random, DifficultyInstance difficulty) {
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(random.nextInt(4) == 0 ? Items.STONE_PICKAXE : Items.IRON_PICKAXE));
        this.setDropChance(EquipmentSlot.MAINHAND, 0.04F);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 120), this);
        }
        return hit;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level && this.tickCount % 2 == 0) tunnel(level);
    }

    /**
     * Can't get to its target, or lost sight of it behind a wall? Dig toward it, one block at a
     * time, with cracks showing. It remembers its quarry for 30 s after losing it.
     */
    private void tunnel(ServerLevel level) {
        if (this.getTarget() != null) {
            this.quarry = this.getTarget();
            this.quarryTicks = 300;   // tunnel() runs every 2 ticks
        } else if (this.quarryTicks > 0) {
            this.quarryTicks--;
        }
        LivingEntity target = this.quarryTicks > 0 ? this.quarry : null;
        if (target != null && (!target.isAlive() || target.isRemoved() || this.distanceToSqr(target) > 24 * 24)) {
            this.quarry = null;
            this.quarryTicks = 0;
            target = null;
        }
        boolean blocked = target != null && this.distanceToSqr(target) > 2.5
                && (this.getTarget() == null || this.getNavigation().isDone() || this.getNavigation().isStuck()) && Griefing.allowed(level);
        BlockPos next = blocked ? nextDig(level, target) : null;
        if (next == null || !next.equals(this.digging)) {
            stopDigging(level);
            if (next == null) return;
            this.digging = next;
            float hardness = level.getBlockState(next).getDestroySpeed(level, next);
            this.digNeeded = 10 + (int) (hardness * 12);   // in 2-tick steps: stone ~1.4 s, deepslate ~2.4 s
        }
        this.getLookControl().setLookAt(next.getX() + 0.5, next.getY() + 0.5, next.getZ() + 0.5);
        if (this.digTicks % 4 == 0) {
            var sound = level.getBlockState(next).getSoundType();
            level.playSound(null, next, sound.getHitSound(), net.minecraft.sounds.SoundSource.HOSTILE, sound.getVolume() * 0.5F, sound.getPitch() * 0.8F);
        }
        int stage = (int) (10.0F * ++this.digTicks / this.digNeeded);
        level.destroyBlockProgress(this.getId(), next, Math.min(stage, 9));
        if (this.digTicks >= this.digNeeded) {
            level.destroyBlock(next, true, this);
            stopDigging(level);
        }
    }

    private void stopDigging(ServerLevel level) {
        if (this.digging != null) level.destroyBlockProgress(this.getId(), this.digging, -1);
        this.digging = null;
        this.digTicks = 0;
    }

    private BlockPos nextDig(ServerLevel level, LivingEntity target) {
        BlockPos feet = this.blockPosition();
        double dy = target.getY() - this.getY();
        Direction toward = Direction.getApproximateNearest(target.getX() - this.getX(), 0, target.getZ() - this.getZ());
        BlockPos ahead = feet.relative(toward);
        BlockPos[] order = dy > 1.5 ? new BlockPos[]{feet.above(2), ahead.above(), ahead}
                : dy < -1.5 ? new BlockPos[]{ahead.above(), ahead, ahead.below()}
                : new BlockPos[]{ahead.above(), ahead};
        for (BlockPos p : order) {
            if (diggable(level, p)) return p;
        }
        return null;
    }

    static boolean diggable(ServerLevel level, BlockPos pos) {
        BlockState s = level.getBlockState(pos);
        if (s.isAir() || !s.getFluidState().isEmpty() || s.hasBlockEntity()) return false;
        if (s.is(BlockTags.ORES) || s.is(BlockTags.WITHER_IMMUNE) || s.is(BlockTags.FEATURES_CANNOT_REPLACE)) return false;
        float hardness = s.getDestroySpeed(level, pos);
        return hardness >= 0 && hardness <= 3.5F && (s.is(BlockTags.MINEABLE_WITH_PICKAXE) || s.is(BlockTags.MINEABLE_WITH_SHOVEL));
    }

    @Override
    public void remove(RemovalReason reason) {
        if (this.level() instanceof ServerLevel level) stopDigging(level);
        super.remove(reason);
    }
}
