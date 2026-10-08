package dev.nsvmobs.entity;

import java.util.List;

import dev.nsvmobs.NsvEntities;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.chicken.Chicken;
import net.minecraft.world.entity.animal.feline.Cat;
import net.minecraft.world.entity.animal.feline.Ocelot;
import net.minecraft.world.entity.animal.fox.Fox;
import net.minecraft.world.entity.animal.frog.Frog;
import net.minecraft.world.entity.animal.parrot.Parrot;
import net.minecraft.world.entity.animal.rabbit.Rabbit;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import org.jspecify.annotations.Nullable;

/**
 * The calmest animal in the world. Small animals hop on its back for a ride, and a player who
 * crouches beside it feels better (Regeneration).
 */
public class Capybara extends Animal {
    private int rideTicks;

    public Capybara(EntityType<? extends Capybara> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.15, s -> s.is(Items.SUGAR_CANE), false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8, 0.002F));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
    }

    /** Animals small enough to ride on its back. */
    static boolean rider(Entity e) {
        if (!(e instanceof Mob mob) || mob.isPassenger() || mob.isVehicle() || mob.isLeashed() || mob instanceof Capybara) return false;
        if (mob instanceof TamableAnimal pet && pet.isOrderedToSit()) return false;
        if (mob instanceof Chicken || mob instanceof Rabbit || mob instanceof Frog || mob instanceof Cat || mob instanceof Ocelot
                || mob instanceof Fox || mob instanceof Parrot) return true;
        return mob instanceof Animal animal && animal.isBaby() && animal.getBbWidth() < 0.8F;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || this.isBaby()) return;
        if (this.isVehicle()) {
            if (--this.rideTicks <= 0 || this.isInWater()) this.ejectPassengers();
        } else if (this.tickCount % 100 == 0 && this.random.nextInt(3) == 0) {
            List<Mob> near = level.getEntitiesOfClass(Mob.class, this.getBoundingBox().inflate(4.0), Capybara::rider);
            if (!near.isEmpty()) {
                Mob hopper = near.get(this.random.nextInt(near.size()));
                if (hopper.startRiding(this)) {
                    this.rideTicks = 400 + this.random.nextInt(800);
                }
            }
        }
        if (this.tickCount % 20 == 0) {
            for (Player p : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(2.5))) {
                if (p.isCrouching() && !p.hasEffect(MobEffects.REGENERATION)) {
                    p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 60, 0, true, true), this);
                }
            }
        }
    }

    /** Riders sit quietly; they never steer. */
    @Override public @Nullable LivingEntity getControllingPassenger() { return null; }

    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }
    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.SUGAR_CANE); }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.CAPYBARA.create(level, EntitySpawnReason.BREEDING);
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.CAMEL_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.CAMEL_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.CAMEL_DEATH; }
    @Override protected float getSoundVolume() { return 0.4F; }
    @Override public float getVoicePitch() { return 1.5F + this.random.nextFloat() * 0.2F; }
    @Override public int getAmbientSoundInterval() { return 240; }
}
