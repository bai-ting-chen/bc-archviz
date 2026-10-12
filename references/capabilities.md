# Pipeline capabilities

What this pipeline can do and which technique does it. Every row was proved with a control
render (RULES 9), not assumed. This is a capability index, not a settings list — the technique
is the durable part; its dial positions belong to whichever study last used it.

| Effect | Technique | State |
|---|---|---|
| Daylight | HDRI scaled to real lux, rotated to place its sun; the sole natural light | solid |
| Specified light fixtures | manufacturer IES on a point light at 177.83/683 W (`interior.ies_light`), candela reproduced 1.000; room direct illuminance = hand calc ±1 % | solid |
| Linear fixtures (cove, linear pendant) | the IES split into N point lights at lumens/N along the run | solid |
| Eulumdat-only fixtures | `scripts/ldt2ies.py` (lumens checked; rotational symmetry tested, other symmetries untested) | partial |
| Camera | `physical_camera`, `straighten_verticals` | solid |
| Tone match to a reference | Mix Multiply (`color_mult`) | solid |
| Edge highlight | Bevel node with Normal input, or Bevel modifier | solid |
| Edge wear (shading) | GN `edge_dist` x noise | solid |
| Edge chips (geometry) | GN band subdivision + Set Position; per-object `Seed` | solid |
| Displacement | Displacement + adaptive subdivision | solid, fast |
| Tiling by real height | `height_span_uv` + REPEAT | solid |
| Caustics | `caustic_photons.py` (glassware), GN wavefront (pools) | solid |
| Caustics through patterned glass / glass block (sun, room-scale) | LuxCore PATH, GPU + CPU light tracing (luxcore.md), energy-checked (caustics.md) | solid |
| Glass-block wall | block definitions with real inner relief, random variants + turns, mortar mesh (materials › Glass block) | solid |
| Baked procedural textures for LuxCore (terrazzo, smooth concrete, sand mortar) | numpy seamless colour + roughness maps | test |
| Tangled glass-block caustics across units | long-wave relief at higher slope (Wave/Iceberg mix), sized by a thin-lens sim (caustics.md › Designing a relief) | test |
| Clean caustic renders without OIDN blotches | LuxCore radiance clamping (camera paths only) | solid, measured |
| Concave-corner dust | AO band × noise × height; Cycles live or baked for LuxCore (`lux_materials.bake_dust`) | test |
| Anti-tiling | LuxCore Randomized Tiling (native); Cycles: noise-mixed lookups / hex tiling built from nodes | LuxCore test, Cycles untested |
| Per-instance variation | Object Info Random / Attribute Instancer (converts to LuxCore per instance) | test |
| Layered BRDF | Mix Shader | solid |
| White-backdrop product shot | Light Path *Is Camera Ray* backdrop | solid |
| Headless batch | `blender -b … render_variant.py` | solid |
| Model-vs-reference geometry check | `scripts/rhino/project_edges.py` + `scripts/edge_overlay.py` | solid |
| Matching overcast HDRI | tag shortlist → equirect strip with elevation lines → rotation formula | solid |
| Burnished / polished white concrete | low roughness clouds, two-scale tone, stretched-noise trowel marks | solid |
| Faint dirty arris on huge meshes | shader Bevel normal vs true normal mask | solid, control-proved |
| Wind ripples on a pool | Ocean DISPLACE on a finely diced mesh, slight chop | solid |
| Pool water, reflective + slightly clear | IOR 1.333 transmission + Volume Absorption + Scatter (volume_bounces > 0) | solid |
| Opaque stylised pool | opaque diffuse body under IOR 1.333 surface (declared) | solid |
| 3ds Max assets (vegetation, V-Ray materials) | io_scene_max + `max_import` repairs (bands, IDs, slots, UV channel), materials rebuilt from maps; checked on 4 models 25–320 MB | solid |
| Foliage cards | Principled + Translucent (transmission map) cut by opacity; roughness from the glossiness map | solid, control-proved |
| Wet surround, splashes, dried marks | analytic edge distance mask; dry**1.4 + coat film IOR 1.33; patchy by noise | test |
| Hill / landform around a building pad | GN smoothstep fall on noise-warped pad distance (`terrain`) | solid |
| Meadow on terrain (multi-species, upright) | native Scatter on Surface + patch / bare-soil / pad / frustum masks (`scatter.meadow_layer_group`) | solid |
| Modelled grass blades | Principled + Translucent, per-instance tone + dry patches (`vegetation.blade_material`) | solid |
| Wet lawn / wet ground | dry^gamma + water coat (`vegetation.WET`, `terrain.ground_material(wet_gamma)`) | solid, control-proved |
| Dew near camera | effective-reflectance glossy beads faded by distance (declared approximation) | test |
| Volumetric fog / mist | Volume Scatter Mie, sigma = 3.912/V (`atmosphere.fog_volume`) | solid, control-proved (1.000) |
| Runoff / leak streaks below drip edges | GN raycast drip-edge field + streak shader (`wear.add_leak_field`, `add_runoff`) | solid, control-proved |
| Concrete cracks | corner shrinkage cracks + patchy Voronoi map-cracking (`wear.add_cracks`) | solid, control-proved |
| Glazing distortion | roller wave + IGU pillowing bump (`lookdev.glass_distortion`) | solid |
| Soft backplate vs crisp model | measured edge widths + slight DOF in front of the subject | solid |
| No-limit Cycles final in the UI | `finals.py` (untiled, savers, OIDN from passes) | solid |
