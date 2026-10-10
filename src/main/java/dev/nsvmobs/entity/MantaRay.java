package dev.nsvmobs.entity;

import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PlayerRideableJumping;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.behavior.BehaviorUtils;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.TryFindLiquidGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraft.world.entity.animal.fish.WaterAnimal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A great manta ray of the warm seas. It glides in slow, wide loops with lazy wing beats, near the
 * surface by day and deeper at night, and now and then races up and leaps clear of the water. Swim
 * up and use it with an empty hand to grab on: hold forward and it swims where you look, faster than
 * any swimmer; let go and it glides to a stop; jump (charge the bar) for a powerful stroke, or at the
 * surface a breach with you aboard. Crouch to let go. Gentle: it never attacks, and speeds away when
 * hurt. Out of the water it dries out like a dolphin, and drops its rider.
 * <p>Ridden swimming is simulated where vanilla simulates ridden movement, on the rider's client
 * ({@link #travel}); the server keeps {@link #BREACHING} in step with the jumps and movement it sees.
 * A breach is ballistic (it bursts out through the surface and arcs back down), and runs in
 * {@code aiStep} too, so {@link #breach()} also works on a NoAI manta.
 */
public class MantaRay extends WaterAnimal implements PlayerRideableJumping {
    /** Airborne from a breach (the server's view, synced to every client). */
    private static final EntityDataAccessor<Boolean> BREACHING = SynchedEntityData.defineId(MantaRay.class, EntityDataSerializers.BOOLEAN);
    /** Ridden top speed (blocks per tick): a sprint-swimming player does about 0.2. */
    private static final double RIDE_SPEED = 0.6;
    /** How fast the ridden velocity eases toward where the rider steers, and toward a stop. */
    private static final double ACCEL = 0.07, GLIDE = 0.035;
    /** Within this much water above its back a leap carries it out through the surface. */
    private static final double BREACH_DEPTH = 2.5;
    private static final int MAX_MOISTNESS = 2400;
    private int moistness = MAX_MOISTNESS;
    /** This side's leap in progress: ticks since it launched (0 = none). */
    private int leapTicks;
    private boolean leftWater;
    /** The rider's released jump, waiting for {@link #tickRidden} (0 = none). */
    private float pendingStroke;
    private int strokeCooldown, breachCooldown, landTicks, breachAge;
    private boolean breachAirborne;

    public MantaRay(EntityType<? extends MantaRay> type, Level level) {
        super(type, level);
        // slow, wide turns; it cruises at about 0.15 blocks a tick (travelInWater) and barely crawls on land
        this.moveControl = new SmoothSwimmingMoveControl<>(this, 85, 10, 0.015F, 0.1F, false);
        this.lookControl = new SmoothSwimmingLookControl(this, 10);
        this.breachCooldown = 200 + this.random.nextInt(600);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 30.0).add(Attributes.MOVEMENT_SPEED, 1.0);
    }

    /** In open water within 25 blocks of sea level, with water above it too. */
    public static boolean checkSpawnRules(EntityType<MantaRay> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        int sea = level.getSeaLevel();
        return pos.getY() >= sea - 25 && pos.getY() <= sea - 2
                && level.getFluidState(pos).is(FluidTags.WATER)
                && level.getFluidState(pos.below()).is(FluidTags.WATER)
                && level.getFluidState(pos.above()).is(FluidTags.WATER);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WaterBoundPathNavigation(this, level);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(BREACHING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new TryFindLiquidGoal(this, FluidTags.WATER));
        this.goalSelector.addGoal(1, new FleeGoal());
        this.goalSelector.addGoal(3, new BreachGoal());
        this.goalSelector.addGoal(4, new CruiseGoal());
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Moistness", this.moistness);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.moistness = input.getIntOr("Moistness", MAX_MOISTNESS);
    }

    // -- breaching ---------------------------------------------------------------------------------
    /** Airborne from a breach. True on every client (synced), and at once on the rider's own client. */
    public boolean isBreaching() {
        return this.entityData.get(BREACHING) || this.leapTicks > 0;
    }

    /**
     * Leaps now: near the surface it shoots up and out of the water and arcs back down with a big
     * splash; deeper down it's a strong upward stroke instead.
     */
    public void breach() {
        if (this.leapTicks > 0) return;
        if (this.depth() <= BREACH_DEPTH) {
            this.leap(1.0F);
            if (!this.level().isClientSide()) {
                this.startBreach();
                this.needsSync = true;
            }
        } else {
            this.upStroke(1.0F);
        }
    }

    /** Blocks of water above its back up to an open surface: negative once its back is out of the
     *  water, large under a ceiling or very deep down. */
    double depth() {
        Level level = this.level();
        double back = this.getY() + this.getBbHeight();
        BlockPos.MutableBlockPos p = BlockPos.containing(this.getX(), back, this.getZ()).mutable();
        for (int i = 0; i < 16; i++) {
            FluidState fluid = level.getFluidState(p);
            if (!fluid.is(FluidTags.WATER)) {
                if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) return 99.0;   // a ceiling, not a surface
                BlockPos below = p.below();
                return below.getY() + level.getFluidState(below).getHeight(level, below) - back;
            }
            p.move(0, 1, 0);
        }
        return 99.0;
    }

    /** The leap itself: up through the surface (two to four blocks high, with the jump charge
     *  0..1) with a forward push, keeping any speed it already had. */
    private void leap(float scale) {
        float yaw = this.getYRot() * Mth.DEG_TO_RAD;
        Vec3 v = this.getDeltaMovement();
        double ahead = Math.max(0.15 + 0.15 * scale, -Mth.sin(yaw) * v.x + Mth.cos(yaw) * v.z);
        this.setDeltaMovement(-Mth.sin(yaw) * ahead, 0.5 + 0.3 * scale, Mth.cos(yaw) * ahead);
        this.leapTicks = 1;
        this.leftWater = false;
        this.playSound(SoundEvents.DOLPHIN_JUMP, 1.0F, 0.6F);
    }

    /** A deep, strong downstroke of the wings that drives it up and forward. */
    private void upStroke(float scale) {
        float yaw = this.getYRot() * Mth.DEG_TO_RAD;
        double ahead = 0.1 + 0.15 * scale;
        this.addDeltaMovement(new Vec3(-Mth.sin(yaw) * ahead, 0.3 + 0.35 * scale, Mth.cos(yaw) * ahead));
        this.playSound(SoundEvents.DOLPHIN_SWIM, 1.0F, 0.6F);
        if (!this.level().isClientSide()) this.needsSync = true;
    }

    /** Ballistic flight: gravity and air drag, even while it's still rising through the water, so it
     *  bursts out; it ends when it falls back in (or lands, or never got out). */
    private void leapTravel() {
        boolean wet = this.isInWater();
        if (!wet) this.leftWater = true;
        Vec3 v = this.getDeltaMovement();
        this.move(MoverType.SELF, v);
        this.setDeltaMovement(v.x * 0.98, (v.y - 0.08) * 0.98, v.z * 0.98);
        if (v.lengthSqr() > 1.0E-4) this.setXRot((float) (Mth.atan2(-v.y, v.horizontalDistance()) * Mth.RAD_TO_DEG) * 0.8F);
        this.leapTicks++;
        if ((this.leftWater && wet && v.y < 0.0) || this.onGround() || this.leapTicks > 60 || (!this.leftWater && this.leapTicks > 15)) {
            this.leapTicks = 0;
        }
    }

    private void startBreach() {
        this.entityData.set(BREACHING, true);
        this.breachAge = 0;
        this.breachAirborne = false;
    }

    /** The server's view of a breach, from the leap or the movement the rider's client sends. */
    private void breachTick(ServerLevel level) {
        if (!this.entityData.get(BREACHING)) return;
        this.breachAge++;
        boolean wet = this.isInWater();
        if (!wet) this.breachAirborne = true;
        boolean done = this.breachAirborne ? wet || this.onGround() : this.breachAge > 15;
        if (done || this.breachAge > 80) {
            this.entityData.set(BREACHING, false);
            if (this.breachAirborne && wet) this.splashdown(level);
        }
    }

    /** It smacks back down flat on the water: a big splash and a spray of bubbles. */
    private void splashdown(ServerLevel level) {
        double y = this.getY() + this.getBbHeight();
        level.sendParticles(ParticleTypes.SPLASH, this.getX(), y, this.getZ(), 80, 1.3, 0.2, 1.3, 0.3);
        level.sendParticles(ParticleTypes.BUBBLE, this.getX(), this.getY(), this.getZ(), 30, 1.0, 0.3, 1.0, 0.1);
        this.playSound(SoundEvents.GENERIC_SPLASH, 1.6F, 0.7F);
        this.playSound(SoundEvents.DOLPHIN_SPLASH, 1.0F, 0.6F);
    }

    // -- riding ------------------------------------------------------------------------------------
    /** Grab on: an empty main hand, in the water, nobody else aboard. */
    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (hand == InteractionHand.MAIN_HAND && player.getItemInHand(hand).isEmpty() && this.isInWater() && !this.isVehicle()
                && !this.isBreaching() && !player.isSecondaryUseActive()) {
            if (!this.level().isClientSide()) player.startRiding(this);
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    /** Once ridden, the rider's client simulates the movement and the server never travels, so a
     *  leap the server had started would never end there. */
    @Override
    protected void addPassenger(Entity passenger) {
        super.addPassenger(passenger);
        if (!this.level().isClientSide()) this.leapTicks = 0;
    }

    @Override
    public @Nullable LivingEntity getControllingPassenger() {
        return this.getFirstPassenger() instanceof Player player ? player : null;
    }

    /** Turns toward where the rider looks (a graceful arc, not a snap) and pitches with its swim;
     *  a released jump is carried out here, on the side that simulates the movement. */
    @Override
    protected void tickRidden(Player rider, Vec3 input) {
        super.tickRidden(rider, input);
        if (this.isLocalInstanceAuthoritative()) {
            // only the side that simulates the swim steers; the server takes the rider's result as sent
            float yaw = this.getYRot() + Mth.clamp(Mth.wrapDegrees(rider.getYRot() - this.getYRot()) * 0.3F, -15.0F, 15.0F);
            float pitch = this.getXRot();
            if (this.leapTicks == 0) {
                Vec3 v = this.getDeltaMovement();
                float swim = v.lengthSqr() > 0.004 ? (float) (Mth.atan2(-v.y, v.horizontalDistance()) * Mth.RAD_TO_DEG) : 0.0F;
                pitch = Mth.rotLerp(0.25F, pitch, Mth.clamp(swim, -45.0F, 45.0F));
            }
            this.setRot(yaw, pitch);
        }
        this.yRotO = this.yBodyRot = this.yHeadRot = this.getYRot();
        if (this.isLocalInstanceAuthoritative() && this.pendingStroke > 0.0F) {
            if (this.isInWater() && this.leapTicks == 0) {
                if (this.depth() <= BREACH_DEPTH) this.leap(this.pendingStroke);
                else this.upStroke(this.pendingStroke);
            }
            this.pendingStroke = 0.0F;
        }
    }

    @Override
    protected Vec3 getRiddenInput(Player rider, Vec3 selfInput) {
        return this.isInWater() ? new Vec3(rider.xxa * 0.5F, 0.0, rider.zza) : Vec3.ZERO;
    }

    /** Runs wherever movement is simulated: the rider's client while ridden, else the server. */
    @Override
    public void travel(Vec3 input) {
        if (this.leapTicks > 0) {
            this.leapTravel();
        } else if (this.getControllingPassenger() instanceof Player rider && this.isInWater()) {
            this.swimRidden(rider, input);
        } else {
            super.travel(input);
        }
    }

    /** The velocity eases toward where the rider looks while forward is held, and glides to a stop
     *  (drifting up toward the air) when it isn't. It won't break the surface on its own: jump for that. */
    private void swimRidden(Player rider, Vec3 input) {
        float yaw = this.getYRot();
        double forward = input.z, side = input.x;
        double sin = Mth.sin(yaw * Mth.DEG_TO_RAD), cos = Mth.cos(yaw * Mth.DEG_TO_RAD);
        Vec3 target = forward > 0.0
                ? Vec3.directionFromRotation(rider.getXRot(), yaw).scale(RIDE_SPEED * forward)
                : new Vec3(-sin * forward * 0.15, 0.03, cos * forward * 0.15);
        target = target.add(cos * side * 0.2, 0.0, sin * side * 0.2);
        double depth = this.depth();
        if (target.y > 0.0 && depth < 0.15) target = new Vec3(target.x, 0.0, target.z);
        Vec3 v = this.getDeltaMovement();
        v = v.add(target.subtract(v).scale(forward > 0.0 ? ACCEL : GLIDE));
        if (depth < 0.0) {
            v = new Vec3(v.x, Math.min(v.y, 0.0) - 0.02, v.z);   // its back broke the surface: it settles back in
        } else if (depth < 0.15 && v.y > 0.0) {
            v = new Vec3(v.x, v.y * 0.5, v.z);                 // skims along just under the surface
        }
        this.setDeltaMovement(v);
        this.move(MoverType.SELF, v);
    }

    /** Unridden in water: steers in 3D with no sinking, cruising at about 0.15 blocks a tick. */
    @Override
    protected void travelInWater(Vec3 input, double baseGravity, boolean isFalling, double oldY) {
        this.moveRelative(this.getSpeed(), input);
        this.move(MoverType.SELF, this.getDeltaMovement());
        this.setDeltaMovement(this.getDeltaMovement().scale(0.9));
    }

    @Override
    public void onPlayerJump(int amount) {
        if (amount > 0 && this.isInWater()) {
            this.pendingStroke = this.getPlayerJumpPendingScale(amount);
            this.strokeCooldown = 20;
        }
    }

    @Override public boolean canJump() { return this.isInWater() && this.leapTicks == 0; }

    /** Jump released (on the server): a breach at the surface (the rider's client does the leap). */
    @Override
    public void handleStartJump(int jumpScale) {
        this.strokeCooldown = 20;
        if (this.depth() <= BREACH_DEPTH) {
            this.startBreach();
            this.playSound(SoundEvents.DOLPHIN_JUMP, 1.0F, 0.6F);
        } else {
            this.playSound(SoundEvents.DOLPHIN_SWIM, 1.0F, 0.6F);
        }
    }

    @Override public void handleStopJump() {}
    @Override public int getJumpCooldown() { return this.strokeCooldown; }

    @Override
    protected void positionRider(Entity passenger, Entity.MoveFunction moveFunction) {
        super.positionRider(passenger, moveFunction);
        if (passenger instanceof LivingEntity living) living.yBodyRot = this.yBodyRot;
    }

    /** The server's floating-vehicle check leaves a breaching manta alone. */
    @Override public boolean isFlyingVehicle() { return this.isBreaching(); }

    @Override
    public boolean requiresCustomPersistence() {
        return super.requiresCustomPersistence() || this.isVehicle();
    }

    // -- ticking -----------------------------------------------------------------------------------
    @Override
    public void tick() {
        super.tick();
        if (this.strokeCooldown > 0) this.strokeCooldown--;
        if (this.level() instanceof ServerLevel level) {
            this.breachTick(level);
            if (this.breachCooldown > 0) this.breachCooldown--;
            // stranded with a rider for over a second: it drops them
            this.landTicks = this.isVehicle() && !this.isInWater() && !this.isBreaching() ? this.landTicks + 1 : 0;
            if (this.landTicks > 20) {
                this.ejectPassengers();
                this.landTicks = 0;
            }
            if (!this.isNoAi()) this.dryOut(level);
        } else if (this.isInWater() && Mth.lengthSquared(this.getX() - this.xo, this.getZ() - this.zo) > 0.06 && this.random.nextInt(3) == 0) {
            // a trail of bubbles off the wingtips at speed
            float yaw = this.getYRot() * Mth.DEG_TO_RAD;
            double c = Mth.cos(yaw) * 1.3, s = Mth.sin(yaw) * 1.3;
            int sign = this.random.nextBoolean() ? 1 : -1;
            this.level().addParticle(ParticleTypes.BUBBLE, this.getX() + c * sign, this.getY() + 0.25, this.getZ() + s * sign, 0.0, 0.02, 0.0);
        }
    }

    /** Like a dolphin: it stays moist in water or rain and dries out, slowly, on land. */
    private void dryOut(ServerLevel level) {
        if (this.isInWaterOrRain()) {
            this.moistness = MAX_MOISTNESS;
        } else if (--this.moistness <= 0) {
            this.moistness = 0;
            this.hurtServer(level, this.damageSources().dryOut(), 1.0F);
        }
        if (!this.isInWater() && this.onGround() && !this.isVehicle() && this.random.nextInt(60) == 0) {
            // now and then a heavy flop
            this.setDeltaMovement(this.getDeltaMovement().add((this.random.nextFloat() - 0.5F) * 0.15F, 0.25, (this.random.nextFloat() - 0.5F) * 0.15F));
            this.setOnGround(false);
            this.needsSync = true;
            this.playSound(SoundEvents.GUARDIAN_FLOP, 0.8F, 0.6F);
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        // a NoAI manta doesn't travel, but a breach must still play out (the leap runs in travel otherwise)
        if (this.isNoAi() && !this.level().isClientSide()) {
            if (this.leapTicks > 0) this.leapTravel();
            else if (this.getXRot() != 0.0F) this.setXRot(Math.abs(this.getXRot()) < 1.0F ? 0.0F : this.getXRot() * 0.8F);
        }
        if (this.isVehicle() && !this.level().isClientSide()) this.getNavigation().stop();
    }

    /** It breathes water and doesn't suffocate in air: it dries out instead ({@link #dryOut}). */
    @Override
    protected void handleAirSupply(ServerLevel level, int preTickAirSupply) {
        this.setAirSupply(this.getMaxAirSupply());
    }

    @Override public int getMaxHeadXRot() { return 1; }
    @Override public int getMaxHeadYRot() { return 1; }
    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}

    // -- sounds ------------------------------------------------------------------------------------
    @Override protected @Nullable SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.COD_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.COD_DEATH; }
    @Override protected SoundEvent getSwimSound() { return SoundEvents.DOLPHIN_SWIM; }
    @Override protected SoundEvent getSwimSplashSound() { return SoundEvents.DOLPHIN_SPLASH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) {}
    @Override public float getVoicePitch() { return 0.55F + this.random.nextFloat() * 0.1F; }

    // -- goals -------------------------------------------------------------------------------------
    /** Top of the open water above this point (its y), or 32 blocks up if it's that deep. */
    private static double surfaceAbove(Level level, BlockPos from) {
        BlockPos.MutableBlockPos p = from.mutable();
        for (int i = 0; i < 32; i++) {
            if (!level.getFluidState(p).is(FluidTags.WATER)) return p.getY();
            p.move(0, 1, 0);
        }
        return p.getY();
    }

    /** Slow, wide loops toward far-off points: near the surface by day, deeper at night. */
    final class CruiseGoal extends RandomSwimmingGoal {
        CruiseGoal() {
            super(MantaRay.this, 1.0, 20);
        }

        @Override
        public boolean canUse() {
            return !MantaRay.this.isVehicle() && super.canUse();
        }

        @Override
        protected @Nullable Vec3 getPosition() {
            MantaRay m = MantaRay.this;
            double want = m.level().isBrightOutside() ? 2.0 : 9.0;
            Vec3 best = null;
            double bestScore = Double.MAX_VALUE;
            for (int i = 0; i < 5; i++) {
                Vec3 p = BehaviorUtils.getRandomSwimmablePos(m, 16, 6);
                if (p == null) continue;
                double depth = surfaceAbove(m.level(), BlockPos.containing(p)) - p.y;
                double score = Math.abs(depth - want) - Math.sqrt(p.distanceToSqr(m.position())) * 0.15;
                if (score < bestScore) {
                    bestScore = score;
                    best = p;
                }
            }
            return best;
        }
    }

    /** Hurt: it speeds away, as far from whatever hurt it as it can get. */
    final class FleeGoal extends PanicGoal {
        FleeGoal() {
            super(MantaRay.this, 2.2);
        }

        @Override
        public boolean canUse() {
            return !MantaRay.this.isVehicle() && super.canUse();
        }

        @Override
        protected boolean findRandomPosition() {
            MantaRay m = MantaRay.this;
            LivingEntity from = m.getLastHurtByMob();
            Vec3 best = null;
            double bestDist = -1.0;
            for (int i = 0; i < 6; i++) {
                Vec3 p = BehaviorUtils.getRandomSwimmablePos(m, 14, 5);
                if (p == null) continue;
                double d = from != null ? p.distanceToSqr(from.position()) : m.random.nextDouble();
                if (d > bestDist) {
                    bestDist = d;
                    best = p;
                }
            }
            if (best == null) return super.findRandomPosition();
            this.posX = best.x;
            this.posY = best.y;
            this.posZ = best.z;
            return true;
        }
    }

    /** Now and then, with open air above, it races up to the surface and leaps clear of the water. */
    final class BreachGoal extends Goal {
        private int ticks;
        private boolean leapt;

        BreachGoal() {
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            MantaRay m = MantaRay.this;
            if (m.isVehicle() || !m.isInWater() || m.breachCooldown > 0 || m.isBreaching() || m.getLastHurtByMob() != null) return false;
            return m.random.nextInt(reducedTickDelay(300)) == 0 && m.depth() < 6.0;
        }

        @Override
        public void start() {
            MantaRay m = MantaRay.this;
            this.ticks = 0;
            this.leapt = false;
            // race up toward the surface a few blocks ahead
            float yaw = m.getYRot() * Mth.DEG_TO_RAD;
            double top = surfaceAbove(m.level(), m.blockPosition());
            m.getNavigation().moveTo(m.getX() - Mth.sin(yaw) * 6.0, top - 1.5, m.getZ() + Mth.cos(yaw) * 6.0, 2.4);
        }

        @Override
        public boolean canContinueToUse() {
            MantaRay m = MantaRay.this;
            return this.ticks < 100 && !m.isVehicle() && (this.leapt ? m.isBreaching() : m.isInWater());
        }

        @Override
        public void tick() {
            MantaRay m = MantaRay.this;
            this.ticks++;
            if (!this.leapt && m.depth() <= BREACH_DEPTH) {
                m.getNavigation().stop();
                this.leapt = true;
                if (this.clearAhead()) m.breach();
                else this.ticks = 100;   // it would come down on the shore: not here
            }
        }

        /** Open water to come down in: the surface ahead is water, with air above it. */
        private boolean clearAhead() {
            MantaRay m = MantaRay.this;
            float yaw = m.getYRot() * Mth.DEG_TO_RAD;
            int top = (int) surfaceAbove(m.level(), m.blockPosition());
            for (int i = 2; i <= 6; i += 2) {
                BlockPos p = BlockPos.containing(m.getX() - Mth.sin(yaw) * i, top - 1, m.getZ() + Mth.cos(yaw) * i);
                if (!m.level().getFluidState(p).is(FluidTags.WATER) || !m.level().getBlockState(p.above()).isAir()) return false;
            }
            return true;
        }

        @Override
        public void stop() {
            MantaRay.this.breachCooldown = 600 + MantaRay.this.random.nextInt(1200);
        }
    }
}
