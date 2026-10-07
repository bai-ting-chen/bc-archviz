# V-Ray for Rhino → Blender

Sources: `Desktop\DESIGN TEMP_2026\ROOK TEST\2608xx_VRAY` (skill `vray-rhino`); rebuilt in
`studies/261006_vray_parity`, `261006_edge_wear`.

| V-Ray | Blender | Status |
|---|---|---|
| Dome + HDRI by eye | HDRI scaled to real lux | better |
| CameraPhysical / vertical shift | `physical_camera`, `straighten_verticals` | parity |
| `color_mult` | Mix Multiply | parity (0.265 vs 0.26) |
| TexEdges + normal | Bevel node with Normal input (or Bevel modifier) | parity |
| TexCurvature wear | GN `edge_dist` × noise | better |
| Procedural 3D-displaced chips | GN band subdivision + Set Position | better |
| GeomDisplacedMesh | Displacement + adaptive subdivision | parity, faster |
| UVWGenChannel repeat_v | `height_span_uv` + REPEAT | parity |
| Photon caustics | `caustic_photons.py` (glassware), GN wavefront (pools) | parity |
| BRDFLayered | Mix Shader | parity |
| White bg / override_gi | Light Path *Is Camera Ray* backdrop | parity |
| AppSDK headless | `blender -b … render_variant.py` | parity |

Open: pine brightness vs V-Ray 260825; canopy contrast vs Berlin reference (softer HDRI).
