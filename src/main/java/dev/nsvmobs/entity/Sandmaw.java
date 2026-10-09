package dev.nsvmobs.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A colossal desert worm. Burrowed, it swims unseen under loose ground (sand, gravel, dirt) faster
 * than you can run, given away only by the trembling sand. Under its prey the ground shakes for a
 * moment, then it bursts out, tossing everything above it into the air, rears up and bites for a few
 * seconds, and dives again. It can't touch you on hard ground (sandstone, stone, planks), and while
 * it's underground nothing can hurt it.
 */
public class Sandmaw extends Monster {
    public static final byte BURROWED = 0, TREMOR = 1, SURFACED = 2, DIVING = 3;
    private static final EntityDataAccessor<Byte> PHASE = SynchedEntityData.defineId(Sandmaw.class, EntityDataSerializers.BYTE);
    public static final int TREMOR_TICKS = 18, SURFACE_TICKS = 110, DIVE_TICKS = 20, RISE_TICKS = 6;
    static final double SPEED = 0.3, ERUPT_RADIUS = 1.6, BITE_REACH = 3.6;
    private int phaseTicks, cooldown, biteCooldown, stuckTicks;
    private float wanderYaw;
    private int wanderTicks;
    /** Client: when the current phase began (for the rise/sink animation). */
    private int phaseStart;

    public Sandmaw(EntityType<? extends Sandmaw> type, Level level) {
        super(type, level);
        this.xpReward = 25;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 70.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0);
    }

    /**
     * Desert sand under the open sky, by night or (much more rarely, since by day little else can
     * spawn there to share the monster cap) by day.
     */
    public static boolean checkSpawnRules(EntityType<Sandmaw> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        if (level.getDifficulty() == Difficulty.PEACEFUL) return false;
        if (EntitySpawnReason.isSpawner(reason)) return true;
        int odds = level.getLevel().isBrightOutside() ? 15 : 3;
        return level.getBlockState(pos.below()).is(BlockTags.SAND) && level.canSeeSky(pos) && random.nextInt(odds) == 0;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(PHASE, SURFACED);
    }

    @Override
    protected void registerGoals() {
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        // it feels footsteps through the sand: a sneaking player has to come close before it notices
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, false, false,
                (t, level) -> !t.isShiftKeyDown() || t.distanceToSqr(this) < 16.0));
    }

    public byte phase() { return this.entityData.get(PHASE); }
    public boolean isUnderground() { return this.phase() == BURROWED || this.phase() == TREMOR; }

    /** Client: ticks (with partial) since the current phase began. */
    public float phaseAge(float partialTick) {
        return this.tickCount - this.phaseStart + partialTick;
    }

    public void setPhase(byte phase) {
        this.entityData.set(PHASE, phase);
        this.phaseTicks = 0;
        boolean under = phase == BURROWED || phase == TREMOR;
        this.noPhysics = under;
        this.setNoGravity(under);
        if (under) this.setDeltaMovement(Vec3.ZERO);
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (PHASE.equals(key)) {
            this.phaseStart = this.tickCount;
            boolean under = this.isUnderground();
            this.noPhysics = under;
        }
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData groupData) {
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, groupData);
        if (reason == EntitySpawnReason.NATURAL || reason == EntitySpawnReason.CHUNK_GENERATION) this.setPhase(BURROWED);
        return data;
    }

    /** Loose ground it can swim through and burst out of. */
    static boolean loose(BlockState s) {
        return s.is(BlockTags.SAND) || s.is(BlockTags.DIRT) || s.is(Blocks.GRAVEL) || s.is(Blocks.SUSPICIOUS_GRAVEL)
                || s.is(Blocks.SNOW_BLOCK) || s.is(Blocks.CLAY);
    }

    /** The top of the ground at x, z near height y (the block an entity would stand on), or null. */
    private @Nullable BlockPos groundAt(double x, double y, double z) {
        BlockPos.MutableBlockPos p = BlockPos.containing(x, y + 2, z).mutable();
        for (int i = 0; i < 6; i++, p.move(0, -1, 0)) {
            BlockState s = this.level().getBlockState(p);
            if (!s.getCollisionShape(this.level(), p).isEmpty() && this.level().getBlockState(p.above()).getCollisionShape(this.level(), p.above()).isEmpty()) {
                return p.immutable();
            }
        }
        return null;
    }

    /** Whether something is standing on ground it could burst out of. */
    private boolean onLooseGround(Entity e) {
        BlockPos under = e.getBlockPosBelowThatAffectsMyMovement();
        return e.onGround() && loose(this.level().getBlockState(under));
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        this.phaseTicks++;
        if (this.cooldown > 0) this.cooldown--;
        if (this.biteCooldown > 0) this.biteCooldown--;
        LivingEntity target = this.getTarget();
        if (target != null && (!target.isAlive() || target instanceof Player p && (p.isCreative() || p.isSpectator()))) {
            this.setTarget(null);
            target = null;
        }
        switch (this.phase()) {
            case BURROWED -> this.swim(level, target);
            case TREMOR -> {
                if (this.phaseTicks % 2 == 0) this.dust(level, 10, 0.7);
                if (this.phaseTicks % 6 == 0) this.playSound(SoundEvents.SAND_BREAK, 1.2F, 0.5F);
                if (this.phaseTicks >= TREMOR_TICKS) this.erupt(level);
            }
            case SURFACED -> {
                if (target != null) {
                    this.turnToward(target, 18.0F);
                    if (this.biteCooldown == 0 && this.canBite(target)) {
                        this.swingForAttack(InteractionHand.MAIN_HAND);
                        this.doHurtTarget(level, target);
                        this.biteCooldown = 20;
                    }
                }
                if (this.phaseTicks >= SURFACE_TICKS) {
                    this.setPhase(DIVING);
                    this.playSound(SoundEvents.SAND_BREAK, 1.5F, 0.6F);
                }
            }
            case DIVING -> {
                if (this.phaseTicks % 3 == 0) this.dust(level, 8, 0.8);
                if (this.phaseTicks >= DIVE_TICKS) {
                    this.setPhase(BURROWED);
                    this.cooldown = 40;
                }
            }
            default -> {}
        }
    }

    private boolean canBite(LivingEntity t) {
        double dx = t.getX() - this.getX(), dz = t.getZ() - this.getZ();
        return dx * dx + dz * dz < BITE_REACH * BITE_REACH && t.getY() < this.getY() + 3.5 && t.getY() > this.getY() - 1.5;
    }

    private void turnToward(Entity t, float maxTurn) {
        float want = (float) (Mth.atan2(t.getZ() - this.getZ(), t.getX() - this.getX()) * Mth.RAD_TO_DEG) - 90.0F;
        float yaw = Mth.approachDegrees(this.getYRot(), want, maxTurn);
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    /** Underground: head for the target (or wander), staying just under the surface of loose ground. */
    private void swim(ServerLevel level, @Nullable LivingEntity target) {
        double dx, dz, speed;
        if (target != null) {
            dx = target.getX() - this.getX();
            dz = target.getZ() - this.getZ();
            double flat = Math.sqrt(dx * dx + dz * dz);
            if (flat < 1.3 && this.cooldown == 0 && this.onLooseGround(target)) {
                this.setPhase(TREMOR);
                this.playSound(SoundEvents.WARDEN_DIG, 1.5F, 1.2F);
                return;
            }
            speed = Math.min(SPEED, flat);
            if (flat > 1.0E-3) { dx /= flat; dz /= flat; }
        } else {
            if (--this.wanderTicks <= 0) {
                this.wanderYaw = this.random.nextFloat() * Mth.TWO_PI;
                this.wanderTicks = 40 + this.random.nextInt(80);
            }
            dx = Mth.cos(this.wanderYaw);
            dz = Mth.sin(this.wanderYaw);
            speed = this.wanderTicks > 30 ? 0.08 : 0.0;
        }
        if (speed > 0) {
            double nx = this.getX() + dx * speed, nz = this.getZ() + dz * speed;
            BlockPos ground = this.groundAt(nx, this.getY(), nz);
            if (ground != null && loose(level.getBlockState(ground))) {
                this.setPos(nx, ground.getY() + 1, nz);
                this.setYRot((float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90.0F);
                this.yBodyRot = this.getYRot();
                this.stuckTicks = 0;
                if (this.tickCount % (target != null ? 2 : 6) == 0) this.dust(level, target != null ? 4 : 2, 0.4);
                if (target != null && this.tickCount % 10 == 0) this.playSound(SoundEvents.SAND_BREAK, 0.7F, 0.6F);
            } else {
                this.wanderTicks = 0;
                // its prey is somewhere it can't follow (hard ground, water, a cliff): it gives up after a while
                if (target != null && ++this.stuckTicks > 200) {
                    this.setTarget(null);
                    this.stuckTicks = 0;
                }
            }
        }
    }

    /** Sand (or whatever it's in) spraying up from the ground at its position. */
    private void dust(ServerLevel level, int count, double spread) {
        BlockState under = level.getBlockState(BlockPos.containing(this.getX(), this.getY() - 0.5, this.getZ()));
        if (under.isAir()) under = Blocks.SAND.defaultBlockState();
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, under), this.getX(), this.getY() + 0.1, this.getZ(),
                count, spread, 0.1, spread, 0.15);
    }

    /** Burst out of the ground: everything standing over it is hurt and thrown into the air. */
    void erupt(ServerLevel level) {
        this.setPhase(SURFACED);
        this.dust(level, 60, 0.9);
        level.sendParticles(ParticleTypes.POOF, this.getX(), this.getY() + 0.5, this.getZ(), 12, 0.6, 0.6, 0.6, 0.05);
        this.playSound(SoundEvents.RAVAGER_ROAR, 1.6F, 0.7F);
        this.playSound(SoundEvents.SAND_BREAK, 2.0F, 0.5F);
        AABB above = new AABB(this.getX() - ERUPT_RADIUS, this.getY() - 0.5, this.getZ() - ERUPT_RADIUS,
                this.getX() + ERUPT_RADIUS, this.getY() + 3.0, this.getZ() + ERUPT_RADIUS);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, above, e -> e != this && e.isAlive() && !(e instanceof Sandmaw))) {
            if (e instanceof Player p && (p.isCreative() || p.isSpectator())) continue;
            if (e.hurtServer(level, this.damageSources().mobAttack(this), 9.0F)) {
                double ox = e.getX() - this.getX(), oz = e.getZ() - this.getZ();
                double len = Math.max(0.1, Math.sqrt(ox * ox + oz * oz));
                e.push(ox / len * 0.35, 0.95, oz / len * 0.35);
                e.needsSync = true;
            }
        }
    }

    @Override
    public boolean isInvulnerableTo(ServerLevel level, DamageSource source) {
        if (this.isUnderground() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) return true;
        return source.is(DamageTypeTags.IS_FALL) || super.isInvulnerableTo(level, source);
    }

    @Override public boolean isPickable() { return !this.isUnderground() && super.isPickable(); }
    @Override public boolean canBeCollidedWith(@Nullable Entity other) { return false; }
    @Override public boolean isPushable() { return false; }
    @Override public boolean isPushedByFluid() { return false; }
    @Override protected void doPush(Entity entity) {}
    @Override public boolean isInWall() { return false; }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putByte("Phase", this.phase());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        byte p = input.getByteOr("Phase", SURFACED);
        // a worm saved mid-attack comes back burrowed
        this.setPhase(p == SURFACED ? SURFACED : BURROWED);
    }

    @Override public float getVoicePitch() { return 0.6F + this.random.nextFloat() * 0.15F; }
    @Override protected SoundEvent getAmbientSound() { return this.isUnderground() ? null : SoundEvents.RAVAGER_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.RAVAGER_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.RAVAGER_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) {}
}
