"""Baseline for the edge-wear builders: node graphs of the chip modifier, the concrete wear material,
the mask views, the leak field, runoff and cracks, dumped as JSON.

Each case starts from an empty file. The legacy library (ARCHVIZ_PROJECT=<folder with
library/polyhaven/textures/concrete_wall_009>) supplies the concrete maps. Used as the refactor proof for
scripts/blender/effects/edge_wear.py (RULES GOV_04): dump before, dump after, compare.

Usage: ARCHVIZ_PROJECT=<project> blender -b --factory-startup --python scripts/controls/effects/edge_wear_graph_check.py -- <out.json>
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "blender"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import effects.edge_wear as edge_wear  # noqa: E402
from graph_dump import dump_material, dump_tree, write  # noqa: E402

OUT = Path(sys.argv[sys.argv.index("--") + 1])
OPENINGS = [("x", 0.0, 0.0, 1.0, 0.0, 1.0, False),
            ("y", 1.0, 0.0, 1.0, 0.0, 1.0, True, (135, 45))]


def fresh():
    """An empty file, as each case needs its own node groups and materials."""
    bpy.ops.wm.read_homefile(use_empty=True)


def modifier_inputs(mod):
    """Each modifier input by its interface name, as the value Blender stores for it."""
    out = {}
    for item in mod.node_group.interface.items_tree:
        if getattr(item, "in_out", "") != "INPUT":
            continue
        slot = getattr(mod.properties.inputs, item.identifier)
        if not hasattr(slot, "value"):          # geometry sockets carry no value
            continue
        v = slot.value
        out[item.name] = [round(x, 6) for x in v] if hasattr(v, "__len__") else round(v, 6)
    return out


result = {}

fresh()
result["chip_group"] = {"tree": dump_tree(edge_wear.edge_wear_group())}
fresh()
result["chip_group_no_chips"] = {"tree": dump_tree(edge_wear.edge_wear_group("Edge NoChip", chips=False))}

fresh()
group = edge_wear.edge_wear_group()
wall = bpy.data.meshes.new("Wall")
wall.from_pydata([(0, 0, 0), (1, 0, 0), (1, 0.2, 0), (0, 0.2, 0), (0, 0, 2), (1, 0, 2), (1, 0.2, 2), (0, 0.2, 2)],
                 [], [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)])
obj = bpy.data.objects.new("Wall", wall)
bpy.context.scene.collection.objects.link(obj)
mod = edge_wear.add_edge_wear(obj, group, Band=0.1, Chip_Reach=0.02, Seed=(1.0, 2.0, 3.0))
result["modifier_inputs"] = modifier_inputs(mod)
result["modifier_dice_faces"] = edge_wear.dice(obj, size=0.5)

fresh()
result["weathered"] = dump_material(edge_wear.weathered_concrete(stain=False))

for method in ("pointiness", "ao_inside", "bevel", "edge_dist", "chip", "damage"):
    fresh()
    result["mask_" + method] = dump_material(edge_wear.mask_material("MK_" + method, method))

fresh()
result["leak_group"] = {"tree": dump_tree(edge_wear.leak_field_group())}

fresh()
wall_mat = edge_wear.weathered_concrete(stain=False)
wall = bpy.data.meshes.new("LeakWall")
wall.from_pydata([(0, 0, 0), (1, 0, 0), (1, 0.2, 0), (0, 0.2, 0), (0, 0, 2), (1, 0, 2), (1, 0.2, 2), (0, 0.2, 2)],
                 [], [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)])
leak_obj = bpy.data.objects.new("LeakWall", wall)
bpy.context.scene.collection.objects.link(leak_obj)
edge_wear.add_leak_field(leak_obj)
edge_wear.add_runoff(wall_mat)
result["runoff"] = dump_material(wall_mat)
result["runoff_leak_group"] = {"tree": dump_tree(edge_wear.leak_field_group())}
result["runoff_modifiers"] = [m.name for m in leak_obj.modifiers]

fresh()
crack_mat = edge_wear.weathered_concrete(stain=False)
edge_wear.add_cracks(crack_mat, openings=OPENINGS)
result["cracks"] = dump_material(crack_mat)

fresh()
both = edge_wear.weathered_concrete(stain=False)
edge_wear.add_runoff(both)
edge_wear.add_cracks(both, openings=OPENINGS, crack={"seed": 5})
result["runoff_and_cracks"] = dump_material(both)

write(OUT, result)
print("EDGE_WEAR_GRAPH_CHECK written", OUT, "cases:", sorted(result))
