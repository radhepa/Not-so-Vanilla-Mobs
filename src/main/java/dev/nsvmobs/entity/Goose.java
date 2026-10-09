package dev.nsvmobs.entity;

import java.util.EnumSet;
import java.util.List;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A Canada goose of the plains and rivers. Neutral but territorial: walk up to its goslings and it
 * hisses at you, neck low and wings out, then chases you off with pecks if you don't back away; hurt
 * one and the whole gaggle comes for you. A thief that picks up whatever lies near it and waddles
 * off with it in its bill. It swims and floats, and moults the odd feather.
 */
public class Goose extends Animal {
    private static final EntityDataAccessor<Boolean> HISSING = SynchedEntityData.defineId(Goose.class, EntityDataSerializers.BOOLEAN);
    /** How long it hisses before deciding whether to chase (2 s). */
    private static final int HISS_TIME = 40;
    private int moultTime;
    private int hissTicks;
    private int stealCooldown;
    private @Nullable Player hissAt;

    public Goose(EntityType<? extends Goose> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
        this.setCanPickUpLoot(true);
        this.moultTime = 6000 + this.random.nextInt(6000);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.ATTACK_DAMAGE, 1.5)
                .add(Attributes.FOLLOW_RANGE, 8.0);   // the gaggle it alerts, and how far it chases
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(HISSING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6) {
            @Override public boolean canUse() { return Goose.this.isBaby() && super.canUse(); }
        });
        this.goalSelector.addGoal(1, new HissGoal());
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.35, true) {
            @Override public boolean canUse() { return !Goose.this.isBaby() && super.canUse(); }
        });
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, this::isFood, false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.1));
        // off it goes with its loot, keeping out of reach
        this.goalSelector.addGoal(6, new AvoidEntityGoal<>(this, Player.class, 6.0F, 1.0, 1.25,
                p -> this.isCarrying() && this.getTarget() == null && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(p)));
        this.goalSelector.addGoal(7, new StealGoal());
        this.goalSelector.addGoal(8, new RandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(9, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(10, new RandomLookAroundGoal(this));
        // hurt one and the whole gaggle has a go at you
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData groupData) {
        // gaggles often come with goslings
        return super.finalizeSpawn(level, difficulty, reason, groupData == null ? new AgeableMobGroupData(0.25F) : groupData);
    }

    /** Hissing at someone, or chasing them off: neck low, wings out. */
    public boolean isHissing() {
        return this.entityData.get(HISSING);
    }

    /** Whatever it's carrying in its bill. */
    public boolean isCarrying() {
        return !this.getMainHandItem().isEmpty();
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        if (target != null && this.isBaby()) return;   // goslings only ever run
        if (target != null && this.getTarget() == null) this.playSound(SoundEvents.CAT_HISS_BABY.value(), 1.0F, 0.55F);
        if (target != null) this.dropCarried();   // never pecks with a stolen sword
        super.setTarget(target);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || !this.isAlive()) return;
        if (this.stealCooldown > 0) this.stealCooldown--;
        if (!this.isBaby() && --this.moultTime <= 0) {
            this.moultTime = 6000 + this.random.nextInt(6000);
            this.playSound(SoundEvents.PARROT_FLY, 0.6F, 0.8F);
            this.spawnAtLocation(level, Items.FEATHER);
        }

        LivingEntity target = this.getTarget();
        if (target != null) {
            // it gives up once you're 8 blocks away
            if (!target.isAlive() || this.distanceToSqr(target) > 8 * 8 || !EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(target)) {
                this.setTarget(null);
            }
            this.hissTicks = 0;
            this.hissAt = null;
        } else if (this.hissTicks > 0) {
            Player p = this.hissAt;
            if (p == null || !p.isAlive() || !EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(p)) {
                this.hissTicks = 0;
                this.hissAt = null;
            } else if (--this.hissTicks == 0) {
                // still within 3 blocks after the warning: chase them off
                if (this.distanceToSqr(p) <= 3 * 3) this.setTarget(p);
                this.hissAt = null;
            }
        } else if (!this.isBaby() && this.tickCount % 10 == 0) {
            Player intruder = this.intruder(level);
            if (intruder != null) this.hiss(intruder);
        }
        boolean hissing = this.hissTicks > 0 || this.getTarget() != null;
        if (hissing != this.isHissing()) this.entityData.set(HISSING, hissing);
    }

    /** A survival player within 4 blocks of one of the goslings near this goose. */
    private @Nullable Player intruder(ServerLevel level) {
        List<Goose> goslings = level.getEntitiesOfClass(Goose.class, this.getBoundingBox().inflate(12.0), Goose::isBaby);
        for (Goose g : goslings) {
            Player p = level.getNearestPlayer(g.getX(), g.getY(), g.getZ(), 4.0, EntitySelector.NO_CREATIVE_OR_SPECTATOR);
            if (p != null) return p;
        }
        return null;
    }

    private void hiss(Player p) {
        this.hissAt = p;
        this.hissTicks = HISS_TIME;
        this.getNavigation().stop();
        this.playSound(SoundEvents.CAT_HISS_BABY.value(), 1.0F, 0.6F + this.random.nextFloat() * 0.1F);
    }

    // -- the thief ---------------------------------------------------------------------------------
    @Override
    public boolean wantsToPickUp(ServerLevel level, ItemStack stack) {
        return !this.isBaby() && !this.isCarrying() && this.stealCooldown <= 0 && this.getTarget() == null && !stack.isEmpty()
                && !stack.has(DataComponents.DEATH_PROTECTION);   // a goose with a totem would be unkillable once
    }

    @Override
    protected void pickUpItem(ServerLevel level, ItemEntity entity) {
        ItemStack stack = entity.getItem();
        this.onItemPickup(entity);
        this.setItemSlot(EquipmentSlot.MAINHAND, stack.copyWithCount(1));
        this.setGuaranteedDrop(EquipmentSlot.MAINHAND);
        this.take(entity, 1);
        if (stack.getCount() <= 1) entity.discard();
        else entity.setItem(stack.copyWithCount(stack.getCount() - 1));
        this.playSound(SoundEvents.PARROT_AMBIENT, 0.8F, 0.75F);
    }

    /** Lets go of whatever it carries, and leaves loose items alone for a while. */
    public void dropCarried() {
        ItemStack stack = this.getMainHandItem();
        if (stack.isEmpty() || this.level().isClientSide()) return;
        Vec3 look = this.getLookAngle();
        ItemEntity item = new ItemEntity(this.level(), this.getX() + look.x * 0.5, this.getY() + 0.6, this.getZ() + look.z * 0.5, stack);
        item.setPickUpDelay(20);
        item.setThrower(this);
        this.level().addFreshEntity(item);
        this.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        this.stealCooldown = 400;
        this.playSound(SoundEvents.FOX_SPIT, 0.7F, 0.8F);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt) this.dropCarried();
        return hurt;
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (this.isFood(player.getItemInHand(hand)) && this.isCarrying()) this.dropCarried();
        return super.mobInteract(player, hand);
    }

    @Override
    protected void dropAllDeathLoot(ServerLevel level, DamageSource source) {
        ItemStack carried = this.getMainHandItem();
        if (!carried.isEmpty()) {
            this.spawnAtLocation(level, carried);
            this.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        }
        super.dropAllDeathLoot(level, source);
    }

    // -- breeding, swimming, sounds ----------------------------------------------------------------
    @Override protected float getWaterSlowDown() { return 0.9F; }
    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.WHEAT); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.GOOSE.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("MoultTime", this.moultTime);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.moultTime = input.getIntOr("MoultTime", this.moultTime);
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.PARROT_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.PARROT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PARROT_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.CHICKEN_STEP.value(), 0.15F, 0.9F); }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.4F : 0.55F) + this.random.nextFloat() * 0.1F; }

    /** Stands its ground, staring the intruder down, while it hisses. */
    private class HissGoal extends Goal {
        HissGoal() {
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
        }

        @Override public boolean canUse() { return Goose.this.hissTicks > 0 && Goose.this.hissAt != null; }
        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            Goose.this.getNavigation().stop();
            if (Goose.this.hissAt != null) Goose.this.getLookControl().setLookAt(Goose.this.hissAt, 30.0F, 30.0F);
        }
    }

    /** Waddles over to an item lying nearby to pick it up (the pick-up itself is vanilla's, mobGriefing-gated). */
    private class StealGoal extends Goal {
        private @Nullable ItemEntity loot;

        StealGoal() {
            this.setFlags(EnumSet.of(Goal.Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            Goose g = Goose.this;
            if (g.isBaby() || g.isCarrying() || g.stealCooldown > 0 || g.getTarget() != null || g.getRandom().nextInt(reducedTickDelay(20)) != 0) return false;
            if (!(g.level() instanceof ServerLevel level) || !Griefing.allowed(level)) return false;
            List<ItemEntity> items = level.getEntitiesOfClass(ItemEntity.class, g.getBoundingBox().inflate(6.0, 2.0, 6.0),
                    e -> e.isAlive() && !e.hasPickUpDelay() && !e.getItem().isEmpty());
            if (items.isEmpty()) return false;
            this.loot = items.get(0);
            return true;
        }

        @Override
        public boolean canContinueToUse() {
            return this.loot != null && this.loot.isAlive() && !Goose.this.isCarrying() && Goose.this.getTarget() == null
                    && !Goose.this.getNavigation().isDone();
        }

        @Override
        public void start() {
            if (this.loot != null) Goose.this.getNavigation().moveTo(this.loot, 1.15);
        }

        @Override
        public void stop() {
            this.loot = null;
        }
    }
}
