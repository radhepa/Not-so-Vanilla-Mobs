package dev.nsvmobs.entity;

import java.util.EnumSet;
import java.util.HashSet;
import java.util.Set;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * A hulking brute of basalt and magma from the Basalt Deltas. It walks across lava as if it were
 * stone. Up close it raises both fists and slams the ground: a ring of fire races outward along the
 * ground and burns everything standing on it (jump it!). Further off it lobs chunks of magma. Badly
 * hurt, it enrages: faster, and slamming twice as often.
 */
public class Cinderhulk extends Monster {
    public static final byte IDLE = 0, SLAM_WINDUP = 1, SLAMMING = 2, HURLING = 3;
    private static final EntityDataAccessor<Byte> ACTION = SynchedEntityData.defineId(Cinderhulk.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Boolean> ENRAGED = SynchedEntityData.defineId(Cinderhulk.class, EntityDataSerializers.BOOLEAN);
    private static final Identifier RAGE_SPEED = Identifier.fromNamespaceAndPath("nsvmobs", "cinderhulk_rage");
    static final byte SLAM_EVENT = 90;
    public static final int SLAM_WINDUP_TICKS = 24, HURL_WINDUP_TICKS = 16;
    /** The shockwave: starts at the fists, grows this much per tick, out to this radius. */
    public static final float WAVE_START = 1.0F, WAVE_SPEED = 0.5F, WAVE_MAX = 9.0F;
    static final float WAVE_DAMAGE = 9.0F;

    private int actionStart;
    /** Server: the running shockwave (its age in ticks, or -1), where it started and who it already hit. */
    private int waveAge = -1;
    private Vec3 waveCenter = Vec3.ZERO;
    private final Set<Integer> waveHit = new HashSet<>();
    /** Client: the shockwave to draw. */
    private int clientWaveStart = -1;
    private Vec3 clientWaveCenter = Vec3.ZERO;

    public Cinderhulk(EntityType<? extends Cinderhulk> type, Level level) {
        super(type, level);
        this.xpReward = 30;
        this.setPathfindingMalus(PathType.LAVA, 8.0F);
        this.setPathfindingMalus(PathType.FIRE_IN_NEIGHBOR, 0.0F);
        this.setPathfindingMalus(PathType.FIRE, 0.0F);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 90.0)
                .add(Attributes.ATTACK_DAMAGE, 11.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.2)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ACTION, IDLE);
        builder.define(ENRAGED, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new SlamGoal());
        this.goalSelector.addGoal(3, new HurlGoal());
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.0, false));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.6));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 10.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    public byte action() { return this.entityData.get(ACTION); }
    public boolean isEnraged() { return this.entityData.get(ENRAGED); }

    /** Client: ticks (with partial) since the current action began. */
    public float actionAge(float partialTick) {
        return this.tickCount - this.actionStart + partialTick;
    }

    public void setAction(byte action) {
        this.entityData.set(ACTION, action);
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (ACTION.equals(key)) this.actionStart = this.tickCount;
    }

    /** It walks on lava like a strider walks on lava. */
    @Override
    public boolean canStandOnFluid(FluidState fluid) {
        return fluid.is(FluidTags.LAVA);
    }

    /** Basalt cools and cracks in water and rain. */
    @Override public boolean isSensitiveToWater() { return true; }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            target.igniteForSeconds(3.0F);
            target.push(0, 0.3, 0);
            target.needsSync = true;
        }
        return hit;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive() && !this.isEnraged() && this.getHealth() < this.getMaxHealth() * 0.35F) this.enrage();
        return hurt;
    }

    /** Below a third of its health its cracks blaze up and it speeds up. */
    void enrage() {
        this.entityData.set(ENRAGED, true);
        var speed = this.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null && !speed.hasModifier(RAGE_SPEED)) {
            speed.addPermanentModifier(new AttributeModifier(RAGE_SPEED, 0.3, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        this.playSound(SoundEvents.RAVAGER_ROAR, 2.0F, 0.5F);
        if (this.level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.LAVA, this.getX(), this.getY() + 1.5, this.getZ(), 20, 0.6, 0.8, 0.6, 0.0);
        }
    }

    // -- the slam's shockwave ---------------------------------------------------------------------

    /** Start a shockwave at its feet; the server hurts what it passes, the client draws it. */
    public void slam(ServerLevel level) {
        this.waveAge = 0;
        this.waveCenter = this.position();
        this.waveHit.clear();
        level.broadcastEntityEvent(this, SLAM_EVENT);
        this.playSound(SoundEvents.GENERIC_EXPLODE.value(), 1.6F, 0.5F);
        this.playSound(SoundEvents.ANVIL_LAND, 1.2F, 0.5F);
    }

    /** The ring's radius after {@code age} ticks. */
    public static float waveRadius(float age) {
        return WAVE_START + age * WAVE_SPEED;
    }

    private void tickWave(ServerLevel level) {
        if (this.waveAge < 0) return;
        float r = waveRadius(this.waveAge);
        if (r > WAVE_MAX) {
            this.waveAge = -1;
            return;
        }
        this.waveAge++;
        var box = new net.minecraft.world.phys.AABB(this.waveCenter, this.waveCenter).inflate(r + 1.0, 1.5, r + 1.0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, e -> e != this && e.isAlive() && !(e instanceof Cinderhulk))) {
            if (this.waveHit.contains(e.getId())) continue;
            double dx = e.getX() - this.waveCenter.x, dz = e.getZ() - this.waveCenter.z;
            double d = Math.sqrt(dx * dx + dz * dz);
            // the wave runs along the ground: whoever is in the air when it passes is safe
            if (Math.abs(d - r) > 0.8 || !e.onGround() || Math.abs(e.getY() - this.waveCenter.y) > 1.25) continue;
            this.waveHit.add(e.getId());
            if (e instanceof Player p && (p.isCreative() || p.isSpectator())) continue;
            if (e.hurtServer(level, this.damageSources().mobAttack(this), WAVE_DAMAGE)) {
                e.igniteForSeconds(3.0F);
                double len = Math.max(0.1, d);
                e.push(dx / len * 0.6, 0.55, dz / len * 0.6);
                e.needsSync = true;
            }
        }
    }

    @Override
    public void handleEntityEvent(byte id) {
        if (id == SLAM_EVENT) {
            this.clientWaveStart = this.tickCount;
            this.clientWaveCenter = this.position();
        } else {
            super.handleEntityEvent(id);
        }
    }

    /** Client: the ring of fire and flying basalt, drawn as particles while the wave runs. */
    private void drawWave() {
        if (this.clientWaveStart < 0) return;
        int age = this.tickCount - this.clientWaveStart;
        float r = waveRadius(age);
        if (r > WAVE_MAX) {
            this.clientWaveStart = -1;
            return;
        }
        Level level = this.level();
        BlockState ground = level.getBlockState(BlockPos.containing(this.clientWaveCenter).below());
        int points = Mth.ceil(r * 7.0F);
        for (int i = 0; i < points; i++) {
            float a = (i + this.random.nextFloat()) / points * Mth.TWO_PI;
            double x = this.clientWaveCenter.x + Mth.cos(a) * r, z = this.clientWaveCenter.z + Mth.sin(a) * r;
            double y = this.clientWaveCenter.y + 0.1;
            level.addParticle(ParticleTypes.FLAME, x, y, z, 0, 0.06 + this.random.nextFloat() * 0.05, 0);
            if (this.random.nextInt(3) == 0 && !ground.isAir()) {
                level.addParticle(new BlockParticleOption(ParticleTypes.BLOCK, ground), x, y, z, 0, 0.25, 0);
            }
            if (this.random.nextInt(12) == 0) level.addParticle(ParticleTypes.LAVA, x, y, z, 0, 0, 0);
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel level) {
            this.tickWave(level);
        } else {
            this.drawWave();
            int glow = this.isEnraged() ? 2 : 10;
            if (this.random.nextInt(glow) == 0) {
                this.level().addParticle(this.isEnraged() ? ParticleTypes.FLAME : ParticleTypes.SMOKE,
                        this.getRandomX(0.6), this.getY() + 1.0 + this.random.nextDouble() * 1.6, this.getRandomZ(0.6), 0, 0.03, 0);
            }
        }
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Enraged", this.isEnraged());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(ENRAGED, input.getBooleanOr("Enraged", false));
    }

    @Override protected float getSoundVolume() { return 1.3F; }
    @Override public float getVoicePitch() { return 0.55F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.RAVAGER_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.IRON_GOLEM_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.IRON_GOLEM_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.IRON_GOLEM_STEP, 1.0F, 0.6F); }

    /** Within 7 blocks: both fists up, then down on the ground. */
    final class SlamGoal extends Goal {
        private int ticks, next;

        SlamGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Cinderhulk.this.getTarget();
            return t != null && t.isAlive() && Cinderhulk.this.tickCount >= this.next && Cinderhulk.this.onGround()
                    && Cinderhulk.this.distanceToSqr(t) < 49.0;
        }

        @Override public boolean canContinueToUse() { return this.ticks < SLAM_WINDUP_TICKS + 12; }

        @Override
        public void start() {
            this.ticks = 0;
            Cinderhulk.this.getNavigation().stop();
            Cinderhulk.this.setAction(SLAM_WINDUP);
            Cinderhulk.this.playSound(SoundEvents.RAVAGER_ROAR, 1.5F, 0.6F);
        }

        @Override
        public void stop() {
            Cinderhulk.this.setAction(IDLE);
            this.next = Cinderhulk.this.tickCount + (Cinderhulk.this.isEnraged() ? 70 : 140);
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = Cinderhulk.this.getTarget();
            if (t != null && this.ticks < SLAM_WINDUP_TICKS) Cinderhulk.this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (this.ticks % 6 == 0 && this.ticks < SLAM_WINDUP_TICKS) Cinderhulk.this.playSound(SoundEvents.LAVA_POP, 1.5F, 0.6F);
            if (++this.ticks == SLAM_WINDUP_TICKS && Cinderhulk.this.level() instanceof ServerLevel level) {
                Cinderhulk.this.setAction(SLAMMING);
                Cinderhulk.this.slam(level);
            }
        }
    }

    /** From 7 to 24 blocks away: a chunk of magma, lobbed in an arc. */
    final class HurlGoal extends Goal {
        private int ticks, next;

        HurlGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = Cinderhulk.this.getTarget();
            if (t == null || !t.isAlive() || Cinderhulk.this.tickCount < this.next) return false;
            double d = Cinderhulk.this.distanceToSqr(t);
            return d > 49.0 && d < 576.0 && Cinderhulk.this.hasLineOfSight(t);
        }

        @Override public boolean canContinueToUse() { return this.ticks < HURL_WINDUP_TICKS + 6; }

        @Override
        public void start() {
            this.ticks = 0;
            Cinderhulk.this.getNavigation().stop();
            Cinderhulk.this.setAction(HURLING);
        }

        @Override
        public void stop() {
            Cinderhulk.this.setAction(IDLE);
            this.next = Cinderhulk.this.tickCount + (Cinderhulk.this.isEnraged() ? 60 : 100);
        }

        @Override public boolean requiresUpdateEveryTick() { return true; }

        @Override
        public void tick() {
            LivingEntity t = Cinderhulk.this.getTarget();
            if (t == null) return;
            Cinderhulk.this.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (++this.ticks == HURL_WINDUP_TICKS) {
                Boulder magma = new Boulder(NsvEntities.BOULDER, Cinderhulk.this, true);
                magma.setPos(Cinderhulk.this.getX(), Cinderhulk.this.getY() + 2.4, Cinderhulk.this.getZ());
                magma.aimAt(t, 1.3F, 3.0F);
                Cinderhulk.this.level().addFreshEntity(magma);
                Cinderhulk.this.playSound(SoundEvents.BLAZE_SHOOT, 1.5F, 0.5F);
            }
        }
    }
}
