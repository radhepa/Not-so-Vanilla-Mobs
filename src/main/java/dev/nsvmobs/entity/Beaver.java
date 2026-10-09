package dev.nsvmobs.entity;

import java.util.EnumSet;
import java.util.Optional;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.BlockTransformer;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
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
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.BlockTransformers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A river beaver. Every couple of minutes it finds a log and gnaws it: wood chips fly, a few sticks
 * drop and (with mobGriefing on) the log is left stripped, never destroyed. A sprinting player or
 * anything that hurts it gets a loud tail slap, and every beaver around flees from them for a while.
 * Swims well and holds its breath for two minutes.
 */
public class Beaver extends Animal {
    private static final EntityDataAccessor<Boolean> SLAPPING = SynchedEntityData.defineId(Beaver.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> GNAWING = SynchedEntityData.defineId(Beaver.class, EntityDataSerializers.BOOLEAN);
    static final int GNAW_INTERVAL = 2400;
    private int gnawTime;
    private int gnawTicks;
    private @Nullable BlockPos gnawPos;
    private int slapTicks;
    private int slapCooldown;
    private int fleeTicks;
    private @Nullable LivingEntity fleeFrom;

    public Beaver(EntityType<? extends Beaver> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
        this.gnawTime = 1200 + this.random.nextInt(GNAW_INTERVAL);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25);
    }

    /** River banks: grass, dirt, podzol, sand or gravel, in daylight. */
    public static boolean checkSpawnRules(EntityType<Beaver> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return (below.is(BlockTags.ANIMALS_SPAWNABLE_ON) || below.is(BlockTags.DIRT) || below.is(BlockTags.SAND) || below.is(Blocks.GRAVEL))
                && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SLAPPING, false);
        builder.define(GNAWING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new FleeGoal());
        this.goalSelector.addGoal(2, new PanicGoal(this, 1.5));
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, s -> s.is(Items.STICK), false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(6, new GnawGoal());
        this.goalSelector.addGoal(7, new RandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
    }

    /** Mid tail slap. */
    public boolean isSlapping() {
        return this.entityData.get(SLAPPING);
    }

    /** Chewing on a log. */
    public boolean isGnawing() {
        return this.entityData.get(GNAWING);
    }

    /** A log right beside it: same level or one up, the side it faces first. */
    private @Nullable BlockPos adjacentLog(ServerLevel level) {
        BlockPos at = this.blockPosition();
        for (Direction d : Direction.orderedByNearest(this)) {
            if (!d.getAxis().isHorizontal()) continue;
            for (int dy = 0; dy <= 1; dy++) {
                BlockPos p = at.relative(d).above(dy);
                if (level.getBlockState(p).is(BlockTags.LOGS)) return p;
            }
        }
        return null;
    }

    /** What an axe would turn this log into (its stripped form), or null. */
    private static @Nullable BlockState stripped(ServerLevel level, BlockPos pos, BlockState log) {
        Optional<BlockTransformer> axe = level.registryAccess().lookupOrThrow(Registries.BLOCK_TRANSFORMER).getOptional(BlockTransformers.AXE);
        if (axe.isEmpty()) return null;
        for (BlockTransformer.BlockTransformData t : axe.get().transforms()) {
            BlockState s = t.blockStateProvider().value().getOptionalState(level, level.getRandom(), pos);
            if (s != null && s.is(BlockTags.LOGS) && !s.is(log.getBlock())) return s;
        }
        return null;
    }

    /**
     * Gnaws a log within 1 block (beside it, at its level or one up): chewing sound, wood chips, 1-3
     * sticks, and the log is stripped when mobGriefing allows it. Returns false if there's no log.
     */
    public boolean gnawNearbyLog(ServerLevel level) {
        BlockPos log = this.adjacentLog(level);
        if (log == null) return false;
        BlockState state = level.getBlockState(log);
        this.gnawPos = log;
        this.gnawTicks = 40;
        this.gnawTime = GNAW_INTERVAL + this.random.nextInt(1200);
        this.entityData.set(GNAWING, true);
        this.getNavigation().stop();
        this.spawnAtLocation(level, new ItemStack(Items.STICK, 1 + this.random.nextInt(3)));
        if (Griefing.allowed(level)) {
            BlockState bare = stripped(level, log, state);
            if (bare != null) {
                level.setBlock(log, bare, Block.UPDATE_ALL);
                level.gameEvent(GameEvent.BLOCK_CHANGE, log, GameEvent.Context.of(this, bare));
                level.playSound(null, log, SoundEvents.AXE_STRIP.value(), SoundSource.BLOCKS, 0.8F, 1.3F);
            }
        }
        this.chips(level);
        return true;
    }

    /** Wood chips flying off the face of the log it's chewing, and the crunch of it. */
    private void chips(ServerLevel level) {
        if (this.gnawPos == null) return;
        BlockState s = level.getBlockState(this.gnawPos);
        if (s.isAir()) return;
        Vec3 c = Vec3.atCenterOf(this.gnawPos);
        Vec3 out = new Vec3(this.getX() - c.x, 0.0, this.getZ() - c.z);
        out = out.lengthSqr() > 1.0E-4 ? out.normalize().scale(0.55) : Vec3.ZERO;
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, s), c.x + out.x, Math.min(c.y, this.getY() + 0.4), c.z + out.z,
                5, 0.12, 0.12, 0.12, 0.08);
        this.playSound(this.gnawTicks % 8 == 0 ? s.getSoundType().getHitSound() : SoundEvents.GENERIC_EAT.value(), 0.5F, 1.3F + this.random.nextFloat() * 0.3F);
    }

    /** A loud tail slap: every beaver within 16 blocks (this one too) flees from {@code threat} for 10 s. */
    void slap(ServerLevel level, LivingEntity threat) {
        if (this.slapTicks == 0) {
            this.slapTicks = 12;
            this.entityData.set(SLAPPING, true);
            this.playSound(SoundEvents.GENERIC_SPLASH, this.isInWater() ? 1.6F : 1.0F, 0.75F + this.random.nextFloat() * 0.15F);
            double bx = Mth.sin(this.yBodyRot * Mth.DEG_TO_RAD), bz = -Mth.cos(this.yBodyRot * Mth.DEG_TO_RAD);
            level.sendParticles(this.isInWater() ? ParticleTypes.SPLASH : ParticleTypes.POOF,
                    this.getX() + bx * 0.7, this.getY() + 0.15, this.getZ() + bz * 0.7, this.isInWater() ? 24 : 4, 0.3, 0.1, 0.3, 0.05);
        }
        this.slapCooldown = 100;
        for (Beaver b : level.getEntitiesOfClass(Beaver.class, this.getBoundingBox().inflate(16.0), LivingEntity::isAlive)) {
            b.fleeFrom = threat;
            b.fleeTicks = 200;
            b.gnawTicks = 0;
            b.entityData.set(GNAWING, false);
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        if (this.gnawTicks > 0) {
            this.getNavigation().stop();
            if (this.gnawPos != null) this.getLookControl().setLookAt(Vec3.atCenterOf(this.gnawPos));
            if (this.gnawTicks % 4 == 0) this.chips(level);
            if (--this.gnawTicks == 0) {
                this.entityData.set(GNAWING, false);
                this.gnawPos = null;
            }
        } else if (this.gnawTime > 0) {
            this.gnawTime--;
        } else if (this.tickCount % 20 == 0 && !this.isBaby() && this.fleeTicks == 0) {
            this.gnawNearbyLog(level);   // time to gnaw, if there's a log right here
        }
        if (this.slapTicks > 0 && --this.slapTicks == 0) this.entityData.set(SLAPPING, false);
        if (this.slapCooldown > 0) this.slapCooldown--;
        if (this.fleeTicks > 0 && --this.fleeTicks == 0) this.fleeFrom = null;
        if (this.slapCooldown == 0 && this.tickCount % 10 == 0) {
            Player p = level.getNearestPlayer(this.getX(), this.getY(), this.getZ(), 8.0,
                    e -> EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(e) && e.isSprinting());
            if (p != null) this.slap(level, p);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive() && source.getEntity() instanceof LivingEntity attacker && !(attacker instanceof Beaver)) {
            this.slap(level, attacker);
        }
        return hurt;
    }

    /** Swims well and holds its breath a long time. */
    @Override protected float getWaterSlowDown() { return 0.9F; }
    @Override public int getMaxAirSupply() { return 2400; }
    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.STICK); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.BEAVER.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("GnawTime", this.gnawTime);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.gnawTime = input.getIntOr("GnawTime", this.gnawTime);
    }

    @Override protected SoundEvent getAmbientSound() { return this.isGnawing() ? null : SoundEvents.FOX_SNIFF; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.RABBIT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.RABBIT_DEATH; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.5F : 0.95F) + this.random.nextFloat() * 0.15F; }
    @Override protected float getSoundVolume() { return 0.6F; }
    @Override public int getAmbientSoundInterval() { return 200; }

    /** Runs from whoever set off the alarm, for water if there's some close by on the far side. */
    final class FleeGoal extends Goal {
        FleeGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            Beaver b = Beaver.this;
            return b.fleeTicks > 0 && b.fleeFrom != null && b.fleeFrom.isAlive() && b.distanceToSqr(b.fleeFrom) < 16.0 * 16.0;
        }

        @Override public boolean canContinueToUse() { return this.canUse(); }

        @Override
        public void start() {
            Beaver b = Beaver.this;
            if (b.fleeFrom == null || b.isInWater()) return;
            BlockPos water = this.waterAway(b.fleeFrom);
            if (water != null) b.getNavigation().moveTo(water.getX() + 0.5, water.getY(), water.getZ() + 0.5, 1.5);
        }

        /** The nearest water within 8 blocks that's farther from the threat than the beaver is. */
        private @Nullable BlockPos waterAway(LivingEntity threat) {
            Beaver b = Beaver.this;
            BlockPos at = b.blockPosition();
            double mine = b.distanceToSqr(threat);
            BlockPos best = null;
            double bestDist = Double.MAX_VALUE;
            for (BlockPos p : BlockPos.betweenClosed(at.offset(-8, -2, -8), at.offset(8, 1, 8))) {
                if (!b.level().getFluidState(p).is(FluidTags.WATER)) continue;
                if (threat.distanceToSqr(Vec3.atCenterOf(p)) <= mine) continue;
                double d = p.distSqr(at);
                if (d < bestDist) {
                    bestDist = d;
                    best = p.immutable();
                }
            }
            return best;
        }

        @Override
        public void tick() {
            Beaver b = Beaver.this;
            if (b.fleeFrom != null && b.getNavigation().isDone()) {
                Vec3 to = DefaultRandomPos.getPosAway(b, 16, 7, b.fleeFrom.position());
                if (to != null) b.getNavigation().moveTo(to.x, to.y, to.z, b.distanceToSqr(b.fleeFrom) < 7.0 * 7.0 ? 1.5 : 1.25);
            }
        }

        @Override
        public void stop() {
            Beaver.this.getNavigation().stop();
        }
    }

    /** When it's ready to gnaw, it goes to a log nearby (within 8 blocks) and gets chewing. */
    final class GnawGoal extends Goal {
        private @Nullable BlockPos log;
        private int ticks;

        GnawGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            Beaver b = Beaver.this;
            if (b.isBaby() || b.gnawTime > 0 || b.gnawTicks > 0 || b.fleeTicks > 0 || b.isInWater() || !b.onGround()) return false;
            if (b.random.nextInt(reducedTickDelay(20)) != 0) return false;
            this.log = this.findLog();
            if (this.log == null) b.gnawTime = 600;   // none about: look again in half a minute
            return this.log != null;
        }

        /** The nearest log at its own level (or one up) within 8 blocks. */
        private @Nullable BlockPos findLog() {
            Beaver b = Beaver.this;
            BlockPos at = b.blockPosition();
            BlockPos best = null;
            double bestDist = Double.MAX_VALUE;
            for (BlockPos p : BlockPos.betweenClosed(at.offset(-8, 0, -8), at.offset(8, 1, 8))) {
                if (!b.level().getBlockState(p).is(BlockTags.LOGS)) continue;
                double d = p.distSqr(at);
                if (d < bestDist) {
                    bestDist = d;
                    best = p.immutable();
                }
            }
            return best;
        }

        @Override
        public void start() {
            this.ticks = 0;
            this.walk();
        }

        private void walk() {
            if (this.log != null) {
                Beaver.this.getNavigation().moveTo(this.log.getX() + 0.5, this.log.getY(), this.log.getZ() + 0.5, 1, 1.0);
            }
        }

        @Override
        public boolean canContinueToUse() {
            Beaver b = Beaver.this;
            return this.log != null && this.ticks < 200 && b.gnawTime <= 0 && b.gnawTicks == 0 && b.fleeTicks == 0
                    && b.level().getBlockState(this.log).is(BlockTags.LOGS);
        }

        @Override
        public void tick() {
            Beaver b = Beaver.this;
            this.ticks++;
            if (this.log == null) return;
            b.getLookControl().setLookAt(Vec3.atCenterOf(this.log));
            if (b.distanceToSqr(Vec3.atBottomCenterOf(this.log)) < 2.0 * 2.0 && b.level() instanceof ServerLevel level && b.gnawNearbyLog(level)) {
                return;
            }
            if (this.ticks % 20 == 0) this.walk();
        }

        @Override
        public void stop() {
            Beaver b = Beaver.this;
            if (b.gnawTime <= 0) b.gnawTime = 600;   // couldn't get to it: try again later
            this.log = null;
            b.getNavigation().stop();
        }
    }
}
