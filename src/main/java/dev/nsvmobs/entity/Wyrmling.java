package dev.nsvmobs.entity;

import dev.nsvmobs.NsvEntities;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RangedAttackGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A tiny dragon. Tame it with blaze powder; it flies after you, sits when told and spits embers at
 * monsters that hurt you or that you attack. Embers never set blocks alight.
 */
public class Wyrmling extends TamableAnimal implements RangedAttackMob {
    public Wyrmling(EntityType<? extends Wyrmling> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 10, false);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return TamableAnimal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.FLYING_SPEED, 0.5)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    /** Wild wyrmlings live high in the mountains: any solid ground with open sky will do. */
    public static boolean checkSpawnRules(EntityType<Wyrmling> type, LevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        return level.getBlockState(pos.below()).isSolid() && level.canSeeSky(pos) && level.getRawBrightness(pos, 0) > 8;
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(2, new RangedAttackGoal(this, 1.1, 30, 12.0F));
        this.goalSelector.addGoal(3, new FollowOwnerGoal(this, 1.0, 6.0F, 2.0F));
        this.goalSelector.addGoal(4, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(5, new TemptGoal(this, 1.1, s -> s.is(Items.BLAZE_POWDER), false));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomFlyingGoal(this, 1.0));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new OwnerHurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new OwnerHurtTargetGoal(this));
    }

    /** Only ever fights monsters, whatever its owner swings at. */
    @Override
    public boolean wantsToAttack(LivingEntity target, LivingEntity owner) {
        return target instanceof Enemy && super.wantsToAttack(target, owner);
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        if (!(this.level() instanceof ServerLevel level)) return;
        Vec3 from = new Vec3(this.getX(), this.getEyeY() - 0.1, this.getZ());
        Vec3 dir = new Vec3(target.getX() - from.x, target.getY(0.5) - from.y, target.getZ() - from.z).normalize();
        WyrmlingEmber ember = new WyrmlingEmber(NsvEntities.WYRMLING_EMBER, level);
        ember.setOwner(this);
        ember.setPos(from.add(dir.scale(0.5)));
        ember.shoot(dir.x, dir.y, dir.z, 1.2F, 1.0F);
        level.addFreshEntity(ember);
        this.playSound(SoundEvents.BLAZE_SHOOT, 0.5F, 1.8F + this.random.nextFloat() * 0.2F);
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && stack.is(Items.BLAZE_POWDER)) {
            this.usePlayerItem(player, hand, stack);
            if (!this.level().isClientSide()) {
                if (this.random.nextInt(4) == 0) {
                    this.tame(player);
                    this.navigation.stop();
                    this.setTarget(null);
                    this.setOrderedToSit(true);
                    this.level().broadcastEntityEvent(this, (byte) 7);
                } else {
                    this.level().broadcastEntityEvent(this, (byte) 6);
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (this.isTame() && this.isOwnedBy(player)) {
            if (stack.is(Items.BLAZE_POWDER) && this.getHealth() < this.getMaxHealth()) {
                this.usePlayerItem(player, hand, stack);
                this.heal(6.0F);
                this.playSound(SoundEvents.BLAZE_AMBIENT, 0.4F, 1.9F);
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

    @Override public float getAgeScale() { return this.isBaby() ? 0.6F : 1.0F; }
    @Override public boolean isFood(ItemStack stack) { return stack.is(Items.BLAZE_POWDER); }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        Wyrmling baby = NsvEntities.WYRMLING.create(level, EntitySpawnReason.BREEDING);
        if (baby != null && this.getOwnerReference() != null) {
            baby.setOwnerReference(this.getOwnerReference());
            baby.setTame(true, true);
        }
        return baby;
    }

    public boolean isFlying() { return !this.onGround(); }
    @Override protected boolean canFlyToOwner() { return true; }
    @Override protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {}
    @Override public boolean isFlapping() { return this.isFlying(); }

    @Override protected SoundEvent getAmbientSound() { return SoundEvents.PARROT_IMITATE_ENDER_DRAGON; }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.PARROT_HURT; }
    @Override protected SoundEvent getDeathSound() { return SoundEvents.PARROT_DEATH; }
    @Override protected float getSoundVolume() { return 0.6F; }
    @Override public float getVoicePitch() { return 0.9F + this.random.nextFloat() * 0.2F; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) { this.playSound(SoundEvents.PARROT_STEP, 0.15F, 1.0F); }
}
