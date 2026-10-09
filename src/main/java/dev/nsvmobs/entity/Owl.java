package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BiomeTags;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A round, fluffy owl: tawny in forests, snowy in snowy biomes. Wild owls perch by day and fly about
 * at night, silently. Tame one with raw rabbit or chicken; it flies after you, sits when told, rakes
 * monsters that hurt you (or that you attack) with its talons, and while it's near you in the dark
 * you have Night Vision.
 */
public class Owl extends TamableAnimal {
    /** Looks, in texture order: owl (tawny), owl_snowy. */
    public static final int VARIANTS = 2;
    private static final EntityDataAccessor<Integer> VARIANT = SynchedEntityData.defineId(Owl.class, EntityDataSerializers.INT);
    private int secondHoot;

    public Owl(EntityType<? extends Owl> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 10, false);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return TamableAnimal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 12.0)
                .add(Attributes.FLYING_SPEED, 0.5)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    /** Forest floors and snowy ground (grass, podzol, snow, leaves, logs); no light needed, so dark forests count. */
    public static boolean checkSpawnRules(EntityType<Owl> type, LevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return below.is(BlockTags.ANIMALS_SPAWNABLE_ON) || below.is(Blocks.PODZOL) || below.is(BlockTags.SNOW)
                || below.is(BlockTags.LEAVES) || below.is(BlockTags.LOGS) || below.is(Blocks.PALE_MOSS_BLOCK);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(VARIANT, 0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.4, true));
        this.goalSelector.addGoal(3, new FollowOwnerGoal(this, 1.0, 8.0F, 2.0F));
        this.goalSelector.addGoal(4, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(5, new TemptGoal(this, 1.1, Owl::meat, false));
        this.goalSelector.addGoal(6, new OwlWanderGoal(this));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new OwnerHurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new OwnerHurtTargetGoal(this));
    }

    static boolean meat(ItemStack stack) {
        return stack.is(Items.RABBIT) || stack.is(Items.CHICKEN);
    }

    public int variant() { return this.entityData.get(VARIANT); }
    private void setVariant(int v) { this.entityData.set(VARIANT, Math.floorMod(v, VARIANTS)); }

    /** In the air (it walks on the ground and perches on branches). */
    public boolean isFlying() { return !this.onGround(); }

    /** Snowy owls hatch in snowy biomes, tawny ones everywhere else. */
    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData data) {
        BlockPos pos = this.blockPosition();
        Holder<Biome> biome = level.getBiome(pos);
        boolean snowy = biome.is(BiomeTags.SPAWNS_SNOW_FOXES) || biome.value().coldEnoughToSnow(pos, level.getSeaLevel());
        this.setVariant(snowy ? 1 : 0);
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        // night eyes: keep the owner's Night Vision topped up while they're near in the dark. The
        // effect is long (400 ticks) and refreshed well before it runs low, so it never flickers.
        if (this.isTame() && this.tickCount % 10 == 0 && this.getOwner() instanceof LivingEntity owner
                && owner.isAlive() && owner.level() == level && this.distanceToSqr(owner) < 16 * 16 && isDark(level, owner)) {
            MobEffectInstance current = owner.getEffect(MobEffects.NIGHT_VISION);
            if (current == null || (current.getDuration() >= 0 && current.getDuration() < 300)) {
                owner.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 400, 0, true, false, true), this);
            }
        }
        if (this.secondHoot > 0 && --this.secondHoot == 0 && this.isAlive()) {
            this.playSound(SoundEvents.NOTE_BLOCK_FLUTE.value(), 0.5F, 0.56F);
        }
    }

    /** Night, or a dark spot (a cave, a dark forest floor, an unlit room) where the owner stands. */
    static boolean isDark(Level level, LivingEntity owner) {
        return level.isDarkOutside() || level.getMaxLocalRawBrightness(owner.blockPosition()) < 7;
    }

    /** Only ever fights monsters, whatever its owner swings at. */
    @Override
    public boolean wantsToAttack(LivingEntity target, LivingEntity owner) {
        return target instanceof Enemy && super.wantsToAttack(target, owner);
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && meat(stack)) {
            this.usePlayerItem(player, hand, stack);
            if (!this.level().isClientSide()) {
                if (this.random.nextInt(4) == 0) {
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
            if (meat(stack) && this.getHealth() < this.getMaxHealth()) {
                this.usePlayerItem(player, hand, stack);
                this.heal(4.0F);
                this.playSound(SoundEvents.PARROT_EAT, 0.6F, 0.8F);
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

    @Override public boolean isFood(ItemStack stack) { return meat(stack); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Owl baby = NsvEntities.OWL.create(level, EntitySpawnReason.BREEDING);
        if (baby != null) {
            baby.setVariant(partner instanceof Owl other && this.random.nextBoolean() ? other.variant() : this.variant());
            if (this.getOwnerReference() != null) {
                baby.setOwnerReference(this.getOwnerReference());
                baby.setTame(true, true);
            }
        }
        return baby;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Variant", this.variant());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.setVariant(input.getIntOr("Variant", 0));
    }

    @Override protected boolean canFlyToOwner() { return true; }
    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}

    // silent flight: no wing sounds and no flap vibrations (isFlapping stays false)

    /** A soft two-note hoot, mostly after dark. */
    @Override
    public void playAmbientSound() {
        if (this.level().isBrightOutside() && this.random.nextInt(4) != 0) return;
        this.playSound(SoundEvents.NOTE_BLOCK_FLUTE.value(), 0.5F, 0.62F);
        this.secondHoot = 7;
    }

    @Override public int getAmbientSoundInterval() { return 320; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.NOTE_BLOCK_FLUTE.value(); }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.PARROT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PARROT_DEATH; }
    @Override public float getVoicePitch() { return 0.6F + this.random.nextFloat() * 0.1F; }
    @Override protected float getSoundVolume() { return 0.6F; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.PARROT_STEP, 0.1F, 0.8F); }

    /**
     * Wandering: about at night; by day it mostly stays on its perch. When it does fly, it likes to
     * land on a branch (leaves or a log with room above), like a parrot.
     */
    static final class OwlWanderGoal extends WaterAvoidingRandomFlyingGoal {
        OwlWanderGoal(PathfinderMob mob) {
            super(mob, 1.0);
        }

        @Override
        public boolean canUse() {
            if (this.mob.level().isBrightOutside() && this.mob.getRandom().nextInt(6) != 0) return false;
            return super.canUse();
        }

        @Override
        protected @Nullable Vec3 getPosition() {
            if (this.mob.getRandom().nextFloat() < 0.6F) {
                Vec3 perch = this.perch();
                if (perch != null) return perch;
            }
            return super.getPosition();
        }

        private @Nullable Vec3 perch() {
            Level level = this.mob.level();
            BlockPos origin = this.mob.blockPosition();
            BlockPos.MutableBlockPos below = new BlockPos.MutableBlockPos();
            for (int i = 0; i < 24; i++) {
                BlockPos p = origin.offset(this.mob.getRandom().nextInt(13) - 6, this.mob.getRandom().nextInt(9) - 3,
                        this.mob.getRandom().nextInt(13) - 6);
                BlockState under = level.getBlockState(below.setWithOffset(p, 0, -1, 0));
                if ((under.getBlock() instanceof LeavesBlock || under.is(BlockTags.LOGS))
                        && level.isEmptyBlock(p) && level.isEmptyBlock(p.above())) {
                    return Vec3.atBottomCenterOf(p);
                }
            }
            return null;
        }
    }
}
