package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
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
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * A jungle chameleon. Its skin slowly takes on the colour of whatever it stands on. Tame it with
 * spider eyes; while its owner crouches beside it, the owner vanishes from sight as well.
 */
public class Chameleon extends TamableAnimal {
    private static final EntityDataAccessor<Integer> SKIN = SynchedEntityData.defineId(Chameleon.class, EntityDataSerializers.INT);
    /** Leaf green, until it has stood on something. */
    private static final int START = 0xFF000000 | MapColor.GRASS.col;
    // client: the colour the model is drawn in right now, easing toward the skin colour
    private float tintR, tintG, tintB;
    private boolean tintReady;

    public Chameleon(EntityType<? extends Chameleon> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return TamableAnimal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 8.0)
                .add(Attributes.MOVEMENT_SPEED, 0.16);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SKIN, START);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(3, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(4, new FollowOwnerGoal(this, 1.3, 6.0F, 2.0F));
        this.goalSelector.addGoal(5, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(6, new TemptGoal(this, 1.1, s -> s.is(Items.SPIDER_EYE), false));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
    }

    /** The colour its skin is turning to (ARGB): the map colour of the block it last stood on. */
    public int skinColour() {
        return this.entityData.get(SKIN);
    }

    /** Client side: the colour the model is tinted with right now (eases toward the skin colour). */
    public int tint() {
        if (!this.tintReady) return pale(this.skinColour());
        return 0xFF000000 | Math.round(this.tintR) << 16 | Math.round(this.tintG) << 8 | Math.round(this.tintB);
    }

    /** Mixed a quarter of the way to white, so the model never turns muddy. */
    private static int pale(int argb) {
        int r = argb >> 16 & 0xFF, g = argb >> 8 & 0xFF, b = argb & 0xFF;
        return 0xFF000000 | (r + (255 - r) / 4) << 16 | (g + (255 - g) / 4) << 8 | (b + (255 - b) / 4);
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide()) return;
        int target = pale(this.skinColour());
        float r = target >> 16 & 0xFF, g = target >> 8 & 0xFF, b = target & 0xFF;
        if (!this.tintReady) {
            this.tintR = r;
            this.tintG = g;
            this.tintB = b;
            this.tintReady = true;
            return;
        }
        // a slow blush: about three seconds to change colour
        this.tintR += (r - this.tintR) * 0.05F;
        this.tintG += (g - this.tintG) * 0.05F;
        this.tintB += (b - this.tintB) * 0.05F;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || this.tickCount % 5 != 0) return;
        BlockPos below = this.blockPosition().below();
        BlockState state = level.getBlockState(below);
        if (!state.isAir()) {
            MapColor colour = state.getMapColor(level, below);
            if (colour != MapColor.NONE) {
                int skin = 0xFF000000 | colour.col;
                if (skin != this.skinColour()) this.entityData.set(SKIN, skin);
            }
        }
        // shared camouflage: an owner crouching close by fades from sight too
        LivingEntity owner = this.getOwner();
        if (this.tickCount % 10 == 0 && owner != null && owner.isAlive() && (owner.isCrouching() || owner.isShiftKeyDown())
                && this.distanceToSqr(owner) < 3 * 3) {
            owner.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 40, 0, true, false), this);
        }
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && stack.is(Items.SPIDER_EYE)) {
            this.usePlayerItem(player, hand, stack);
            this.playSound(SoundEvents.FROG_EAT, 0.6F, 1.4F);
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
            if (stack.is(Items.SPIDER_EYE) && this.getHealth() < this.getMaxHealth()) {
                this.usePlayerItem(player, hand, stack);
                this.heal(4.0F);
                this.playSound(SoundEvents.FROG_EAT, 0.6F, 1.4F);
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

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.SPIDER_EYE); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Chameleon baby = NsvEntities.CHAMELEON.create(level, EntitySpawnReason.BREEDING);
        if (baby != null) {
            baby.entityData.set(SKIN, this.skinColour());
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
        output.putInt("SkinColour", this.skinColour());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(SKIN, input.getIntOr("SkinColour", START));
    }

    /** A quiet animal: no calls, just a frog-like croak when hurt. */
    @Override protected @Nullable SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.FROG_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.FROG_DEATH; }
    @Override public float getVoicePitch() { return 1.3F + this.random.nextFloat() * 0.15F; }
    @Override protected float getSoundVolume() { return 0.5F; }
}
