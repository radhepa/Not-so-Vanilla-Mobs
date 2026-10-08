package dev.nsvmobs.entity;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.hurtingprojectile.SmallFireball;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;

/** A wyrmling's ember: burns what it hits, but never sets blocks alight and never hits friends. */
public class WyrmlingEmber extends SmallFireball {
    public WyrmlingEmber(EntityType<? extends WyrmlingEmber> type, Level level) {
        super(type, level);
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        // no fire on blocks
    }

    @Override
    protected boolean canHitEntity(Entity target) {
        Entity owner = this.getOwner();
        if (target instanceof Player || target instanceof AbstractVillager) return false;
        if (owner instanceof OwnableEntity pet && target instanceof OwnableEntity other && other.getOwner() == pet.getOwner()) return false;
        return super.canHitEntity(target);
    }
}
