package dev.nsvmobs.entity;

import java.util.EnumSet;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.BodyRotationControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.chicken.Chicken;
import net.minecraft.world.entity.animal.rabbit.Rabbit;
import net.minecraft.world.entity.monster.Endermite;
import net.minecraft.world.entity.monster.Silverfish;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A giant orchid mantis of the cherry groves. It stands among the blossoms swaying like a flower in
 * the breeze and makes no sound; only its head turns to follow whatever moves. Rabbits, chickens,
 * glowmoths, silverfish and endermites that come within reach are snatched. Walk right up to it
 * without crouching and it strikes you too: you're snagged and held for a moment, then it flares
 * its wings to flash the eye-spots. Hit it and it fights back with strikes and fluttering hops.
 * It doesn't breed.
 */
public class OrchidMantis extends Animal {
    public static final int NONE = 0, STRIKE = 1, SNAG = 2, THREAT = 3;
    private static final EntityDataAccessor<Byte> ACTION = SynchedEntityData.defineId(OrchidMantis.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Boolean> STILL = SynchedEntityData.defineId(OrchidMantis.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> FLUTTERING = SynchedEntityData.defineId(OrchidMantis.class, EntityDataSerializers.BOOLEAN);
    static final float STRIKE_DAMAGE = 4.0F, BITE_DAMAGE = 2.0F;
    /** The forelegs are out by STRIKE_HIT; the strike pose ends at STRIKE_TICKS. */
    public static final int STRIKE_HIT = 2, STRIKE_TICKS = 4, SNAG_TICKS = 30, THREAT_TICKS = 40, THREAT_MAX = 100;
    /** How long its head tracks a victim before the forelegs snap out. */
    static final int AIM_TICKS = 6;
    /** Rest after a threat display, after a meal, and between blows in a fight. */
    static final int COOLDOWN = 80, MEAL_COOLDOWN = 100, FIGHT_COOLDOWN = 16;
    /** Strike reach (players and fight targets), prey reach, and where a snagged victim is held. */
    static final double REACH = 2.0, PREY_REACH = 2.2, HOLD = 1.0;
    private int actionStart, cooldown, aimTicks, stillTicks;
    private @Nullable LivingEntity aimed, victim;
    /** Who its eyes are on while it aims, holds or displays. */
    private @Nullable LivingEntity eyesOn;
    /** The last strike connected; it was a blow in a fight (no snag); hop back after it. */
    private boolean struck, fightStrike, hopBack;

    public OrchidMantis(EntityType<? extends OrchidMantis> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.ATTACK_DAMAGE, STRIKE_DAMAGE)
                .add(Attributes.FOLLOW_RANGE, 16.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ACTION, (byte) NONE);
        builder.define(STILL, false);
        builder.define(FLUTTERING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new FightGoal());
        this.goalSelector.addGoal(2, new HoldStillGoal());
        this.goalSelector.addGoal(3, new StalkPreyGoal());
        // mostly it waits among the flowers, now and then moving on
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6) {
            { this.setInterval(600); }
        });
        this.goalSelector.addGoal(6, new WatchMoverGoal());
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    public int action() { return this.entityData.get(ACTION); }

    void setAction(int action) {
        this.entityData.set(ACTION, (byte) action);
        this.actionStart = this.tickCount;
    }

    /** Ticks (with partial) since the current action began (either side). */
    public float actionAge(float partialTick) {
        return this.tickCount - this.actionStart + partialTick;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (ACTION.equals(key)) this.actionStart = this.tickCount;
    }

    /** Standing motionless in its blossom disguise. */
    public boolean isStill() { return this.entityData.get(STILL); }

    /** Airborne on a fluttering hop (or fluttering down from a height). */
    public boolean isFluttering() { return this.entityData.get(FLUTTERING); }

    /** Rabbits, chickens, glowmoths, silverfish and endermites. Never villagers. */
    static boolean isPrey(Entity e) {
        return e instanceof Rabbit || e instanceof Chicken || e instanceof Glowmoth || e instanceof Silverfish || e instanceof Endermite;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        // it flutters down rather than falling, like a chicken
        Vec3 v = this.getDeltaMovement();
        boolean dropping = !this.onGround() && v.y < -0.12;
        if (!this.onGround() && v.y < 0.0) this.setDeltaMovement(v.multiply(1.0, 0.6, 1.0));
        if (!(this.level() instanceof ServerLevel level)) return;

        LivingEntity target = this.getTarget();
        if (target != null && (!target.isAlive() || this.distanceToSqr(target) > 16.0 * 16.0)) this.setTarget(null);
        this.tickAction(level);

        boolean airborne = !this.onGround() && !this.isInWater();
        this.entityData.set(FLUTTERING, airborne && (this.isFluttering() || dropping));
        boolean moving = this.getDeltaMovement().horizontalDistanceSqr() > 2.5E-4 || airborne;
        this.stillTicks = this.action() == NONE && this.getTarget() == null && !moving ? this.stillTicks + 1 : 0;
        this.entityData.set(STILL, this.stillTicks > 10);
    }

    /**
     * The strike, the snag and the threat display. This runs in aiStep, so it also works on a mob
     * without AI, and nothing can interrupt it halfway.
     */
    private void tickAction(ServerLevel level) {
        int age = this.tickCount - this.actionStart;
        switch (this.action()) {
            case NONE -> {
                if (this.cooldown > 0) {
                    this.cooldown--;
                    this.aimed = null;
                    return;
                }
                LivingEntity v = this.pickVictim(level);
                if (v != this.aimed) this.aimTicks = 0;
                this.aimed = v;
                this.eyesOn = v;
                if (v == null) return;
                this.getLookControl().setLookAt(v, 60.0F, 60.0F);
                // its head swivels onto the victim for a moment, then the forelegs snap out
                if (++this.aimTicks >= AIM_TICKS) this.strike(v);
            }
            case STRIKE -> {
                if (age == STRIKE_HIT) this.landStrike(level);
                else if (age >= STRIKE_TICKS) this.afterStrike();
            }
            case SNAG -> this.tickSnag(level, age);
            case THREAT -> {
                Player near = this.nearestIntruder(level, 3.5);
                this.eyesOn = near;
                // it holds the display while you stay close, and settles once you back off
                if (age >= THREAT_MAX || age >= THREAT_TICKS && near == null) {
                    this.setAction(NONE);
                    this.cooldown = this.getTarget() != null ? FIGHT_COOLDOWN : COOLDOWN;
                }
            }
            default -> this.setAction(NONE);
        }
    }

    /** Whoever it strikes next: the one it's fighting, a player who walked up, or prey within reach. */
    private @Nullable LivingEntity pickVictim(ServerLevel level) {
        LivingEntity t = this.getTarget();
        if (t != null && t.isAlive() && this.distanceToSqr(t) <= (REACH + 0.4) * (REACH + 0.4) && this.hasLineOfSight(t)) return t;
        Player p = this.nearestIntruder(level, REACH);
        if (p != null && this.hasLineOfSight(p)) return p;
        LivingEntity prey = this.nearestPrey(PREY_REACH);
        return prey != null && this.hasLineOfSight(prey) ? prey : null;
    }

    /** The closest survival or adventure player within range who isn't crouching or invisible. */
    private @Nullable Player nearestIntruder(ServerLevel level, double range) {
        Player best = null;
        double bestDist = range * range;
        for (Player p : level.players()) {
            if (!p.isAlive() || p.isCreative() || p.isSpectator() || p.isInvisible() || p.isCrouching() || p.isShiftKeyDown()) continue;
            double d = this.distanceToSqr(p);
            if (d <= bestDist) {
                best = p;
                bestDist = d;
            }
        }
        return best;
    }

    @Nullable LivingEntity nearestPrey(double range) {
        List<LivingEntity> near = this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(range),
                e -> e.isAlive() && isPrey(e));
        LivingEntity best = null;
        double bestDist = range * range;
        for (LivingEntity e : near) {
            double d = this.distanceToSqr(e);
            if (d <= bestDist) {
                best = e;
                bestDist = d;
            }
        }
        return best;
    }

    private void strike(LivingEntity v) {
        this.victim = v;
        this.fightStrike = v == this.getTarget();
        this.struck = false;
        this.aimed = null;
        this.aimTicks = 0;
        this.faceToward(v);
        this.getNavigation().stop();
        this.setAction(STRIKE);
        this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 0.7F, 1.7F + this.random.nextFloat() * 0.2F);
    }

    private void landStrike(ServerLevel level) {
        LivingEntity v = this.victim;
        if (v == null || !v.isAlive() || this.distanceToSqr(v) > (REACH + 1.2) * (REACH + 1.2)) return;
        this.faceToward(v);
        this.swingForAttack(InteractionHand.MAIN_HAND);
        this.struck = v.hurtServer(level, this.damageSources().mobAttack(this), STRIKE_DAMAGE);
        if (this.struck) this.playSound(SoundEvents.FOX_BITE, 0.9F, 1.5F);
    }

    private void afterStrike() {
        LivingEntity v = this.victim;
        if (this.fightStrike || v == null) {
            // a blow in a fight: no snag, it hops back and comes again
            this.setAction(NONE);
            this.cooldown = FIGHT_COOLDOWN;
            this.hopBack = this.struck;
            this.victim = null;
        } else if (v instanceof Player) {
            if (this.struck) {
                this.setAction(SNAG);
            } else {
                this.flare();      // a shield or a dodge: it flares at you instead
            }
        } else if (this.struck || !v.isAlive()) {
            this.setAction(SNAG);  // clutches its catch
        } else {
            this.setAction(NONE);
            this.cooldown = FIGHT_COOLDOWN;
            this.victim = null;
        }
    }

    /** Holds the victim about a block in front of it; prey is bitten until it stops struggling. */
    private void tickSnag(ServerLevel level, int age) {
        LivingEntity v = this.victim;
        boolean held = v != null && v.isAlive() && !v.isRemoved() && v.level() == this.level()
                && this.distanceToSqr(v) < 4.0 * 4.0 && !(v instanceof Player p && (p.isCreative() || p.isSpectator()));
        if (v instanceof Player) {
            if (!held || age >= SNAG_TICKS) this.flare();
            else this.hold(v);
            return;
        }
        if (age >= SNAG_TICKS) {
            if (v == null || !v.isAlive()) this.heal(2.0F);    // a meal
            this.setAction(NONE);
            this.cooldown = MEAL_COOLDOWN;
            this.victim = null;
            return;
        }
        if (held) {
            this.hold(v);
            if (age % 8 == 7 && v.hurtServer(level, this.damageSources().mobAttack(this), BITE_DAMAGE)) {
                this.playSound(SoundEvents.FOX_BITE, 0.6F, 1.7F);
            }
        } else if (age % 6 == 0) {
            this.playSound(SoundEvents.GENERIC_EAT.value(), 0.4F, 1.6F + this.random.nextFloat() * 0.2F);
        }
    }

    private void hold(LivingEntity v) {
        Vec3 front = Vec3.directionFromRotation(0.0F, this.yBodyRot);
        Vec3 to = this.position().add(front.scale(v instanceof Player ? HOLD : HOLD * 0.8)).subtract(v.position());
        double dx = to.x * 0.5, dz = to.z * 0.5, len = Math.sqrt(dx * dx + dz * dz);
        if (len > 0.6) {
            dx *= 0.6 / len;
            dz *= 0.6 / len;
        }
        // to move a player from the server: set their motion and flag it to be sent
        v.setDeltaMovement(dx, Math.min(v.getDeltaMovement().y, 0.0), dz);
        v.needsSync = true;
        this.eyesOn = v;
    }

    /** Wings flared up and out to flash the eye-spots, forelegs raised wide. */
    private void flare() {
        this.setAction(THREAT);
        this.eyesOn = this.victim;
        this.victim = null;
        this.playSound(SoundEvents.ARMOR_EQUIP_ELYTRA.value(), 1.0F, 1.4F);
        this.playSound(SoundEvents.CAT_HISS_BABY.value(), 0.5F, 1.3F);
    }

    private void faceToward(Entity e) {
        float yaw = (float) (Mth.atan2(e.getZ() - this.getZ(), e.getX() - this.getX()) * Mth.RAD_TO_DEG) - 90.0F;
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    /** A fluttering hop: wings beating, it bounds toward (or away from) a point. */
    void hop(Vec3 toward, boolean away) {
        Vec3 d = toward.subtract(this.position()).multiply(1.0, 0.0, 1.0);
        if (d.lengthSqr() < 1.0E-4) return;
        d = d.normalize().scale(away ? -0.38 : 0.48);
        this.setDeltaMovement(d.x, away ? 0.36 : 0.42, d.z);
        this.entityData.set(FLUTTERING, true);
        this.playSound(SoundEvents.PARROT_FLY, 0.8F, 0.9F + this.random.nextFloat() * 0.2F);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (!hurt || !this.isAlive()) return hurt;
        if (this.action() == SNAG) {
            // being hit breaks the hold
            if (this.victim instanceof Player) {
                this.flare();
            } else {
                this.setAction(NONE);
                this.victim = null;
            }
        } else if (this.action() == THREAT && this.tickCount - this.actionStart > 10 && source.getEntity() instanceof LivingEntity) {
            // hit again while it displays: the display is over and the fight is on
            this.setAction(NONE);
            this.cooldown = FIGHT_COOLDOWN;
        }
        return hurt;
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        if (target instanceof AbstractVillager) return;     // it never bothers villagers
        super.setTarget(target);
    }

    /** While it is still, only its head turns; during a strike it squares up to its victim at once. */
    @Override
    protected BodyRotationControl createBodyControl() {
        return new BodyRotationControl(this) {
            @Override
            public void clientTick() {
                OrchidMantis m = OrchidMantis.this;
                if (m.action() != NONE) m.yBodyRot = Mth.approachDegrees(m.yBodyRot, m.yHeadRot, 30.0F);
                else if (!m.isStill()) super.clientTick();
            }
        };
    }

    /** Mantises turn their heads a long way round. */
    @Override public int getMaxHeadYRot() { return 110; }

    /** Never spawns as a nymph: it doesn't breed, so there's nothing to grow up into. */
    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason, @Nullable SpawnGroupData data) {
        return super.finalizeSpawn(level, difficulty, reason, new AgeableMobGroupData(false));
    }

    @Override public boolean isFood(ItemStack stack) { return false; }
    @Override public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) { return null; }

    /** Silent in its disguise: a flower makes no sound. */
    @Override protected @Nullable SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.SILVERFISH_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.SILVERFISH_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.SILVERFISH_STEP, 0.1F, 1.3F); }
    @Override public float getVoicePitch() { return 0.9F + this.random.nextFloat() * 0.1F; }
    @Override protected float getSoundVolume() { return 0.6F; }

    /** While it aims, strikes, holds or displays it stays put with its eyes on its victim. */
    private class HoldStillGoal extends Goal {
        HoldStillGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override public boolean canUse() { return OrchidMantis.this.action() != NONE || OrchidMantis.this.aimed != null; }
        @Override public void start() { OrchidMantis.this.getNavigation().stop(); }
        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            OrchidMantis m = OrchidMantis.this;
            m.getNavigation().stop();
            if (m.eyesOn != null && m.eyesOn.isAlive()) m.getLookControl().setLookAt(m.eyesOn, 60.0F, 60.0F);
        }
    }

    /** Hit it and it fights: fluttering hops in, a strike, a hop back out, and again. */
    private class FightGoal extends Goal {
        private int hopDelay;

        FightGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        private @Nullable LivingEntity target() {
            LivingEntity t = OrchidMantis.this.getTarget();
            return t != null && t.isAlive() && !(t instanceof Player p && (p.isCreative() || p.isSpectator())) ? t : null;
        }

        @Override public boolean canUse() { return this.target() != null; }

        @Override
        public void start() {
            OrchidMantis.this.setAggressive(true);
            this.hopDelay = 10;
        }

        @Override
        public void stop() {
            OrchidMantis.this.setAggressive(false);
            OrchidMantis.this.getNavigation().stop();
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            OrchidMantis m = OrchidMantis.this;
            LivingEntity t = this.target();
            if (t == null) return;
            m.getLookControl().setLookAt(t, 60.0F, 60.0F);
            if (this.hopDelay > 0) this.hopDelay--;
            if (m.action() != NONE) {
                m.getNavigation().stop();
                return;
            }
            double d = m.distanceToSqr(t);
            if (m.hopBack && m.onGround()) {
                m.hopBack = false;
                m.getNavigation().stop();
                m.hop(t.position(), true);
                this.hopDelay = 20 + m.random.nextInt(15);
            } else if (d <= REACH * REACH) {
                m.getNavigation().stop();          // in reach: the strike comes from aiStep
            } else if (this.hopDelay == 0 && m.onGround() && d < 7.0 * 7.0) {
                m.getNavigation().stop();
                m.hop(t.position(), false);
                this.hopDelay = 25 + m.random.nextInt(15);
            } else if (m.onGround()) {
                m.getNavigation().moveTo(t, 1.2);
            }
        }
    }

    /** Prey in sight but out of reach: it creeps closer, slow as a swaying flower. */
    private class StalkPreyGoal extends Goal {
        private @Nullable LivingEntity prey;
        private int repath;

        StalkPreyGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            OrchidMantis m = OrchidMantis.this;
            if (m.action() != NONE || m.getTarget() != null || m.random.nextInt(reducedTickDelay(10)) != 0) return false;
            this.prey = m.nearestPrey(8.0);
            return this.prey != null && m.distanceToSqr(this.prey) > PREY_REACH * PREY_REACH && m.hasLineOfSight(this.prey);
        }

        @Override
        public boolean canContinueToUse() {
            OrchidMantis m = OrchidMantis.this;
            return this.prey != null && this.prey.isAlive() && m.action() == NONE && m.getTarget() == null
                    && m.distanceToSqr(this.prey) < 10.0 * 10.0;
        }

        @Override public void start() { this.repath = 0; }

        @Override
        public void stop() {
            this.prey = null;
            OrchidMantis.this.getNavigation().stop();
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            OrchidMantis m = OrchidMantis.this;
            if (this.prey == null) return;
            m.getLookControl().setLookAt(this.prey, 30.0F, 30.0F);
            if (m.distanceToSqr(this.prey) <= 1.5 * 1.5) {
                m.getNavigation().stop();
            } else if (--this.repath <= 0) {
                this.repath = 10;
                m.getNavigation().moveTo(this.prey, 0.7);
            }
        }
    }

    /** The only giveaway of the disguise: its head follows whatever moves nearby. */
    private class WatchMoverGoal extends Goal {
        private @Nullable LivingEntity watched;
        private int time;

        WatchMoverGoal() {
            this.setFlags(EnumSet.of(Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            OrchidMantis m = OrchidMantis.this;
            if (m.random.nextInt(reducedTickDelay(8)) != 0) return false;
            LivingEntity best = null;
            double bestDist = 8.0 * 8.0;
            for (LivingEntity e : m.level().getEntitiesOfClass(LivingEntity.class, m.getBoundingBox().inflate(8.0), e -> e != m && e.isAlive())) {
                double dx = e.getX() - e.xo, dz = e.getZ() - e.zo;
                double d = m.distanceToSqr(e);
                if (dx * dx + dz * dz > 1.0E-4 && d < bestDist && !(e instanceof Player p && p.isSpectator())) {
                    best = e;
                    bestDist = d;
                }
            }
            this.watched = best;
            return best != null;
        }

        @Override
        public boolean canContinueToUse() {
            return this.watched != null && this.watched.isAlive() && this.time > 0 && OrchidMantis.this.distanceToSqr(this.watched) < 10.0 * 10.0;
        }

        @Override public void start() { this.time = 40 + OrchidMantis.this.random.nextInt(40); }
        @Override public void stop() { this.watched = null; }
        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            this.time--;
            if (this.watched != null) OrchidMantis.this.getLookControl().setLookAt(this.watched, 25.0F, 30.0F);
        }
    }
}
