package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;
import dev.nsvmobs.NsvMobs;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.navigation.AmphibiousPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.polarbear.PolarBear;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import org.jspecify.annotations.Nullable;

/**
 * A penguin of the frozen shores. It waddles about in colonies, flops onto its belly to toboggan
 * fast over ice and snow, and is a quick swimmer. Keeps clear of polar bears. Breeds with fish.
 */
public class Penguin extends Animal {
    private static final EntityDataAccessor<Boolean> SLIDING = SynchedEntityData.defineId(Penguin.class, EntityDataSerializers.BOOLEAN);
    private static final Identifier SLIDE_SPEED = Identifier.fromNamespaceAndPath(NsvMobs.MOD_ID, "penguin_slide");
    private int slideTicks;

    public Penguin(EntityType<? extends Penguin> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2);
    }

    /** Snow, ice or sand (snowy beaches), in daylight. */
    public static boolean checkSpawnRules(EntityType<Penguin> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return (below.is(BlockTags.RABBITS_SPAWNABLE_ON) || below.is(BlockTags.ICE) || below.is(BlockTags.SNOW)) && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SLIDING, false);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new AmphibiousPathNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(2, new AvoidEntityGoal<>(this, PolarBear.class, 10.0F, 1.2, 1.6));
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.2, this::isFood, false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(6, new RandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    /** Belly-down: tobogganing over ice or snow, or swimming. */
    public boolean isSliding() {
        return this.entityData.get(SLIDING);
    }

    static boolean slippery(BlockState s) {
        return s.is(BlockTags.ICE) || s.is(BlockTags.SNOW) || s.is(net.minecraft.world.level.block.Blocks.SNOW);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        boolean moving = this.getDeltaMovement().horizontalDistanceSqr() > 0.0016 || !this.getNavigation().isDone();
        boolean onSlope = this.onGround() && (slippery(level.getBlockState(this.blockPosition().below())) || slippery(level.getBlockState(this.blockPosition())));
        if (onSlope && moving && !this.isBaby()) {
            this.slideTicks = Math.min(this.slideTicks + 1, 20);
        } else if (this.slideTicks > 0) {
            this.slideTicks--;
        }
        boolean slide = this.isInWater() || this.slideTicks > 8;
        if (slide != this.isSliding()) {
            this.entityData.set(SLIDING, slide);
            AttributeInstance speed = this.getAttribute(Attributes.MOVEMENT_SPEED);
            speed.removeModifier(SLIDE_SPEED);
            if (slide && !this.isInWater()) {
                speed.addTransientModifier(new AttributeModifier(SLIDE_SPEED, 0.8, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
                this.playSound(SoundEvents.POWDER_SNOW_STEP, 0.6F, 1.4F);
            }
        }
    }

    /** It cuts through water much faster than it walks. */
    @Override protected float getWaterSlowDown() { return 0.95F; }
    @Override public int getMaxAirSupply() { return 2400; }
    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.COD) || stack.is(Items.SALMON); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.PENGUIN.create(level, EntitySpawnReason.BREEDING);
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.PARROT_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.PARROT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PARROT_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.CHICKEN_STEP.value(), 0.15F, 0.8F); }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.3F : 0.65F) + this.random.nextFloat() * 0.1F; }
}
