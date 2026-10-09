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
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;

/**
 * A desert meerkat. They live in groups; one often stands up on its hind legs to keep watch, and when
 * it spots a monster (even a Dune Scorpion buried in the sand) it chirps the alarm and the monster
 * glows for a while. Immune to poison, a group of them will gang up on Dune Scorpions.
 */
public class Meerkat extends Animal {
    private static final EntityDataAccessor<Boolean> SENTRY = SynchedEntityData.defineId(Meerkat.class, EntityDataSerializers.BOOLEAN);
    static final double WATCH_RANGE = 16.0;

    public Meerkat(EntityType<? extends Meerkat> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.FOLLOW_RANGE, 16.0);
    }

    /** Sand, red sand, terracotta, coarse dirt or grass, in daylight. */
    public static boolean checkSpawnRules(EntityType<Meerkat> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return (below.is(BlockTags.SAND) || below.is(BlockTags.ARMADILLO_SPAWNABLE_ON) || below.is(BlockTags.ANIMALS_SPAWNABLE_ON))
                && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SENTRY, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6) {
            @Override public boolean canUse() { return Meerkat.this.getTarget() == null && super.canUse(); }
        });
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.3, true));
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.2, s -> s.is(Items.SPIDER_EYE), false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(6, new SentryGoal());
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
        // a mob of meerkats (two or more grown-ups nearby) takes on a Dune Scorpion
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, DuneScorpion.class, 10, false, false,
                (t, l) -> !this.isBaby() && this.mob().size() >= 2));
    }

    /** Grown-up meerkats within 8 blocks, counting this one. */
    private List<Meerkat> mob() {
        return this.level().getEntitiesOfClass(Meerkat.class, this.getBoundingBox().inflate(8.0), m -> !m.isBaby() && m.isAlive());
    }

    public boolean isSentry() {
        return this.entityData.get(SENTRY);
    }

    public void setSentry(boolean sentry) {
        this.entityData.set(SENTRY, sentry);
    }

    /** Never poisoned (scorpion stings included). */
    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        return !effect.is(MobEffects.POISON) && super.canBeAffected(effect);
    }

    /** Look out for monsters: any within range that aren't glowing yet get lit up, with an alarm call. */
    void keepWatch(ServerLevel level) {
        List<Mob> spotted = level.getEntitiesOfClass(Mob.class, this.getBoundingBox().inflate(WATCH_RANGE),
                m -> m instanceof Enemy && m.isAlive() && !m.hasEffect(MobEffects.GLOWING));
        if (spotted.isEmpty()) return;
        for (Mob m : spotted) m.addEffect(new MobEffectInstance(MobEffects.GLOWING, 120), this);
        this.playSound(SoundEvents.FOX_SCREECH, 0.5F, 1.9F);
        // the rest of the group sits up to look
        for (Meerkat other : this.mob()) {
            if (other != this && !other.isSentry() && other.getTarget() == null) other.setSentry(true);
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level && this.isSentry()) {
            this.getNavigation().stop();
            if (this.tickCount % 20 == 0) keepWatch(level);
            if (this.getTarget() != null || this.isInWater()) this.setSentry(false);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt) this.setSentry(false);
        return hurt;
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.SPIDER_EYE); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.MEERKAT.create(level, EntitySpawnReason.BREEDING);
    }

    @Override protected SoundEvent getAmbientSound() { return this.isSentry() ? null : SoundEvents.FOX_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.RABBIT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.RABBIT_DEATH; }
    @Override public float getVoicePitch() { return 1.7F + this.random.nextFloat() * 0.2F; }
    @Override protected float getSoundVolume() { return 0.5F; }

    /** Now and then a grown-up stops, stands up on its hind legs and keeps watch for a few seconds. */
    final class SentryGoal extends Goal {
        private int ticks;

        SentryGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            Meerkat m = Meerkat.this;
            return !m.isBaby() && m.onGround() && !m.isInWater() && m.getTarget() == null
                    && (m.isSentry() || m.random.nextInt(m.mob().size() > 2 ? 120 : 300) == 0);
        }

        @Override
        public void start() {
            this.ticks = 100 + Meerkat.this.random.nextInt(200);
            Meerkat.this.setSentry(true);
            Meerkat.this.getNavigation().stop();
        }

        @Override
        public boolean canContinueToUse() {
            return this.ticks > 0 && Meerkat.this.isSentry() && Meerkat.this.getTarget() == null;
        }

        @Override
        public void tick() {
            this.ticks--;
        }

        @Override
        public void stop() {
            Meerkat.this.setSentry(false);
        }
    }
}
