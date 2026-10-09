package dev.nsvmobs.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/**
 * A rock hurled by a Crag Troll, or (as a magma block) a chunk of molten rock lobbed by a
 * Cinderhulk. Heavy: it falls in a steep arc, hits hard, and its splash hurts anything right next to
 * where it lands. Magma sets things alight. Never breaks or lights blocks.
 */
public class Boulder extends MobMissile {
    static final float DIRECT = 9.0F, SPLASH = 4.0F, MAGMA_DIRECT = 6.0F;

    public Boulder(EntityType<? extends Boulder> type, Level level) {
        super(type, level);
    }

    public Boulder(EntityType<? extends Boulder> type, LivingEntity thrower, boolean magma) {
        super(type, thrower, new ItemStack(magma ? Items.MAGMA_BLOCK : Items.COBBLESTONE));
    }

    @Override
    protected Item getDefaultItem() {
        return Items.COBBLESTONE;
    }

    @Override
    protected double getDefaultGravity() {
        return 0.05;
    }

    public boolean isMagma() {
        return this.getItem().is(Items.MAGMA_BLOCK);
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        super.onHitEntity(hit);
        if (!(this.level() instanceof ServerLevel level)) return;
        var target = hit.getEntity();
        if (target.hurtServer(level, this.damageSources().mobProjectile(this, this.thrower()), this.isMagma() ? MAGMA_DIRECT : DIRECT)) {
            this.shove(target, 0.9, 0.35);
            if (this.isMagma()) target.igniteForSeconds(4.0F);
        }
    }

    @Override
    protected void onHit(HitResult hit) {
        if (this.level() instanceof ServerLevel level) {
            // the splash: everything within a block and a half of the impact, except what was hit directly
            var direct = hit instanceof EntityHitResult e ? e.getEntity() : null;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(1.5),
                    e -> e != direct && this.canHitEntity(e) && e.isAlive())) {
                if (e.hurtServer(level, this.damageSources().mobProjectile(this, this.thrower()), SPLASH) && this.isMagma()) {
                    e.igniteForSeconds(3.0F);
                }
            }
            level.playSound(null, this.getX(), this.getY(), this.getZ(),
                    this.isMagma() ? SoundEvents.LAVA_EXTINGUISH : SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 1.2F, 0.7F);
        }
        super.onHit(hit);
    }
}
