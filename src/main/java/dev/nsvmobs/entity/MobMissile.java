package dev.nsvmobs.entity;

import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemStackTemplate;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;

/**
 * Something a monster throws (a boulder, an ice shard, a web glob). Drawn as its item. It never hits
 * its thrower or the thrower's own kind, and it breaks apart on whatever it hits.
 */
public abstract class MobMissile extends ThrowableItemProjectile {
    protected MobMissile(EntityType<? extends MobMissile> type, Level level) {
        super(type, level);
    }

    protected MobMissile(EntityType<? extends MobMissile> type, LivingEntity thrower, ItemStack item) {
        super(type, thrower, thrower.level(), item);
    }

    /**
     * Launch at a target, aiming high enough that gravity brings it down on them (ballistic lead for
     * this missile's own gravity; a little inaccuracy).
     */
    public void aimAt(Entity target, float speed, float inaccuracy) {
        double dx = target.getX() - this.getX();
        double dz = target.getZ() - this.getZ();
        double dy = target.getY(0.4) - this.getY();
        double flat = Math.sqrt(dx * dx + dz * dz);
        double lift = this.getGravity() * flat * flat / (2.0 * speed * speed) * 1.15;
        this.shoot(dx, dy + lift, dz, speed, inaccuracy);
    }

    @Override
    protected boolean canHitEntity(Entity target) {
        Entity owner = this.getOwner();
        if (owner != null && (target == owner || target.getType() == owner.getType())) return false;
        return super.canHitEntity(target);
    }

    @Override
    protected void onHit(HitResult hit) {
        super.onHit(hit);
        if (this.level() instanceof ServerLevel level) {
            level.sendParticles(new ItemParticleOption(ParticleTypes.ITEM, ItemStackTemplate.fromNonEmptyStack(this.getItem())),
                    this.getX(), this.getY(), this.getZ(), 12, 0.2, 0.2, 0.2, 0.08);
            this.discard();
        }
    }

    /** The thrower, if it's a living thing (for damage sources). */
    protected LivingEntity thrower() {
        return this.getOwner() instanceof LivingEntity l ? l : null;
    }

    /** Shove something away along this missile's flight (and up a little), so players feel it too. */
    protected void shove(Entity e, double strength, double up) {
        double vx = this.getDeltaMovement().x, vz = this.getDeltaMovement().z;
        double len = Math.max(1.0E-4, Math.sqrt(vx * vx + vz * vz));
        e.push(vx / len * strength, up, vz / len * strength);
        e.needsSync = true;
    }
}
