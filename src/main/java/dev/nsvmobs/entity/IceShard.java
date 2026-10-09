package dev.nsvmobs.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/** A Rimewraith's ice shard: flies fast and nearly straight, stings, and chills (unless you wear leather). */
public class IceShard extends MobMissile {
    static final float DAMAGE = 4.0F;
    static final int CHILL = 60;

    public IceShard(EntityType<? extends IceShard> type, Level level) {
        super(type, level);
    }

    public IceShard(EntityType<? extends IceShard> type, LivingEntity thrower) {
        super(type, thrower, new ItemStack(Items.ICE));
    }

    @Override
    protected Item getDefaultItem() {
        return Items.ICE;
    }

    @Override
    protected double getDefaultGravity() {
        return 0.006;
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        super.onHitEntity(hit);
        if (!(this.level() instanceof ServerLevel level) || !(hit.getEntity() instanceof LivingEntity target)) return;
        if (target.hurtServer(level, this.damageSources().mobProjectile(this, this.thrower()), DAMAGE)) {
            Rimewraith.chill(target, CHILL);
            if (target.canFreeze()) target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60), this.getOwner());
        }
    }

    @Override
    protected void onHit(HitResult hit) {
        if (!this.level().isClientSide()) {
            this.level().playSound(null, this.getX(), this.getY(), this.getZ(), SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 0.6F, 1.6F);
        }
        super.onHit(hit);
    }
}
