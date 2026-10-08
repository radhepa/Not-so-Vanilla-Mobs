package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.Endermite;
import net.minecraft.world.entity.monster.Silverfish;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * A palm-sized pet. Tame it with sweet berries. It curls into a spiky ball when hurt, hunts
 * silverfish and endermites, and forages berries while it follows you.
 */
public class Hedgehog extends TamableAnimal {
    private static final EntityDataAccessor<Integer> CURLED = SynchedEntityData.defineId(Hedgehog.class, EntityDataSerializers.INT);
    private int forageTime;

    public Hedgehog(EntityType<? extends Hedgehog> type, Level level) {
        super(type, level);
        this.forageTime = 4800 + this.random.nextInt(4800);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return TamableAnimal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.ATTACK_DAMAGE, 3.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(CURLED, 0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.2, true) {
            @Override public boolean canUse() { return !Hedgehog.this.isCurled() && super.canUse(); }
        });
        this.goalSelector.addGoal(4, new FollowOwnerGoal(this, 1.0, 8.0F, 2.0F));
        this.goalSelector.addGoal(5, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(6, new TemptGoal(this, 1.1, s -> s.is(Items.SWEET_BERRIES), false));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new OwnerHurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new OwnerHurtTargetGoal(this));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Silverfish.class, false));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Endermite.class, false));
    }

    public boolean isCurled() { return this.entityData.get(CURLED) > 0; }

    /** Helps only against monsters, whatever its owner swings at. */
    @Override
    public boolean wantsToAttack(LivingEntity target, LivingEntity owner) {
        return target instanceof Enemy && super.wantsToAttack(target, owner);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        int curled = this.entityData.get(CURLED);
        if (curled > 0) {
            this.entityData.set(CURLED, curled - 1);
            this.getNavigation().stop();
            this.setDeltaMovement(this.getDeltaMovement().multiply(0, 1, 0));
            if (curled == 1) this.playSound(SoundEvents.ARMADILLO_UNROLL_FINISH, 0.8F, 1.4F);
        }
        if (this.isTame() && !this.isOrderedToSit() && !this.isBaby() && --this.forageTime <= 0) {
            this.forageTime = 4800 + this.random.nextInt(4800);
            if (level.getBlockState(this.blockPosition().below()).is(Blocks.GRASS_BLOCK)) {
                this.playSound(SoundEvents.FOX_SNIFF, 1.0F, 1.5F);
                int roll = this.random.nextInt(10);
                this.spawnAtLocation(level, new ItemStack(roll < 7 ? Items.SWEET_BERRIES : roll < 9 ? Items.BROWN_MUSHROOM : Items.RED_MUSHROOM));
            }
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (this.isCurled()) damage *= 0.4F;
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive()) {
            if (!this.isCurled()) this.playSound(SoundEvents.ARMADILLO_ROLL, 0.8F, 1.5F);
            this.entityData.set(CURLED, 100);
            if (source.getDirectEntity() instanceof LivingEntity attacker && source.getEntity() == attacker && !(attacker instanceof Hedgehog)) {
                attacker.hurtServer(level, this.damageSources().thorns(this), 2.0F);
            }
        }
        return hurt;
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && stack.is(Items.SWEET_BERRIES)) {
            this.usePlayerItem(player, hand, stack);
            if (!this.level().isClientSide()) {
                if (this.random.nextInt(3) == 0) {
                    this.tame(player);
                    this.navigation.stop();
                    this.setTarget(null);
                    this.setOrderedToSit(true);
                    this.level().broadcastEntityEvent(this, (byte) 7);
                } else {
                    this.level().broadcastEntityEvent(this, (byte) 6);
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (this.isTame() && this.isOwnedBy(player)) {
            if (stack.is(Items.SWEET_BERRIES) && this.getHealth() < this.getMaxHealth()) {
                this.usePlayerItem(player, hand, stack);
                this.heal(4.0F);
                this.playSound(SoundEvents.FOX_EAT, 0.6F, 1.6F);
                return InteractionResult.SUCCESS;
            }
            InteractionResult result = super.mobInteract(player, hand);
            if (!result.consumesAction() && stack.isEmpty()) {
                this.setOrderedToSit(!this.isOrderedToSit());
                this.jumping = false;
                this.navigation.stop();
                this.setTarget(null);
                return InteractionResult.SUCCESS;
            }
            return result;
        }
        return super.mobInteract(player, hand);
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.SWEET_BERRIES); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Hedgehog baby = NsvEntities.HEDGEHOG.create(level, EntitySpawnReason.BREEDING);
        if (baby != null && this.getOwnerReference() != null) {
            baby.setOwnerReference(this.getOwnerReference());
            baby.setTame(true, true);
        }
        return baby;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("ForageTime", this.forageTime);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.forageTime = input.getIntOr("ForageTime", this.forageTime);
    }

    @Override protected SoundEvent getAmbientSound() { return this.isCurled() ? null : SoundEvents.FOX_SNIFF; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.RABBIT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.RABBIT_DEATH; }
    @Override public float getVoicePitch() { return 1.4F + this.random.nextFloat() * 0.2F; }
    @Override protected float getSoundVolume() { return 0.6F; }
}
