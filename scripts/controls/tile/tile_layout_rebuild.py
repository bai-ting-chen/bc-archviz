"""Check layout upgrade values and both link directions."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import bpy
import numpy as np
import materials.tile.tile_layout as tile_layout
from tile_layout_rig import CASES, plane_with, pixel_coords, stable

def check_rebuild(change_interface=False):
    """Check values and both link directions through an old-version group rebuild."""
    material = bpy.data.materials.new("rebuild_probe")
    material.use_nodes = True
    nt = material.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    group = tile_layout.add_layout(nt, tc.outputs["Object"], joint=0.004)
    sink = nt.nodes.new("ShaderNodeMath")
    nt.links.new(group.outputs["Edge"], sink.inputs[0])
    old = group.node_tree
    # Removing the newly added socket simulates the previous interface version.
    if change_interface:
        item = next(item for item in old.interface.items_tree
                    if item.item_type == "SOCKET" and item.in_out == "INPUT"
                    and item.name == "Corner Radius")
        old.interface.remove(item)
    old["tile_layout_version"] = 0
    rebuilt = tile_layout.layout_group()
    assert group.node_tree == rebuilt, "instance not retargeted"
    assert abs(group.inputs["Joint"].default_value - 0.004) < 1e-8, "Joint value lost"
    assert any(link.from_node == tc and link.from_socket.name == "Object"
               and link.to_node == group and link.to_socket.name == "Vector"
               for link in nt.links), "Vector link lost"
    assert any(link.from_node == group and link.from_socket.name == "Edge"
               and link.to_node == sink and link.to_socket == sink.inputs[0]
               for link in nt.links), "Edge link lost"
    if not change_interface:
        assert rebuilt == old, "matching interface was replaced"
