"""Material and geometry helper-regression case catalogue."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)


CASES = {
    "pbr_material": lambda m: m['materials.shared.pbr'].pbr_material("concrete_wall_009"),
    "glass_material": lambda m: m['materials.shared.pbr'].glass_material(),
    "simple_material": lambda m: m['materials.shared.pbr'].simple_material("S", (0.5, 0.4, 0.3)),
    "material_from_spec": lambda m: m['materials.shared.pbr'].material_from_spec({"type": "simple", "name": "S2", "color": (.2, .2, .2)}),
    "world_hdri": lambda m: m['core.archviz'].world_hdri("kloppenheim_06_puresky"),
    "concrete_study": lambda m: m['materials.concrete.concrete'].concrete_study(),
    "displaced_ground": lambda m: m['materials.ground.ground'].displaced_ground(),
    "coated_wood": lambda m: m['materials.wood.wood'].coated_wood(),
    "clear_glass": lambda m: m['materials.glass.glass'].clear_glass(),
    "white_backdrop": lambda m: m['materials.shared.pbr'].white_backdrop(),
    "glazed_tiles": lambda m: m['materials.tile.tile_surface'].glazed_tiles(),
    "emitter": lambda m: m['scene.lighting.interior'].emitter("E", 1000.0),
    "emitter_dots": lambda m: m['scene.lighting.interior'].emitter_dots("ED", 1000.0),
    "polished_granite": lambda m: m['materials.stone.stone'].polished_granite(),
    "stone_tiles": lambda m: m['materials.stone.stone'].stone_tiles(),
    "polished_steel": lambda m: m['materials.metal.metal'].polished_steel(),
    "pool_water": lambda m: m['materials.water.water'].pool_water(),
    "steam": lambda m: m['materials.shared.volumes'].steam(),
    "sheer": lambda m: m['materials.fabric.fabric'].sheer(),
    "random_tone": lambda m: m['effects.variation'].random_tone_material("R", (0.1, 0.1, 0.1), (0.2, 0.2, 0.2)),
    "albedo_material": lambda m: m['materials.shared.pbr'].albedo_material("concrete_wall_009", "AM", (0.5, 0.5, 0.5)),
    "vertical_boards": lambda m: m['materials.concrete.concrete'].vertical_boards(m['materials.shared.pbr'].albedo_material("concrete_wall_009", "VB", (0.5, 0.5, 0.5))),
    "long_pavers": lambda m: m['materials.stone.stone'].long_pavers("concrete_wall_009", "LP", (0.4, 0.4, 0.4)),
    "dielectric": lambda m: m['materials.shared.pbr'].dielectric("D", 1.52),
    "caustic_sheet_group": lambda m: m['effects.caustics.gn_caustics'].caustic_sheet_group(),
    "caustic_sheet_material": lambda m: m['effects.caustics.gn_caustics'].caustic_sheet_material(),
    "scatter_group": lambda m: m['scene.environment.scatter'].scatter_group(),
    "edge_wear_group": lambda m: m['effects.edge_wear'].edge_wear_group(),
    "weathered_concrete": lambda m: m['effects.edge_wear'].weathered_concrete(),
    "mask_edge_dist": lambda m: m['effects.edge_wear'].mask_material("MK", "edge_dist"),
    "mask_damage": lambda m: m['effects.edge_wear'].mask_material("MK2", "damage"),
    "wood_wear_group": lambda m: m['materials.wood.wood_wear'].wood_wear_group(),
    "weathered_wood": lambda m: m['materials.wood.wood_wear'].weathered_wood(),
}
