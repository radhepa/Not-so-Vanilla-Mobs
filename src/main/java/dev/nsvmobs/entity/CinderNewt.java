package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.navigation.GroundPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * A Nether newt with glowing spots. It walks on lava like a strider and basks in it to heal. Leave
 * it be and it ignores you; hurt one and the whole group bites back, and its bite sets you alight.
 */
public class CinderNewt extends Animal {
    public CinderNewt(EntityType<? extends CinderNewt> type, Level level) {
        super(type, level);
        this.setPathfindingMalus(PathType.LAVA, 0.0F);
        this.setPathfindingMalus(PathType.FIRE_IN_NEIGHBOR, 0.0F);
        this.setPathfindingMalus(PathType.FIRE, 0.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.FOLLOW_RANGE, 12.0);   // also how far the call to bite back carries
    }

    /** Any solid ground but nether wart blocks and the bedrock roof, at any light; never inside lava. */
    public static boolean checkSpawnRules(EntityType<CinderNewt> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return below.isSolid() && !below.is(Blocks.NETHER_WART_BLOCK) && !below.is(Blocks.BEDROCK)
                && !level.getFluidState(pos).is(FluidTags.LAVA);
    }

    @Override
    protected void registerGoals() {
        // swims up in water; in lava it stands on the surface instead (see tick)
        this.goalSelector.addGoal(0, new FloatGoal(this) {
            @Override public boolean canUse() { return !CinderNewt.this.isInLava() && super.canUse(); }
        });
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6) {
            @Override public boolean canUse() { return CinderNewt.this.isBaby() && super.canUse(); }
        });
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.4, true) {
            @Override public boolean canUse() { return !CinderNewt.this.isBaby() && super.canUse(); }
        });
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, this::isFood, false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(6, new RandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        // hurt one and every newt within 12 blocks (the follow range) bites back
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
    }

    // -- lava walking, as the strider does it ----------------------------------------------------
    @Override public boolean canStandOnFluid(FluidState fluid) { return fluid.is(FluidTags.LAVA); }
    @Override public VoxelShape getLiquidCollisionShape() { return Block.column(16.0, 0.0, 8.0); }
    @Override protected PathNavigation createNavigation(Level level) { return new LavaWalkerNavigation(this, level); }

    /** Lava is a nice place to be, but it happily wanders off it too. */
    @Override
    public float getWalkTargetValue(BlockPos pos, LevelReader level) {
        return level.getBlockState(pos).getFluidState().is(FluidTags.LAVA) ? 4.0F : super.getWalkTargetValue(pos, level);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.isInLava()) {
            // bob back up to the surface if it ever sinks in
            CollisionContext context = CollisionContext.of(this);
            if (context.isAbove(this.getLiquidCollisionShape(), this.blockPosition(), true)
                    && !this.level().getFluidState(this.blockPosition().above()).is(FluidTags.LAVA)) {
                this.setOnGround(true);
            } else {
                this.setDeltaMovement(this.getDeltaMovement().scale(0.5).add(0.0, 0.05, 0.0));
            }
        }
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
        if (this.isInLava()) this.resetFallDistance();
        else super.checkFallDamage(ya, onGround, onState, pos);
    }

    /** In or on lava. */
    public boolean isBasking() {
        return this.isInLava() || this.level().getFluidState(this.blockPosition()).is(FluidTags.LAVA)
                || this.onGround() && this.level().getFluidState(this.blockPosition().below()).is(FluidTags.LAVA);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level && this.tickCount % 40 == 0 && this.isBasking()
                && this.getHealth() < this.getMaxHealth()) {
            this.heal(1.0F);
            level.sendParticles(ParticleTypes.FLAME, this.getX(), this.getY() + 0.3, this.getZ(), 3, 0.2, 0.1, 0.2, 0.01);
        }
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        if (target != null && this.getTarget() == null) this.playSound(SoundEvents.AXOLOTL_HURT, 0.8F, 0.6F);
        super.setTarget(target);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            target.igniteForSeconds(4.0F);
            this.playSound(SoundEvents.AXOLOTL_ATTACK, 1.0F, this.getVoicePitch());
        }
        return hit;
    }

    /** Its own glow does the job; no flames drawn over it while it basks. */
    @Override public boolean isOnFire() { return false; }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.MAGMA_CREAM); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.CINDER_NEWT.create(level, EntitySpawnReason.BREEDING);
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.AXOLOTL_IDLE_AIR; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.AXOLOTL_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.AXOLOTL_DEATH; }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        if (this.isBasking()) this.playSound(SoundEvents.STRIDER_STEP_LAVA, 0.25F, 1.5F);
        else super.playStepSound(pos, state);
    }

    @Override public float getVoicePitch() { return (this.isBaby() ? 1.1F : 0.8F) + this.random.nextFloat() * 0.1F; }
    @Override protected float getSoundVolume() { return 0.6F; }

    /** Ground navigation that also counts a lava surface as somewhere to stand (the strider's). */
    private static class LavaWalkerNavigation extends GroundPathNavigation {
        LavaWalkerNavigation(CinderNewt mob, Level level) {
            super(mob, level);
        }

        @Override
        protected PathFinder createPathFinder(int maxVisitedNodes) {
            this.nodeEvaluator = new WalkNodeEvaluator();
            return new PathFinder(this.nodeEvaluator, maxVisitedNodes);
        }

        @Override
        public boolean isStableDestination(BlockPos pos) {
            return this.level.getBlockState(pos).is(Blocks.LAVA) || super.isStableDestination(pos);
        }
    }
}
