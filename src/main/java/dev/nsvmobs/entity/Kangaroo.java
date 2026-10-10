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
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A red kangaroo of the badlands and windswept savannas. It bounds everywhere in long hops and lies
 * about on its side, propped on an elbow. A doe carries her joey in her pouch: when she's frightened
 * (hurt, or a player sprints close by) or bounding off, it hops in, head and paws poking out, and hops
 * out again once she's been calm for a while. A buck boxes: hit one and it rears up on its tail and
 * fights back with quick jabs and, every third blow, a two-footed kick that launches you. Does bound
 * away instead. Bucks sometimes spar with each other for fun, no harm done.
 */
public class Kangaroo extends Animal {
    public static final int NONE = 0, RIGHT_JAB = 1, LEFT_JAB = 2, KICK = 3;
    private static final EntityDataAccessor<Boolean> BUCK = SynchedEntityData.defineId(Kangaroo.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> BOXING = SynchedEntityData.defineId(Kangaroo.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> LOUNGING = SynchedEntityData.defineId(Kangaroo.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Byte> ACTION = SynchedEntityData.defineId(Kangaroo.class, EntityDataSerializers.BYTE);
    static final double BUCK_HEALTH = 30.0, DOE_HEALTH = 24.0;
    static final float JAB_DAMAGE = 3.0F, KICK_DAMAGE = 7.0F;
    /** Each blow's length and the tick it lands on (the kick is telegraphed by rocking back first). */
    static final int JAB_TICKS = 8, JAB_HIT = 3, KICK_TICKS = 16, KICK_HIT = 8;
    /** How long a fright lasts (10 s) and how long the joey waits after it before hopping out (10 s). */
    static final int FRIGHT_TICKS = 200, CALM_TICKS = 200;
    /** Where a joey rides: the pouch, low on the doe's belly (blocks up and forward). */
    static final double POUCH_UP = 0.0, POUCH_FORWARD = 0.2;
    private int actionStart;
    private int blows;
    private int blowCooldown;
    private int boxTicks;
    private int idleBoxTicks;
    private int frightTicks;
    private int calmTicks;
    private int sparTicks;
    private int sparCooldown;
    private @Nullable Kangaroo sparPartner;

    public Kangaroo(EntityType<? extends Kangaroo> type, Level level) {
        super(type, level);
        // buck or doe for life, decided when it's born (the client gets it from the server)
        if (!level.isClientSide()) this.setBuck(this.random.nextBoolean());
        this.sparCooldown = 1200 + this.random.nextInt(2400);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, DOE_HEALTH)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.ATTACK_DAMAGE, JAB_DAMAGE)
                .add(Attributes.STEP_HEIGHT, 1.0)
                .add(Attributes.FOLLOW_RANGE, 16.0);
    }

    /** Sand, red sand, terracotta, coarse dirt, dirt or grass underfoot (the badlands have no grass), in daylight. */
    public static boolean checkSpawnRules(EntityType<Kangaroo> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        return (below.is(BlockTags.SAND) || below.is(BlockTags.TERRACOTTA) || below.is(Blocks.COARSE_DIRT) || below.is(Blocks.DIRT)
                || below.is(BlockTags.ANIMALS_SPAWNABLE_ON)) && isBrightEnoughToSpawn(level, pos);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(BUCK, false);
        builder.define(BOXING, false);
        builder.define(LOUNGING, false);
        builder.define(ACTION, (byte) NONE);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 2.0) {
            @Override public boolean canUse() { return !Kangaroo.this.isBoxing() && super.canUse(); }
        });
        this.goalSelector.addGoal(2, new BoxGoal());
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.2, this::isFood, false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.2));
        this.goalSelector.addGoal(6, new SparGoal());
        this.goalSelector.addGoal(7, new LoungeGoal());
        this.goalSelector.addGoal(8, new WaterAvoidingRandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(9, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(10, new RandomLookAroundGoal(this));
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData groupData) {
        // a mob of kangaroos often has a joey or two with it
        return super.finalizeSpawn(level, difficulty, reason, groupData == null ? new AgeableMobGroupData(0.3F) : groupData);
    }

    // -- state ---------------------------------------------------------------------------------------

    /** A buck (red, boxes); otherwise a doe (blue-grey, has a pouch). Joeys are one or the other too. */
    public boolean isBuck() {
        return this.entityData.get(BUCK);
    }

    /** Makes it a buck or a doe (health 30 or 24, keeping it at full health if it was). */
    public void setBuck(boolean buck) {
        this.entityData.set(BUCK, buck);
        AttributeInstance health = this.getAttribute(Attributes.MAX_HEALTH);
        if (health != null) {
            boolean full = this.getHealth() >= this.getMaxHealth();
            health.setBaseValue(buck ? BUCK_HEALTH : DOE_HEALTH);
            if (full || this.getHealth() > this.getMaxHealth()) this.setHealth(this.getMaxHealth());
        }
    }

    /** Reared up on its tail to fight (or to spar). */
    public boolean isBoxing() {
        return this.entityData.get(BOXING);
    }

    /** Lying on its side, propped on an elbow. */
    public boolean isLounging() {
        return this.entityData.get(LOUNGING);
    }

    void setLounging(boolean lounging) {
        if (lounging != this.isLounging()) this.entityData.set(LOUNGING, lounging);
    }

    /** The blow being thrown: {@link #NONE}, {@link #RIGHT_JAB}, {@link #LEFT_JAB} or {@link #KICK}. */
    public int action() {
        return this.entityData.get(ACTION);
    }

    /** Ticks (with partial) since the current blow began (either side). */
    public float actionAge(float partialTick) {
        return this.tickCount - this.actionStart + partialTick;
    }

    void setAction(int action) {
        this.entityData.set(ACTION, (byte) action);
        this.actionStart = this.tickCount;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (ACTION.equals(key)) this.actionStart = this.tickCount;
    }

    /** Hurt in the last 10 s, or a player is sprinting within 6 blocks. */
    boolean isFrightened() {
        return this.frightTicks > 0 || this.level().getNearestPlayer(this.getX(), this.getY(), this.getZ(), 6.0,
                e -> e.isSprinting() && !e.isSpectator()) != null;
    }

    /** Bounding along faster than a stroll. */
    boolean isOnTheMove() {
        return this.getDeltaMovement().horizontalDistanceSqr() > 0.15 * 0.15;
    }

    // -- boxing --------------------------------------------------------------------------------------

    void startBoxing(LivingEntity foe) {
        this.endSpar();
        this.setTarget(foe);
        this.boxTicks = 0;
        this.idleBoxTicks = 0;
        this.blows = 0;
        this.blowCooldown = 6;
        this.setLounging(false);
        if (!this.isBoxing()) {
            this.entityData.set(BOXING, true);
            this.getNavigation().stop();
            this.playSound(SoundEvents.GOAT_PREPARE_RAM, 1.0F, this.getVoicePitch() * 1.3F);
        }
    }

    void stopBoxing() {
        this.entityData.set(BOXING, false);
        this.setTarget(null);
        this.sparPartner = null;
        this.sparTicks = 0;
    }

    /** The one it's fighting (or sparring with), if they're still fair game. */
    @Nullable LivingEntity opponent() {
        if (this.sparPartner != null) return this.sparPartner.isAlive() ? this.sparPartner : null;
        LivingEntity t = this.getTarget();
        if (t == null || !t.isAlive() || t instanceof Player p && (p.isCreative() || p.isSpectator())) return null;
        return t;
    }

    /** Throws the next blow: right jab, left jab, then the kick, and round again. */
    void throwBlow() {
        this.blows++;
        int action = this.blows % 3 == 0 ? KICK : this.blows % 3 == 1 ? RIGHT_JAB : LEFT_JAB;
        if (this.sparPartner != null && action == KICK && this.random.nextInt(3) != 0) action = RIGHT_JAB;   // sparring is mostly jabs
        this.setAction(action);
        this.blowCooldown = action == KICK ? KICK_TICKS + 10 : JAB_TICKS + 4 + this.random.nextInt(5);
        if (action == KICK) this.playSound(SoundEvents.GOAT_PREPARE_RAM, 0.8F, this.getVoicePitch() * 1.5F);
    }

    /** The blow lands (if the opponent is still in reach): a jab knocks you back, the kick launches you. */
    private void landBlow(ServerLevel level, boolean kick) {
        LivingEntity o = this.opponent();
        double reach = kick ? 3.0 : 2.6;
        if (o == null || this.distanceToSqr(o) > reach * reach || !this.hasLineOfSight(o)) return;
        float yaw = this.yBodyRot * Mth.DEG_TO_RAD;
        if (this.sparPartner != null) {
            // play-fighting: a soft thump and a nudge
            this.playSound(SoundEvents.PLAYER_ATTACK_NODAMAGE, 0.7F, 1.3F);
            o.push(-Mth.sin(yaw) * 0.15, 0.0, Mth.cos(yaw) * 0.15);
            return;
        }
        DamageSource source = this.damageSources().mobAttack(this);
        if (!o.hurtServer(level, source, kick ? KICK_DAMAGE : JAB_DAMAGE)) return;
        this.setLastHurtMob(o);
        this.idleBoxTicks = 0;
        o.knockback(kick ? 0.8 : 0.6, Mth.sin(yaw), -Mth.cos(yaw), source, kick ? KICK_DAMAGE : JAB_DAMAGE);
        if (kick) o.push(0.0, 0.25, 0.0);
        o.needsSync = true;
        this.playSound(kick ? SoundEvents.GOAT_RAM_IMPACT : SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.0F, kick ? 1.3F : 1.1F);
    }

    // -- sparring ------------------------------------------------------------------------------------

    void startSpar(Kangaroo other, int ticks) {
        for (Kangaroo k : new Kangaroo[]{this, other}) {
            k.sparPartner = k == this ? other : this;
            k.sparTicks = ticks;
            k.blows = 0;
            k.blowCooldown = 10 + k.random.nextInt(10);
            k.entityData.set(BOXING, true);
            k.setLounging(false);
            k.getNavigation().stop();
        }
    }

    void endSpar() {
        Kangaroo other = this.sparPartner;
        if (other == null) return;
        this.sparPartner = null;
        this.sparTicks = 0;
        this.sparCooldown = 2400 + this.random.nextInt(3600);
        if (this.getTarget() == null) this.entityData.set(BOXING, false);
        if (other.sparPartner == this) other.endSpar();
    }

    // -- the pouch -----------------------------------------------------------------------------------

    /** The nearest grown doe within 8 blocks with room in her pouch. */
    private @Nullable Kangaroo mother(ServerLevel level) {
        List<Kangaroo> does = level.getEntitiesOfClass(Kangaroo.class, this.getBoundingBox().inflate(8.0),
                k -> k.isAlive() && !k.isBaby() && !k.isBuck() && !k.isVehicle() && k.distanceToSqr(this) <= 64.0);
        Kangaroo best = null;
        for (Kangaroo k : does) {
            if (best == null || k.distanceToSqr(this) < best.distanceToSqr(this)) best = k;
        }
        return best;
    }

    /** A joey hops into its mother's pouch when she's frightened or bounding off, and out once she's calm. */
    private void tickPouch(ServerLevel level) {
        Entity vehicle = this.getVehicle();
        if (vehicle instanceof Kangaroo mother) {
            if (!this.isBaby() || !mother.isAlive() || mother.isBaby()) {
                this.stopRiding();
            } else if (mother.isFrightened() || mother.isOnTheMove()) {
                this.calmTicks = 0;
            } else if (++this.calmTicks >= CALM_TICKS) {
                this.calmTicks = 0;
                this.stopRiding();
                this.playSound(SoundEvents.RABBIT_JUMP, 0.6F, 1.6F);
            }
            return;
        }
        if (vehicle != null || !this.isBaby() || this.tickCount % 5 != 0) return;
        Kangaroo mother = this.mother(level);
        if (mother != null && (mother.isFrightened() || mother.isOnTheMove()) && this.startRiding(mother)) {
            this.calmTicks = 0;
            this.setLounging(false);
            mother.setLounging(false);
            this.playSound(SoundEvents.RABBIT_JUMP, 0.6F, 1.6F);
        }
    }

    @Override
    protected boolean canAddPassenger(Entity passenger) {
        // one joey, in a grown doe's pouch; nobody else rides a kangaroo
        return passenger instanceof Kangaroo k && k.isBaby() && !this.isBaby() && !this.isBuck() && this.getPassengers().isEmpty();
    }

    /** A joey never steers its mother. */
    @Override
    public @Nullable LivingEntity getControllingPassenger() {
        return null;
    }

    @Override
    protected Vec3 getPassengerAttachmentPoint(Entity passenger, EntityDimensions dimensions, float scale) {
        return new Vec3(0.0, POUCH_UP * scale, POUCH_FORWARD * scale).yRot(-this.yBodyRot * Mth.DEG_TO_RAD);
    }

    @Override
    protected void positionRider(Entity passenger, Entity.MoveFunction moveFunction) {
        super.positionRider(passenger, moveFunction);
        // the joey faces the way its mother does
        if (passenger instanceof LivingEntity joey) {
            joey.setYBodyRot(this.yBodyRot);
            joey.yBodyRotO = this.yBodyRotO;
        }
    }

    // -- ticking -------------------------------------------------------------------------------------

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || !this.isAlive()) return;
        if (this.frightTicks > 0) this.frightTicks--;
        if (this.blowCooldown > 0) this.blowCooldown--;
        if (this.sparCooldown > 0) this.sparCooldown--;

        // a blow in progress always plays out, AI or not
        int action = this.action();
        if (action != NONE) {
            int age = this.tickCount - this.actionStart;
            if (age == (action == KICK ? KICK_HIT : JAB_HIT)) this.landBlow(level, action == KICK);
            if (age >= (action == KICK ? KICK_TICKS : JAB_TICKS)) this.setAction(NONE);
        }

        if (this.sparPartner != null) {
            Kangaroo p = this.sparPartner;
            if (--this.sparTicks <= 0 || !p.isAlive() || p.sparPartner != this || this.distanceToSqr(p) > 12 * 12) this.endSpar();
        } else if (this.isBoxing()) {
            // the fight lasts at least 3 s; it ends when the foe is gone, out of reach or untouched for 30 s
            this.boxTicks++;
            this.idleBoxTicks++;
            LivingEntity foe = this.opponent();
            boolean over = foe == null || this.distanceToSqr(foe) > 16 * 16 || this.idleBoxTicks > 600;
            if (over && this.boxTicks >= 60) this.stopBoxing();
        }
        if (this.isBoxing() && (this.isBaby() || !this.isBuck())) this.stopBoxing();
        if (this.isLounging() && (this.isVehicle() || this.isPassenger() || this.isInWater())) this.setLounging(false);

        this.tickPouch(level);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && this.isAlive()) {
            this.frightTicks = FRIGHT_TICKS;
            this.setLounging(false);
            // a buck rears up and boxes whoever hit it; a doe (or a joey) bounds off instead
            if (!this.isBaby() && this.isBuck() && source.getEntity() instanceof LivingEntity foe && foe != this) {
                this.startBoxing(foe);
            }
        }
        return hurt;
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        // only bucks fight, and only back
        if (target != null && (this.isBaby() || !this.isBuck())) return;
        super.setTarget(target);
    }

    // -- breeding, saving, sounds --------------------------------------------------------------------

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.WHEAT); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.KANGAROO.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Buck", this.isBuck());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.setBuck(input.getBooleanOr("Buck", this.isBuck()));
    }

    @Override protected SoundEvent getAmbientSound() { return this.isLounging() ? null : SoundEvents.CAMEL_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.CAMEL_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.CAMEL_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.RABBIT_JUMP, 0.25F, this.isBaby() ? 1.2F : 0.6F); }
    @Override protected float nextStep() { return this.moveDist + 1.5F; }   // a thump per bound, not per block
    @Override public int getAmbientSoundInterval() { return 200; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.8F : this.isBuck() ? 1.2F : 1.4F) + this.random.nextFloat() * 0.1F; }
    @Override protected float getSoundVolume() { return 0.6F; }

    /**
     * Fights its opponent: hops in close, rears up face to face and throws its blows (the blow itself
     * plays out in {@link #aiStep}, so it always finishes).
     */
    final class BoxGoal extends Goal {
        BoxGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override public boolean canUse() { return Kangaroo.this.isBoxing() && Kangaroo.this.opponent() != null; }
        @Override public boolean canContinueToUse() { return this.canUse(); }
        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void stop() {
            Kangaroo.this.getNavigation().stop();
        }

        @Override
        public void tick() {
            Kangaroo k = Kangaroo.this;
            LivingEntity o = k.opponent();
            if (o == null) return;
            k.getLookControl().setLookAt(o, 30.0F, 30.0F);
            double close = k.sparPartner != null ? 1.6 : 1.9;
            if (k.distanceToSqr(o) > close * close) {
                if (k.action() == NONE) k.getNavigation().moveTo(o, k.sparPartner != null ? 1.0 : 1.4);
                return;
            }
            // face to face
            k.getNavigation().stop();
            float yaw = (float) (Mth.atan2(o.getZ() - k.getZ(), o.getX() - k.getX()) * Mth.RAD_TO_DEG) - 90.0F;
            k.setYRot(Mth.approachDegrees(k.getYRot(), yaw, 20.0F));
            k.setYBodyRot(k.getYRot());
            if (k.action() == NONE && k.blowCooldown <= 0 && k.hasLineOfSight(o)) {
                k.throwBlow();
                k.swingForAttack(InteractionHand.MAIN_HAND);
            }
        }
    }

    /** Now and then two grown bucks square up and spar for a few seconds (the BoxGoal runs the bout). */
    final class SparGoal extends Goal {
        private @Nullable Kangaroo rival;

        @Override
        public boolean canUse() {
            Kangaroo k = Kangaroo.this;
            if (k.isBaby() || !k.isBuck() || k.isBoxing() || k.sparCooldown > 0 || k.getTarget() != null || !k.onGround()
                    || k.isVehicle() || k.random.nextInt(this.reducedTickDelay(400)) != 0) return false;
            this.rival = null;
            for (Kangaroo other : k.level().getEntitiesOfClass(Kangaroo.class, k.getBoundingBox().inflate(8.0))) {
                if (other != k && other.isAlive() && other.isBuck() && !other.isBaby() && !other.isBoxing() && other.getTarget() == null
                        && other.sparCooldown <= 0 && !other.isLounging() && !other.isVehicle()) {
                    this.rival = other;
                    break;
                }
            }
            return this.rival != null;
        }

        @Override public boolean canContinueToUse() { return false; }

        @Override
        public void start() {
            if (this.rival != null) Kangaroo.this.startSpar(this.rival, 100 + Kangaroo.this.random.nextInt(80));
            this.rival = null;
        }
    }

    /** On the ground and at ease, it often lies down on its side for a while. */
    final class LoungeGoal extends Goal {
        private int ticks;

        LoungeGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        private boolean atEase() {
            Kangaroo k = Kangaroo.this;
            return k.onGround() && !k.isInWater() && !k.isBoxing() && k.getTarget() == null && !k.isPassenger() && !k.isVehicle()
                    && !k.isFrightened();
        }

        @Override
        public boolean canUse() {
            return Kangaroo.this.random.nextInt(this.reducedTickDelay(500)) == 0 && this.atEase();
        }

        @Override
        public boolean canContinueToUse() {
            return this.ticks > 0 && Kangaroo.this.isLounging() && this.atEase();
        }

        @Override
        public void start() {
            this.ticks = 400 + Kangaroo.this.random.nextInt(800);
            Kangaroo.this.getNavigation().stop();
            Kangaroo.this.setLounging(true);
        }

        @Override
        public void tick() {
            this.ticks--;
            Kangaroo.this.getNavigation().stop();
        }

        @Override
        public void stop() {
            Kangaroo.this.setLounging(false);
        }
    }
}
