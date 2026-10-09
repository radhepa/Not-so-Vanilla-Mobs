package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WallClimberNavigation;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.spider.CaveSpider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * A spider queen twice the size of a spider. She climbs walls like one, spits webs that stick you in
 * place, bites with a strong poison, and at two-thirds and one-third health a brood of cave spiders
 * spills off her back.
 */
public class Broodmother extends Monster {
    private static final EntityDataAccessor<Byte> FLAGS = SynchedEntityData.defineId(Broodmother.class, EntityDataSerializers.BYTE);
    private static final int CLIMBING = 1, SPITTING = 2;
    /** Cave spiders per brood. */
    static final int BROOD_SIZE = 3;
    private int broods;

    public Broodmother(EntityType<? extends Broodmother> type, Level level) {
        super(type, level);
        this.xpReward = 20;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.5)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    /** Deep caves anywhere (below y 0), or the dark floor of a Dark Forest. */
    public static boolean checkSpawnRules(EntityType<Broodmother> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        boolean place = EntitySpawnReason.isSpawner(reason) || pos.getY() < 0 || level.getBiome(pos).is(Biomes.DARK_FOREST);
        return place && Monster.checkMonsterSpawnRules(type, level, reason, pos, random);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(FLAGS, (byte) 0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WallClimberNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new SpitWebGoal());
        this.goalSelector.addGoal(3, new LeapAtTargetGoal(this, 0.4F));
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.1, true));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(6, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, true));
    }

    private boolean flag(int f) {
        return (this.entityData.get(FLAGS) & f) != 0;
    }

    private void setFlag(int f, boolean on) {
        byte b = this.entityData.get(FLAGS);
        this.entityData.set(FLAGS, (byte) (on ? b | f : b & ~f));
    }

    public boolean isClimbing() { return this.flag(CLIMBING); }
    /** Reared up, about to spit a web. */
    public boolean isSpitting() { return this.flag(SPITTING); }
    public int broodsReleased() { return this.broods; }
    public void setSpitting(boolean spitting) { this.setFlag(SPITTING, spitting); }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide()) this.setFlag(CLIMBING, this.horizontalCollision);
    }

    @Override public boolean onClimbable() { return this.isClimbing(); }

    @Override
    public void makeStuckInBlock(BlockState state, Vec3 speedMultiplier) {
        if (!state.is(Blocks.COBWEB)) super.makeStuckInBlock(state, speedMultiplier);
    }

    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        return !effect.is(MobEffects.POISON) && super.canBeAffected(effect);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        if (!super.doHurtTarget(level, target)) return false;
        if (target instanceof LivingEntity victim) {
            Difficulty d = level.getDifficulty();
            if (d == Difficulty.NORMAL) victim.addEffect(new MobEffectInstance(MobEffects.POISON, 160, 0), this);
            else if (d == Difficulty.HARD) victim.addEffect(new MobEffectInstance(MobEffects.POISON, 160, 1), this);
        }
        return true;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive()) {
            float left = this.getHealth() / this.getMaxHealth();
            if ((this.broods == 0 && left < 2.0F / 3.0F) || (this.broods == 1 && left < 1.0F / 3.0F)) {
                this.broods++;
                this.releaseBrood(level, source.getEntity() instanceof LivingEntity l ? l : this.getTarget());
            }
        }
        return hurt;
    }

    /** A brood of cave spiders spills off her back and goes for whoever she's fighting. */
    void releaseBrood(ServerLevel level, LivingEntity foe) {
        for (int i = 0; i < BROOD_SIZE; i++) {
            CaveSpider spider = EntityTypes.CAVE_SPIDER.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (spider == null) continue;
            spider.snapTo(this.getX() + this.random.nextGaussian() * 0.6, this.getY() + 0.8, this.getZ() + this.random.nextGaussian() * 0.6,
                    this.random.nextFloat() * 360.0F, 0.0F);
            spider.finalizeSpawn(level, level.getCurrentDifficultyAt(this.blockPosition()), EntitySpawnReason.MOB_SUMMONED, null);
            spider.setDeltaMovement(this.random.nextGaussian() * 0.2, 0.3, this.random.nextGaussian() * 0.2);
            if (foe != null && foe.isAlive()) spider.setTarget(foe);
            level.addFreshEntity(spider);
        }
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.COBWEB.defaultBlockState()),
                this.getX(), this.getY() + 1.0, this.getZ(), 30, 0.7, 0.4, 0.7, 0.1);
        this.playSound(SoundEvents.TURTLE_EGG_CRACK, 1.5F, 0.6F);
        this.playSound(SoundEvents.SPIDER_HURT, 1.5F, 0.5F);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Broods", this.broods);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.broods = input.getIntOr("Broods", 0);
    }

    @Override protected float getSoundVolume() { return 1.4F; }
    @Override public float getVoicePitch() { return 0.55F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.SPIDER_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.SPIDER_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.SPIDER_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.SPIDER_STEP, 0.3F, 0.6F); }

    /** From 4 to 16 blocks away, she rears up and spits a web at her target. */
    final class SpitWebGoal extends Goal {
        private int windup, next;

        SpitWebGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Broodmother.this.getTarget();
            if (t == null || !t.isAlive() || Broodmother.this.tickCount < this.next) return false;
            double d = Broodmother.this.distanceToSqr(t);
            return d > 16.0 && d < 256.0 && Broodmother.this.hasLineOfSight(t);
        }

        @Override
        public boolean canContinueToUse() {
            LivingEntity t = Broodmother.this.getTarget();
            return this.windup > 0 && t != null && t.isAlive();
        }

        @Override
        public void start() {
            this.windup = 14;
            Broodmother.this.getNavigation().stop();
            Broodmother.this.setFlag(SPITTING, true);
            Broodmother.this.playSound(SoundEvents.SPIDER_AMBIENT, 1.5F, 1.5F);
        }

        @Override
        public void stop() {
            Broodmother.this.setFlag(SPITTING, false);
            this.next = Broodmother.this.tickCount + 60 + Broodmother.this.random.nextInt(40);
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = Broodmother.this.getTarget();
            if (t == null) return;
            Broodmother.this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (--this.windup == 0) {
                WebGlob glob = new WebGlob(NsvEntities.WEB_GLOB, Broodmother.this);
                glob.aimAt(t, 1.2F, 2.0F);
                Broodmother.this.level().addFreshEntity(glob);
                Broodmother.this.playSound(SoundEvents.LLAMA_SPIT, 1.2F, 0.6F);
            }
        }
    }
}
