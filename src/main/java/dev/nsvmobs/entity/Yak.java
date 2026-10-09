package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Shearable;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.cow.CowSoundVariant;
import net.minecraft.world.entity.animal.cow.CowSoundVariants;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * A huge, shaggy mountain yak. Shear its long coat for brown wool (it grows back) and milk it like a
 * cow. While it wears its coat, a player standing close to it never freezes, even in powder snow.
 */
public class Yak extends Animal implements Shearable {
    private static final EntityDataAccessor<Boolean> SHEARED = SynchedEntityData.defineId(Yak.class, EntityDataSerializers.BOOLEAN);
    static final double WARM_RANGE = 3.0;
    private int regrowTicks;

    public Yak(EntityType<? extends Yak> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.MOVEMENT_SPEED, 0.17)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.3);
    }

    /** Snow, stone and grass of the mountains (where goats spawn) or any animal ground, in daylight. */
    public static boolean checkSpawnRules(EntityType<Yak> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return (below.is(BlockTags.GOATS_SPAWNABLE_ON) || below.is(BlockTags.ANIMALS_SPAWNABLE_ON)) && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SHEARED, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.2, this::isFood, false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
    }

    public boolean isSheared() { return this.entityData.get(SHEARED); }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        if (this.isSheared() && --this.regrowTicks <= 0) {
            this.entityData.set(SHEARED, false);
        }
        // warm coat: players close by never start to freeze
        if (!this.isSheared()) {
            for (Player p : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(WARM_RANGE))) {
                p.setTicksFrozen(0);
            }
        }
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.is(Items.SHEARS)) {
            if (this.level() instanceof ServerLevel level && this.readyForShearing()) {
                this.shear(level, SoundSource.PLAYERS, stack);
                this.gameEvent(GameEvent.SHEAR, player);
                stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
                return InteractionResult.SUCCESS_SERVER;
            }
            return InteractionResult.CONSUME;
        }
        if (stack.is(Items.BUCKET) && !this.isBaby()) {
            player.playSound(SoundEvents.COW_MILK, 1.0F, 0.9F);
            player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, Items.MILK_BUCKET.getDefaultInstance()));
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    @Override
    public void shear(ServerLevel level, SoundSource source, ItemStack tool) {
        level.playSound(null, this, SoundEvents.SHEEP_SHEAR, source, 1.0F, 0.8F);
        this.entityData.set(SHEARED, true);
        this.regrowTicks = 6000 + this.random.nextInt(6000);
        int count = 2 + this.random.nextInt(3);
        for (int i = 0; i < count; i++) {
            ItemEntity wool = this.spawnAtLocation(level, new ItemStack(Items.WOOL.brown()), 1.0F);
            if (wool != null) {
                wool.setDeltaMovement(wool.getDeltaMovement().add((this.random.nextFloat() - this.random.nextFloat()) * 0.1F,
                        this.random.nextFloat() * 0.05F, (this.random.nextFloat() - this.random.nextFloat()) * 0.1F));
            }
        }
    }

    @Override
    public boolean readyForShearing() {
        return this.isAlive() && !this.isSheared() && !this.isBaby();
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.WHEAT); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.YAK.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Sheared", this.isSheared());
        output.putInt("RegrowTicks", this.regrowTicks);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(SHEARED, input.getBooleanOr("Sheared", false));
        this.regrowTicks = input.getIntOr("RegrowTicks", 0);
    }

    /** The deep "moody" cow voice, pitched down further. */
    private static CowSoundVariant voice() {
        return SoundEvents.COW_SOUNDS.get(CowSoundVariants.SoundSet.MOODY);
    }

    @Override protected SoundEvent getAmbientSound() { return voice().ambientSound().value(); }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return voice().hurtSound().value(); }
    @Override protected SoundEvent getDeathSound() { return voice().deathSound().value(); }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(voice().stepSound().value(), 0.2F, 0.8F); }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.2F : 0.7F) + this.random.nextFloat() * 0.1F; }
}
