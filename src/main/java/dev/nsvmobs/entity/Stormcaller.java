package dev.nsvmobs.entity;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.illager.SpellcasterIllager;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.raid.Raider;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * An illager storm mystic. It keeps its distance and calls lightning: sparks crackle in rings on
 * the ground under and around you for a second and a half (move!), then bolts strike every marked
 * spot. Get close and it blasts you away with a gust of wind. In a thunderstorm it calls more bolts,
 * faster.
 */
public class Stormcaller extends SpellcasterIllager {
    /** A spot marked for a lightning strike. */
    private record Mark(Vec3 pos, int strikeAt) {}

    static final float BOLT_DAMAGE = 7.0F, BOLT_RADIUS = 1.6F;
    public static final int MARK_TICKS = 30, STORM_MARK_TICKS = 20;
    private final List<Mark> marks = new ArrayList<>();

    public Stormcaller(EntityType<? extends Stormcaller> type, Level level) {
        super(type, level);
        this.xpReward = 15;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 36.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.MOVEMENT_SPEED, 0.5)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new CastingGoal());
        this.goalSelector.addGoal(2, new GaleSpellGoal());
        this.goalSelector.addGoal(3, new AvoidEntityGoal<>(this, Player.class, 8.0F, 0.6, 1.0));
        this.goalSelector.addGoal(4, new LightningSpellGoal());
        this.goalSelector.addGoal(8, new RandomStrollGoal(this, 0.6));
        this.goalSelector.addGoal(9, new LookAtPlayerGoal(this, Player.class, 3.0F, 1.0F));
        this.goalSelector.addGoal(10, new LookAtPlayerGoal(this, Mob.class, 8.0F));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this, Raider.class).setAlertOthers());
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true).setUnseenMemoryTicks(300));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, AbstractVillager.class, false).setUnseenMemoryTicks(300));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, false));
    }

    /** Natural spawns never come with a captain's banner. */
    @Override
    public boolean canBeLeader() {
        return false;
    }

    @Override
    public void applyRaidBuffs(ServerLevel level, int wave, boolean isCaptain) {}

    /** Raise both arms as if casting (for a few seconds' worth of ticks; only an AI tick ends it). */
    public void raiseArms() {
        this.setIsCastingSpell(IllagerSpell.DISAPPEAR);
        this.spellCastingTickCount = 60;
    }

    public int pendingStrikes() {
        return this.marks.size();
    }

    // -- lightning --------------------------------------------------------------------------------

    /** Mark spots for lightning around a target: where they stand, where they're heading, and nearby. */
    public void callLightning(ServerLevel level, LivingEntity target) {
        boolean storm = level.isThundering();
        int fuse = storm ? STORM_MARK_TICKS : MARK_TICKS;
        int count = storm ? 5 : 3;
        Vec3 at = target.position();
        Vec3 ahead = at.add(target.getDeltaMovement().multiply(18.0, 0.0, 18.0));
        this.mark(level, at, fuse);
        this.mark(level, ahead.distanceToSqr(at) > 1.0 ? ahead : at.add(this.random.nextGaussian() * 2.5, 0, this.random.nextGaussian() * 2.5), fuse);
        for (int i = 2; i < count; i++) {
            float a = this.random.nextFloat() * Mth.TWO_PI;
            double r = 2.0 + this.random.nextDouble() * 2.0;
            this.mark(level, at.add(Mth.cos(a) * r, 0, Mth.sin(a) * r), fuse + i * 3);
        }
    }

    private void mark(ServerLevel level, Vec3 near, int fuse) {
        Vec3 ground = this.groundUnder(level, near);
        if (ground == null) return;
        this.marks.add(new Mark(ground, this.tickCount + fuse));
        level.playSound(null, ground.x, ground.y, ground.z, SoundEvents.AXE_SCRAPE.value(), this.getSoundSource(), 1.0F, 1.6F);
    }

    /** The ground surface at or a little below a point (lightning strikes the ground, not the air). */
    private @Nullable Vec3 groundUnder(ServerLevel level, Vec3 p) {
        BlockPos.MutableBlockPos b = BlockPos.containing(p.x, p.y + 1.0, p.z).mutable();
        for (int i = 0; i < 8; i++, b.move(0, -1, 0)) {
            if (!level.getBlockState(b).getCollisionShape(level, b).isEmpty()) return new Vec3(p.x, b.getY() + 1.0, p.z);
        }
        return null;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level) || this.marks.isEmpty()) return;
        this.marks.removeIf(m -> {
            int left = m.strikeAt - this.tickCount;
            if (left > 0) {
                if (left % 2 == 0) {
                    // a crackling ring around the marked spot
                    for (int i = 0; i < 6; i++) {
                        float a = this.random.nextFloat() * Mth.TWO_PI;
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, m.pos.x + Mth.cos(a) * BOLT_RADIUS * 0.8, m.pos.y + 0.05,
                                m.pos.z + Mth.sin(a) * BOLT_RADIUS * 0.8, 1, 0, 0.1, 0, 0.0);
                    }
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, m.pos.x, m.pos.y + 0.1, m.pos.z, 2, 0.15, 0.4, 0.15, 0.05);
                }
                return false;
            }
            this.strike(level, m.pos);
            return true;
        });
    }

    private void strike(ServerLevel level, Vec3 at) {
        LightningBolt bolt = EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
        if (bolt != null) {
            bolt.snapTo(at.x, at.y, at.z);
            bolt.setVisualOnly(true);   // no fires, no charged creepers, no witches: the damage is ours
            level.addFreshEntity(bolt);
        }
        AABB box = new AABB(at.x - BOLT_RADIUS, at.y - 1.0, at.z - BOLT_RADIUS, at.x + BOLT_RADIUS, at.y + 3.0, at.z + BOLT_RADIUS);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, e -> e.isAlive() && !(e instanceof Raider))) {
            if (e instanceof Player p && (p.isCreative() || p.isSpectator())) continue;
            if (e.hurtServer(level, this.damageSources().mobAttack(this), BOLT_DAMAGE)) e.igniteForSeconds(2.0F);
        }
    }

    @Override
    public void die(DamageSource source) {
        this.marks.clear();   // the storm dies with its caller
        super.die(source);
    }

    // -- gale -------------------------------------------------------------------------------------

    /** A blast of wind that throws everything within 5 blocks away from it. */
    void gale(ServerLevel level) {
        level.sendParticles(ParticleTypes.GUST_EMITTER_LARGE, this.getX(), this.getY() + 1.0, this.getZ(), 1, 0, 0, 0, 0);
        this.playSound(SoundEvents.WIND_CHARGE_BURST.value(), 1.5F, 0.8F);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(5.0),
                e -> e != this && e.isAlive() && !(e instanceof Raider))) {
            if (e instanceof Player p && (p.isCreative() || p.isSpectator())) continue;
            Vec3 away = e.position().subtract(this.position());
            double flat = Math.max(0.3, Math.sqrt(away.x * away.x + away.z * away.z));
            e.hurtServer(level, this.damageSources().mobAttack(this), 2.0F);
            e.push(away.x / flat * 1.6, 0.6, away.z / flat * 1.6);
            e.needsSync = true;
        }
    }

    @Override public SoundEvent getCelebrateSound() { return SoundEvents.EVOKER_CELEBRATE; }
    @Override protected SoundEvent getCastingSoundEvent() { return SoundEvents.EVOKER_CAST_SPELL; }
    @Override public float getVoicePitch() { return 0.85F + this.random.nextFloat() * 0.1F; }
    @Override protected SoundEvent getAmbientSound() { return SoundEvents.EVOKER_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.EVOKER_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.EVOKER_DEATH; }

    final class CastingGoal extends SpellcasterCastingSpellGoal {
        @Override
        public void tick() {
            if (Stormcaller.this.getTarget() != null) {
                Stormcaller.this.getLookControl().setLookAt(Stormcaller.this.getTarget(), Stormcaller.this.getMaxHeadYRot(), Stormcaller.this.getMaxHeadXRot());
            }
        }
    }

    final class LightningSpellGoal extends SpellcasterUseSpellGoal {
        @Override
        public boolean canUse() {
            LivingEntity t = Stormcaller.this.getTarget();
            return super.canUse() && t != null && Stormcaller.this.hasLineOfSight(t) && Stormcaller.this.distanceToSqr(t) < 400.0;
        }

        @Override
        protected void performSpellCasting() {
            LivingEntity t = Stormcaller.this.getTarget();
            if (t != null && Stormcaller.this.level() instanceof ServerLevel level) Stormcaller.this.callLightning(level, t);
        }

        @Override protected int getCastingTime() { return 40; }
        @Override protected int getCastingInterval() { return Stormcaller.this.level().isThundering() ? 60 : 90; }
        @Override protected @Nullable SoundEvent getSpellPrepareSound() { return SoundEvents.EVOKER_PREPARE_ATTACK; }
        @Override protected IllagerSpell getSpell() { return IllagerSpell.DISAPPEAR; }
    }

    final class GaleSpellGoal extends SpellcasterUseSpellGoal {
        @Override
        public boolean canUse() {
            LivingEntity t = Stormcaller.this.getTarget();
            return super.canUse() && t != null && Stormcaller.this.distanceToSqr(t) < 20.0;
        }

        @Override
        protected void performSpellCasting() {
            if (Stormcaller.this.level() instanceof ServerLevel level) Stormcaller.this.gale(level);
        }

        @Override protected int getCastWarmupTime() { return 8; }
        @Override protected int getCastingTime() { return 16; }
        @Override protected int getCastingInterval() { return 70; }
        @Override protected @Nullable SoundEvent getSpellPrepareSound() { return SoundEvents.BREEZE_IDLE_GROUND; }
        @Override protected IllagerSpell getSpell() { return IllagerSpell.SUMMON_VEX; }
    }
}
