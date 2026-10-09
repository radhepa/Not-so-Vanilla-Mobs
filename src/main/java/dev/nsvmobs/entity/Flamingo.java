package dev.nsvmobs.entity;

import java.util.EnumSet;
import java.util.List;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A flamingo of the mangroves, swamps and beaches. It wades into shallow water, rests on one leg
 * when it stands about, and startles easily: hurt one, or sprint up to the flock, and they all
 * flap up and flutter off to land softly a little way away. Now and then a flock of three or more
 * puts on a display, marching together with their heads flagging from side to side.
 */
public class Flamingo extends Animal {
    private static final EntityDataAccessor<Boolean> RESTING = SynchedEntityData.defineId(Flamingo.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> FLUTTERING = SynchedEntityData.defineId(Flamingo.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> DANCING = SynchedEntityData.defineId(Flamingo.class, EntityDataSerializers.BOOLEAN);
    /** Fastest it sinks while fluttering down (blocks per tick). */
    private static final double FLUTTER_FALL = -0.12;
    private int idleTicks;
    private int flutterTicks;
    private int startleCooldown;
    private int danceTicks;
    private int nextDisplay;
    private Vec3 flutterDir = Vec3.ZERO;
    private @Nullable Vec3 marchTo;

    public Flamingo(EntityType<? extends Flamingo> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
        this.nextDisplay = 1200 + this.random.nextInt(2400);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22);
    }

    /** Mud, mangrove roots, grass, sand or dirt, in daylight. */
    public static boolean checkSpawnRules(EntityType<Flamingo> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        boolean ground = below.is(Blocks.MUD) || below.is(Blocks.MANGROVE_ROOTS) || below.is(Blocks.MUDDY_MANGROVE_ROOTS)
                || below.is(BlockTags.ANIMALS_SPAWNABLE_ON) || below.is(BlockTags.SAND) || below.is(BlockTags.DIRT);
        return ground && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(RESTING, false);
        builder.define(FLUTTERING, false);
        builder.define(DANCING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.5) {
            @Override public boolean canUse() { return !Flamingo.this.isFluttering() && super.canUse(); }
        });
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.1, this::isFood, false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new MarchGoal());
        this.goalSelector.addGoal(6, new RandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    /** Standing idle on one leg. */
    public boolean isResting() {
        return this.entityData.get(RESTING);
    }

    /** Flapping off after a scare. */
    public boolean isFluttering() {
        return this.entityData.get(FLUTTERING);
    }

    /** Marching in the flock display. */
    public boolean isDancing() {
        return this.entityData.get(DANCING);
    }

    /** Long legs: it wades belly-deep before it starts to float. */
    @Override public double getFluidJumpThreshold() { return 0.6; }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || !this.isAlive()) return;
        if (this.startleCooldown > 0) this.startleCooldown--;

        if (this.isFluttering()) {
            this.flutterTicks++;
            Vec3 v = this.getDeltaMovement();
            if (this.flutterTicks < 10) {
                // wingbeats: keep driving up and away for the first half second
                v = v.add(this.flutterDir.x * 0.04, this.flutterTicks < 6 ? 0.03 : 0.0, this.flutterDir.z * 0.04);
            }
            if (v.y < FLUTTER_FALL) v = new Vec3(v.x, FLUTTER_FALL, v.z);   // then it floats down softly
            this.setDeltaMovement(v);
            this.resetFallDistance();
            this.getNavigation().stop();
            float yaw = (float) (Mth.atan2(this.flutterDir.z, this.flutterDir.x) * Mth.RAD_TO_DEG) - 90.0F;
            this.setYRot(yaw);
            this.setYBodyRot(yaw);
            if (this.flutterTicks > 5 && (this.onGround() || this.isInWater()) || this.flutterTicks > 120) {
                this.entityData.set(FLUTTERING, false);
            }
        } else if (!this.isBaby() && this.startleCooldown <= 0 && this.tickCount % 5 == 0) {
            // sprinting up to the flock sends it flapping off
            Player runner = level.getNearestPlayer(this.getX(), this.getY(), this.getZ(), 6.0,
                    e -> e.isSprinting() && !e.isSpectator());
            if (runner != null) this.startle(level, runner.position(), false);
        }

        if (this.isDancing() && --this.danceTicks <= 0) {
            this.entityData.set(DANCING, false);
            this.marchTo = null;
        }
        if (!this.isBaby() && !this.isDancing() && --this.nextDisplay <= 0) {
            this.nextDisplay = 2400 + this.random.nextInt(3600);
            this.tryDisplay(level);
        }

        boolean idle = this.onGround() && !this.isInWater() && !this.isFluttering() && !this.isDancing()
                && this.getNavigation().isDone() && this.getDeltaMovement().horizontalDistanceSqr() < 0.0004;
        this.idleTicks = idle ? this.idleTicks + 1 : 0;
        boolean resting = this.idleTicks > 60;
        if (resting != this.isResting()) this.entityData.set(RESTING, resting);
    }

    /** It and every flamingo within 8 blocks flap up and away from {@code from}. */
    public void startle(ServerLevel level, Vec3 from) {
        this.startle(level, from, true);
    }

    /** A sprinter only startles birds that have settled since their last flight; a hurt one startles all. */
    private void startle(ServerLevel level, Vec3 from, boolean hurt) {
        List<Flamingo> flock = level.getEntitiesOfClass(Flamingo.class, this.getBoundingBox().inflate(8.0),
                f -> f.isAlive() && !f.isFluttering() && !f.isBaby() && (hurt || f.startleCooldown <= 0));
        for (Flamingo f : flock) f.takeOff(from);
    }

    private void takeOff(Vec3 from) {
        Vec3 away = new Vec3(this.getX() - from.x, 0, this.getZ() - from.z);
        double angle = away.lengthSqr() < 1.0E-4 ? this.random.nextDouble() * Math.PI * 2 : Math.atan2(away.z, away.x);
        angle += (this.random.nextDouble() - 0.5) * 0.8;
        this.flutterDir = new Vec3(Math.cos(angle), 0, Math.sin(angle));
        double speed = 0.45 + this.random.nextDouble() * 0.15;
        this.setDeltaMovement(this.flutterDir.x * speed, 0.55, this.flutterDir.z * speed);
        float yaw = (float) (angle * Mth.RAD_TO_DEG) - 90.0F;
        this.setYRot(yaw);
        this.setYBodyRot(yaw);
        this.setYHeadRot(yaw);
        this.getNavigation().stop();
        this.flutterTicks = 0;
        this.startleCooldown = 100;
        this.idleTicks = 0;
        this.entityData.set(FLUTTERING, true);
        this.entityData.set(RESTING, false);
        this.entityData.set(DANCING, false);
        this.marchTo = null;
        this.playSound(SoundEvents.PARROT_FLY, 1.0F, 0.7F + this.random.nextFloat() * 0.2F);
    }

    /** With 3+ grown flamingos around, they all march off the same way for 5 s. */
    private void tryDisplay(ServerLevel level) {
        List<Flamingo> flock = level.getEntitiesOfClass(Flamingo.class, this.getBoundingBox().inflate(8.0),
                f -> f.isAlive() && !f.isBaby() && !f.isFluttering() && !f.isDancing() && !f.isInWater());
        if (flock.size() < 3) return;
        double angle = this.random.nextDouble() * Math.PI * 2;
        Vec3 step = new Vec3(Math.cos(angle) * 5.0, 0, Math.sin(angle) * 5.0);
        for (Flamingo f : flock) {
            f.marchTo = f.position().add(step);
            f.danceTicks = 100;
            f.nextDisplay = 2400 + f.random.nextInt(3600);
            f.idleTicks = 0;
            f.entityData.set(DANCING, true);
            f.entityData.set(RESTING, false);
        }
        this.playSound(SoundEvents.PARROT_AMBIENT, 1.0F, this.getVoicePitch());
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && this.isAlive()) {
            Entity attacker = source.getEntity();
            this.startle(level, attacker != null ? attacker.position() : this.position());
        }
        return hurt;
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.BEETROOT); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.FLAMINGO.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("NextDisplay", this.nextDisplay);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.nextDisplay = input.getIntOr("NextDisplay", this.nextDisplay);
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.PARROT_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.PARROT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PARROT_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.CHICKEN_STEP.value(), 0.15F, 0.8F); }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.5F : 0.8F) + this.random.nextFloat() * 0.1F; }

    /** The display march: straight on toward a point 5 blocks off, at a stately pace. */
    private class MarchGoal extends Goal {
        MarchGoal() {
            this.setFlags(EnumSet.of(Goal.Flag.MOVE));
        }

        @Override public boolean canUse() { return Flamingo.this.isDancing() && Flamingo.this.marchTo != null; }
        @Override public boolean canContinueToUse() { return this.canUse() && !Flamingo.this.getNavigation().isDone(); }

        @Override
        public void start() {
            Vec3 to = Flamingo.this.marchTo;
            if (to != null) Flamingo.this.getNavigation().moveTo(to.x, to.y, to.z, 0.8);
        }
    }
}
