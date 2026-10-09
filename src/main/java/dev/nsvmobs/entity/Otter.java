package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
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
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.fish.AbstractFish;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * A river otter. Tame it with raw cod or salmon. It swims like a fish, floats on its back when it
 * has nothing to do, gives its owner Dolphin's Grace while they swim together, and every few minutes
 * dives and comes back up with a fish (or something odder) for you.
 */
public class Otter extends TamableAnimal {
    private static final EntityDataAccessor<Boolean> FLOATING = SynchedEntityData.defineId(Otter.class, EntityDataSerializers.BOOLEAN);
    private int fishTime;

    public Otter(EntityType<? extends Otter> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
        this.fishTime = 3600 + this.random.nextInt(3600);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return TamableAnimal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.ATTACK_DAMAGE, 2.0);
    }

    /** River banks: grass, sand, gravel or dirt, in daylight. */
    public static boolean checkSpawnRules(EntityType<Otter> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return (below.is(BlockTags.ANIMALS_SPAWNABLE_ON) || below.is(BlockTags.SAND) || below.is(Blocks.GRAVEL) || below.is(BlockTags.DIRT))
                && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(FLOATING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.3, true));
        this.goalSelector.addGoal(4, new FollowOwnerGoal(this, 1.0, 8.0F, 2.0F));
        this.goalSelector.addGoal(5, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(6, new TemptGoal(this, 1.1, Otter::fish, false));
        this.goalSelector.addGoal(7, new RandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
        // it hunts the fish it swims among (never when told to sit)
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, AbstractFish.class, 60, true, false,
                (t, l) -> !this.isOrderedToSit() && t.isInWater()));
    }

    static boolean fish(ItemStack stack) {
        return stack.is(Items.COD) || stack.is(Items.SALMON);
    }

    /** Lying on its back at the surface, paws up. */
    public boolean isFloating() {
        return this.entityData.get(FLOATING);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        boolean idle = this.isInWater() && this.getTarget() == null && this.getNavigation().isDone()
                && this.getDeltaMovement().horizontalDistanceSqr() < 0.002;
        if (idle != this.isFloating()) this.entityData.set(FLOATING, idle);

        LivingEntity owner = this.getOwner();
        if (owner != null && this.isInWater() && owner.isInWater() && this.distanceToSqr(owner) < 8 * 8 && this.tickCount % 20 == 0) {
            owner.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 60, 0, true, true), this);
        }
        if (this.isTame() && !this.isOrderedToSit() && !this.isBaby() && this.isInWater() && --this.fishTime <= 0) {
            this.fishTime = 3600 + this.random.nextInt(3600);
            this.playSound(SoundEvents.FISHING_BOBBER_SPLASH, 0.8F, 1.3F);
            this.spawnAtLocation(level, new ItemStack(catchSomething(this.random)));
        }
    }

    /** What an otter brings back up: mostly fish. */
    static Item catchSomething(RandomSource r) {
        int roll = r.nextInt(100);
        if (roll < 45) return Items.COD;
        if (roll < 80) return Items.SALMON;
        if (roll < 88) return Items.INK_SAC;
        if (roll < 94) return Items.KELP;
        if (roll < 99) return Items.LILY_PAD;
        return Items.NAUTILUS_SHELL;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, net.minecraft.world.entity.Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && !target.isAlive()) {
            this.heal(2.0F);
            this.playSound(SoundEvents.FOX_EAT, 0.7F, 1.4F);
        }
        return hit;
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && fish(stack)) {
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
            if (fish(stack) && this.getHealth() < this.getMaxHealth()) {
                this.usePlayerItem(player, hand, stack);
                this.heal(4.0F);
                this.playSound(SoundEvents.FOX_EAT, 0.6F, 1.4F);
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

    /** Swims fast and holds its breath a long time. */
    @Override protected float getWaterSlowDown() { return 0.94F; }
    @Override public int getMaxAirSupply() { return 2400; }
    @Override public boolean isFood(ItemStack stack) { return fish(stack); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Otter baby = NsvEntities.OTTER.create(level, EntitySpawnReason.BREEDING);
        if (baby != null && this.getOwnerReference() != null) {
            baby.setOwnerReference(this.getOwnerReference());
            baby.setTame(true, true);
        }
        return baby;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("FishTime", this.fishTime);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.fishTime = input.getIntOr("FishTime", this.fishTime);
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.FOX_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.FOX_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.FOX_DEATH; }
    @Override public float getVoicePitch() { return 1.5F + this.random.nextFloat() * 0.2F; }
    @Override protected float getSoundVolume() { return 0.6F; }
}
