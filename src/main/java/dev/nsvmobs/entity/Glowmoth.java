package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
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
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/** A big gentle moth. At night it's drawn to torches and lanterns; now and then it sheds glowstone dust. */
public class Glowmoth extends Animal {
    private int dustTime;

    public Glowmoth(EntityType<? extends Glowmoth> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 20, true);
        this.dustTime = 6000 + this.random.nextInt(6000);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 6.0)
                .add(Attributes.FLYING_SPEED, 0.4)
                .add(Attributes.MOVEMENT_SPEED, 0.2);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.1, s -> s.is(ItemTags.BEE_FOOD), false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new SeekLightGoal());
        this.goalSelector.addGoal(8, new WaterAvoidingRandomFlyingGoal(this, 1.0));
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level && this.isAlive() && !this.isBaby() && --this.dustTime <= 0) {
            this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 0.6F, 1.4F);
            this.spawnAtLocation(level, new ItemStack(Items.GLOWSTONE_DUST));
            this.dustTime = 6000 + this.random.nextInt(6000);
        }
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(ItemTags.BEE_FOOD); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.GLOWMOTH.create(level, EntitySpawnReason.BREEDING);
    }

    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override public boolean isFlapping() { return true; }
    @Override protected SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.BAT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.BAT_DEATH; }
    @Override public float getVoicePitch() { return 1.5F + this.random.nextFloat() * 0.2F; }
    @Override protected float getSoundVolume() { return 0.4F; }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("DustTime", this.dustTime);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.dustTime = input.getIntOr("DustTime", this.dustTime);
    }

    /** At night: find a bright light nearby and flutter in circles around it. */
    final class SeekLightGoal extends Goal {
        private BlockPos light;
        private int searchCooldown, circleTicks;
        private float angle;

        SeekLightGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            if (Glowmoth.this.level().isBrightOutside() || --this.searchCooldown > 0) return false;
            this.searchCooldown = 40;
            this.light = findLight();
            return this.light != null;
        }

        @Override
        public boolean canContinueToUse() {
            return this.light != null && this.circleTicks > 0 && !Glowmoth.this.level().isBrightOutside()
                    && Glowmoth.this.level().getBlockState(this.light).getLightEmission() >= 10;
        }

        @Override
        public void start() {
            this.circleTicks = 300 + Glowmoth.this.random.nextInt(600);
            this.angle = Glowmoth.this.random.nextFloat() * Mth.TWO_PI;
        }

        @Override
        public void tick() {
            this.circleTicks--;
            this.angle += 0.12F;
            double r = 1.4 + Mth.sin(this.angle * 0.7F) * 0.4;
            Glowmoth.this.getMoveControl().setWantedPosition(this.light.getX() + 0.5 + Mth.cos(this.angle) * r,
                    this.light.getY() + 1.0 + Mth.sin(this.angle * 1.9F) * 0.5, this.light.getZ() + 0.5 + Mth.sin(this.angle) * r, 1.0);
        }

        /**
         * Light spreads ~14 blocks from its source, so random samples within 16 find the lit area
         * cheaply; the brightest sample sits right by the source, and a small scan there finds it.
         */
        private @Nullable BlockPos findLight() {
            Level level = Glowmoth.this.level();
            BlockPos origin = Glowmoth.this.blockPosition(), brightest = null;
            int bestLight = 6;
            for (int i = 0; i < 48; i++) {
                BlockPos p = origin.offset(Glowmoth.this.random.nextInt(33) - 16, Glowmoth.this.random.nextInt(13) - 6,
                        Glowmoth.this.random.nextInt(33) - 16);
                int light = level.getBrightness(LightLayer.BLOCK, p);
                if (light > bestLight) {
                    bestLight = light;
                    brightest = p.immutable();
                }
            }
            if (brightest == null) return null;
            BlockPos source = null;
            int bestEmission = 9;
            for (BlockPos p : BlockPos.betweenClosed(brightest.offset(-4, -3, -4), brightest.offset(4, 3, 4))) {
                int emission = level.getBlockState(p).getLightEmission();
                if (emission > bestEmission) {
                    bestEmission = emission;
                    source = p.immutable();
                }
            }
            return source;
        }
    }
}
