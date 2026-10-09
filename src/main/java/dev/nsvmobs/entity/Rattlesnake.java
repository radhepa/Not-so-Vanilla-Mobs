package dev.nsvmobs.entity;

import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;

/**
 * A rattlesnake of the badlands and dry savannas. It basks in the sun and leaves you be, but walk
 * up to it and it coils, rears its head and rattles a warning. Keep coming (or hurt it) and it
 * strikes with a venomous bite, and keeps at it until you're well away. It doesn't breed.
 */
public class Rattlesnake extends Animal {
    private static final EntityDataAccessor<Boolean> RATTLING = SynchedEntityData.defineId(Rattlesnake.class, EntityDataSerializers.BOOLEAN);
    /** Warning range, and how close a crouching player can creep before it notices. */
    private static final double WARN = 5.0, WARN_CROUCHING = 2.0;
    /** Closer than this while it rattles and it strikes; farther than LET_GO and it gives up. */
    private static final double STRIKE = 2.0, LET_GO = 8.0;
    private @Nullable Player warned;
    private int rattleTime;

    public Rattlesnake(EntityType<? extends Rattlesnake> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.FOLLOW_RANGE, LET_GO);
    }

    /** Sand, red sand, terracotta, grass or coarse dirt, in daylight. */
    public static boolean checkSpawnRules(EntityType<Rattlesnake> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return (below.is(BlockTags.SAND) || below.is(BlockTags.TERRACOTTA) || below.is(BlockTags.GLAZED_TERRACOTTA)
                || below.is(Blocks.GRASS_BLOCK) || below.is(Blocks.COARSE_DIRT)) && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(RATTLING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        // MeleeAttackGoal only runs with a target: given by a strike (aiStep) or by being hurt
        this.goalSelector.addGoal(1, new MeleeAttackGoal(this, 1.7, true));
        this.goalSelector.addGoal(2, new HoldGroundGoal());
        // mostly lies still in the sun, now and then moving on
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8) {
            { this.setInterval(240); }
        });
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    /** Coiled with its head up, rattling at a player who came too close. */
    public boolean isRattling() {
        return this.entityData.get(RATTLING);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        LivingEntity target = this.getTarget();
        if (target != null && (!target.isAlive() || this.distanceToSqr(target) > LET_GO * LET_GO)) {
            this.setTarget(null);           // you got away: it settles down again
            target = null;
        }
        Player intruder = target == null ? this.nearestIntruder(level) : null;
        if (intruder != this.warned) this.rattleTime = 0;
        this.warned = intruder;
        boolean rattling = intruder != null;
        if (rattling != this.isRattling()) this.entityData.set(RATTLING, rattling);
        if (!rattling) return;

        if (this.rattleTime++ % 8 == 0) {
            this.playSound(SoundEvents.SCULK_CLICKING, 0.9F, 1.8F + this.random.nextFloat() * 0.25F);
        }
        // still too close after a second of warning: strike
        if (this.rattleTime > 20 && this.distanceToSqr(intruder) < STRIKE * STRIKE) {
            this.setTarget(intruder);
            this.entityData.set(RATTLING, false);
        }
    }

    /** The closest survival or adventure player inside the warning range (shorter if they crouch). */
    private @Nullable Player nearestIntruder(ServerLevel level) {
        Player best = null;
        double bestDist = Double.MAX_VALUE;
        for (Player p : level.players()) {
            if (!p.isAlive() || p.isCreative() || p.isSpectator()) continue;
            double range = p.isCrouching() || p.isShiftKeyDown() ? WARN_CROUCHING : WARN;
            double d = this.distanceToSqr(p);
            if (d <= range * range && d < bestDist) {
                best = p;
                bestDist = d;
            }
        }
        return best;
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        if (target != null && this.getTarget() == null) this.playSound(SoundEvents.CAT_HISS_BABY.value(), 1.0F, 0.6F);
        super.setTarget(target);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            this.playSound(SoundEvents.FOX_BITE, 0.8F, 1.3F);
            if (target instanceof LivingEntity living) living.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 0), this);
        }
        return hit;
    }

    /** Never spawns as a hatchling: it doesn't breed, so there's nothing to grow up into. */
    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason, @Nullable SpawnGroupData data) {
        return super.finalizeSpawn(level, difficulty, reason, new AgeableMobGroupData(false));
    }

    @Override public boolean isFood(ItemStack stack) { return false; }
    @Override public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) { return null; }

    /** Quiet while it basks: the rattle is its voice. */
    @Override protected @Nullable SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.CAT_HISS_BABY.value(); }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.CAT_HISS_BABY.value(); }
    /** A snake slides along without footsteps. */
    @Override protected void playStepSound(BlockPos pos, BlockState state) {}
    /** The cat hiss is a kitten's (pitched up), so these voices sit low to bring it back down. */
    @Override public float getVoicePitch() { return 0.5F + this.random.nextFloat() * 0.08F; }
    @Override protected float getSoundVolume() { return 0.5F; }

    /** While it rattles it stays put, coiled, and keeps its eyes on the intruder. */
    private class HoldGroundGoal extends Goal {
        HoldGroundGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override public boolean canUse() { return Rattlesnake.this.isRattling(); }
        @Override public void start() { Rattlesnake.this.getNavigation().stop(); }
        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            if (Rattlesnake.this.warned != null) Rattlesnake.this.getLookControl().setLookAt(Rattlesnake.this.warned, 30.0F, 30.0F);
        }
    }
}
