# Materials

Recipes describe node structure and mechanisms; tune scene values in study notes (GOV_01).
Use all applicable maps at real size with physical surface ranges (MAT_01).

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
[LuxCore materials](../renderer/luxcore.md): `materials.luxcore`; [all helper signatures](../scene/helpers.md).
