package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.BreathAirGoal;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.AmphibiousPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.util.LandRandomPos;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.fish.AbstractFish;
import net.minecraft.world.entity.animal.fish.Cod;
import net.minecraft.world.entity.animal.fish.Salmon;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.throwableitemprojectile.Snowball;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A plump harbour seal. Slow and humping on land, fast in the water, where it hunts cod and salmon
 * and can stay under for three minutes; it likes to haul out and lounge on the rocks and ice by the
 * shore. Throw a snowball at it and it catches it on its nose, balances it, claps and flips one back.
 */
public class Seal extends Animal {
    private static final EntityDataAccessor<Boolean> BALANCING = SynchedEntityData.defineId(Seal.class, EntityDataSerializers.BOOLEAN);
    /** How long it balances a caught snowball (ticks). */
    static final int BALANCE_TIME = 60;
    private int balanceTicks;
    private @Nullable LivingEntity playmate;

    public Seal(EntityType<? extends Seal> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
        // full 3D steering in water (travelInWater sets the swim speed), plain and slow on land
        this.moveControl = new SmoothSwimmingMoveControl<>(this, 85, 10, 1.0F, 1.0F, false);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.14)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    /** Hauled out on the shore: stone, gravel, sand, snow or ice underneath, in daylight. */
    public static boolean checkSpawnRules(EntityType<Seal> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        boolean shore = below.is(BlockTags.BASE_STONE_OVERWORLD) || below.is(Blocks.GRAVEL) || below.is(BlockTags.SAND)
                || below.is(BlockTags.SNOW) || below.is(BlockTags.ICE);
        return shore && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new AmphibiousPathNavigation(this, level);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(BALANCING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new BalanceGoal());
        this.goalSelector.addGoal(1, new BreathAirGoal(this));
        this.goalSelector.addGoal(2, new PanicGoal(this, 1.5));
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, Seal::fish, false));
        this.goalSelector.addGoal(5, new MeleeAttackGoal(this, 1.4, true));
        this.goalSelector.addGoal(6, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(7, new ShoreGoal());
        this.goalSelector.addGoal(8, new LoungeGoal());
        this.goalSelector.addGoal(9, new RandomSwimmingGoal(this, 1.0, 40));
        this.goalSelector.addGoal(10, new LandStrollGoal());
        this.goalSelector.addGoal(11, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(12, new RandomLookAroundGoal(this));
        // grown seals hunt the cod and salmon they swim among
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, AbstractFish.class, 80, true, false,
                (t, l) -> (t instanceof Cod || t instanceof Salmon) && t.isInWater() && !this.isBaby() && !this.isBalancing()));
    }

    static boolean fish(ItemStack stack) {
        return stack.is(Items.COD) || stack.is(Items.SALMON);
    }

    /** Balancing a snowball on its nose. */
    public boolean isBalancing() {
        return this.entityData.get(BALANCING);
    }

    /**
     * Catches a snowball on its nose and balances it for about 3 s, then claps and flips a snowball
     * back at the thrower (a harmless one). Ignored while it's already balancing one.
     */
    public void catchSnowball(@Nullable Entity thrower) {
        if (this.level().isClientSide() || this.isBalancing()) return;
        this.balanceTicks = BALANCE_TIME;
        this.playmate = thrower instanceof LivingEntity living && !(thrower instanceof Seal) ? living : null;
        this.entityData.set(BALANCING, true);
        this.getNavigation().stop();
        this.setTarget(null);
        this.playSound(SoundEvents.SNOW_HIT, 0.8F, 1.5F);
    }

    /** A snowball doesn't hurt a seal: it catches it (but ignores the ones seals flip about). */
    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (source.getDirectEntity() instanceof Snowball snowball) {
            if (!(snowball.getOwner() instanceof Seal)) this.catchSnowball(snowball.getOwner());
            return false;
        }
        return super.hurtServer(level, source, damage);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || this.balanceTicks <= 0) return;
        // the balancing act runs here, not in a goal, so it also plays out with NoAI
        this.getNavigation().stop();
        int left = --this.balanceTicks;
        if (left == 16 || left == 10 || left == 4) this.playSound(SoundEvents.SLIME_SQUISH_SMALL, 0.7F, 1.8F);   // clap
        if (left == 0) {
            this.entityData.set(BALANCING, false);
            this.flipSnowball(level);
            this.playSound(SoundEvents.POLAR_BEAR_AMBIENT_BABY, 0.6F, 1.5F);
            this.playmate = null;
        }
    }

    /** Flips a snowball back at the player who threw one, or tosses it straight up for fun. */
    private void flipSnowball(ServerLevel level) {
        ItemStack stack = new ItemStack(Items.SNOWBALL);
        Snowball ball = new Snowball(level, this, stack);
        LivingEntity at = this.playmate;
        if (at instanceof Player && at.isAlive() && at.level() == level && this.distanceToSqr(at) < 24 * 24) {
            double dx = at.getX() - this.getX(), dz = at.getZ() - this.getZ();
            double dy = at.getEyeY() - 1.1;
            double lift = Math.sqrt(dx * dx + dz * dz) * 0.2;
            Projectile.spawnProjectile(ball, level, stack, p -> p.shoot(dx, dy + lift - p.getY(), dz, 1.3F, 4.0F));
        } else {
            Projectile.spawnProjectile(ball, level, stack, p -> p.shoot(0, 1, 0, 0.5F, 3.0F));
        }
        this.playSound(SoundEvents.SNOWBALL_THROW, 0.6F, 0.5F + this.random.nextFloat() * 0.2F);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && !target.isAlive()) {
            this.heal(2.0F);
            this.playSound(SoundEvents.DOLPHIN_EAT, 0.7F, 0.8F);
        }
        return hit;
    }

    /**
     * In water it steers in 3D with no gravity, cruising at about 1.25 x its movement speed in blocks
     * a tick (3.5 blocks a second, against barely one on land); idle, it drifts up until its head is out.
     */
    @Override
    protected void travelInWater(Vec3 input, double baseGravity, boolean isFalling, double oldY) {
        this.moveRelative(0.125F, input);
        this.move(MoverType.SELF, this.getDeltaMovement());
        this.setDeltaMovement(this.getDeltaMovement().scale(0.9));
        if (this.getNavigation().isDone() && this.getTarget() == null && this.isUnderWater()) {
            this.setDeltaMovement(this.getDeltaMovement().add(0.0, 0.006, 0.0));
        }
    }

    /** Holds its breath for three minutes. */
    @Override public int getMaxAirSupply() { return 3600; }
    @Override public boolean isPushedByFluid() { return false; }
    @Override public boolean isFood(ItemStack stack) { return fish(stack); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.SEAL.create(level, EntitySpawnReason.BREEDING);
    }

    @Override protected SoundEvent getAmbientSound() { return this.isInWater() ? null : SoundEvents.POLAR_BEAR_AMBIENT_BABY; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.POLAR_BEAR_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.POLAR_BEAR_DEATH; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.6F : 1.25F) + this.random.nextFloat() * 0.15F; }
    @Override protected float getSoundVolume() { return 0.6F; }
    @Override public int getAmbientSoundInterval() { return 240; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.SLIME_SQUISH_SMALL, 0.15F, 0.7F); }

    /** Holds still (facing its playmate) while it balances the snowball. */
    final class BalanceGoal extends Goal {
        BalanceGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override public boolean canUse() { return Seal.this.isBalancing(); }

        @Override
        public void tick() {
            Seal.this.getNavigation().stop();
            if (Seal.this.playmate != null) Seal.this.getLookControl().setLookAt(Seal.this.playmate, 30.0F, 30.0F);
        }
    }

    /** Now and then it hauls out onto the shore, or slips back into the water. */
    final class ShoreGoal extends Goal {
        ShoreGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            Seal seal = Seal.this;
            if (seal.getTarget() != null || seal.random.nextInt(this.reducedTickDelay(seal.isInWater() ? 300 : 900)) != 0) return false;
            Vec3 to = seal.isInWater() ? LandRandomPos.getPos(seal, 12, 4) : this.water();
            if (to == null) return false;
            return seal.getNavigation().moveTo(to.x, to.y, to.z, 1.0);
        }

        @Override public boolean canContinueToUse() { return !Seal.this.getNavigation().isDone(); }

        private @Nullable Vec3 water() {
            Level level = Seal.this.level();
            BlockPos origin = Seal.this.blockPosition();
            for (int i = 0; i < 32; i++) {
                BlockPos p = origin.offset(Seal.this.random.nextInt(21) - 10, Seal.this.random.nextInt(7) - 4, Seal.this.random.nextInt(21) - 10);
                if (level.getFluidState(p).is(FluidTags.WATER) && level.getFluidState(p.below()).is(FluidTags.WATER)) {
                    return Vec3.atBottomCenterOf(p);
                }
            }
            return null;
        }
    }

    /** On land it often just lies there for a while, lounging on the rocks or ice. */
    final class LoungeGoal extends Goal {
        private int ticks;

        LoungeGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            Seal seal = Seal.this;
            return !seal.isInWater() && seal.onGround() && seal.getTarget() == null
                    && seal.random.nextInt(this.reducedTickDelay(160)) == 0;
        }

        @Override
        public boolean canContinueToUse() {
            return this.ticks > 0 && !Seal.this.isInWater() && Seal.this.getTarget() == null;
        }

        @Override
        public void start() {
            this.ticks = 400 + Seal.this.random.nextInt(1000);
            Seal.this.getNavigation().stop();
        }

        @Override public void tick() { this.ticks--; }
    }

    /** Wanders on land only (in water it swims about instead). */
    final class LandStrollGoal extends RandomStrollGoal {
        LandStrollGoal() {
            super(Seal.this, 1.0, 160);
        }

        @Override
        public boolean canUse() {
            return !Seal.this.isInWater() && super.canUse();
        }
    }
}
