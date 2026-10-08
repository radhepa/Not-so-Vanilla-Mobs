package dev.nsvmobs.entity;

import java.util.List;

import dev.nsvmobs.NsvEntities;

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
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/** A small crab in a borrowed shell. Ducks inside when startled; digs up beach trinkets. */
public class HermitCrab extends Animal {
    /** Shell textures, in variant order: hermit_crab (conch), hermit_crab_whelk, hermit_crab_snail. */
    public static final int SHELLS = 3;
    private static final EntityDataAccessor<Integer> SHELL = SynchedEntityData.defineId(HermitCrab.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> HIDING = SynchedEntityData.defineId(HermitCrab.class, EntityDataSerializers.INT);
    private int digTime;

    public HermitCrab(EntityType<? extends HermitCrab> type, Level level) {
        super(type, level);
        this.digTime = 2400 + this.random.nextInt(4800);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 8.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2);
    }

    /** Beaches and shores: sand, gravel, stone or mud underfoot, in daylight. */
    public static boolean checkSpawnRules(EntityType<HermitCrab> type, LevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        BlockState below = level.getBlockState(pos.below());
        boolean shore = below.is(BlockTags.SAND) || below.is(Blocks.GRAVEL) || below.is(Blocks.STONE) || below.is(Blocks.MUD);
        return shore && level.getRawBrightness(pos, 0) > 8;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(SHELL, 0);
        builder.define(HIDING, 0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.1, s -> s.is(Items.KELP), false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 5.0F));
    }

    public int shell() { return this.entityData.get(SHELL); }
    public boolean isHiding() { return this.entityData.get(HIDING) > 0; }

    private void hide(int ticks) {
        if (!this.isHiding()) this.playSound(SoundEvents.TURTLE_SHAMBLE_BABY, 1.0F, 1.6F);
        this.entityData.set(HIDING, Math.max(ticks, this.entityData.get(HIDING)));
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
                                                  @Nullable SpawnGroupData data) {
        this.entityData.set(SHELL, this.random.nextInt(SHELLS));
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        int hiding = this.entityData.get(HIDING);
        if (hiding > 0) {
            this.entityData.set(HIDING, hiding - 1);
            this.getNavigation().stop();
            this.setDeltaMovement(this.getDeltaMovement().multiply(0, 1, 0));
            return;
        }
        if (this.tickCount % 5 == 0) {
            for (Player p : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(4.0))) {
                if (p.isSprinting() && !p.isSpectator()) {
                    this.hide(60 + this.random.nextInt(60));
                    return;
                }
            }
        }
        if (!this.isBaby() && --this.digTime <= 0) {
            this.digTime = 2400 + this.random.nextInt(4800);
            BlockState below = level.getBlockState(this.blockPosition().below());
            if (below.is(BlockTags.SAND) && this.onGround()) dig(level, below);
        }
    }

    private void dig(ServerLevel level, BlockState sand) {
        this.playSound(SoundEvents.BRUSH_SAND, 1.0F, 1.2F);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, sand), this.getX(), this.getY() + 0.1, this.getZ(),
                16, 0.25, 0.05, 0.25, 0.05);
        this.spawnAtLocation(level, new ItemStack(trinket(this.random)));
    }

    /** What a crab turns up in the sand. */
    static Item trinket(RandomSource random) {
        int roll = random.nextInt(100);
        if (roll == 0) return Items.NAUTILUS_SHELL;
        List<Item> common = List.of(Items.CLAY_BALL, Items.CLAY_BALL, Items.BONE_MEAL, Items.BONE_MEAL, Items.GOLD_NUGGET,
                Items.PRISMARINE_SHARD, Items.SEA_PICKLE);
        return common.get(random.nextInt(common.size()));
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (this.isHiding()) damage *= 0.2F;
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && this.isAlive()) this.hide(100);
        return hurt;
    }

    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.KELP); }
    @Override public float getAgeScale() { return this.isBaby() ? 0.5F : 1.0F; }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        HermitCrab baby = NsvEntities.HERMIT_CRAB.create(level, EntitySpawnReason.BREEDING);
        if (baby != null) baby.entityData.set(SHELL, this.random.nextInt(SHELLS));
        return baby;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Shell", this.shell());
        output.putInt("DigTime", this.digTime);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(SHELL, Math.floorMod(input.getIntOr("Shell", 0), SHELLS));
        this.digTime = input.getIntOr("DigTime", this.digTime);
    }

    @Override protected SoundEvent getAmbientSound() { return null; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.TURTLE_HURT_BABY; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.TURTLE_DEATH_BABY; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.TURTLE_SHAMBLE_BABY, 0.15F, 1.5F); }
}
