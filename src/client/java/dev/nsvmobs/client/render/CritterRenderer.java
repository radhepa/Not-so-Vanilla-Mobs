package dev.nsvmobs.client.render;

import java.util.List;
import java.util.function.BiConsumer;
import java.util.function.Function;

import dev.nsvmobs.client.model.CritterModel;
import dev.nsvmobs.client.model.Geometry;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Mob;

/** Renderer for the non-humanoid mobs: one baked model, one texture, an optional glow layer. */
public class CritterRenderer<T extends Mob> extends MobRenderer<T, CritterRenderState, CritterModel> {
    private final List<Identifier> textures;
    private final BiConsumer<T, CritterRenderState> extract;

    public CritterRenderer(EntityRendererProvider.Context context, String id, Function<ModelPart, CritterModel> model,
                           float shadow, BiConsumer<T, CritterRenderState> extract) {
        this(context, id, model, shadow, extract, List.of(id));
    }

    /**
     * With texture variants: {@code textureIds} are names under textures/entity/, picked by
     * {@link CritterRenderState#variant} (the extract lambda sets it).
     */
    public CritterRenderer(EntityRendererProvider.Context context, String id, Function<ModelPart, CritterModel> model,
                           float shadow, BiConsumer<T, CritterRenderState> extract, List<String> textureIds) {
        super(context, model.apply(context.bakeLayer(Geometry.layer(id))), shadow);
        this.textures = textureIds.stream().map(t -> Identifier.fromNamespaceAndPath("nsvmobs", "textures/entity/" + t + ".png")).toList();
        this.extract = extract;
        if (GlowLayer.exists(id)) this.addLayer(new GlowLayer<>(this, id));
    }

    @Override
    public Identifier getTextureLocation(CritterRenderState state) {
        return this.textures.get(Math.floorMod(state.variant, this.textures.size()));
    }

    @Override
    public CritterRenderState createRenderState() {
        return new CritterRenderState();
    }

    @Override
    public void extractRenderState(T entity, CritterRenderState state, float partialTicks) {
        super.extractRenderState(entity, state, partialTicks);
        state.aggressive = entity.isAggressive();
        this.extract.accept(entity, state);
    }
}
