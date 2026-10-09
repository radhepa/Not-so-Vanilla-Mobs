package dev.nsvmobs.entity;

import java.util.EnumSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;

/**
 * A masked raccoon. Wild ones snatch food lying on the ground and make off with it. Tame one with a
 * snack and it turns pack rat: it gathers up the items lying around and drops them at your feet, one
 * stack at a time. Not a fighter, it keeps clear of monsters, and food it finds near water gets a
 * good wash in its little hands first.
 */
public class Raccoon extends TamableAnimal {
    private static final EntityDataAccessor<Integer> WASHING = SynchedEntityData.defineId(Raccoon.class, EntityDataSerializers.INT);
    static final double GATHER_RANGE = 10.0;
    /** Items it gave up on (couldn't reach), until the given tick. */
    private final Map<UUID, Integer> ignored = new HashMap<>();
    private int holdTicks;
    private int snatchTicks;

    public Raccoon(EntityType<? extends Raccoon> type, Level level) {
        super(type, level);
        this.setCanPickUpLoot(true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return TamableAnimal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3);
    }

    /** The forest floor (grass, podzol, snow), at any light level: raccoons are out at night too. */
    public static boolean checkSpawnRules(EntityType<Raccoon> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return below.is(BlockTags.WOLVES_SPAWNABLE_ON) || below.is(BlockTags.ANIMALS_SPAWNABLE_ON);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(WASHING, 0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new WashGoal());
        this.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(3, new AvoidEntityGoal<>(this, Monster.class, 8.0F, 1.1, 1.4));
        this.goalSelector.addGoal(4, new PanicGoal(this, 1.5));
        // a wild one makes off with what it stole
        this.goalSelector.addGoal(5, new AvoidEntityGoal<>(this, Player.class, 10.0F, 1.2, 1.5,
                p -> this.snatchTicks > 0 && !this.isTame()));
        this.goalSelector.addGoal(6, new DeliverGoal());
        this.goalSelector.addGoal(7, new GatherGoal());
        this.goalSelector.addGoal(8, new FollowOwnerGoal(this, 1.0, 8.0F, 2.0F));
        this.goalSelector.addGoal(9, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(10, new TemptGoal(this, 1.1, Raccoon::snack, false));
        this.goalSelector.addGoal(11, new WaterAvoidingRandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(12, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(13, new RandomLookAroundGoal(this));
    }

    /** Snacks: tame, heal and breed with these. */
    static boolean snack(ItemStack stack) {
        return stack.is(Items.COOKIE) || stack.is(Items.APPLE) || stack.is(Items.BREAD)
                || stack.is(Items.SWEET_BERRIES) || stack.is(Items.GLOW_BERRIES);
    }

    static boolean edible(ItemStack stack) {
        return stack.has(DataComponents.FOOD);
    }

    /** Rubbing its food clean in its hands. */
    public boolean isWashing() {
        return this.entityData.get(WASHING) > 0;
    }

    /**
     * Whether it would take this item off the ground: wild ones only take food (and only when
     * mobGriefing is on); a tame one takes anything except what a player threw (its owner's own
     * throws, and what raccoons already delivered to someone) and what already lies at its owner's
     * feet. Never while sitting, never a totem, and only with empty hands.
     */
    boolean wants(ItemEntity e) {
        if (!e.isAlive() || e.hasPickUpDelay() || e.getItem().isEmpty() || !this.getMainHandItem().isEmpty()) return false;
        if (e.getItem().has(DataComponents.DEATH_PROTECTION)) return false;
        if (!this.isTame()) return edible(e.getItem()) && this.level() instanceof ServerLevel level && Griefing.allowed(level);
        if (this.isOrderedToSit()) return false;
        LivingEntity owner = this.getOwner();
        if (owner == null || owner.level() != this.level()) return false;
        if (e.getOwner() instanceof Player) return false;
        return e.distanceToSqr(owner) > 2.0 * 2.0;
    }

    /** The nearest item it wants within reach (tame: 10 blocks; wild: 8), or null. */
    @Nullable ItemEntity nearestWanted() {
        double range = this.isTame() ? GATHER_RANGE : 8.0;
        if (this.isTame()) {
            LivingEntity owner = this.getOwner();
            if (owner == null || this.distanceToSqr(owner) > 24 * 24) return null;
        }
        int now = this.tickCount;
        this.ignored.values().removeIf(until -> until < now);
        List<ItemEntity> items = this.level().getEntitiesOfClass(ItemEntity.class, this.getBoundingBox().inflate(range, 4.0, range),
                e -> this.wants(e) && !this.ignored.containsKey(e.getUUID()) && this.distanceToSqr(e) <= range * range);
        ItemEntity best = null;
        for (ItemEntity e : items) {
            if (best == null || this.distanceToSqr(e) < this.distanceToSqr(best)) best = e;
        }
        return best;
    }

    @Override
    public boolean wantsToPickUp(ServerLevel level, ItemStack stack) {
        return this.getMainHandItem().isEmpty() && (this.isTame() ? !this.isOrderedToSit() : edible(stack));
    }

    /** Vanilla's walk-over pickup goes through the same rules as the goals. */
    @Override
    protected void pickUpItem(ServerLevel level, ItemEntity entity) {
        if (this.wants(entity)) this.grab(level, entity);
    }

    /** Takes the item into its hands: the whole stack when tame (pack rat), a single bite when wild. */
    void grab(ServerLevel level, ItemEntity entity) {
        ItemStack stack = entity.getItem();
        int count = this.isTame() ? stack.getCount() : 1;
        this.onItemPickup(entity);
        ItemStack taken = stack.split(count);
        this.setItemSlot(EquipmentSlot.MAINHAND, taken);
        this.take(entity, count);
        if (stack.isEmpty()) entity.discard();
        else entity.setItem(stack.copy());
        this.holdTicks = 0;
        if (!this.isTame()) this.snatchTicks = 100;
        this.playSound(SoundEvents.FOX_SNIFF, 0.6F, 1.6F);
        if (edible(taken) && nearWater(level)) {
            this.entityData.set(WASHING, 50);
            this.getNavigation().stop();
        }
    }

    /** Water within 3 blocks. */
    private boolean nearWater(ServerLevel level) {
        BlockPos at = this.blockPosition();
        for (BlockPos p : BlockPos.betweenClosed(at.offset(-3, -3, -3), at.offset(3, 3, 3))) {
            if (level.getFluidState(p).is(FluidTags.WATER)) return true;
        }
        return false;
    }

    /** Drops what it carries at its owner's feet. It counts as theirs now, so it won't fetch it again. */
    void deliver(ServerLevel level, LivingEntity owner) {
        ItemStack held = this.getMainHandItem();
        if (held.isEmpty()) return;
        this.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        ItemEntity drop = new ItemEntity(level, owner.getX(), owner.getY() + 0.1, owner.getZ(), held, 0.0, 0.1, 0.0);
        drop.setPickUpDelay(20);
        drop.setThrower(owner);
        level.addFreshEntity(drop);
        this.playSound(SoundEvents.FOX_SPIT, 0.5F, 1.5F);
    }

    /** Roughly where its hands and mouth are, in the world. */
    private double mouthX() { return this.getX() - Mth.sin(this.yBodyRot * Mth.DEG_TO_RAD) * 0.45; }
    private double mouthZ() { return this.getZ() + Mth.cos(this.yBodyRot * Mth.DEG_TO_RAD) * 0.45; }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        int wash = this.entityData.get(WASHING);
        if (wash > 0) {
            this.entityData.set(WASHING, wash - 1);
            this.getNavigation().stop();
            if (wash % 10 == 0) {
                this.playSound(SoundEvents.GENERIC_SWIM, 0.25F, 1.8F);
                level.sendParticles(ParticleTypes.SPLASH, this.mouthX(), this.getY() + 0.3, this.mouthZ(), 4, 0.1, 0.05, 0.1, 0.0);
            }
        }
        if (this.snatchTicks > 0) this.snatchTicks--;
        // a wild raccoon eats what it stole once it has got away with it
        ItemStack held = this.getMainHandItem();
        if (!this.isTame() && edible(held)) {
            if (++this.holdTicks > 600 && wash == 0 && this.onGround()) {
                level.sendParticles(new ItemParticleOption(ParticleTypes.ITEM, held.getItem()), this.mouthX(), this.getY() + 0.35, this.mouthZ(),
                        8, 0.1, 0.1, 0.1, 0.05);
                this.playSound(SoundEvents.FOX_EAT, 0.8F, 1.3F);
                this.heal(2.0F);
                held.shrink(1);
                if (held.isEmpty()) this.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
                this.holdTicks = 0;
            }
        } else {
            this.holdTicks = 0;
        }
    }

    @Override
    protected void dropAllDeathLoot(ServerLevel level, DamageSource source) {
        ItemStack held = this.getMainHandItem();
        if (!held.isEmpty()) {
            this.spawnAtLocation(level, held);
            this.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        }
        super.dropAllDeathLoot(level, source);
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && snack(stack)) {
            this.usePlayerItem(player, hand, stack);
            if (!this.level().isClientSide()) {
                if (this.random.nextInt(3) == 0) {
                    this.tame(player);
                    this.navigation.stop();
                    this.setTarget(null);
                    this.setOrderedToSit(true);
                    this.snatchTicks = 0;
                    this.level().broadcastEntityEvent(this, (byte) 7);
                } else {
                    this.level().broadcastEntityEvent(this, (byte) 6);
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (this.isTame() && this.isOwnedBy(player)) {
            if (snack(stack) && this.getHealth() < this.getMaxHealth()) {
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

    @Override public boolean isFood(ItemStack stack) { return snack(stack); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Raccoon baby = NsvEntities.RACCOON.create(level, EntitySpawnReason.BREEDING);
        if (baby != null && this.getOwnerReference() != null) {
            baby.setOwnerReference(this.getOwnerReference());
            baby.setTame(true, true);
        }
        return baby;
    }

    @Override protected SoundEvent getAmbientSound() { return this.random.nextInt(3) == 0 ? SoundEvents.FOX_SNIFF : SoundEvents.FOX_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.FOX_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.FOX_DEATH; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.7F : 1.3F) + this.random.nextFloat() * 0.2F; }
    @Override protected float getSoundVolume() { return 0.6F; }

    /** Holds still while it washes its food. */
    final class WashGoal extends Goal {
        WashGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        @Override public boolean canUse() { return Raccoon.this.isWashing(); }
        @Override public void start() { Raccoon.this.getNavigation().stop(); }
    }

    /** Goes to the nearest item it wants and takes it (tame: anything; wild: food). */
    final class GatherGoal extends Goal {
        private @Nullable ItemEntity item;
        private int ticks;

        GatherGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            Raccoon r = Raccoon.this;
            if (!r.getMainHandItem().isEmpty() || r.isOrderedToSit() || r.getLastHurtByMob() != null) return false;
            if (r.random.nextInt(reducedTickDelay(10)) != 0) return false;
            this.item = r.nearestWanted();
            return this.item != null;
        }

        @Override
        public void start() {
            this.ticks = 0;
            Raccoon.this.getNavigation().moveTo(this.item, 1.2);
        }

        @Override
        public boolean canContinueToUse() {
            return this.item != null && this.ticks < 300 && Raccoon.this.wants(this.item);
        }

        @Override
        public void tick() {
            Raccoon r = Raccoon.this;
            this.ticks++;
            r.getLookControl().setLookAt(this.item, 30.0F, 30.0F);
            if (r.distanceToSqr(this.item) < 1.6 * 1.6 && r.level() instanceof ServerLevel level) {
                r.grab(level, this.item);
            } else if (this.ticks % 10 == 0) {
                r.getNavigation().moveTo(this.item, 1.2);
            }
        }

        @Override
        public void stop() {
            Raccoon r = Raccoon.this;
            // couldn't get to it: leave it be for half a minute
            if (this.item != null && this.ticks >= 300) r.ignored.put(this.item.getUUID(), r.tickCount + 600);
            this.item = null;
            r.getNavigation().stop();
        }
    }

    /** A tame raccoon carrying something takes it to its owner and drops it at their feet. */
    final class DeliverGoal extends Goal {
        private int ticks;

        DeliverGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        private @Nullable LivingEntity owner() {
            Raccoon r = Raccoon.this;
            if (!r.isTame() || r.isOrderedToSit() || r.isWashing() || r.getMainHandItem().isEmpty()) return null;
            LivingEntity owner = r.getOwner();
            return owner != null && owner.isAlive() && !owner.isSpectator() && owner.level() == r.level() ? owner : null;
        }

        @Override public boolean canUse() { return this.owner() != null; }
        @Override public boolean canContinueToUse() { return this.owner() != null; }

        @Override
        public void start() {
            this.ticks = 0;
        }

        @Override
        public void tick() {
            Raccoon r = Raccoon.this;
            LivingEntity owner = this.owner();
            if (owner == null) return;
            r.getLookControl().setLookAt(owner, 30.0F, 30.0F);
            if (r.distanceToSqr(owner) < 2.0 * 2.0 && r.level() instanceof ServerLevel level) {
                r.deliver(level, owner);
            } else if (this.ticks++ % 10 == 0) {
                if (r.shouldTryTeleportToOwner()) r.tryToTeleportToOwner();
                else r.getNavigation().moveTo(owner, 1.2);
            }
        }

        @Override
        public void stop() {
            Raccoon.this.getNavigation().stop();
        }
    }
}
