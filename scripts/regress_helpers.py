"""Regression check for the Blender helpers: build every material / node-group helper in a fresh
file and fingerprint each node graph by content (node types, settings, input values, links --
not names or layout), plus evaluated vertex positions of the GN wear groups.

  1. snapshot the current code:  git archive HEAD scripts | tar -x -C <dir>/old
  2. assets: a project folder whose library/ holds polyhaven/textures/{concrete_wall_009,
     coated_pine, gray_rocks}, polyhaven/hdris/kloppenheim_06_puresky and local/leakage_tdlbbd1c
     (polyhaven_fetch.py; the leak map is a Megascans download) -- a throwaway copy, since
     albedo_material caches into meta.json
  3. blender -b --factory-startup --python regress_helpers.py -- dump <scripts/blender> <project> <out.json>
     using each snapshot's own regress_helpers.py and matching scripts/blender directory.
     A pre-package snapshot uses its pre-package runner; the current runner uses canonical materials modules.
  4. python regress_helpers.py compare old.json new.json   -> only intended differences may print
"""
import json
import os
import sys

if len(sys.argv) > 1 and sys.argv[1] == "compare":
    a, b = json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if x == y:
            continue
        print("##", k)
        if not isinstance(x, dict) or not isinstance(y, dict) or "ERROR" in x or "ERROR" in y or k.startswith("eval"):
            print("  old:", str(x)[:300]); print("  new:", str(y)[:300]); continue
        for dk in sorted(set(x) | set(y)):
            gx, gy = x.get(dk), y.get(dk)
            if gx == gy: continue
            if gx is None or gy is None: print("  only in", "new" if gx is None else "old", dk); continue
            for part in ("nodes", "links", "interface"):
                ox, oy = gx[part], gy[part]
                if ox == oy: continue
                from collections import Counter
                cx, cy = Counter(map(str, ox)), Counter(map(str, oy))
                for s in (cx - cy): print("  -", dk, part, s[:260])
                for s in (cy - cx): print("  +", dk, part, s[:260])
elif "--" in sys.argv and sys.argv[sys.argv.index("--") + 1] == "dump":
    import traceback
    import bpy

    SRC, HERE, OUT = sys.argv[sys.argv.index("--") + 2:][:3]
    sys.path.insert(0, SRC)

    SKIP = {"name", "location", "location_absolute", "width", "height", "select", "hide", "mute", "show_options",
            "show_preview", "show_texture", "use_custom_color", "color", "label_size", "shrink", "parent",
            "dimensions", "is_active_output", "warning_propagation", "color_tag", "bl_idname", "bl_label",
            "bl_description", "bl_icon", "bl_static_type", "bl_width_default", "bl_width_min",
            "bl_width_max", "bl_height_default", "bl_height_min", "bl_height_max", "type", "internal_links",
            "inputs", "outputs", "rna_type", "image_user", "texture_mapping", "color_mapping"}


    def val(v):
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


    def eval_positions(group, add):
        bpy.ops.mesh.primitive_cube_add(size=0.4)
        ob = bpy.context.object
        import materials.edge_wear as wear
        wear.dice(ob, 0.05)
        add(ob, group)
        dg = bpy.context.evaluated_depsgraph_get()
        me = ob.evaluated_get(dg).to_mesh()
        pts = sorted((round(v.co.x, 7), round(v.co.y, 7), round(v.co.z, 7)) for v in me.vertices)
        return {"n": len(pts), "sum": [round(sum(p[i] for p in pts), 6) for i in range(3)], "head": pts[:5]}


    def B(fn):
        def run():
            # Each dump uses a fresh Blender process; preserve one project-root state.
            import archviz as a
            a.set_project(HERE)
            return fn()
        return run


    def mods():
        """Import only modules needed by a case; do not let an unrelated import fail every case."""
        import importlib
        class Modules(dict):
            def __missing__(self, name):
                self[name] = importlib.import_module(name)
                return self[name]
        return Modules()


    CASES = {
        "pbr_material": lambda m: m['materials.pbr'].pbr_material("concrete_wall_009"),
        "glass_material": lambda m: m['materials.pbr'].glass_material(),
        "simple_material": lambda m: m['materials.pbr'].simple_material("S", (0.5, 0.4, 0.3)),
        "material_from_spec": lambda m: m['materials.pbr'].material_from_spec({"type": "simple", "name": "S2", "color": (.2, .2, .2)}),
        "world_hdri": lambda m: m['archviz'].world_hdri("kloppenheim_06_puresky"),
        "concrete_study": lambda m: m['materials.concrete'].concrete_study(),
        "displaced_ground": lambda m: m['materials.ground'].displaced_ground(),
        "coated_wood": lambda m: m['materials.wood'].coated_wood(),
        "clear_glass": lambda m: m['materials.glass'].clear_glass(),
        "white_backdrop": lambda m: m['materials.pbr'].white_backdrop(),
        "glazed_tiles": lambda m: m['materials.tile_surface'].glazed_tiles(),
        "emitter": lambda m: m['interior'].emitter("E", 1000.0),
        "emitter_dots": lambda m: m['interior'].emitter_dots("ED", 1000.0),
        "polished_granite": lambda m: m['materials.stone'].polished_granite(),
        "stone_tiles": lambda m: m['materials.stone'].stone_tiles(),
        "polished_steel": lambda m: m['materials.metal'].polished_steel(),
        "pool_water": lambda m: m['materials.water'].pool_water(),
        "steam": lambda m: m['materials.volumes'].steam(),
        "sheer": lambda m: m['materials.fabric'].sheer(),
        "random_tone": lambda m: m['materials.variation'].random_tone_material("R", (0.1, 0.1, 0.1), (0.2, 0.2, 0.2)),
        "albedo_material": lambda m: m['materials.pbr'].albedo_material("concrete_wall_009", "AM", (0.5, 0.5, 0.5)),
        "vertical_boards": lambda m: m['materials.concrete'].vertical_boards(m['materials.pbr'].albedo_material("concrete_wall_009", "VB", (0.5, 0.5, 0.5))),
        "long_pavers": lambda m: m['materials.stone'].long_pavers("concrete_wall_009", "LP", (0.4, 0.4, 0.4)),
        "dielectric": lambda m: m['materials.pbr'].dielectric("D", 1.52),
        "caustic_sheet_group": lambda m: m['gn_caustics'].caustic_sheet_group(),
        "caustic_sheet_material": lambda m: m['gn_caustics'].caustic_sheet_material(),
        "scatter_group": lambda m: m['scatter'].scatter_group(),
        "edge_wear_group": lambda m: m['materials.edge_wear'].edge_wear_group(),
        "weathered_concrete": lambda m: m['materials.edge_wear'].weathered_concrete(),
        "mask_edge_dist": lambda m: m['materials.edge_wear'].mask_material("MK", "edge_dist"),
        "mask_damage": lambda m: m['materials.edge_wear'].mask_material("MK2", "damage"),
        "wood_wear_group": lambda m: m['materials.wood_wear'].wood_wear_group(),
        "weathered_wood": lambda m: m['materials.wood_wear'].weathered_wood(),
    }
    res = {}
    for k, f in CASES.items():
        bpy.ops.wm.read_homefile(use_empty=True)
        try:
            B(lambda: f(mods()))()
            res[k] = snapshot()
        except Exception:
            res[k] = {"ERROR": traceback.format_exc().splitlines()[-1]}
    for k, fn in (("eval edge_wear", lambda m: eval_positions(m['materials.edge_wear'].edge_wear_group(), m['materials.edge_wear'].add_edge_wear)),
                  ("eval wood_wear", lambda m: eval_positions(m['materials.wood_wear'].wood_wear_group(), m['materials.edge_wear'].add_edge_wear))):
        bpy.ops.wm.read_homefile(use_empty=True)
        try:
            res[k] = B(lambda: fn(mods()))()
        except Exception:
            res[k] = {"ERROR": traceback.format_exc().splitlines()[-1]}
    json.dump(res, open(OUT, "w"), indent=1, sort_keys=True)
    print("DUMPED", len(res), sum(1 for v in res.values() if "ERROR" in v), "errors")
