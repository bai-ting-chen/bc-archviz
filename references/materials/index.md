# Materials

Recipes describe node structure and mechanisms; tune scene values in study notes (GOV_01).
Use all applicable maps at real size with physical surface ranges (MAT_01).

## Layer assembly (MAT_07)
- **Colour and roughness:** each layer is a multiplier around 1 on the base, chained in sequence.
  Older helpers that mix whole BSDFs or MAXIMUM masks (`edge_wear.weathered_concrete`,
  `add_runoff`) predate MAT_07: migrate them when they are next changed.
- **Height:** geometry-scale relief goes to the Displacement output ([displacement.md](displacement.md)),
  surface texture to a Bump node on the Normal input.
- **Switching off (MAT_07):** a Value node per layer that scales its deviation from 1 does it; an
  AOV of the layer's multiplier lets you measure what reaches the image ([variation.md](variation.md)).
- **Geometry fields** measured in Geometry Nodes run before modifiers that move the mesh (RULES MAT_08).

| Family or technique | Canonical helper |
|---|---|
| [Physical Ranges](physical-ranges.md) | `materials.pbr` |
| [Texture Selection](texture-selection.md) | `materials.pbr` |
| [Concrete](concrete.md) | `materials.concrete` |
| [Tiles](tiles.md) | `materials.tile_surface` |
| [Board Formed Concrete](board-formed-concrete.md) | `materials.concrete` |
| [Ground](ground.md) | `materials.ground` |
| [Vegetation](vegetation.md) | `materials.vegetation` |
| [Wet Surfaces](wet-surfaces.md) | `materials.vegetation` |
| [Displacement](displacement.md) | `materials.displacement` |
| [Wood](wood.md) | `materials.wood` |
| [Stone](stone.md) | `materials.stone` |
| [Metal](metal.md) | `materials.metal` |
| [Glass](glass.md) | `materials.glass` |
| [Caustics](caustics.md) | `gn_caustics` / `caustic_photons.py` |
| [Fabric](fabric.md) | `materials.fabric` |
| [Water](water.md) | `materials.water` |
| [Variation](variation.md) | `materials.variation` |
| [Scale](scale.md) | `materials.nodes` |
| [Edge Wear](edge-wear.md) | `materials.edge_wear` |
| [Water Features](water-features.md) | `materials.water` |

Shared graph/socket helpers: `materials.nodes.G` / `sock`; asset lookup and project state: `archviz`.
Lighting stays in `interior`; geometry stays in `terrain` and `scatter`.
[LuxCore materials](../renderer/luxcore.md): `materials.luxcore`; [all helper signatures](../scene/blender-python-helpers.md).
