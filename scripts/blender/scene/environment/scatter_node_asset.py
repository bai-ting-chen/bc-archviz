"""Scatter asset; implementation for scatter."""
import os
import bpy


def load_scatter_on_surface():
    """Append Blender's essentials 'Scatter on Surface' node group (native, 5.x)."""
    ng = bpy.data.node_groups.get("Scatter on Surface")
    if ng:
        return ng
    path = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "nodes", "geometry_nodes_essentials.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.node_groups = ["Scatter on Surface"]
    return bpy.data.node_groups["Scatter on Surface"]
