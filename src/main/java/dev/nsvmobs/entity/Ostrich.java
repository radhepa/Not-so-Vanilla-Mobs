package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.equine.AbstractHorse;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * An ostrich of the savannas: tamed and ridden like a horse (mount it until it stops throwing you,
 * feed it to calm it sooner, then saddle it). The fastest mount on flat ground but a poor jumper,
 * and with a rider it spreads its wings and glides down from any drop, so neither of you takes fall
 * damage. Eats what horses eat; breeds with golden carrots or golden apples.
 */
public class Ostrich extends AbstractHorse {
    private static final EntityDataAccessor<Boolean> GLIDING = SynchedEntityData.defineId(Ostrich.class, EntityDataSerializers.BOOLEAN);
    /** Speeds and jumps (attribute values) ostriches are born with: every one outruns the best horse (0.3375). */
    private static final double MIN_SPEED = 0.34, MAX_SPEED = 0.40;
    /** A jump strength of 0.46-0.50 clears about 1.5 blocks. */
    private static final double MIN_JUMP = 0.46, MAX_JUMP = 0.50;
    /** Fastest it sinks with a rider aboard, wings spread (blocks per tick). */
    private static final double GLIDE_FALL = -0.15;
    private int airTicks;

    public Ostrich(EntityType<? extends Ostrich> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return AbstractHorse.createBaseHorseAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.MOVEMENT_SPEED, 0.36)
                .add(Attributes.JUMP_STRENGTH, 0.48);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(GLIDING, false);
    }

    @Override
    protected void randomizeAttributes(RandomSource random) {
        this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(22.0);
        this.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(MIN_SPEED + random.nextDouble() * (MAX_SPEED - MIN_SPEED));
        this.getAttribute(Attributes.JUMP_STRENGTH).setBaseValue(MIN_JUMP + random.nextDouble() * (MAX_JUMP - MIN_JUMP));
    }

    /** In the air with a rider: wings spread, sinking slowly. */
    public boolean isGliding() {
        return this.entityData.get(GLIDING);
    }

    private boolean airborneWithRider() {
        return this.isVehicle() && !this.onGround() && !this.isInWater() && !this.isInLava();
    }

    @Override
    public void tick() {
        super.tick();
        if (this.airborneWithRider()) {
            // nobody takes fall damage on an ostrich's wings
            this.resetFallDistance();
            for (Entity rider : this.getPassengers()) rider.resetFallDistance();
        }
        if (this.level() instanceof ServerLevel) {
            this.airTicks = this.airborneWithRider() ? this.airTicks + 1 : 0;
            boolean gliding = this.airTicks > 3;
            if (gliding != this.isGliding()) this.entityData.set(GLIDING, gliding);
            if (gliding && this.airTicks % 8 == 0) this.playSound(SoundEvents.PARROT_FLY, 0.7F, 0.6F);
        }
    }

    /** Runs wherever its movement is simulated (the rider's client while ridden): cap the fall. */
    @Override
    public void travel(Vec3 input) {
        super.travel(input);
        if (this.airborneWithRider()) {
            Vec3 v = this.getDeltaMovement();
            if (v.y < GLIDE_FALL) this.setDeltaMovement(v.x, GLIDE_FALL, v.z);
        }
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        if (this.isVehicle()) return false;   // it glided down: no damage for it or its rider
        return super.causeFallDamage(fallDistance, damageModifier, damageSource);
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        boolean openInventory = !this.isBaby() && this.isTamed() && player.isSecondaryUseActive();
        if (!this.isVehicle() && !openInventory && (!this.isBaby() || !player.isHolding(Items.GOLDEN_DANDELION))) {
            ItemStack stack = player.getItemInHand(hand);
            if (!stack.isEmpty()) {
                if (this.isFood(stack)) return this.fedFood(player, stack);
                if (!this.isTamed()) {
                    this.makeMad();
                    return InteractionResult.SUCCESS;
                }
            }
        }
        return super.mobInteract(player, hand);
    }

    /** Ostriches don't rear like horses (and have no eating-grass animation to stand still for). */
    @Override protected boolean canPerformRearing() { return false; }
    @Override public boolean canEatGrass() { return false; }

    /** A saddle, but no horse armour. */
    @Override
    public boolean canUseSlot(EquipmentSlot slot) {
        return slot != EquipmentSlot.BODY && super.canUseSlot(slot);
    }

    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public boolean canMate(Animal partner) {
        return partner != this && partner instanceof Ostrich other && this.canParent() && other.canParent();
    }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Ostrich baby = NsvEntities.OSTRICH.create(level, EntitySpawnReason.BREEDING);
        if (baby != null) {
            // like a horse foal, but within the ostrich's own (faster, lower-jumping) ranges
            baby.getAttribute(Attributes.MAX_HEALTH).setBaseValue(22.0);
            baby.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(createOffspringAttribute(
                    this.getAttributeBaseValue(Attributes.MOVEMENT_SPEED), partner.getAttributeBaseValue(Attributes.MOVEMENT_SPEED),
                    MIN_SPEED, MAX_SPEED, this.random));
            baby.getAttribute(Attributes.JUMP_STRENGTH).setBaseValue(createOffspringAttribute(
                    this.getAttributeBaseValue(Attributes.JUMP_STRENGTH), partner.getAttributeBaseValue(Attributes.JUMP_STRENGTH),
                    MIN_JUMP, MAX_JUMP, this.random));
        }
        return baby;
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.CAMEL_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.CAMEL_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.CAMEL_DEATH; }
    @Override protected @Nullable SoundEvent getEatingSound() { return SoundEvents.CAMEL_EAT; }
    /** It hisses when it throws you off. */
    @Override protected @Nullable SoundEvent getAngrySound() { return SoundEvents.CAT_HISS_BABY.value(); }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.CAMEL_STEP, 0.4F, 1.3F); }
    @Override protected void playJumpSound() { this.playSound(SoundEvents.PARROT_FLY, 0.5F, 0.7F); }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.8F : 1.2F) + this.random.nextFloat() * 0.1F; }
}
