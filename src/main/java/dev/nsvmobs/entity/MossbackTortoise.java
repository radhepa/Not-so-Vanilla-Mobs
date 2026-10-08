package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Shearable;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * A big, slow tortoise with a garden on its shell. Shear the garden for moss; it grows back.
 * When hurt it pulls into its shell for a few seconds.
 */
public class MossbackTortoise extends Animal implements Shearable {
    private static final EntityDataAccessor<Boolean> SHEARED = SynchedEntityData.defineId(MossbackTortoise.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> HIDING = SynchedEntityData.defineId(MossbackTortoise.class, EntityDataSerializers.INT);
    private static final int HIDE_TICKS = 100;
    private int regrowTicks;

    public MossbackTortoise(EntityType<? extends MossbackTortoise> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.MOVEMENT_SPEED, 0.12)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SHEARED, false);
        builder.define(HIDING, 0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.2, s -> s.is(Items.MELON_SLICE), false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
    }

    public boolean isSheared() { return this.entityData.get(SHEARED); }
    public boolean isHiding() { return this.entityData.get(HIDING) > 0; }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level().isClientSide()) return;
        int hiding = this.entityData.get(HIDING);
        if (hiding > 0) {
            this.entityData.set(HIDING, hiding - 1);
            this.getNavigation().stop();
            this.setDeltaMovement(this.getDeltaMovement().multiply(0, 1, 0));
        }
        if (this.isSheared() && --this.regrowTicks <= 0) {
            this.entityData.set(SHEARED, false);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (this.isHiding()) damage *= 0.3F;
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive()) {
            if (!this.isHiding()) this.playSound(SoundEvents.ARMADILLO_ROLL, 1.0F, 0.7F);
            this.entityData.set(HIDING, HIDE_TICKS);
        }
        return hurt;
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
        return super.mobInteract(player, hand);
    }

    @Override
    public void shear(ServerLevel level, SoundSource source, ItemStack tool) {
        level.playSound(null, this, SoundEvents.SHEEP_SHEAR, source, 1.0F, 0.8F);
        this.entityData.set(SHEARED, true);
        this.regrowTicks = 4800 + this.random.nextInt(2400);
        this.spawnAtLocation(level, new ItemStack(Items.MOSS_BLOCK, 1 + this.random.nextInt(2)), 1.0F);
        if (this.random.nextInt(3) == 0) {
            ItemStack flower = new ItemStack(switch (this.random.nextInt(4)) {
                case 0 -> Items.DANDELION;
                case 1 -> Items.AZURE_BLUET;
                case 2 -> Items.OXEYE_DAISY;
                default -> Items.CORNFLOWER;
            });
            this.spawnAtLocation(level, flower, 1.0F);
        }
    }

    @Override
    public boolean readyForShearing() {
        return this.isAlive() && !this.isSheared() && !this.isBaby();
    }

    @Override public float getAgeScale() { return this.isBaby() ? 0.4F : 1.0F; }
    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.MELON_SLICE); }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.MOSSBACK_TORTOISE.create(level, net.minecraft.world.entity.EntitySpawnReason.BREEDING);
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

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.TURTLE_AMBIENT_LAND; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.TURTLE_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.TURTLE_DEATH; }
    @Override public float getVoicePitch() { return 0.7F + this.random.nextFloat() * 0.1F; }
    @Override protected void playStepSound(net.minecraft.core.BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
        this.playSound(SoundEvents.TURTLE_SHAMBLE, 0.2F, 0.7F);
    }
}
