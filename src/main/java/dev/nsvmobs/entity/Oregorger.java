package dev.nsvmobs.entity;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
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
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A massive armoured beast of the deep caves. Its plates turn most blows (12 armour). It curls into
 * a ball, revs, and bowls straight at you, flattening whatever it hits; dodge so it rolls into a
 * wall instead and it's left stunned on the cave floor, its armour useless, for three and a half
 * seconds. Between fights it eats exposed ore veins (with mobGriefing on) and keeps the ore in its
 * gut: kill it and you get it all back.
 */
public class Oregorger extends Monster {
    public static final byte WALKING = 0, CURLING = 1, ROLLING = 2, STUNNED = 3, EATING = 4;
    private static final EntityDataAccessor<Byte> MODE = SynchedEntityData.defineId(Oregorger.class, EntityDataSerializers.BYTE);
    private static final Identifier STUN_ARMOR = Identifier.fromNamespaceAndPath("nsvmobs", "oregorger_stunned");
    public static final int CURL_TICKS = 20, ROLL_MAX = 50, STUN_TICKS = 70, EAT_TICKS = 30;
    static final double ROLL_SPEED = 0.6;
    static final float ROLL_DAMAGE = 12.0F;
    private int modeStart;
    private Vec3 rollDir = Vec3.ZERO;
    private final Set<Integer> rolledOver = new HashSet<>();
    private final List<ItemStack> gut = new ArrayList<>();
    private @Nullable BlockPos meal;

    public Oregorger(EntityType<? extends Oregorger> type, Level level) {
        super(type, level);
        this.xpReward = 25;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 80.0)
                .add(Attributes.ATTACK_DAMAGE, 9.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    /** Deep caves only (below y 0). */
    public static boolean checkSpawnRules(EntityType<Oregorger> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        return (EntitySpawnReason.isSpawner(reason) || pos.getY() < 0) && Monster.checkMonsterSpawnRules(type, level, reason, pos, random);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(MODE, WALKING);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new RollGoal());
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.0, true));
        this.goalSelector.addGoal(5, new EatOreGoal());
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.7));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    public byte mode() { return this.entityData.get(MODE); }

    public void setMode(byte mode) {
        this.entityData.set(MODE, mode);
        this.modeStart = this.tickCount;
    }

    public float modeAge(float partialTick) {
        return this.tickCount - this.modeStart + partialTick;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (MODE.equals(key)) this.modeStart = this.tickCount;
    }

    public boolean isStunned() { return this.mode() == STUNNED; }
    public boolean isBall() { return this.mode() == ROLLING || this.mode() == CURLING && this.tickCount - this.modeStart > CURL_TICKS / 2; }
    public List<ItemStack> gut() { return this.gut; }

    /** Curling, rolling and stunned, it isn't steering: the roll runs on its own until it ends. */
    @Override
    protected boolean isImmobile() {
        byte m = this.mode();
        return super.isImmobile() || m == CURLING || m == ROLLING || m == STUNNED;
    }

    /** Curl up and, a second later, roll off along {@code dir} (horizontal). */
    public void curl(Vec3 dir) {
        this.rollDir = new Vec3(dir.x, 0, dir.z).normalize();
        this.setMode(CURLING);
        this.getNavigation().stop();
        this.playSound(SoundEvents.ARMADILLO_ROLL, 1.5F, 0.5F);
    }

    @Override
    public void aiStep() {
        if (this.level() instanceof ServerLevel level) this.tickMode(level);
        super.aiStep();
        if (this.level() instanceof ServerLevel level && this.mode() == ROLLING) this.flatten(level);
        if (this.level().isClientSide() && this.isStunned() && this.tickCount % 4 == 0) {
            this.level().addParticle(ParticleTypes.CRIT, this.getX() + Mth.cos(this.tickCount * 0.3F) * 0.6, this.getY() + 1.4,
                    this.getZ() + Mth.sin(this.tickCount * 0.3F) * 0.6, 0, 0.05, 0);
        }
    }

    /** The curl, the roll, the crash and the daze run here, outside the goals, so they always finish. */
    private void tickMode(ServerLevel level) {
        int age = this.tickCount - this.modeStart;
        switch (this.mode()) {
            case CURLING -> {
                this.getNavigation().stop();
                if (age % 4 == 0) {
                    // revving: grit sprays out behind it
                    BlockState ground = level.getBlockState(this.getBlockPosBelowThatAffectsMyMovement());
                    if (!ground.isAir()) level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground),
                            this.getX() - this.rollDir.x, this.getY() + 0.1, this.getZ() - this.rollDir.z, 8, 0.3, 0.1, 0.3, 0.2);
                }
                if (age >= CURL_TICKS) {
                    this.setMode(ROLLING);
                    this.rolledOver.clear();
                    this.playSound(SoundEvents.ARMADILLO_LAND, 2.0F, 0.5F);
                }
            }
            case ROLLING -> {
                this.getNavigation().stop();
                if (age > 2 && this.horizontalCollision) {
                    this.crash(level);
                } else if (age >= ROLL_MAX) {
                    this.setMode(WALKING);
                } else {
                    this.setDeltaMovement(this.rollDir.x * ROLL_SPEED, this.getDeltaMovement().y, this.rollDir.z * ROLL_SPEED);
                    this.setYRot((float) (Mth.atan2(this.rollDir.z, this.rollDir.x) * Mth.RAD_TO_DEG) - 90.0F);
                    this.yBodyRot = this.getYRot();
                    if (age % 5 == 0) this.playSound(SoundEvents.ARMADILLO_STEP, 1.5F, 0.4F);
                }
            }
            case STUNNED -> {
                if (age >= STUN_TICKS) {
                    var armor = this.getAttribute(Attributes.ARMOR);
                    if (armor != null) armor.removeModifier(STUN_ARMOR);
                    this.setMode(WALKING);
                }
            }
            default -> {}
        }
    }

    /** Anything it rolls into is flattened and thrown aside (once per roll). */
    private void flatten(ServerLevel level) {
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(0.3),
                e -> e != this && e.isAlive() && !(e instanceof Oregorger) && !this.rolledOver.contains(e.getId()))) {
            if (e instanceof Player p && (p.isCreative() || p.isSpectator())) continue;
            this.rolledOver.add(e.getId());
            if (e.hurtServer(level, this.damageSources().mobAttack(this), ROLL_DAMAGE)) {
                e.push(this.rollDir.x * 1.4, 0.45, this.rollDir.z * 1.4);
                e.needsSync = true;
                this.playSound(SoundEvents.GOAT_RAM_IMPACT, 1.5F, 0.6F);
            }
        }
    }

    /** It hit a wall: dazed, uncurled, its belly exposed. */
    void crash(ServerLevel level) {
        this.setMode(STUNNED);
        this.setDeltaMovement(-this.rollDir.x * 0.3, 0.3, -this.rollDir.z * 0.3);
        var armor = this.getAttribute(Attributes.ARMOR);
        if (armor != null && !armor.hasModifier(STUN_ARMOR)) {
            armor.addTransientModifier(new AttributeModifier(STUN_ARMOR, -1.0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        }
        this.playSound(SoundEvents.RAVAGER_STUNNED, 1.5F, 0.6F);
        this.playSound(SoundEvents.ANVIL_LAND, 1.0F, 0.5F);
        BlockPos wall = BlockPos.containing(this.position().add(this.rollDir.scale(1.2)).add(0, 0.5, 0));
        BlockState hit = level.getBlockState(wall);
        if (!hit.isAir()) level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, hit), wall.getX() + 0.5, wall.getY() + 0.5,
                wall.getZ() + 0.5, 40, 0.5, 0.5, 0.5, 0.2);
    }

    // -- eating ore ---------------------------------------------------------------------------------

    /** What an ore block gives when it eats it (and gives back when it dies), or empty for non-ore. */
    static ItemStack oreYield(BlockState s, RandomSource random) {
        if (s.is(BlockTags.IRON_ORES)) return new ItemStack(Items.RAW_IRON);
        if (s.is(BlockTags.COPPER_ORES)) return new ItemStack(Items.RAW_COPPER, 2 + random.nextInt(3));
        if (s.is(BlockTags.GOLD_ORES)) return new ItemStack(Items.RAW_GOLD);
        if (s.is(Blocks.COAL_ORE) || s.is(Blocks.DEEPSLATE_COAL_ORE)) return new ItemStack(Items.COAL);
        if (s.is(Blocks.REDSTONE_ORE) || s.is(Blocks.DEEPSLATE_REDSTONE_ORE)) return new ItemStack(Items.REDSTONE, 4 + random.nextInt(2));
        if (s.is(Blocks.LAPIS_ORE) || s.is(Blocks.DEEPSLATE_LAPIS_ORE)) return new ItemStack(Items.LAPIS_LAZULI, 4 + random.nextInt(5));
        if (s.is(Blocks.DIAMOND_ORE) || s.is(Blocks.DEEPSLATE_DIAMOND_ORE)) return new ItemStack(Items.DIAMOND);
        if (s.is(Blocks.EMERALD_ORE) || s.is(Blocks.DEEPSLATE_EMERALD_ORE)) return new ItemStack(Items.EMERALD);
        return ItemStack.EMPTY;
    }

    /** An ore block it can reach: at least one face open to air. */
    private boolean exposedOre(ServerLevel level, BlockPos p) {
        if (oreYield(level.getBlockState(p), this.random).isEmpty()) return false;
        for (Direction d : Direction.values()) {
            if (level.getBlockState(p.relative(d)).isAir()) return true;
        }
        return false;
    }

    /** Chew an ore block down to bare rock and keep the ore. */
    public boolean eat(ServerLevel level, BlockPos p) {
        BlockState s = level.getBlockState(p);
        ItemStack ore = oreYield(s, this.random);
        if (ore.isEmpty()) return false;
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, s), p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 30, 0.4, 0.4, 0.4, 0.1);
        level.setBlockAndUpdate(p, p.getY() < 0 ? Blocks.DEEPSLATE.defaultBlockState() : Blocks.STONE.defaultBlockState());
        if (this.gut.size() < 64) this.gut.add(ore);
        this.heal(8.0F);
        this.playSound(SoundEvents.GENERIC_EAT.value(), 1.5F, 0.5F);
        this.playSound(SoundEvents.STONE_BREAK, 1.2F, 0.6F);
        return true;
    }

    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean killedByPlayer) {
        super.dropCustomDeathLoot(level, source, killedByPlayer);
        for (ItemStack s : this.gut) this.spawnAtLocation(level, s);
        this.gut.clear();
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.store("Gorged", ItemStack.CODEC.listOf(), List.copyOf(this.gut));
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.gut.clear();
        input.read("Gorged", ItemStack.CODEC.listOf()).ifPresent(this.gut::addAll);
    }

    @Override protected float getSoundVolume() { return 1.2F; }
    @Override public float getVoicePitch() { return 0.5F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.ARMADILLO_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return this.isStunned() ? SoundEvents.ARMADILLO_HURT : SoundEvents.ARMADILLO_HURT_REDUCED; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.ARMADILLO_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.IRON_GOLEM_STEP, 0.6F, 0.5F); }

    /** From 5 to 20 blocks away, with a clear line: curl up and bowl at the target. */
    final class RollGoal extends Goal {
        private int next;

        RollGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            Oregorger o = Oregorger.this;
            LivingEntity t = o.getTarget();
            if (t == null || !t.isAlive() || o.mode() != WALKING || o.tickCount < this.next || !o.onGround()) return false;
            double d = o.distanceToSqr(t);
            return d > 25.0 && d < 400.0 && o.hasLineOfSight(t);
        }

        @Override public boolean canContinueToUse() { return Oregorger.this.mode() != WALKING; }

        @Override
        public void start() {
            Oregorger o = Oregorger.this;
            LivingEntity t = o.getTarget();
            if (t != null) o.curl(t.position().subtract(o.position()));
        }

        @Override
        public void stop() {
            this.next = Oregorger.this.tickCount + 120 + Oregorger.this.random.nextInt(40);
        }

    }

    /** With nothing to fight (and mobGriefing on), it sniffs out an exposed ore vein and eats it. */
    final class EatOreGoal extends Goal {
        private int ticks, next;

        EatOreGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            Oregorger o = Oregorger.this;
            if (o.getTarget() != null || o.mode() != WALKING || o.tickCount < this.next || !(o.level() instanceof ServerLevel level)
                    || !Griefing.allowed(level)) return false;
            this.next = o.tickCount + 200 + o.random.nextInt(200);
            BlockPos at = o.blockPosition();
            BlockPos best = null;
            double bestD = Double.MAX_VALUE;
            for (BlockPos p : BlockPos.betweenClosed(at.offset(-6, -2, -6), at.offset(6, 3, 6))) {
                double d = p.distSqr(at);
                if (d < bestD && o.exposedOre(level, p)) {
                    best = p.immutable();
                    bestD = d;
                }
            }
            o.meal = best;
            return best != null;
        }

        @Override
        public boolean canContinueToUse() {
            Oregorger o = Oregorger.this;
            return o.meal != null && o.getTarget() == null && this.ticks < 300 && (o.mode() == WALKING || o.mode() == EATING);
        }

        @Override
        public void start() {
            this.ticks = 0;
            BlockPos m = Oregorger.this.meal;
            if (m != null) Oregorger.this.getNavigation().moveTo(m.getX() + 0.5, m.getY(), m.getZ() + 0.5, 0.9);
        }

        @Override
        public void stop() {
            if (Oregorger.this.mode() == EATING) Oregorger.this.setMode(WALKING);
            Oregorger.this.meal = null;
        }

        @Override
        public void tick() {
            Oregorger o = Oregorger.this;
            BlockPos m = o.meal;
            if (m == null) return;
            this.ticks++;
            o.getLookControl().setLookAt(m.getX() + 0.5, m.getY() + 0.5, m.getZ() + 0.5);
            boolean close = o.position().distanceToSqr(m.getX() + 0.5, m.getY() + 0.5, m.getZ() + 0.5) < 6.25;
            if (o.mode() == WALKING && close) {
                o.getNavigation().stop();
                o.setMode(EATING);
            } else if (o.mode() == EATING && o.tickCount - o.modeStart >= EAT_TICKS) {
                o.eat((ServerLevel) o.level(), m);
                o.setMode(WALKING);
                o.meal = null;
            } else if (o.mode() == WALKING && o.getNavigation().isDone()) {
                o.meal = null;   // couldn't get there
            }
        }
    }
}
