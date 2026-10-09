package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.equine.AbstractHorse;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A griffin of the high peaks: an eagle's head, wings and talons on a lion's body. Tame it like a
 * horse (raw meat calms it sooner) and saddle it, and it flies: jump to take off (a longer charge
 * climbs higher), hold forward to fly where you look, tap jump for a strong wing-beat, let go to
 * hover and sink slowly, touch the ground to land. Wild ones prowl the slopes and glide off ledges.
 * Neither it nor its rider ever takes fall damage.
 * <p>Ridden flight is simulated where vanilla simulates ridden movement, on the rider's client
 * ({@link #travel}); the server keeps {@link #FLYING} (and no-gravity, so the vehicle isn't kicked
 * for floating) in step with what it sees.
 */
public class Griffin extends AbstractHorse {
    /** Powered flight with a rider (the server's view, synced to every client). */
    private static final EntityDataAccessor<Boolean> FLYING = SynchedEntityData.defineId(Griffin.class, EntityDataSerializers.BOOLEAN);
    /** Wings spread with nobody at the reins: a wild glide, or sinking down after the rider got off. */
    private static final EntityDataAccessor<Boolean> GLIDING = SynchedEntityData.defineId(Griffin.class, EntityDataSerializers.BOOLEAN);
    /** Top flight speed (blocks per tick); the fastest horse gallops at about 0.73. */
    private static final double FLY_SPEED = 0.95;
    private static final double MAX_CLIMB = 0.4, MAX_DIVE = -1.0, HOVER_SINK = -0.03, GLIDE_FALL = -0.12;
    /** How fast the velocity eases toward where the rider steers: across, upward, downward (inertia). */
    private static final double TURN = 0.06, RISE = 0.08, SINK = 0.15;
    private static final double MIN_SPEED = 0.18, MAX_SPEED = 0.22;
    /** The controlling client's own flight state, a few ticks ahead of the server's {@link #FLYING}. */
    private boolean localFlight;
    private boolean wildGlide;
    private boolean seenAirborne;
    private int flightTicks, airTicks, glideCooldown;
    private double lastY;

    public Griffin(EntityType<? extends Griffin> type, Level level) {
        super(type, level);
        this.glideCooldown = 200 + this.random.nextInt(600);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return AbstractHorse.createBaseHorseAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.JUMP_STRENGTH, 0.7);
    }

    /** Solid ground under open sky, in good light (the mountain tops). */
    public static boolean checkSpawnRules(EntityType<Griffin> type, LevelAccessor level, EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        return level.getBlockState(pos.below()).isSolid() && level.canSeeSky(pos) && level.getRawBrightness(pos, 0) > 8;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(FLYING, false);
        builder.define(GLIDING, false);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.2, Griffin::meat, false));
        this.goalSelector.addGoal(5, new GlideGoal());
    }

    @Override
    protected void randomizeAttributes(RandomSource random) {
        this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(30.0);
        this.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(MIN_SPEED + random.nextDouble() * (MAX_SPEED - MIN_SPEED));
    }

    // -- flight state ------------------------------------------------------------------------------
    /** Wings spread: flying with a rider, or gliding. True on every client (synced). */
    public boolean isFlying() {
        return this.entityData.get(FLYING) || this.entityData.get(GLIDING) || this.localFlight;
    }

    /** A saddled grown griffin with a player at the reins, out of the water. */
    private boolean canFly() {
        return !this.isBaby() && this.isSaddled() && !this.isInWater() && this.getControllingPassenger() instanceof Player;
    }

    private boolean aloft() {
        return !this.onGround() && !this.isInWater() && !this.isInLava();
    }

    /** Launches into flight as if the rider had jumped at full charge (works without a rider too:
     *  then it glides back down). */
    public void takeOff() {
        if (this.isBaby() || this.isInWater()) return;
        this.launch(1.0F);
        this.wildGlide = !this.isVehicle();
        if (!this.level().isClientSide()) {
            this.entityData.set(FLYING, true);
            this.flightTicks = 0;
            this.seenAirborne = false;
        }
    }

    private void launch(float scale) {
        Vec3 v = this.getDeltaMovement();
        this.setDeltaMovement(v.x, 0.45 + 0.55 * scale, v.z);
        this.localFlight = true;
        this.flap(1.0F);
    }

    private void wingBeat(float scale) {
        Vec3 v = this.getDeltaMovement();
        this.setDeltaMovement(v.x, Math.max(v.y, 0.0) + 0.45 + 0.3 * scale, v.z);
    }

    /** Wing-beat sound, from the server (so the rider doesn't hear it twice). */
    private void flap(float volume) {
        if (!this.level().isClientSide()) this.playSound(SoundEvents.ENDER_DRAGON_FLAP, volume, 1.3F + this.random.nextFloat() * 0.2F);
    }

    // -- the rider's controls ----------------------------------------------------------------------
    /** Jump released (on the rider's client): in the air it's a wing-beat; on the ground the charge
     *  is stored and {@link #executeRidersJump} launches. */
    @Override
    public void onPlayerJump(int amount) {
        if (this.canFly() && !this.onGround()) {
            this.localFlight = true;
            this.wingBeat(this.getPlayerJumpPendingScale(Math.max(amount, 0)));
            return;
        }
        super.onPlayerJump(amount);
    }

    @Override
    protected void executeRidersJump(float amount, Vec3 input) {
        if (this.canFly()) {
            this.launch(amount);
            return;
        }
        super.executeRidersJump(amount, input);
    }

    /** Jump released (on the server). */
    @Override
    public void handleStartJump(int jumpScale) {
        if (this.canFly()) {
            this.entityData.set(FLYING, true);
            this.flightTicks = 0;
            this.seenAirborne = this.aloft();
            this.flap(1.0F);
            return;
        }
        super.handleStartJump(jumpScale);
    }

    /** Runs wherever movement is simulated: the rider's client while ridden, else the server. */
    @Override
    public void travel(Vec3 input) {
        boolean powered = this.canFly() && this.aloft() && (this.localFlight || this.entityData.get(FLYING));
        if (this.isNoGravity() != powered) this.setNoGravity(powered);
        if (powered) {
            this.flyTravel(input);
            return;
        }
        super.travel(input);
        if (!this.aloft()) return;
        Vec3 v = this.getDeltaMovement();
        if (this.canFly()) {
            // dropping off a cliff with a rider: it spreads its wings and takes over
            if (v.y < -0.45) this.localFlight = true;
        } else if (v.y < GLIDE_FALL) {
            // nobody flying it: it glides down, never falls hard
            this.setDeltaMovement(v.x, GLIDE_FALL, v.z);
        }
        if (this.wildGlide && !this.isVehicle()) {
            float yaw = this.getYRot() * Mth.DEG_TO_RAD;
            this.addDeltaMovement(new Vec3(-Mth.sin(yaw) * 0.025, 0.0, Mth.cos(yaw) * 0.025));
        }
    }

    /** No gravity: the velocity eases toward where the rider looks (forward held), or a slow sinking
     *  hover; strafing nudges it sideways. */
    private void flyTravel(Vec3 input) {
        LivingEntity rider = this.getControllingPassenger();
        float pitch = rider != null ? rider.getXRot() : 0.0F;
        float yaw = this.getYRot();
        double sin = Mth.sin(yaw * Mth.DEG_TO_RAD), cos = Mth.cos(yaw * Mth.DEG_TO_RAD);
        double forward = input.z, side = input.x;
        Vec3 target;
        if (forward > 0) {
            Vec3 look = Vec3.directionFromRotation(pitch, yaw).scale(FLY_SPEED * forward);
            target = new Vec3(look.x, Mth.clamp(look.y, MAX_DIVE, MAX_CLIMB), look.z);
        } else {
            target = new Vec3(-sin * forward * 0.6, HOVER_SINK, cos * forward * 0.6);   // backing up, gently
        }
        target = target.add(cos * side * 0.6, 0.0, sin * side * 0.6);
        Vec3 v = this.getDeltaMovement();
        double vy = v.y + (target.y - v.y) * (v.y > target.y ? SINK : RISE);
        v = new Vec3(v.x + (target.x - v.x) * TURN, vy, v.z + (target.z - v.z) * TURN);
        this.setDeltaMovement(v);
        this.move(MoverType.SELF, v);
        if (this.onGround() || this.isInWater()) this.localFlight = false;   // touched down
    }

    @Override
    public void tick() {
        super.tick();
        boolean air = this.aloft();
        if (!air || !this.isVehicle()) this.localFlight = false;   // landed, or nobody aboard
        if (air && (this.isFlying() || this.isVehicle())) {
            this.resetFallDistance();
            for (Entity rider : this.getPassengers()) rider.resetFallDistance();
        }
        if (this.level() instanceof ServerLevel) this.serverFlightTick(air);
    }

    /** The server's view of the flight, from the rider's jumps and the movement it receives. */
    private void serverFlightTick(boolean air) {
        double dy = this.getY() - this.lastY;
        this.lastY = this.getY();
        this.airTicks = air ? this.airTicks + 1 : 0;
        if (this.glideCooldown > 0) this.glideCooldown--;
        boolean ridden = this.canFly();
        boolean flying = this.entityData.get(FLYING);
        if (ridden) {
            // holding height in mid-air with a rider: it's flying, whether or not we saw the jump
            if (!flying && air && this.airTicks > 4 && dy > -0.05) flying = true;
            if (flying) {
                this.flightTicks++;
                if (air) this.seenAirborne = true;
                if (this.seenAirborne ? !air : this.flightTicks > 60) flying = false;   // landed, or never got up
            }
        } else {
            flying = false;
        }
        if (!flying) {
            this.flightTicks = 0;
            this.seenAirborne = false;
        }
        if (!air) this.wildGlide = false;
        boolean gliding = !flying && air && !ridden && (this.wildGlide || this.airTicks > 3);
        if (flying != this.entityData.get(FLYING)) this.entityData.set(FLYING, flying);
        if (gliding != this.entityData.get(GLIDING)) this.entityData.set(GLIDING, gliding);
        if (this.isNoGravity() != flying) this.setNoGravity(flying);   // a no-gravity vehicle isn't kicked for floating
        if ((flying || gliding) && this.tickCount % 18 == 0) this.flap(flying ? 0.7F : 0.4F);
    }

    /** The server's floating-vehicle check leaves flying mounts alone. */
    @Override public boolean isFlyingVehicle() { return this.isFlying(); }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;   // it always lands on its wings (and so does its rider)
    }

    // -- taming, food, breeding --------------------------------------------------------------------
    static boolean meat(ItemStack stack) {
        return stack.is(Items.BEEF) || stack.is(Items.PORKCHOP) || stack.is(Items.MUTTON) || stack.is(Items.CHICKEN) || stack.is(Items.RABBIT);
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return meat(stack) || stack.is(Items.GOLDEN_APPLE) || stack.is(Items.ENCHANTED_GOLDEN_APPLE);
    }

    /** Raw meat heals it, grows a chick and calms a wild one; golden apples follow the horse rules
     *  (they also put tamed adults in love). */
    @Override
    protected boolean handleEating(Player player, ItemStack stack) {
        if (!meat(stack)) return super.handleEating(player, stack);
        boolean used = false;
        if (this.getHealth() < this.getMaxHealth()) {
            this.heal(4.0F);
            used = true;
        }
        if (this.isBaby() && !this.isAgeLocked()) {
            this.level().addParticle(ParticleTypes.HAPPY_VILLAGER, this.getRandomX(1.0), this.getRandomY() + 0.5, this.getRandomZ(1.0), 0, 0, 0);
            if (!this.level().isClientSide()) this.ageUp(60);
            used = true;
        }
        if ((used || !this.isTamed()) && this.getTemper() < this.getMaxTemper() && !this.level().isClientSide()) {
            this.modifyTemper(5);
            used = true;
        }
        if (used) {
            this.playSound(SoundEvents.GENERIC_EAT.value(), 0.8F, 0.8F);
            this.gameEvent(GameEvent.EAT);
        }
        return used;
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        boolean openInventory = !this.isBaby() && this.isTamed() && player.isSecondaryUseActive();
        if (!this.isVehicle() && !openInventory && (!this.isBaby() || !player.isHolding(Items.GOLDEN_DANDELION))) {
            ItemStack stack = player.getItemInHand(hand);
            if (!stack.isEmpty()) {
                if (this.isFood(stack)) return this.fedFood(player, stack);
                if (!this.isTamed()) {
                    this.makeMad();
                    return InteractionResult.SUCCESS;
                }
            }
        }
        return super.mobInteract(player, hand);
    }

    /** No rearing or grazing animations; a saddle but no horse armour. */
    @Override protected boolean canPerformRearing() { return false; }
    @Override public boolean canEatGrass() { return false; }

    @Override
    public boolean canUseSlot(EquipmentSlot slot) {
        return slot != EquipmentSlot.BODY && super.canUseSlot(slot);
    }

    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public boolean canMate(Animal partner) {
        return partner != this && partner instanceof Griffin other && this.canParent() && other.canParent();
    }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Griffin baby = NsvEntities.GRIFFIN.create(level, EntitySpawnReason.BREEDING);
        if (baby != null) {
            baby.getAttribute(Attributes.MAX_HEALTH).setBaseValue(30.0);
            baby.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(createOffspringAttribute(
                    this.getAttributeBaseValue(Attributes.MOVEMENT_SPEED), partner.getAttributeBaseValue(Attributes.MOVEMENT_SPEED),
                    MIN_SPEED, MAX_SPEED, this.random));
        }
        return baby;
    }

    // -- sounds ----------------------------------------------------------------------------------
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.PHANTOM_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.OCELOT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PHANTOM_DEATH; }
    @Override protected @Nullable SoundEvent getEatingSound() { return SoundEvents.GENERIC_EAT.value(); }
    @Override protected @Nullable SoundEvent getAngrySound() { return SoundEvents.PHANTOM_HURT; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.CAMEL_STEP, 0.5F, 0.9F); }
    @Override protected void playJumpSound() { this.flap(0.8F); }
    @Override protected float getSoundVolume() { return 0.6F; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.8F : 1.35F) + this.random.nextFloat() * 0.1F; }

    /** Wild (unridden) griffins now and then launch into a short glide, often off a ledge. */
    private class GlideGoal extends Goal {
        GlideGoal() {
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            Griffin g = Griffin.this;
            if (g.isVehicle() || g.isBaby() || !g.onGround() || g.isInWater() || g.glideCooldown > 0 || g.isLeashed()) return false;
            return g.getRandom().nextInt(reducedTickDelay(this.nearLedge() ? 60 : 1500)) == 0;
        }

        /** A drop of 4+ blocks a few blocks ahead. */
        private boolean nearLedge() {
            Griffin g = Griffin.this;
            float yaw = g.getYRot() * Mth.DEG_TO_RAD;
            BlockPos ahead = BlockPos.containing(g.getX() - Mth.sin(yaw) * 3.0, g.getY(), g.getZ() + Mth.cos(yaw) * 3.0);
            for (int i = 0; i < 5; i++) {
                BlockPos p = ahead.below(i);
                if (!g.level().getBlockState(p).getCollisionShape(g.level(), p).isEmpty()) return false;
            }
            return true;
        }

        @Override
        public void start() {
            Griffin g = Griffin.this;
            float yaw = g.getYRot() * Mth.DEG_TO_RAD;
            g.getNavigation().stop();
            g.setDeltaMovement(-Mth.sin(yaw) * 0.45, 0.6, Mth.cos(yaw) * 0.45);
            g.wildGlide = true;
            g.glideCooldown = 400 + g.getRandom().nextInt(800);
            g.flap(0.9F);
        }

        @Override public boolean canContinueToUse() { return Griffin.this.wildGlide; }
        @Override public void tick() { Griffin.this.getNavigation().stop(); }
    }
}
