package dev.nsvmobs.entity;

import java.util.EnumSet;
import java.util.List;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.MoveToBlockGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A savanna elephant, in small herds with their calves. At water it drinks and fills its trunk (or
 * take it a water bucket); with a trunkful it hoses down any burning creature close by that isn't a
 * monster, and puts out fires around it. On hot, dry afternoons with an empty trunk it blows dust
 * over its back instead. Neutral: hurt one and it flares its ears, raises its trunk and trumpets,
 * then charges with a launch that throws you clear, and the grown-ups of its herd join in. Walk up to
 * a calf and the adults warn you off the same way, without charging. Melon slices tempt, heal and
 * breed it.
 */
public class Elephant extends Animal {
    private static final EntityDataAccessor<Boolean> WATER = SynchedEntityData.defineId(Elephant.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> SPRAYING = SynchedEntityData.defineId(Elephant.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> THREATENING = SynchedEntityData.defineId(Elephant.class, EntityDataSerializers.BOOLEAN);
    /** How far it hoses down burning creatures, and puts out fire blocks. */
    private static final double SHOWER_RANGE = 8.0, FIRE_RANGE = 6.0;
    /** A spray lasts a second; the jet lands on its target this many ticks in. */
    private static final int SPRAY_TIME = 20, SPRAY_HIT = 4;
    /** The trumpet before a charge, and the warning at someone near a calf. */
    private static final int THREAT_TIME = 24, WARN_TIME = 30;
    /** Standing in or beside water this long fills the trunk. */
    private static final int DRINK_TIME = 40;
    /** It calms down once whoever it's after is this far away. */
    private static final double CALM_RANGE = 16.0;
    private int sprayTicks;
    private boolean dusting;
    private @Nullable LivingEntity sprayTarget;
    private @Nullable Vec3 sprayAt;
    private int threatTicks;
    private @Nullable LivingEntity threatAt;
    private int warnCooldown;
    private int drinkTicks;

    public Elephant(EntityType<? extends Elephant> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 80.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.ATTACK_DAMAGE, 10.0)
                .add(Attributes.ATTACK_KNOCKBACK, 2.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.STEP_HEIGHT, 1.0)
                .add(Attributes.FOLLOW_RANGE, CALM_RANGE);   // the herd it alerts, and how far it chases
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(WATER, false);
        builder.define(SPRAYING, false);
        builder.define(THREATENING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        // calves run from danger; the grown-ups only from fire
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.5) {
            @Override public boolean canUse() { return (Elephant.this.isBaby() || Elephant.this.isOnFire()) && super.canUse(); }
        });
        this.goalSelector.addGoal(1, new HoldGoal());
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.5, true) {
            @Override public boolean canUse() { return !Elephant.this.isBaby() && !Elephant.this.isThreatening() && super.canUse(); }
        });
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, this::isFood, false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(6, new SeekWaterGoal());
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
        // hurt one (or a calf) and the grown-ups of the herd come for you
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData groupData) {
        // herds often come with a calf or two
        return super.finalizeSpawn(level, difficulty, reason, groupData == null ? new AgeableMobGroupData(0.3F) : groupData);
    }

    // -- state -------------------------------------------------------------------------------------
    /** A trunkful of water, ready to spray. */
    public boolean hasWater() {
        return this.entityData.get(WATER);
    }

    /** Fills the trunk now (as if it had drunk its fill). */
    public void fillTrunk() {
        this.entityData.set(WATER, true);
        this.drinkTicks = 0;
    }

    /** Hosing something down, or blowing dust over its back: trunk raised (about a second). */
    public boolean isSpraying() {
        return this.entityData.get(SPRAYING);
    }

    /** Ears flared, trunk raised, trumpeting: before a charge, or warning someone off a calf. */
    public boolean isThreatening() {
        return this.entityData.get(THREATENING);
    }

    // -- the trunk shower, threats and drinking (all in aiStep, so they work without AI too) ----------
    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || !this.isAlive()) return;
        if (this.warnCooldown > 0) this.warnCooldown--;

        LivingEntity target = this.getTarget();
        if (target != null && (!target.isAlive() || this.distanceToSqr(target) > CALM_RANGE * CALM_RANGE
                || !EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(target))) {
            this.setTarget(null);           // you got away: it settles down
            target = null;
        }

        if (this.threatTicks > 0) {
            if (this.threatAt != null) this.faceTowards(this.threatAt.position());
            if (--this.threatTicks == 0) {
                this.entityData.set(THREATENING, false);
                this.threatAt = null;
            }
        } else if (!this.isBaby() && target == null && this.warnCooldown <= 0 && this.tickCount % 10 == 0) {
            Player intruder = this.calfIntruder(level);
            if (intruder != null) {
                this.startThreat(intruder, WARN_TIME);   // a warning only: no charge follows
                this.warnCooldown = 100;
            }
        }

        if (this.sprayTicks > 0) {
            this.tickSpray(level);
        } else if (target == null && !this.isThreatening()) {
            if (this.hasWater()) {
                if ((this.tickCount + this.getId()) % 10 == 0) this.lookForFire(level);
            } else if (!this.isNoAi() && this.random.nextInt(1500) == 0 && this.dustWeather(level)) {
                this.startDust();
            }
        }

        // drinking: standing in water or right next to it fills the trunk
        if (!this.hasWater() && this.sprayTicks == 0 && this.tickCount % 10 == 0) {
            if (this.isInWater() || this.waterNearby(level)) {
                this.drinkTicks += 10;
                if (this.drinkTicks >= DRINK_TIME) {
                    this.fillTrunk();
                    this.playSound(SoundEvents.GENERIC_DRINK.value(), 1.0F, 0.6F);
                    Vec3 tip = this.trunkTip(false);
                    level.sendParticles(ParticleTypes.SPLASH, tip.x, this.getY() + 0.2, tip.z, 12, 0.3, 0.1, 0.3, 0.0);
                }
            } else {
                this.drinkTicks = 0;
            }
        }
    }

    /** Someone burning nearby (or a fire to put out) when it has water: spray it. */
    private void lookForFire(ServerLevel level) {
        if (this.isOnFire()) {
            this.startSpray(this, null);
            return;
        }
        List<LivingEntity> burning = level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(SHOWER_RANGE),
                e -> e != this && e.isAlive() && e.isOnFire() && !(e instanceof Enemy) && !e.isSpectator()
                        && this.distanceToSqr(e) <= SHOWER_RANGE * SHOWER_RANGE && this.hasLineOfSight(e));
        LivingEntity best = null;
        for (LivingEntity e : burning) {
            if (best == null || this.distanceToSqr(e) < this.distanceToSqr(best)) best = e;
        }
        if (best != null) {
            this.startSpray(best, null);
            return;
        }
        if ((this.tickCount + this.getId()) % 60 == 0 && Griefing.allowed(level)) {
            BlockPos fire = this.nearestFire(level);
            if (fire != null) this.startSpray(null, Vec3.atCenterOf(fire));
        }
    }

    private void startSpray(@Nullable LivingEntity target, @Nullable Vec3 at) {
        this.entityData.set(WATER, false);            // the whole trunkful goes in one jet
        this.entityData.set(SPRAYING, true);
        this.sprayTicks = SPRAY_TIME;
        this.dusting = false;
        this.sprayTarget = target;
        this.sprayAt = at;
        this.getNavigation().stop();
        this.playSound(SoundEvents.GENERIC_SPLASH, 1.0F, 0.7F);
    }

    private void startDust() {
        this.entityData.set(SPRAYING, true);
        this.sprayTicks = SPRAY_TIME;
        this.dusting = true;
        this.sprayTarget = null;
        this.sprayAt = null;
        this.getNavigation().stop();
        this.playSound(SoundEvents.SAND_BREAK, 1.0F, 0.6F);
    }

    private void tickSpray(ServerLevel level) {
        int age = SPRAY_TIME - --this.sprayTicks;
        Vec3 tip = this.trunkTip(true);
        if (this.dusting) {
            // red dust flung up and over its back
            if (age >= 3 && age <= 15) {
                Vec3 back = this.position().add(0, this.getBbHeight() + 0.2, 0);
                level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.RED_SAND.defaultBlockState()),
                        back.x, back.y, back.z, 6, 0.6 * this.getAgeScale(), 0.2, 0.8 * this.getAgeScale(), 0.0);
                if (age % 4 == 0) level.sendParticles(ParticleTypes.DUST_PLUME, tip.x, tip.y, tip.z, 2, 0.2, 0.2, 0.2, 0.02);
            }
        } else {
            Vec3 aim = this.sprayTarget != null && this.sprayTarget != this
                    ? this.sprayTarget.position().add(0, this.sprayTarget.getBbHeight() * 0.6, 0)
                    : this.sprayAt != null ? this.sprayAt : this.position().add(0, this.getBbHeight() + 0.3, 0);
            if (this.sprayTarget != this) this.faceTowards(aim);
            // the jet: an arc of water from the trunk to the target while the trunkful lasts
            if (age <= SPRAY_HIT + 6) {
                for (int i = 1; i <= 8; i++) {
                    double f = i / 8.0;
                    Vec3 pt = tip.lerp(aim, f).add(0, Math.sin(f * Math.PI) * 0.7, 0);
                    level.sendParticles(ParticleTypes.SPLASH, pt.x, pt.y, pt.z, 2, 0.06, 0.06, 0.06, 0.0);
                }
            }
            if (age == SPRAY_HIT) this.douse(level, aim);
        }
        if (this.sprayTicks <= 0) {
            this.entityData.set(SPRAYING, false);
            this.sprayTarget = null;
            this.sprayAt = null;
            this.dusting = false;
        }
    }

    /** The jet lands: everything burning around the aim point (and itself) goes out, and so do the fires near it. */
    private void douse(ServerLevel level, Vec3 aim) {
        level.sendParticles(ParticleTypes.SPLASH, aim.x, aim.y, aim.z, 40, 0.5, 0.4, 0.5, 0.0);
        level.sendParticles(ParticleTypes.FALLING_WATER, aim.x, aim.y + 0.5, aim.z, 12, 0.5, 0.2, 0.5, 0.0);
        boolean steam = false;
        if (this.sprayTarget != null && this.sprayTarget.isOnFire()) {
            this.sprayTarget.extinguishFire();
            steam = true;
        }
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, AABB.ofSize(aim, 5.0, 5.0, 5.0),
                e -> e.isOnFire() && !(e instanceof Enemy))) {
            e.extinguishFire();
            steam = true;
        }
        if (this.isOnFire()) {
            this.extinguishFire();
            steam = true;
        }
        if (Griefing.allowed(level)) {
            int r = Mth.ceil(FIRE_RANGE);
            BlockPos origin = this.blockPosition();
            for (BlockPos pos : BlockPos.betweenClosed(origin.offset(-r, -3, -r), origin.offset(r, 3, r))) {
                if (pos.distSqr(origin) <= FIRE_RANGE * FIRE_RANGE && this.canPutOut(level, pos)) {
                    level.removeBlock(pos, false);
                    level.sendParticles(ParticleTypes.CLOUD, pos.getX() + 0.5, pos.getY() + 0.3, pos.getZ() + 0.5, 3, 0.2, 0.1, 0.2, 0.01);
                    steam = true;
                }
            }
        }
        if (steam) {
            level.sendParticles(ParticleTypes.CLOUD, aim.x, aim.y + 0.3, aim.z, 8, 0.4, 0.3, 0.4, 0.02);
            this.playSound(SoundEvents.FIRE_EXTINGUISH, 0.8F, 1.0F);
        }
    }

    /** An ordinary fire block: not one burning for ever on netherrack and the like (never campfires). */
    private boolean canPutOut(ServerLevel level, BlockPos pos) {
        if (!level.getBlockState(pos).is(Blocks.FIRE)) return false;
        BlockState below = level.getBlockState(pos.below());
        return !below.is(BlockTags.INFINIBURN_OVERWORLD) && !below.is(BlockTags.INFINIBURN_NETHER) && !below.is(BlockTags.INFINIBURN_END);
    }

    private @Nullable BlockPos nearestFire(ServerLevel level) {
        int r = Mth.ceil(FIRE_RANGE);
        BlockPos origin = this.blockPosition(), best = null;
        for (BlockPos pos : BlockPos.betweenClosed(origin.offset(-r, -3, -r), origin.offset(r, 3, r))) {
            if (pos.distSqr(origin) <= FIRE_RANGE * FIRE_RANGE && this.canPutOut(level, pos)
                    && (best == null || pos.distSqr(origin) < best.distSqr(origin))) {
                best = pos.immutable();
            }
        }
        return best;
    }

    /** Where the trunk's tip is: hanging in front of it, or (spraying) raised high over its head. */
    private Vec3 trunkTip(boolean raised) {
        float s = this.getAgeScale();
        Vec3 fwd = Vec3.directionFromRotation(0.0F, this.yBodyRot);
        return this.position().add(fwd.scale((raised ? 2.2 : 2.0) * s)).add(0, (raised ? 2.5 : 0.4) * s, 0);
    }

    /** Turns body and head straight toward a point (works without AI as well). */
    private void faceTowards(Vec3 at) {
        double dx = at.x - this.getX(), dz = at.z - this.getZ();
        if (dx * dx + dz * dz < 1.0E-4) return;
        float yaw = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90.0F;
        this.setYRot(yaw);
        this.setYBodyRot(yaw);
        this.setYHeadRot(yaw);
    }

    /** Hot savanna sun, no rain, the afternoon. */
    private boolean dustWeather(ServerLevel level) {
        long time = level.getOverworldClockTime() % 24000L;
        BlockPos pos = this.blockPosition();
        return time >= 6000L && time <= 12000L && !level.isRaining() && !this.isInWater() && this.onGround()
                && level.canSeeSky(pos) && level.getBiome(pos).value().getBaseTemperature() > 1.0F;
    }

    private boolean waterNearby(ServerLevel level) {
        BlockPos base = this.blockPosition();
        int r = Mth.ceil(this.getBbWidth() / 2.0F) + 1;
        for (BlockPos pos : BlockPos.betweenClosed(base.offset(-r, -1, -r), base.offset(r, 0, r))) {
            if (level.getFluidState(pos).is(FluidTags.WATER)) return true;
        }
        return false;
    }

    /** A survival player within 4 blocks of one of the calves near this elephant. */
    private @Nullable Player calfIntruder(ServerLevel level) {
        for (Elephant calf : level.getEntitiesOfClass(Elephant.class, this.getBoundingBox().inflate(12.0), Elephant::isBaby)) {
            Player p = level.getNearestPlayer(calf.getX(), calf.getY(), calf.getZ(), 4.0, EntitySelector.NO_CREATIVE_OR_SPECTATOR);
            if (p != null) return p;
        }
        return null;
    }

    private void startThreat(LivingEntity at, int ticks) {
        this.threatAt = at;
        this.threatTicks = ticks;
        this.entityData.set(THREATENING, true);
        this.getNavigation().stop();
        this.trumpet();
    }

    private void trumpet() {
        float pitch = this.isBaby() ? 1.5F : 0.75F + this.random.nextFloat() * 0.1F;
        this.playSound(SoundEvents.NOTE_BLOCK_TRUMPET.value(), 3.0F, pitch);
        this.playSound(SoundEvents.RAVAGER_ROAR, 0.7F, pitch * 2.0F);
    }

    // -- fighting ----------------------------------------------------------------------------------
    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        // flares its ears and trumpets at once; the charge follows (with AI)
        if (hurt && this.isAlive() && !this.isBaby() && !this.isThreatening() && this.getTarget() == null
                && source.getEntity() instanceof LivingEntity attacker && attacker != this && attacker.isAlive()) {
            this.startThreat(attacker, THREAT_TIME);
        }
        if (hurt && this.isBaby() && this.isAlive()) this.trumpet();   // a calf squeals for its herd
        return hurt;
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        if (target != null && this.isBaby()) return;   // calves only ever run
        // a herd elephant called in (or one just hurt) trumpets before it charges
        if (target != null && this.getTarget() == null && !this.isThreatening()) this.startThreat(target, THREAT_TIME);
        super.setTarget(target);
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            // the big launch: up and away
            Vec3 away = target.position().subtract(this.position()).multiply(1, 0, 1);
            away = away.lengthSqr() < 1.0E-4 ? Vec3.directionFromRotation(0.0F, this.getYRot()) : away.normalize();
            target.push(away.x * 1.1, 0.6, away.z * 1.1);
            target.needsSync = true;
            this.playSound(SoundEvents.RAVAGER_ATTACK, 1.0F, 0.8F);
        }
        return hit;
    }

    // -- feeding and the water bucket ---------------------------------------------------------------
    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.is(Items.WATER_BUCKET) && !this.hasWater()) {
            if (!this.level().isClientSide()) this.fillTrunk();
            this.playSound(SoundEvents.BUCKET_EMPTY, 1.0F, 1.0F);
            player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(Items.BUCKET)));
            return InteractionResult.SUCCESS;
        }
        if (this.isFood(stack) && this.getHealth() < this.getMaxHealth()) {
            if (!this.level().isClientSide()) {
                this.usePlayerItem(player, hand, stack);
                this.heal(4.0F);
                this.playSound(SoundEvents.GENERIC_EAT.value(), 1.0F, 0.7F);
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.MELON_SLICE); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.ELEPHANT.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Water", this.hasWater());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(WATER, input.getBooleanOr("Water", false));
    }

    // -- sounds: the sniffer's big-animal voice, pitched down to a rumble ----------------------------
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.SNIFFER_IDLE; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.SNIFFER_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.SNIFFER_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.SNIFFER_STEP, 0.5F, this.isBaby() ? 1.1F : 0.6F); }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.3F : 0.6F) + this.random.nextFloat() * 0.1F; }
    @Override public int getAmbientSoundInterval() { return 200; }

    /** While it trumpets or sprays it stands its ground, facing whatever it's at. */
    private class HoldGoal extends Goal {
        HoldGoal() {
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK, Goal.Flag.JUMP));
        }

        @Override public boolean canUse() { return Elephant.this.threatTicks > 0 || Elephant.this.sprayTicks > 0; }
        @Override public void start() { Elephant.this.getNavigation().stop(); }
        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            Elephant.this.getNavigation().stop();
            if (Elephant.this.threatAt != null) Elephant.this.getLookControl().setLookAt(Elephant.this.threatAt, 30.0F, 30.0F);
        }
    }

    /** With an empty trunk it now and then walks down to the nearest water's edge to drink. */
    private class SeekWaterGoal extends MoveToBlockGoal {
        SeekWaterGoal() {
            super(Elephant.this, 1.0, 16, 3);
        }

        @Override
        public boolean canUse() {
            return !Elephant.this.hasWater() && !Elephant.this.isBaby() && Elephant.this.getTarget() == null && super.canUse();
        }

        @Override
        public boolean canContinueToUse() {
            return !Elephant.this.hasWater() && Elephant.this.getTarget() == null && super.canContinueToUse();
        }

        @Override
        protected int nextStartTick(PathfinderMob mob) {
            return reducedTickDelay(600 + mob.getRandom().nextInt(600));
        }

        /** A dry block with open air above and water beside it: the bank to drink from. */
        @Override
        protected boolean isValidTarget(LevelReader level, BlockPos pos) {
            if (level.getFluidState(pos).is(FluidTags.WATER) || !level.getBlockState(pos.above()).isAir()
                    || !level.getBlockState(pos).isFaceSturdy(level, pos, Direction.UP)) return false;
            for (BlockPos n : List.of(pos.north(), pos.south(), pos.east(), pos.west())) {
                if (level.getFluidState(n).is(FluidTags.WATER)) return true;
            }
            return false;
        }
    }
}
