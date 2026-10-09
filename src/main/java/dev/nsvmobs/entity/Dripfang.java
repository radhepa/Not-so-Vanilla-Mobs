package dev.nsvmobs.entity;

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
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
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
import org.jspecify.annotations.Nullable;

/**
 * A Dripstone Caves predator that hangs from the ceiling looking exactly like pointed dripstone. When
 * someone walks underneath it drops on them point-first, then fights on the ground. Left alone for a
 * while, it springs back up to the ceiling to wait again.
 */
public class Dripfang extends Monster {
    private static final EntityDataAccessor<Boolean> HANGING = SynchedEntityData.defineId(Dripfang.class, EntityDataSerializers.BOOLEAN);
    /** How far below it a victim can be, and how close to straight below. */
    static final int DROP_REACH = 12;
    static final double DROP_RADIUS = 1.3;
    private boolean falling, climbing;
    private int idleTicks, climbTicks;

    public Dripfang(EntityType<? extends Dripfang> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 18.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(HANGING, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(3, new LeapAtTargetGoal(this, 0.35F));
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.15, true));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    public boolean isHanging() {
        return this.entityData.get(HANGING);
    }

    private void setHanging(boolean hanging) {
        this.entityData.set(HANGING, hanging);
        this.setNoGravity(hanging);
        if (hanging) {
            this.setDeltaMovement(0, 0, 0);
            this.getNavigation().stop();
            this.setTarget(null);
        }
    }

    /** Hanging, it runs no AI: it's a stalactite until something walks underneath. */
    @Override
    protected boolean isImmobile() {
        return super.isImmobile() || this.isHanging();
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData groupData) {
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, groupData);
        if (reason == EntitySpawnReason.NATURAL || reason == EntitySpawnReason.CHUNK_GENERATION || EntitySpawnReason.isSpawner(reason)) {
            BlockPos ceiling = findCeiling(level, this.blockPosition());
            if (ceiling != null) {
                this.setPos(this.getX(), ceiling.getY() - this.getBbHeight(), this.getZ());
                this.setHanging(true);
            }
        }
        return data;
    }

    /** The first sturdy ceiling block straight above, within reach and with a clear drop under it. */
    static @Nullable BlockPos findCeiling(ServerLevelAccessor level, BlockPos from) {
        BlockPos.MutableBlockPos p = from.mutable();
        for (int i = 0; i < DROP_REACH; i++) {
            p.move(Direction.UP);
            BlockState s = level.getBlockState(p);
            if (!s.getCollisionShape(level, p).isEmpty()) {
                return i >= 2 && s.isFaceSturdy(level, p, Direction.DOWN) ? p.immutable() : null;
            }
        }
        return null;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        if (this.isHanging()) {
            this.setDeltaMovement(0, 0, 0);
            BlockPos above = BlockPos.containing(this.getX(), this.getBoundingBox().maxY + 0.1, this.getZ());
            if (level.getBlockState(above).getCollisionShape(level, above).isEmpty()) {
                drop(level);   // the ceiling's gone
            } else if (this.tickCount % 4 == 0) {
                watchBelow(level);
            }
            return;
        }
        if (this.falling) {
            for (var victim : level.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class, this.getBoundingBox().inflate(0.2),
                    e -> e != this && e.isAlive() && !(e instanceof Dripfang))) {
                victim.hurtServer(level, this.damageSources().fallingStalactite(this), 6.0F);
                this.falling = false;
            }
            if (this.onGround() || this.isInWater()) {
                this.falling = false;
                this.playSound(SoundEvents.POINTED_DRIPSTONE_LAND, 1.0F, 0.8F);
            }
        }
        if (this.climbing) {
            climb(level);
            return;
        }
        this.idleTicks = this.getTarget() == null ? this.idleTicks + 1 : 0;
        if (this.idleTicks > 300 && this.onGround() && this.tickCount % 20 == 0 && findCeiling(level, this.blockPosition()) != null) {
            // spring back up to the ceiling
            this.climbing = true;
            this.climbTicks = 0;
            this.setNoGravity(true);
            this.playSound(SoundEvents.SPIDER_AMBIENT, 1.0F, 0.6F);
        }
    }

    private void climb(ServerLevel level) {
        this.getNavigation().stop();
        this.setDeltaMovement(0, 0.45, 0);
        if (this.verticalCollision && this.climbTicks > 0 && this.getDeltaMovement().y >= 0 || this.climbTicks > 40) {
            this.climbing = false;
            this.idleTicks = 0;
            BlockPos above = BlockPos.containing(this.getX(), this.getBoundingBox().maxY + 0.1, this.getZ());
            if (!level.getBlockState(above).getCollisionShape(level, above).isEmpty()) {
                this.setHanging(true);
                this.playSound(SoundEvents.POINTED_DRIPSTONE_PLACE, 1.0F, 0.8F);
            } else {
                this.setNoGravity(false);
            }
        }
        this.climbTicks++;
    }

    /** Anyone (but creative/spectator players) right below and in plain view sets it off. */
    private void watchBelow(ServerLevel level) {
        AABB below = new AABB(this.getX() - DROP_RADIUS, this.getY() - DROP_REACH, this.getZ() - DROP_RADIUS,
                this.getX() + DROP_RADIUS, this.getY(), this.getZ() + DROP_RADIUS);
        for (Player p : level.getEntitiesOfClass(Player.class, below, p -> p.isAlive() && !p.isCreative() && !p.isSpectator())) {
            if (this.hasLineOfSight(p)) {
                drop(level);
                this.setTarget(p);
                return;
            }
        }
    }

    private void drop(ServerLevel level) {
        if (!this.isHanging()) return;
        this.setHanging(false);
        this.falling = true;
        this.setDeltaMovement(0, -0.6, 0);
        this.playSound(SoundEvents.POINTED_DRIPSTONE_FALL, 1.2F, 0.8F);
        BlockPos above = BlockPos.containing(this.getX(), this.getBoundingBox().maxY + 0.1, this.getZ());
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.DRIPSTONE_BLOCK.defaultBlockState()),
                this.getX(), this.getBoundingBox().maxY, this.getZ(), 12, 0.3, 0.1, 0.3, 0.05);
        level.levelEvent(2001, above, net.minecraft.world.level.block.Block.getId(level.getBlockState(above)));
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isHanging()) drop(level);
        return hurt;
    }

    @Override public boolean isPushable() { return !this.isHanging() && super.isPushable(); }
    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Hanging", this.isHanging());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.setHanging(input.getBooleanOr("Hanging", false));
    }

    @Override public float getVoicePitch() { return 0.6F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return this.isHanging() ? null : SoundEvents.SILVERFISH_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.DRIPSTONE_BLOCK_HIT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.DRIPSTONE_BLOCK_BREAK; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.SPIDER_STEP, 0.15F, 0.7F); }
}
