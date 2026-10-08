package dev.nsvmobs.compat;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/**
 * Village Friends RPG keys its Bestiary by entity path. This maps this mod's variants onto the
 * families they belong to, so they count toward the Zombie, Skeleton and Spider masteries.
 * Applied only when the RPG add-on is installed (see {@link CompatMixinPlugin}).
 */
@Pseudo
@Mixin(targets = "dev.villagefriends.rpg.Bestiary", remap = false)
public abstract class RpgBestiaryMixin {
    @ModifyVariable(method = "ofMob", at = @At("HEAD"), argsOnly = true, remap = false)
    private static String nsvmobs$family(String path) {
        return RpgFamilies.alias(path);
    }
}
