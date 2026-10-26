"""Canonical helper-regression graph fingerprints."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import json
import os
import bpy

SKIP = {"name", "location", "location_absolute", "width", "height", "select", "hide", "mute", "show_options",
        "show_preview", "show_texture", "use_custom_color", "color", "label_size", "shrink", "parent",
        "dimensions", "is_active_output", "warning_propagation", "color_tag", "bl_idname", "bl_label",
        "bl_description", "bl_icon", "bl_static_type", "bl_width_default", "bl_width_min",
        "bl_width_max", "bl_height_default", "bl_height_min", "bl_height_max", "type", "internal_links",
        "inputs", "outputs", "rna_type", "image_user", "texture_mapping", "color_mapping"}

def val(v):
    """Convert node values into stable rounded JSON-compatible data."""
    if isinstance(v, float):
        return round(v, 6)
    if hasattr(v, "__len__") and not isinstance(v, str):
        try:
            return [val(x) for x in v]
        except TypeError:
            return str(v)
    if isinstance(v, bpy.types.ID):
        return v.__class__.__name__ + ":" + (os.path.basename(getattr(v, "filepath", "")) or v.name.split(".")[0])
    return v

def sig(n):
    """Fingerprint one node by its settings and unlinked socket values."""
    d = {"type": n.bl_idname, "label": n.label}
    for p in n.bl_rna.properties:
        if p.identifier in SKIP or p.is_readonly and p.type != "POINTER":
            continue
        try:
            v = getattr(n, p.identifier)
        except Exception:
            continue
        if p.type in ("ENUM", "BOOLEAN", "INT", "FLOAT", "STRING") or isinstance(v, bpy.types.ID):
            d[p.identifier] = val(v)
    d["in"] = {s.identifier: val(s.default_value) for s in n.inputs
               if not s.is_linked and hasattr(s, "default_value")}
    if n.bl_idname == "NodeFrame":
        d = {"type": "NodeFrame", "label": n.label}
    return json.dumps(d, sort_keys=True, default=str)

def graph(nt):
    """Fingerprint node content, links and interface without layout or names."""
    s = {n.name: sig(n) for n in nt.nodes}
    nodes = sorted(s.values())
    links = sorted(f"{s[l.from_node.name]}|{l.from_socket.identifier}->{s[l.to_node.name]}|{l.to_socket.identifier}"
                   for l in nt.links)
    iface = []
    if hasattr(nt, "interface"):
        for it in nt.interface.items_tree:
            if it.item_type == "SOCKET":
                iface.append([it.in_out, it.name, it.socket_type, val(getattr(it, "default_value", None))])
    return {"nodes": nodes, "links": links, "interface": iface}

def snapshot():
    """Collect material, group and world graphs from the current fixture."""
    out = {}
    for m in bpy.data.materials:
        if m.node_tree:
            out["MAT " + m.name] = graph(m.node_tree)
    for g in bpy.data.node_groups:
        out["GRP " + g.name] = graph(g)
    for w in bpy.data.worlds:
        if w.node_tree:
            out["WORLD " + w.name] = graph(w.node_tree)
    return out
