"""Baseline for the tile material builder: the node graph of a few tile materials, dumped as JSON.

Each case builds a material from scratch (fresh file) and records every node (type, name, label,
settings, input defaults), every link, and the nested node groups. Random owner ids and custom
properties are left out, so the dump is deterministic. Used as the refactor proof for
scripts/blender/materials/tile/tile_surface.py (RULES GOV_04): dump before, dump after, compare.

Usage: blender -b --factory-startup --python scripts/controls/tile/tile_graph_check.py -- <out.json>
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
import materials.tile.tile_surface as tile_surface  # noqa: E402
from graph_dump import dump_material, value, write  # noqa: E402

OUT = Path(sys.argv[sys.argv.index("--") + 1])


CASES = {
    "default": dict(),
    "features_off": dict(off=("dust", "specks", "macro")),
    "damage_displacement": dict(displacement="damage", pixel_size=0.5),
    "small_tiles_joint": dict(tile_w=0.10, tile_h=0.10, joint=0.0015, row_offset=0.5, rotation=0.3),
}

result = {}
for label, kwargs in CASES.items():
    bpy.ops.wm.read_homefile(use_empty=True)
    mat = tile_surface.tile_material("T_" + label, **kwargs)
    result[label] = dump_material(mat)
bpy.ops.wm.read_homefile(use_empty=True)
result["glazed_pool"] = dump_material(tile_surface.glazed_tiles("G_pool"))

# Mutations on one material: each step is dumped, so a change in any editing path shows up.
bpy.ops.wm.read_homefile(use_empty=True)
mat = tile_surface.tile_material("T_mut")
plane = bpy.data.objects.new("Wall", bpy.data.meshes.new("Wall"))
bpy.context.scene.collection.objects.link(plane)
plane.data.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
plane.data.materials.append(mat)
steps = [
    ("set_tile_w", lambda: tile_surface.set_param(mat, "tile_w", 0.06)),
    ("set_off", lambda: tile_surface.set_param(mat, "off", ("dust", "specks"))),
    ("toggle_macro", lambda: tile_surface.toggle(mat, "macro", False)),
    ("damage_displacement", lambda: tile_surface.use_damage_displacement(mat, [plane], 0.5)),
    ("set_after_displacement", lambda: tile_surface.set_param(mat, "tilt_deg", 0.8)),
    ("use_bump", lambda: tile_surface.use_bump(mat)),
]
for label, step in steps:
    step()
    result["mut_" + label] = dump_material(mat)
result["mut_settings"] = value(tile_surface._settings(mat))

write(OUT, result)
print("TILE_GRAPH_CHECK written", OUT, "cases:", sorted(result))
