package dev.nsvmobs.entity;

import java.util.EnumSet;

import dev.nsvmobs.NsvEntities;

import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtTargetGoal;
import net.minecraft.world.entity.animal.chicken.Chicken;
import net.minecraft.world.entity.animal.rabbit.Rabbit;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Ghast;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A lean savanna cheetah. Wild ones lounge in the grass or sit up on watch by day, walk away from
 * anyone who comes close without crouching, bolt if hurt and never fight back. They hunt rabbits
 * and chickens: a slow, low stalk, then a burst at more than twice a sprinting player's speed and a
 * pounce; catch or miss, the cheetah is winded for 30 s after and only walks, panting. Tame one with
 * raw chicken or rabbit: it follows you, sits when told, races alongside when you sprint (you get
 * Speed II for up to 10 s) and courses down whatever hurts you or you attack, with a sprint and a
 * pounce, then fights on at a walk. No fall damage (an entity tag).
 */
public class Cheetah extends TamableAnimal {
    public static final int IDLE = 0, STALK = 1, SPRINT = 2, WINDED = 3, POUNCE = 4;
    private static final EntityDataAccessor<Byte> MODE = SynchedEntityData.defineId(Cheetah.class, EntityDataSerializers.BYTE);
    /** 0 = up and about, 1 = sitting up on watch, 2 = lounging (wild cheetahs only). */
    private static final EntityDataAccessor<Byte> REST = SynchedEntityData.defineId(Cheetah.class, EntityDataSerializers.BYTE);
    static final int WINDED_TICKS = 600, PACE_TICKS = 200, SPRINT_TICKS = 100, STALK_TICKS = 120;
    static final float POUNCE_DAMAGE = 6.0F;
    /** Speed modifiers on MOVEMENT_SPEED 0.3: a sprint covers about 0.66 blocks a tick, over twice a sprinting player's 0.28. */
    static final double STALK_SPEED = 0.6, SPRINT_SPEED = 1.85, PACE_SPEED = 1.75;
    private int modeStart;
    private int windedTicks;
    private int huntCooldown;
    /** Ticks spent running alongside its sprinting owner (it tires at PACE_TICKS). */
    private int paceTicks;
    private boolean pacing;
    /** Set by huntNow: skip most of the stalk. */
    private boolean quickHunt;
    /** Made in registerGoals (which runs inside the super constructor), so no initializer here. */
    private BoltGoal bolt;

    public Cheetah(EntityType<? extends Cheetah> type, Level level) {
        super(type, level);
        this.huntCooldown = 200 + this.random.nextInt(600);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return TamableAnimal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(MODE, (byte) IDLE);
        builder.define(REST, (byte) 0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new SitWhenOrderedToGoal(this));
        this.bolt = new BoltGoal();
        this.goalSelector.addGoal(2, this.bolt);
        this.goalSelector.addGoal(2, new PaceGoal());
        this.goalSelector.addGoal(3, new HuntGoal());
        this.goalSelector.addGoal(4, new TemptGoal(this, 0.8, Cheetah::treat, true));
        this.goalSelector.addGoal(5, new AvoidEntityGoal<>(this, Player.class, 6.0F, 1.0, 1.15, Cheetah::startles) {
            @Override
            public boolean canUse() {
                return !Cheetah.this.isTame() && super.canUse();
            }
        });
        this.goalSelector.addGoal(6, new FollowOwnerGoal(this, 1.2, 10.0F, 2.0F));
        this.goalSelector.addGoal(7, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(8, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(9, new RestGoal());
        this.goalSelector.addGoal(10, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(11, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(11, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new OwnerHurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new OwnerHurtTargetGoal(this));
        this.targetSelector.addGoal(3, new PreyGoal());
    }

    static boolean treat(ItemStack stack) {
        return stack.is(Items.CHICKEN) || stack.is(Items.RABBIT);
    }

    static boolean rawMeat(ItemStack stack) {
        return treat(stack) || stack.is(Items.BEEF) || stack.is(Items.PORKCHOP) || stack.is(Items.MUTTON);
    }

    static boolean isPrey(LivingEntity e) {
        return e instanceof Rabbit || e instanceof Chicken;
    }

    /** Players it walks away from: anyone in survival or adventure who isn't crouching or holding a treat. */
    static boolean startles(LivingEntity e) {
        return !e.isShiftKeyDown() && !e.isCrouching() && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(e)
                && !treat(e.getMainHandItem()) && !treat(e.getOffhandItem());
    }

    private boolean canHunt() {
        return !this.isBaby() && this.huntCooldown <= 0 && this.mode() == IDLE && !this.pacing;
    }

    // -- state -------------------------------------------------------------------------------------------

    public int mode() {
        return this.entityData.get(MODE);
    }

    void setMode(int mode) {
        this.entityData.set(MODE, (byte) mode);
        this.modeStart = this.tickCount;
    }

    /** Ticks (with partial) since the current mode began (either side). */
    public float modeAge(float partialTick) {
        return this.tickCount - this.modeStart + partialTick;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (MODE.equals(key)) this.modeStart = this.tickCount;
    }

    public boolean isWinded() {
        return this.mode() == WINDED;
    }

    /** Out of breath for 30 s: it pants and only walks. */
    void setWinded() {
        this.setMode(WINDED);
        this.windedTicks = WINDED_TICKS;
        this.pacing = false;
        this.paceTicks = 0;
    }

    /** A wild cheetah sitting up on watch. */
    public boolean isLookout() {
        return this.entityData.get(REST) == 1;
    }

    /** A wild cheetah lying stretched out in the grass. */
    public boolean isLounging() {
        return this.entityData.get(REST) == 2;
    }

    void setRest(int rest) {
        if (this.entityData.get(REST) != rest) this.entityData.set(REST, (byte) rest);
    }

    /** Stalk and run down this prey right now (no hunting cooldown); does nothing while winded. */
    public void huntNow(LivingEntity prey) {
        if (this.isWinded() || this.level().isClientSide()) return;
        this.huntCooldown = 0;
        this.quickHunt = true;
        this.setRest(0);
        this.setTarget(prey);
    }

    /** Winded, it can't go faster than a walk. */
    @Override
    public void setSpeed(float speed) {
        if (this.isWinded()) speed = Math.min(speed, (float) this.getAttributeValue(Attributes.MOVEMENT_SPEED));
        super.setSpeed(speed);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        if (this.huntCooldown > 0) this.huntCooldown--;
        if (this.isWinded()) {
            if (--this.windedTicks <= 0) {
                this.setMode(IDLE);
            } else if (this.windedTicks > 200 && this.tickCount % 14 == 0) {
                // panting hard for the first 20 s
                this.playSound(SoundEvents.WOLF_PANT_BABY.value(), 0.45F, this.isBaby() ? 1.3F : 0.8F + this.random.nextFloat() * 0.1F);
            }
        }
        // a pounce that never came down on anything (it ran out of AI, or caught on a ledge) ends anyway
        if (this.mode() == POUNCE && this.tickCount - this.modeStart > 40) this.setWinded();
        if (this.isTame() && (this.isLookout() || this.isLounging())) this.setRest(0);
        this.sprintPartner(level);
    }

    /**
     * Sprint partner: a tamed adult near its sprinting owner (on foot) runs alongside and lends them
     * Speed II, refreshed in short spells while the run lasts. After 10 s of it, or when a run of 3 s
     * or more ends, it's winded. Runs here (not in a goal) so the effect never depends on its AI.
     */
    private void sprintPartner(ServerLevel level) {
        boolean can = this.isTame() && !this.isBaby() && !this.isOrderedToSit() && !this.isWinded()
                && this.getOwner() instanceof Player owner && owner.isAlive() && !owner.isSpectator()
                && owner.level() == level && owner.isSprinting() && !owner.isPassenger()
                && !owner.isInWater() && !owner.isSwimming() && !owner.getAbilities().flying && !owner.isFallFlying()
                && this.distanceToSqr(owner) <= (this.pacing ? 16.0 * 16.0 : 10.0 * 10.0)
                && (this.pacing || this.mode() == IDLE);
        if (can) {
            Player owner = (Player) this.getOwner();
            if (!this.pacing) {
                this.pacing = true;
                this.setRest(0);
                this.setMode(SPRINT);
                this.playSound(SoundEvents.OCELOT_AMBIENT, 0.8F, 1.7F);
            }
            // a weaker Speed is set aside by vanilla and comes back after; a stronger or endless one is left alone
            MobEffectInstance speed = owner.getEffect(MobEffects.SPEED);
            if (speed == null || speed.getAmplifier() < 1
                    || (speed.getAmplifier() == 1 && speed.getDuration() >= 0 && speed.getDuration() < 25)) {
                owner.addEffect(new MobEffectInstance(MobEffects.SPEED, 30, 1, false, true, true), this);
            }
            if (++this.paceTicks >= PACE_TICKS) this.setWinded();
        } else if (this.pacing) {
            this.pacing = false;
            if (this.paceTicks >= 60) {
                this.setWinded();
            } else if (this.mode() == SPRINT) {
                this.setMode(IDLE);
            }
        } else if (this.paceTicks > 0 && this.tickCount % 2 == 0) {
            this.paceTicks--;   // a short dash is shrugged off
        }
    }

    /** Pounce or bite connects. The pounce (6) also slows the target for a moment. */
    void strike(ServerLevel level, LivingEntity target) {
        this.swingForAttack(InteractionHand.MAIN_HAND);
        boolean hurt = target.hurtServer(level, this.damageSources().mobAttack(this), POUNCE_DAMAGE);
        if (hurt) target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 2), this);
        this.playSound(SoundEvents.PANDA_BITE, 1.0F, 1.3F);
        if (!target.isAlive()) this.heal(4.0F);
        this.setWinded();
        if (!this.isTame()) {
            // a wild hunt is over, catch or miss
            this.setTarget(null);
            this.huntCooldown = 1200 + this.random.nextInt(1200);
        }
    }

    /** Only courses things worth fighting: never creepers or ghasts, its owner's other pets or friends. */
    @Override
    public boolean wantsToAttack(LivingEntity target, LivingEntity owner) {
        if (target instanceof Creeper || target instanceof Ghast || target instanceof ArmorStand) return false;
        if (target instanceof OwnableEntity pet && pet.getOwner() == owner) return false;
        return !(target instanceof Player p && owner instanceof Player o && !o.canHarmPlayer(p));
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt) this.setRest(0);
        return hurt;
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && treat(stack)) {
            this.usePlayerItem(player, hand, stack);
            if (!this.level().isClientSide()) {
                if (this.random.nextInt(3) == 0) {
                    this.tame(player);
                    this.navigation.stop();
                    this.setTarget(null);
                    this.setRest(0);
                    if (this.mode() != WINDED) this.setMode(IDLE);
                    this.setOrderedToSit(true);
                    this.level().broadcastEntityEvent(this, (byte) 7);
                } else {
                    this.level().broadcastEntityEvent(this, (byte) 6);
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (this.isTame() && this.isOwnedBy(player)) {
            if (rawMeat(stack) && this.getHealth() < this.getMaxHealth()) {
                this.usePlayerItem(player, hand, stack);
                this.heal(4.0F);
                this.playSound(SoundEvents.FOX_EAT, 0.6F, 0.9F);
                return InteractionResult.SUCCESS;
            }
            InteractionResult result = super.mobInteract(player, hand);
            if (!result.consumesAction() && stack.isEmpty()) {
                this.setOrderedToSit(!this.isOrderedToSit());
                this.jumping = false;
                this.navigation.stop();
                this.setTarget(null);
                return InteractionResult.SUCCESS;
            }
            return result;
        }
        return super.mobInteract(player, hand);
    }

    /** Wild pairs are a mother and her cub. */
    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData data) {
        if (data == null) data = new AgeableMob.AgeableMobGroupData(1.0F);
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override public boolean isFood(ItemStack stack) { return treat(stack); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Cheetah baby = NsvEntities.CHEETAH.create(level, EntitySpawnReason.BREEDING);
        if (baby != null && this.getOwnerReference() != null) {
            baby.setOwnerReference(this.getOwnerReference());
            baby.setTame(true, true);
        }
        return baby;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("WindedTicks", this.isWinded() ? this.windedTicks : 0);
        output.putInt("HuntCooldown", this.huntCooldown);
        output.putInt("PaceTicks", this.paceTicks);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        int winded = input.getIntOr("WindedTicks", 0);
        if (winded > 0) {
            this.setMode(WINDED);
            this.windedTicks = winded;
        }
        this.huntCooldown = input.getIntOr("HuntCooldown", this.huntCooldown);
        this.paceTicks = input.getIntOr("PaceTicks", 0);
    }

    /** A bird-like chirp; a tamed one sometimes purrs. Winded, it only pants (see aiStep). */
    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        if (this.isWinded()) return null;
        return this.isTame() && this.random.nextInt(3) == 0 ? SoundEvents.CAT_PURR_BABY.value() : SoundEvents.OCELOT_AMBIENT;
    }

    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.OCELOT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.OCELOT_DEATH; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.8F : 1.35F) + this.random.nextFloat() * 0.15F; }
    @Override public int getAmbientSoundInterval() { return 200; }
    @Override protected float getSoundVolume() { return 0.6F; }

    // -- goals --------------------------------------------------------------------------------------------

    /**
     * Wild adults pick a rabbit or chicken to hunt now and then. Unlike vanilla's target goals it lets
     * go for good once the hunt is over (winded, or bolting from danger), instead of re-taking the prey.
     */
    final class PreyGoal extends NearestAttackableTargetGoal<LivingEntity> {
        private int age;

        PreyGoal() {
            super(Cheetah.this, LivingEntity.class, 40, true, false, (t, l) -> isPrey(t));
        }

        @Override
        public boolean canUse() {
            return !Cheetah.this.isTame() && Cheetah.this.canHunt() && super.canUse();
        }

        @Override
        public void start() {
            super.start();
            this.age = 0;
        }

        @Override
        public boolean canContinueToUse() {
            Cheetah c = Cheetah.this;
            int m = c.mode();
            boolean hunting = m == STALK || m == SPRINT || m == POUNCE || this.age++ < 10;
            return hunting && !c.isTame() && !c.bolt.isRunning() && super.canContinueToUse();
        }
    }

    /** Bolts at a gallop when hurt (wild ones only; a tamed one stands by its owner). */
    final class BoltGoal extends PanicGoal {
        BoltGoal() {
            super(Cheetah.this, 2.0);
        }

        @Override
        public boolean canUse() {
            return !Cheetah.this.isTame() && super.canUse();
        }

        @Override
        public void start() {
            super.start();
            Cheetah c = Cheetah.this;
            c.setRest(0);
            c.huntCooldown = Math.max(c.huntCooldown, 600);   // too shaken to hunt for a while
            if (c.mode() == IDLE) c.setMode(SPRINT);
        }

        @Override
        public void stop() {
            super.stop();
            if (Cheetah.this.mode() == SPRINT && !Cheetah.this.pacing) Cheetah.this.setMode(IDLE);
        }
    }

    /** Runs a few blocks ahead of its sprinting owner and off to one side (the pacing itself is in aiStep). */
    final class PaceGoal extends Goal {
        PaceGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override public boolean canUse() { return Cheetah.this.pacing && Cheetah.this.getOwner() != null; }
        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void stop() {
            Cheetah.this.getNavigation().stop();
        }

        @Override
        public void tick() {
            Cheetah c = Cheetah.this;
            LivingEntity owner = c.getOwner();
            if (owner == null) return;
            Vec3 ahead = owner.getLookAngle().multiply(1.0, 0.0, 1.0);
            ahead = ahead.lengthSqr() < 1.0E-4 ? Vec3.directionFromRotation(0.0F, owner.getYRot()) : ahead.normalize();
            Vec3 side = new Vec3(-ahead.z, 0.0, ahead.x);
            Vec3 to = owner.position().add(ahead.scale(3.0)).add(side.scale(1.6));
            if (c.tickCount % 4 == 0 || c.getNavigation().isDone()) {
                c.getNavigation().moveTo(to.x, to.y, to.z, c.distanceToSqr(to) > 4.0 ? PACE_SPEED : 1.45);
            }
            c.getLookControl().setLookAt(to.x, owner.getEyeY(), to.z);
        }
    }

    /**
     * The hunt, for wild prey and for its owner's enemies alike: stalk low and slow (wild hunts only),
     * burst into a sprint, pounce from close range. Then it's winded: a wild one gives up, a tamed
     * one fights on at a walk, biting.
     */
    final class HuntGoal extends Goal {
        private int timer, biteCooldown;

        HuntGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        private @Nullable LivingEntity target() {
            LivingEntity t = Cheetah.this.getTarget();
            return t != null && t.isAlive() && t.level() == Cheetah.this.level()
                    && !(t instanceof Player p && (p.isCreative() || p.isSpectator())) ? t : null;
        }

        @Override
        public boolean canUse() {
            Cheetah c = Cheetah.this;
            return this.target() != null && !c.isOrderedToSit() && !c.pacing && (c.isTame() || !c.isWinded());
        }

        @Override
        public boolean canContinueToUse() {
            return this.canUse() || Cheetah.this.mode() == POUNCE;
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void start() {
            Cheetah c = Cheetah.this;
            LivingEntity t = this.target();
            c.setRest(0);
            this.timer = 0;
            if (c.isWinded() || t == null) return;
            if (c.isTame() || c.distanceTo(t) < 8.0F) {
                this.burst();
            } else {
                c.setMode(STALK);
            }
        }

        @Override
        public void stop() {
            Cheetah c = Cheetah.this;
            if (c.mode() == STALK || c.mode() == SPRINT) c.setMode(IDLE);
            else if (c.mode() == POUNCE) c.setWinded();    // cut short mid-leap (hurt, say): the effort's spent
            c.getNavigation().stop();
            c.quickHunt = false;
            if (!c.isTame()) c.setTarget(null);
        }

        private void burst() {
            Cheetah c = Cheetah.this;
            c.setMode(SPRINT);
            this.timer = 0;
            c.playSound(SoundEvents.HORSE_BREATHE, 0.7F, 1.7F);
        }

        @Override
        public void tick() {
            Cheetah c = Cheetah.this;
            LivingEntity t = this.target();
            if (this.biteCooldown > 0) this.biteCooldown--;
            this.timer++;
            if (t == null) {
                if (c.mode() == POUNCE && c.onGround() && this.timer > 3) c.setWinded();
                return;
            }
            ServerLevel level = (ServerLevel) c.level();
            double d = c.distanceTo(t);
            if (c.mode() != POUNCE) c.getLookControl().setLookAt(t, 30.0F, 30.0F);
            switch (c.mode()) {
                case STALK -> {
                    // creeping up, low and slow; it bursts once close, or when the prey takes off
                    if (this.timer % 10 == 1) c.getNavigation().moveTo(t, STALK_SPEED);
                    boolean fleeing = t.getDeltaMovement().horizontalDistanceSqr() > 0.02;
                    if (d < 9.0 || fleeing || this.timer > (c.quickHunt ? 12 : STALK_TICKS)) this.burst();
                }
                case SPRINT -> {
                    if (this.timer % 3 == 1) c.getNavigation().moveTo(t, SPRINT_SPEED);
                    if (d < 4.0 && c.onGround() && c.hasLineOfSight(t)) {
                        this.leap(t);
                    } else if (this.timer > SPRINT_TICKS) {
                        // out of breath before it got there
                        c.setWinded();
                        if (!c.isTame()) {
                            c.setTarget(null);
                            c.huntCooldown = 1200 + c.random.nextInt(1200);
                        }
                    }
                }
                case POUNCE -> {
                    if (c.getBoundingBox().inflate(0.5).intersects(t.getBoundingBox())) {
                        c.strike(level, t);
                    } else if (this.timer > 3 && c.onGround()) {
                        if (d < 1.8) {
                            c.strike(level, t);
                        } else {
                            // missed
                            c.setWinded();
                            if (!c.isTame()) {
                                c.setTarget(null);
                                c.huntCooldown = 1200 + c.random.nextInt(1200);
                            }
                        }
                    }
                }
                case WINDED -> {
                    // a tamed courser fights on at a walk, biting
                    if (this.timer % 10 == 1) c.getNavigation().moveTo(t, 1.0);
                    if (this.biteCooldown == 0 && c.isWithinMeleeAttackRange(t) && c.hasLineOfSight(t)) {
                        c.swingForAttack(InteractionHand.MAIN_HAND);
                        c.doHurtTarget(level, t);
                        this.biteCooldown = 20;
                    }
                }
                default -> this.burst();   // its wind came back mid-fight
            }
        }

        private void leap(LivingEntity t) {
            Cheetah c = Cheetah.this;
            Vec3 to = t.position().subtract(c.position());
            double flat = Math.max(0.1, Math.sqrt(to.x * to.x + to.z * to.z));
            double speed = Mth.clamp(flat * 0.2, 0.45, 0.95);
            c.getNavigation().stop();
            c.setDeltaMovement(to.x / flat * speed, 0.3 + Math.max(0.0, to.y) * 0.1, to.z / flat * speed);
            c.setYRot((float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90.0F);
            c.yBodyRot = c.getYRot();
            c.setMode(POUNCE);
            this.timer = 0;
            c.playSound(SoundEvents.CAT_HISS_BABY.value(), 0.8F, 0.7F);
        }
    }

    /**
     * Wild cheetahs idle the day away: lounging stretched out in the grass, or sitting up on watch
     * scanning the plains (the look goals keep its head moving). At night it rests less.
     */
    final class RestGoal extends Goal {
        private int timer;

        RestGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
        }

        private boolean free() {
            Cheetah c = Cheetah.this;
            return !c.isTame() && c.onGround() && !c.isInWater() && c.getTarget() == null && c.mode() == IDLE && !c.isLeashed();
        }

        @Override
        public boolean canUse() {
            return this.free() && Cheetah.this.random.nextInt(Cheetah.this.level().isBrightOutside() ? 240 : 900) == 0;
        }

        @Override
        public boolean canContinueToUse() {
            return this.timer > 0 && this.free();
        }

        @Override
        public void start() {
            Cheetah c = Cheetah.this;
            boolean lounge = c.random.nextFloat() < 0.6F;
            this.timer = lounge ? 300 + c.random.nextInt(600) : 160 + c.random.nextInt(240);
            c.getNavigation().stop();
            c.setRest(lounge ? 2 : 1);
        }

        @Override
        public void tick() {
            this.timer--;
        }

        @Override
        public void stop() {
            Cheetah.this.setRest(0);
        }
    }
}
