# Pipeline capabilities

What this pipeline can do and which technique does it. Every row was proved with a control
render (RULES 9), not assumed. This is a capability index, not a settings list — the technique
is the durable part; its dial positions belong to whichever study last used it.

| Effect | Technique | State |
|---|---|---|
| Daylight | HDRI scaled to real lux + matched sun | solid |
| Camera | `physical_camera`, `straighten_verticals` | solid |
| Tone match to a reference | Mix Multiply (`color_mult`) | solid |
| Edge highlight | Bevel node with Normal input, or Bevel modifier | solid |
| Edge wear (shading) | GN `edge_dist` x noise | solid |
| Edge chips (geometry) | GN band subdivision + Set Position | solid |
| Displacement | Displacement + adaptive subdivision | solid, fast |
| Tiling by real height | `height_span_uv` + REPEAT | solid |
| Caustics | `caustic_photons.py` (glassware), GN wavefront (pools) | solid |
| Layered BRDF | Mix Shader | solid |
| White-backdrop product shot | Light Path *Is Camera Ray* backdrop | solid |
| Headless batch | `blender -b … render_variant.py` | solid |
| Model-vs-reference geometry check | `scripts/rhino/project_edges.py` + `scripts/edge_overlay.py` | solid |
| Matching overcast HDRI | tag shortlist → equirect strip with elevation lines → rotation formula | solid |
| Burnished / polished white concrete | low roughness clouds, two-scale tone, stretched-noise trowel marks | solid |
| Faint dirty arris on huge meshes | shader Bevel normal vs true normal mask | solid, control-proved |
| Wind ripples on a pool | Ocean DISPLACE on a 2-3 cm mesh, slight chop | solid |
| Pool water, reflective + slightly clear | IOR 1.333 transmission + Volume Absorption + Scatter (volume_bounces > 0) | solid |
| Opaque stylised pool | opaque diffuse body under IOR 1.333 surface (declared) | solid |
| Wet surround, splashes, dried marks | analytic edge distance mask; dry**1.4 + coat film IOR 1.33; patchy by noise | test |
