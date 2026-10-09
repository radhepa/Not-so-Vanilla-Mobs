package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A skittish forest deer. It bolts from any player who comes near on foot (sneak up instead) and
 * flashes its white tail as it runs, which sends the rest of the herd running too. Half the adults
 * are stags with branching antlers. Breeds with apples.
 */
public class Deer extends Animal {
    private static final EntityDataAccessor<Boolean> STAG = SynchedEntityData.defineId(Deer.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> ALARMED = SynchedEntityData.defineId(Deer.class, EntityDataSerializers.BOOLEAN);
    static final float SHY_RANGE = 10.0F;
    static final double HERD_RANGE = 12.0;
    /** A herd-mate bolted from this player: run from them too (for a couple of seconds). */
    private @Nullable Player startledBy;
    private int startledTicks;

    public Deer(EntityType<? extends Deer> type, Level level) {
        super(type, level);
        // stag or doe for life, decided when it's born (the client gets it from the server)
        if (!level.isClientSide()) this.entityData.set(STAG, this.random.nextBoolean());
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(STAG, false);
        builder.define(ALARMED, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 2.0) {
            @Override
            public void start() {
                super.start();
                Deer.this.setAlarmed(true);
                if (Deer.this.getLastHurtByMob() instanceof Player p) Deer.this.alertHerd(p);
            }

            @Override
            public void stop() {
                super.stop();
                Deer.this.setAlarmed(false);
            }
        });
        this.goalSelector.addGoal(2, new BoltGoal());
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, this::isFood, false));
        this.goalSelector.addGoal(5, new FollowParentGoal(this, 1.15));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    /** A grown stag carries antlers; fawns grow into stags or does. */
    public boolean isStag() {
        return this.entityData.get(STAG);
    }

    /** Running from danger, white tail up. */
    public boolean isAlarmed() {
        return this.entityData.get(ALARMED);
    }

    void setAlarmed(boolean alarmed) {
        this.entityData.set(ALARMED, alarmed);
    }

    /** Players it runs from: anyone on foot, not sneaking, in survival or adventure. */
    static boolean startles(LivingEntity e) {
        return !e.isShiftKeyDown() && !e.isCrouching() && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(e);
    }

    /** The rest of the herd within 12 blocks runs from the same player. */
    void alertHerd(Player threat) {
        this.playSound(SoundEvents.HORSE_BREATHE, 0.6F, 1.6F + this.random.nextFloat() * 0.2F);   // an alarm snort
        for (Deer other : this.level().getEntitiesOfClass(Deer.class, this.getBoundingBox().inflate(HERD_RANGE),
                d -> d != this && d.isAlive() && !d.isAlarmed() && d.distanceToSqr(this) <= HERD_RANGE * HERD_RANGE)) {
            other.startledBy = threat;
            other.startledTicks = 40;
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!this.level().isClientSide() && this.startledTicks > 0 && --this.startledTicks == 0) this.startledBy = null;
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.APPLE); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return NsvEntities.DEER.create(level, EntitySpawnReason.BREEDING);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Stag", this.isStag());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(STAG, input.getBooleanOr("Stag", this.isStag()));
    }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.GOAT_AMBIENT; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.GOAT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.GOAT_DEATH; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.GOAT_STEP, 0.12F, 1.3F); }
    @Override public int getAmbientSoundInterval() { return 240; }
    @Override public float getVoicePitch() { return (this.isBaby() ? 1.8F : 1.4F) + this.random.nextFloat() * 0.15F; }
    @Override protected float getSoundVolume() { return 0.4F; }

    /**
     * Bolts from a player within 10 blocks who isn't sneaking, or from the player a herd-mate just
     * bolted from. Starting to run raises the alarm for the rest of the herd.
     */
    final class BoltGoal extends AvoidEntityGoal<Player> {
        BoltGoal() {
            super(Deer.this, Player.class, Deer::startles, SHY_RANGE, 1.4, 1.8, EntitySelector.NO_CREATIVE_OR_SPECTATOR);
        }

        @Override
        public boolean canUse() {
            Player threat = Deer.this.startledBy;
            if (threat != null && threat.isAlive() && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(threat)
                    && Deer.this.distanceToSqr(threat) < 24 * 24) {
                Vec3 away = DefaultRandomPos.getPosAway(Deer.this, 16, 7, threat.position());
                if (away != null) {
                    this.path = this.pathNav.createPath(away.x, away.y, away.z, 0);
                    if (this.path != null) {
                        this.toAvoid = threat;
                        return true;
                    }
                }
            }
            return super.canUse();
        }

        @Override
        public void start() {
            super.start();
            Deer.this.startledBy = null;
            Deer.this.startledTicks = 0;
            Deer.this.setAlarmed(true);
            if (this.toAvoid != null) Deer.this.alertHerd(this.toAvoid);
        }

        @Override
        public void stop() {
            super.stop();
            Deer.this.setAlarmed(false);
        }
    }
}
