"""Deterministic dump of a node tree (shader, material or Geometry Nodes) for the refactor controls.

Records every node (type, label, settings, input defaults), every link, and nested node groups.
Names are kept (they carry the wiring intent); random owner ids and custom properties are left out.
"""
import json

import bpy


def value(v):
    """Socket or setting value as rounded plain data."""
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, bpy.types.bpy_struct):
        return getattr(v, "name", str(v))
    if hasattr(v, "__len__") and not isinstance(v, str):
        try:
            return [value(x) for x in v]
        except TypeError:
            return str(v)
    return v if isinstance(v, (int, str, bool)) or v is None else str(v)


def dump_tree(tree):
    """Nodes and links of one node tree; group nodes recurse into their node tree."""
    nodes = {}
    for n in tree.nodes:
        entry = {"type": n.bl_idname, "label": n.label, "mute": n.mute,
                 "settings": {}, "inputs": {}}
        for p in n.bl_rna.properties:
            if p.identifier in ("name", "location", "location_absolute", "width", "height", "dimensions",
                                "select", "hide", "parent", "inputs", "outputs", "internal_links",
                                "color", "use_custom_color", "show_options", "show_preview", "show_texture",
                                "bl_idname", "bl_label", "bl_description", "bl_icon", "bl_static_type",
                                "bl_width_default", "bl_width_min", "bl_width_max", "bl_height_default",
                                "bl_height_min", "bl_height_max", "rna_type", "type", "label", "mute",
                                "warning_propagation", "show_expanded", "color_tag", "is_active_output",
                                "image_user", "shrink", "label_size", "show_bounds"):
                continue
            if p.type in ("POINTER", "COLLECTION"):
                continue
            entry["settings"][p.identifier] = value(getattr(n, p.identifier))
        for s in n.inputs:
            if hasattr(s, "default_value"):
                entry["inputs"][s.identifier] = value(s.default_value)
        if n.bl_idname == "ShaderNodeGroup" and n.node_tree is not None:
            entry["group"] = {"name": n.node_tree.name, "tree": dump_tree(n.node_tree)}
        nodes[n.name] = entry
    links = sorted(
        [l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier] for l in tree.links)
    return {"nodes": dict(sorted(nodes.items())), "links": links}


def dump_material(mat):
    """Material node tree, plus its editable settings when it has them (tile_surface), without owner ids."""
    out = {"tree": dump_tree(mat.node_tree)}
    if "tile_surface_settings" in mat:
        settings = json.loads(mat["tile_surface_settings"])
        settings.pop("name", None)
        out["settings"] = value(settings)
    return out


def write(path, result):
    """Write the dump as stable JSON."""
    path.write_text(json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
