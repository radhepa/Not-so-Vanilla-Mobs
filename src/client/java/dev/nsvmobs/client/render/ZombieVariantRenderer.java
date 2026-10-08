package dev.nsvmobs.client.render;

import dev.nsvmobs.client.model.Geometry;

import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.zombie.ZombieModel;
import net.minecraft.client.renderer.entity.AbstractZombieRenderer;
import net.minecraft.client.renderer.entity.ArmorModelSet;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.ZombieRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.monster.zombie.Zombie;

/** Zombie variants: vanilla zombie animation and armour on one of this mod's models. They are never babies. */
public class ZombieVariantRenderer extends AbstractZombieRenderer<Zombie, ZombieRenderState, ZombieModel<ZombieRenderState>> {
    private final Identifier texture;

    public ZombieVariantRenderer(EntityRendererProvider.Context context, String id) {
        this(context, id, new ZombieModel<>(context.bakeLayer(Geometry.layer(id))),
                ArmorModelSet.bake(ModelLayers.ZOMBIE_ARMOR, context.getModelSet(), ZombieModel::new));
    }

    private ZombieVariantRenderer(EntityRendererProvider.Context context, String id, ZombieModel<ZombieRenderState> model,
                                  ArmorModelSet<ZombieModel<ZombieRenderState>> armor) {
        super(context, model, model, armor, armor);
        this.texture = Identifier.fromNamespaceAndPath("nsvmobs", "textures/entity/" + id + ".png");
        if (GlowLayer.exists(id)) this.addLayer(new GlowLayer<>(this, id));
    }

    @Override
    public Identifier getTextureLocation(ZombieRenderState state) {
        return this.texture;
    }

    @Override
    public ZombieRenderState createRenderState() {
        return new ZombieRenderState();
    }
}
