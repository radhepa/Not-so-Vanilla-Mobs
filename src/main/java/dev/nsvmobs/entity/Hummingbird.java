package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.StemBlock;
import net.minecraft.world.level.block.SweetBerryBushBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A tiny hummingbird (ruby-throated, violet-crowned or rufous). It darts from flower to flower and
 * hovers to sip; afterwards it carries pollen and now and then grows nearby crops a stage, like a
 * bee. Now and then it plants a copy of a flower it sipped from (only with mobGriefing on).
 */
public class Hummingbird extends Animal {
    /** Colourways, in texture order: hummingbird (ruby-throated), hummingbird_violet, hummingbird_rufous. */
    public static final int VARIANTS = 3;
    private static final EntityDataAccessor<Integer> VARIANT = SynchedEntityData.defineId(Hummingbird.class, EntityDataSerializers.INT);
    /** Pollinations left from the last sip (0 = no pollen). */
    private int pollen;
    private int pollinateTime = 200;

    public Hummingbird(EntityType<? extends Hummingbird> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 20, true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 4.0)
                .add(Attributes.FLYING_SPEED, 0.6)
                .add(Attributes.MOVEMENT_SPEED, 0.25);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(VARIANT, 0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.1, s -> s.is(Items.SUGAR), false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new SipGoal());
        this.goalSelector.addGoal(6, new PerchGoal());
        this.goalSelector.addGoal(8, new WaterAvoidingRandomFlyingGoal(this, 1.0));
    }

    public int variant() { return this.entityData.get(VARIANT); }
    private void setVariant(int v) { this.entityData.set(VARIANT, Math.floorMod(v, VARIANTS)); }

    /** Hovering or darting about (it hardly ever lands). */
    public boolean isFlying() { return !this.onGround(); }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData data) {
        this.setVariant(this.random.nextInt(VARIANTS));
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        // carrying pollen, it grows the crops it passes over every so often (works with NoAI too)
        if (this.level() instanceof ServerLevel level && this.pollen > 0 && --this.pollinateTime <= 0) {
            this.pollinateTime = 200 + this.random.nextInt(200);
            if (this.pollinateAround(level)) this.pollen--;
        }
    }

    /**
     * Grows every crop within 2 blocks (crops, stems, sweet berry bushes) by one stage, like a bee
     * carrying nectar (only when mobGriefing is on). Returns true if anything grew.
     */
    public boolean pollinateAround(ServerLevel level) {
        if (!Griefing.allowed(level)) return false;   // growing crops changes blocks
        boolean grew = false;
        BlockPos centre = this.blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(centre.offset(-2, -2, -2), centre.offset(2, 2, 2))) {
            BlockState state = level.getBlockState(pos);
            BlockState grown = grownState(state);
            if (grown != null) {
                level.setBlockAndUpdate(pos, grown);
                level.levelEvent(2011, pos, 15);     // the bone meal sparkle
                grew = true;
            }
        }
        if (grew) this.playSound(SoundEvents.BEE_POLLINATE, 0.6F, 1.6F);
        return grew;
    }

    /** The state one growth stage on, or null if the block isn't a crop or is fully grown. */
    static @Nullable BlockState grownState(BlockState state) {
        Block block = state.getBlock();
        if (block instanceof CropBlock crop) {
            return crop.isMaxAge(state) ? null : crop.getStateForAge(crop.getAge(state) + 1);
        }
        if (block instanceof StemBlock) {
            int age = state.getValue(StemBlock.AGE);
            return age < StemBlock.MAX_AGE ? state.setValue(StemBlock.AGE, age + 1) : null;
        }
        if (block instanceof SweetBerryBushBlock) {
            int age = state.getValue(SweetBerryBushBlock.AGE);
            return age < SweetBerryBushBlock.MAX_AGE ? state.setValue(SweetBerryBushBlock.AGE, age + 1) : null;
        }
        return null;
    }

    /** One sip in 8: plant a copy of the flower on a free grass block nearby. */
    private void maybePlantFlower(ServerLevel level, BlockPos flowerPos, BlockState flower) {
        if (this.random.nextInt(8) != 0 || !Griefing.allowed(level)) return;
        if (!flower.is(BlockTags.SMALL_FLOWERS) || flower.is(Blocks.WITHER_ROSE)) return;
        BlockState copy = flower.getBlock().defaultBlockState();
        for (int i = 0; i < 12; i++) {
            BlockPos p = flowerPos.offset(this.random.nextInt(7) - 3, this.random.nextInt(3) - 1, this.random.nextInt(7) - 3);
            if (level.getBlockState(p.below()).is(Blocks.GRASS_BLOCK) && level.isEmptyBlock(p) && copy.canSurvive(level, p)) {
                level.setBlockAndUpdate(p, copy);
                level.levelEvent(2011, p, 6);
                return;
            }
        }
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.SUGAR); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Hummingbird baby = NsvEntities.HUMMINGBIRD.create(level, EntitySpawnReason.BREEDING);
        if (baby != null) {
            baby.setVariant(partner instanceof Hummingbird other && this.random.nextBoolean() ? other.variant() : this.variant());
        }
        return baby;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Variant", this.variant());
        output.putInt("Pollen", this.pollen);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.setVariant(input.getIntOr("Variant", 0));
        this.pollen = input.getIntOr("Pollen", 0);
    }

    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override public boolean isFlapping() { return this.isFlying(); }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.PARROT_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.PARROT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PARROT_DEATH; }
    @Override public float getVoicePitch() { return 1.9F + this.random.nextFloat() * 0.2F; }
    @Override protected float getSoundVolume() { return 0.3F; }
    @Override public int getAmbientSoundInterval() { return 200; }

    /** Once in a long while it stops hovering, drops onto whatever is below and rests a bit. */
    final class PerchGoal extends Goal {
        private int ticks;

        PerchGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            Hummingbird bird = Hummingbird.this;
            if (bird.isInWater() || bird.random.nextInt(this.reducedTickDelay(1600)) != 0) return false;
            for (int dy = 1; dy <= 4; dy++) {                       // only over solid, dry ground
                BlockPos p = bird.blockPosition().below(dy);
                if (!bird.level().getFluidState(p).isEmpty()) return false;
                if (bird.level().getBlockState(p).isFaceSturdy(bird.level(), p, Direction.UP)) return true;
            }
            return false;
        }

        @Override public boolean canContinueToUse() { return this.ticks > 0 && !Hummingbird.this.isInWater(); }

        @Override
        public void start() {
            this.ticks = 160 + Hummingbird.this.random.nextInt(240);
            Hummingbird.this.getNavigation().stop();
            Hummingbird.this.setNoGravity(false);
        }

        @Override public void tick() { this.ticks--; }
    }

    /**
     * Dart to a flower (or, carrying pollen, to a crop), hover in front of it and sip for a few
     * seconds. A sip loads pollen; a visit to a crop spends some of it.
     */
    final class SipGoal extends Goal {
        private BlockPos target;
        private boolean crop;
        private int cooldown = 40, sipTicks, travelTicks;
        private Vec3 hover;

        SipGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (--this.cooldown > 0 || Hummingbird.this.isInLove()) return false;
            this.cooldown = 20;
            this.crop = Hummingbird.this.pollen > 0 && Hummingbird.this.random.nextBoolean();
            this.target = this.find(this.crop);
            if (this.target == null && this.crop) {
                this.crop = false;
                this.target = this.find(false);
            }
            return this.target != null;
        }

        @Override
        public boolean canContinueToUse() {
            return this.target != null && this.travelTicks < 200 && this.sipTicks > 0 && this.stillThere();
        }

        @Override
        public void start() {
            this.sipTicks = 40 + Hummingbird.this.random.nextInt(50);
            this.travelTicks = 0;
            // hover half a block out from the flower, on the side we're coming from, at petal height
            Vec3 c = Vec3.atBottomCenterOf(this.target);
            Vec3 from = Hummingbird.this.position().subtract(c);
            Vec3 side = new Vec3(from.x, 0, from.z);
            side = side.lengthSqr() < 1.0E-4 ? new Vec3(0.6, 0, 0) : side.normalize().scale(0.6);
            this.hover = c.add(side.x, this.crop ? 0.9 : 0.45, side.z);
        }

        @Override
        public void stop() {
            this.target = null;
            this.cooldown = 60 + Hummingbird.this.random.nextInt(140);   // then dart off to the next one
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            Hummingbird bird = Hummingbird.this;
            bird.getMoveControl().setWantedPosition(this.hover.x, this.hover.y, this.hover.z, 1.0);
            bird.getLookControl().setLookAt(this.target.getX() + 0.5, this.target.getY() + 0.4, this.target.getZ() + 0.5);
            if (bird.position().distanceToSqr(this.hover) > 0.5 * 0.5) {
                this.travelTicks++;
                return;
            }
            if (--this.sipTicks != 0) return;   // the sip ends once, even though this ticks on after it
            if (bird.level() instanceof ServerLevel level) {
                if (this.crop) {
                    if (bird.pollinateAround(level)) bird.pollen--;
                } else {
                    bird.pollen = 3;
                    bird.playSound(SoundEvents.HONEY_DRINK.value(), 0.25F, 1.8F);
                    bird.maybePlantFlower(level, this.target, level.getBlockState(this.target));
                }
            }
        }

        private boolean stillThere() {
            BlockState state = Hummingbird.this.level().getBlockState(this.target);
            return this.crop ? grownState(state) != null : state.is(BlockTags.FLOWERS);
        }

        /** The nearest flower (or growing crop) among a scatter of samples within ~10 blocks. */
        private @Nullable BlockPos find(boolean crop) {
            Level level = Hummingbird.this.level();
            BlockPos origin = Hummingbird.this.blockPosition(), best = null;
            double bestDist = Double.MAX_VALUE;
            for (int i = 0; i < 64; i++) {
                BlockPos p = origin.offset(Hummingbird.this.random.nextInt(21) - 10, Hummingbird.this.random.nextInt(9) - 5,
                        Hummingbird.this.random.nextInt(21) - 10);
                BlockState state = level.getBlockState(p);
                boolean ok = crop ? grownState(state) != null : state.is(BlockTags.FLOWERS);
                if (!ok || !level.isEmptyBlock(p.above())) continue;
                double d = p.distSqr(origin);
                if (d < bestDist && d > 1.0) {
                    bestDist = d;
                    best = p.immutable();
                }
            }
            return best;
        }
    }
}
