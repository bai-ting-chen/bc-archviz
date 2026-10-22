"""3ds Max .max -> Blender: repaired import, units and slots, vendor V-Ray materials rebuilt (run in Blender).

Uses the `io_scene_max` extension (Import Autodesk MAX, extensions.blender.org) and repairs
what version 1.9.2 gets wrong, from the importer's own captured face / ID / UV lists:
- Tube segments (trunks, branches, twigs, any lathe/loft tube) come as one record per band
  between two rings ([0,1,2,3,0, 4,7,6,5,4]: ring A to its seam, ring B back). validate() drops
  them -> rebuilt as the strip between the rings with the record's UVs; rings that differ in
  vertex count (a tapering tube) are zipped by their u.
- The full per-face material-ID list is written onto the shorter polygon list (IDs shift after
  the first dropped face) -> re-assigned face by face.
- Slot != Max ID (Multi/Sub parameter block, 2-sided subs take two slots) -> mapped per sub.
- The first UV layer may be Max channel 0 (vertex colour) -> render UV = channel 1.
references/scene/max-import.md has the workflow and the checks.

    import max_import
    objs, report = max_import.load(path)            # repaired meshes + per-object report
    max_import.tidy(objs, unit_scale=0.01)          # Max cm -> m, loose verts, unused slots
    max_import.rebuild_materials(objs, maps_dir)    # V-Ray maps by name -> Principled / leaf cards
"""
import importlib
import os
import re
from collections import Counter

import addon_utils
import bmesh
import bpy
from mathutils import Matrix, Vector

MOD = "bl_ext.user_default.io_scene_max"


def load(path, **kw):
    """Import a .max through io_scene_max and repair faces, material IDs and UVs; returns (objects, reports)."""
    addon_utils.enable(MOD, default_set=False)      # --factory-startup leaves extensions off
    im = importlib.import_module(MOD + ".import_max")
    captured = []
    orig, orig_adj = im.create_shape, im.adjust_material
    # Multi/Sub: the importer appends slots sub by sub, and a 2-sided sub adds two (front, back),
    # so slot != Max ID. Record the first slot each sub-material starts at.
    state = {"depth": 0, "multi": False, "starts": []}

    def adj(filename, search, obj, mat):
        if state["depth"] == 0:
            state["multi"] = mat is not None and im.get_guid(mat) == 0x0200
            state["starts"] = []
        sub = (state["depth"] == 1 and state["multi"] and obj is not None and mat is not None
               and "ParamBlock" not in str(im.get_cls_name(mat)))
        n0 = len(obj.data.materials) if sub else 0
        state["depth"] += 1
        try:
            return orig_adj(filename, search, obj, mat)
        finally:
            state["depth"] -= 1
            if sub:     # None = a sub-material the importer could not build (no slot)
                state["starts"].append(n0 if len(obj.data.materials) > n0 else None)

    def spy(context, settings, node, mesh, mat):
        faces = [list(f) for f in (mesh.faces or [])]
        mats = list(mesh.mats)
        cords = list(mesh.cords or [])
        uvids = [[list(u) for u in ch] for ch in (mesh.uvids or [])]
        mesh_maps = list(mesh.maps or [])
        out = orig(context, settings, node, mesh, mat)
        if out and out[-1].type == "MESH":
            starts = list(state["starts"]) if state["multi"] else [0]
            captured.append((out[-1], faces, mats, cords, uvids, mesh_maps, starts))
        return out

    im.create_shape, im.adjust_material = spy, adj
    try:
        bpy.ops.import_scene.max(filepath=path, **kw)
    finally:
        im.create_shape, im.adjust_material = orig, orig_adj
    return [c[0] for c in captured], [_repair(*c) for c in captured]


def _split(f):
    """Positions of the sub-faces in a run-on record: a sub-face ends where its first vertex repeats."""
    out, start = [], 0
    i = start + 1
    while i < len(f):
        if f[i] == f[start]:
            out.append(list(range(start, i))); start = i + 1; i = start + 1
        else:
            i += 1
    if start < len(f):
        out.append(list(range(start, len(f))))
    return [s for s in out if len(s) >= 3]


def _band(f):
    """Band record -> (ring A positions, ring B positions), both running the same way around.
    Ring A: 0..a with f[a] == f[0]; ring B: the rest, written backwards and also closed."""
    a = next((i for i in range(1, len(f)) if f[i] == f[0]), None)
    if a is None or a < 3 or len(f) - (a + 1) < 4:
        return None
    if f[a + 1] != f[-1]:
        return None
    A = list(range(0, a + 1))
    B = list(range(len(f) - 1, a, -1))
    if len(set(f[p] for p in A[:-1]) | set(f[p] for p in B[:-1])) != len(A) - 1 + len(B) - 1:
        return None
    return A, B


def _uv_table(cords):
    if cords and isinstance(cords[0], (tuple, list)):
        return [tuple(c[:2]) for c in cords]
    c = [co for i, co in enumerate(cords) if i % 3 in (0, 1)]
    return list(zip(c[0::2], c[1::2]))


def _repair(obj, faces, mats, cords_all, uvids_all, maps, starts):
    me = obj.data
    r = {"object": obj.name, "max_faces": len(faces), "blender_faces": len(me.polygons),
         "raw_ids": dict(Counter(mats)), "id_to_slot": starts,
         "slots": [m.name if m else None for m in me.materials]}
    if not mats or len(mats) != len(faces):
        r["skipped"] = "no per-face IDs"
        return r
    top = max(len(me.materials) - 1, 0)
    # Max wraps IDs past the sub-material count; each ID goes to its sub-material's first slot
    unbuilt = Counter(m for m in mats if starts and starts[m % len(starts)] is None)
    if unbuilt:
        r["WARNING_ids_without_material"] = dict(unbuilt)   # these faces fall back to slot 0
    mats = [min(starts[m % len(starts)] or 0, top) if starts else 0 for m in mats]
    # Max map channel 0 is vertex colour, 1 is the UV that bitmaps read by default; the importer
    # makes its first layer from whichever channel comes first. Render UV = channel 1.
    chans = {(maps[i] if i < len(maps) else i): (_uv_table(c), u)
             for i, (c, u) in enumerate(zip(cords_all, uvids_all)) if c is not None and len(u) == len(faces)}
    pick = 1 if 1 in chans else (min(chans) if chans else None)
    uvc, uvids = chans[pick] if pick is not None else (None, None)
    r["uv_channels"] = sorted(chans); r["uv_channel_used"] = pick
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ids, dropped, pairs, j = [None] * len(bm.faces), [], [], 0
    for k, f in enumerate(faces):          # validate() keeps the order of the faces it keeps
        if j < len(bm.faces) and {v.index for v in bm.faces[j].verts} == set(f):
            ids[j] = mats[k]; pairs.append((j, k)); j += 1
        else:
            dropped.append(k)
    r["matched"] = j
    # UVs face by face: the importer flattens every face's UV list into one loop array, so a
    # record whose UV list is out of step shifts the UVs of every later face
    for extra in list(bm.loops.layers.uv.values())[1:]:     # other channels: not used by the maps
        bm.loops.layers.uv.remove(extra)
    layers = list(bm.loops.layers.uv.values())[:1]
    uv = layers[0] if layers else None
    changed = set_ = 0
    for (tab, ch), lay in zip([(uvc, uvids)] if uvc is not None else [], layers):
        for jj, k in pairs:
            if len(ch[k]) != len(faces[k]):
                continue
            pos = {}
            for p_, vi in enumerate(faces[k]):
                pos.setdefault(vi, p_)
            for l in bm.faces[jj].loops:
                new = tab[ch[k][pos[l.vert.index]]]
                if abs(l[lay].uv[0] - new[0]) + abs(l[lay].uv[1] - new[1]) > 1e-5:
                    changed += 1
                l[lay].uv = new; set_ += 1
    r["uv_loops_set"] = set_; r["uv_loops_corrected"] = changed
    r["dropped_by_sides"] = dict(Counter(len(faces[k]) for k in dropped))
    for f, mid in zip(bm.faces, ids):
        if mid is not None:
            f.material_index = mid
    restored = failed = duplicate = sides = 0
    for k in dropped:
        f = faces[k]
        band = _band(f)
        if band:
            # a band: ring A around to its seam, then ring B back the other way; rings may
            # differ in vertex count where a tube tapers. Zip them by their position around
            # the ring (UV u when present), quads where both step, triangles where one does.
            # (Not two caps: those would sit inside every tube segment.)
            A, B = band
            has_uv = uv is not None and uvc is not None and len(uvids[k]) == len(f)
            if has_uv:
                ua = [uvc[uvids[k][p]][0] for p in A]; ub = [uvc[uvids[k][p]][0] for p in B]
                if not (ua[-1] > ua[0] and ub[-1] > ub[0]):
                    has_uv = False
            if not has_uv:
                ua = [i / (len(A) - 1) for i in range(len(A))]; ub = [i / (len(B) - 1) for i in range(len(B))]
            na = lambda i: (ua[i] - ua[0]) / (ua[-1] - ua[0])
            nb = lambda j: (ub[j] - ub[0]) / (ub[-1] - ub[0])
            i = j = 0
            while i < len(A) - 1 or j < len(B) - 1:
                ta = na(i + 1) if i < len(A) - 1 else 9.0
                tb = nb(j + 1) if j < len(B) - 1 else 9.0
                if abs(ta - tb) < 1e-4:
                    pos = [A[i], A[i + 1], B[j + 1], B[j]]; i += 1; j += 1
                elif ta < tb:
                    pos = [A[i], A[i + 1], B[j]]; i += 1
                else:
                    pos = [A[i], B[j + 1], B[j]]; j += 1
                q = [bm.verts[f[p]] for p in pos]
                if len(set(q)) < len(q):
                    failed += 1; continue
                if bm.faces.get(q) is not None:
                    duplicate += 1; continue
                try:
                    nf = bm.faces.new(q)
                except ValueError:
                    failed += 1; continue
                nf.material_index = mats[k]; sides += 1
                if uv is not None and uvc is not None and len(uvids[k]) == len(f):
                    for l, p in zip(nf.loops, pos):
                        l[uv].uv = uvc[uvids[k][p]]
            continue
        for pos in _split(f):
            vs = [bm.verts[faces[k][p]] for p in pos]
            if len(set(vs)) < len(vs):
                failed += 1; continue     # repeated vertex: degenerate in Max too
            if bm.faces.get(vs) is not None:
                duplicate += 1; continue  # same face already present (kept by validate)
            try:
                nf = bm.faces.new(vs)
            except ValueError:
                failed += 1
                continue
            nf.material_index = mats[k]; restored += 1
            if uv is not None and uvc is not None and len(uvids[k]) == len(faces[k]):
                for l, p in zip(nf.loops, pos):
                    l[uv].uv = uvc[uvids[k][p]]
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    r.update(other_restored=restored, restore_failed=failed, already_present=duplicate, band_quads=sides,
             band_records=sum(1 for k in dropped if _band(faces[k])),
             unequal_bands=sum(1 for k in dropped if (b := _band(faces[k])) and len(b[0]) != len(b[1])),
             uv_restored=uvc is not None,
             final_ids=dict(Counter(p.material_index for p in me.polygons)))
    return r


def tidy(objs, unit_scale=0.01):
    """Bake transforms, scale Max system units to metres (cm: 0.01), drop loose verts and unused slots."""
    report = {"loose_removed": 0}
    for o in objs:
        me = o.data
        me.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        bm = bmesh.new(); bm.from_mesh(me)
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bmesh.ops.scale(bm, vec=(unit_scale,) * 3, verts=bm.verts)
        bm.to_mesh(me); bm.free()
        report["loose_removed"] += len(loose)
        used = sorted({p.material_index for p in me.polygons})     # back slots of 2-sided subs
        remap = {old: new for new, old in enumerate(used)}
        idx = [remap[p.material_index] for p in me.polygons]
        keep = [me.materials[i] for i in used]
        me.materials.clear()
        for m in keep:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", idx)
    zs = [v.co.z for o in objs for v in o.data.vertices]
    report["height_m"] = round(max(zs) - min(zs), 3) if zs else 0.0
    return report


# vendor map suffixes, first match wins
SUFFIX = {"albedo": ("albedo", "diffuse", "diff", "basecolor", "color"),
          "opacity": ("opacity", "op", "alpha", "mask"),
          "tran": ("tran", "translucency", "transmission", "sss"),
          "gloss": ("glossiness", "gloss"),
          "rough": ("roughness", "rough"),
          "normal": ("normal", "nrm", "nor")}
EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr")


def _find(maps_dir, base, kind):
    for s in SUFFIX[kind]:
        for e in EXTS:
            p = os.path.join(maps_dir, f"{base}_{s}{e}")
            if os.path.exists(p):
                return p
    return None


def _img(nt, path, colour, x, y):
    n = nt.nodes.new("ShaderNodeTexImage"); n.location = (x, y)
    n.image = bpy.data.images.load(path, check_existing=True)
    n.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return n


def _base_name(mat_name):
    """Map base from the importer's material name ('<max name>_<diffuse bitmap stem>')."""
    m = re.search(r"([A-Za-z0-9]+(?:_[A-Za-z0-9]+)*?)_(?:" + "|".join(SUFFIX["albedo"]) + r")$", mat_name)
    if not m:
        return None
    # the bitmap stem follows the Max material name: try the longest tail that has maps
    parts = m.group(1).split("_")
    return ["_".join(parts[i:]) for i in range(len(parts))]


def rebuild_materials(objs, maps_dir, bark_roughness=0.85, leaf_roughness=0.8):
    """Rebuild imported V-Ray materials from the vendor maps: leaf cards (opacity map) or opaque PBR."""
    log = {}
    for m in {s.material for o in objs for s in o.material_slots if s.material}:
        bases = _base_name(m.name) or []
        base = next((b for b in bases if _find(maps_dir, b, "albedo")), None)
        if not base:
            log[m.name] = "no maps found - left as imported"; continue
        notes = []
        m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
        p = nt.nodes.new("ShaderNodeBsdfPrincipled"); p.location = (300, 0)
        a = _img(nt, _find(maps_dir, base, "albedo"), True, -500, 400)
        nt.links.new(a.outputs["Color"], p.inputs["Base Color"])
        leaf = _find(maps_dir, base, "opacity")
        g, rgh = _find(maps_dir, base, "gloss"), _find(maps_dir, base, "rough")
        if g:   # V-Ray: a wired glossiness map overrides the stored value; roughness = 1 - gloss
            gn = _img(nt, g, False, -500, -650)
            inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.location = (0, -650)
            inv.inputs[0].default_value = 1.0
            nt.links.new(gn.outputs["Color"], inv.inputs[1]); nt.links.new(inv.outputs[0], p.inputs["Roughness"])
        elif rgh:
            nt.links.new(_img(nt, rgh, False, -500, -650).outputs["Color"], p.inputs["Roughness"])
        else:
            p.inputs["Roughness"].default_value = leaf_roughness if leaf else bark_roughness
            notes.append("no glossiness/roughness map")
        n = _find(maps_dir, base, "normal")
        if n:
            t = _img(nt, n, False, -500, -400)
            nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (0, -400)
            nt.links.new(t.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
        else:
            notes.append("no normal map")
        if leaf:
            # thin card: reflection + diffuse transmission, cut by opacity. Leaf R and T are both
            # small (green leaf ~0.05-0.1 each), so adding them stays below 1.
            p.inputs["IOR"].default_value = 1.6
            tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.location = (300, 300)
            tr = _find(maps_dir, base, "tran")
            if tr:
                nt.links.new(_img(nt, tr, True, -500, 100).outputs["Color"], tl.inputs["Color"])
            else:
                nt.links.new(a.outputs["Color"], tl.inputs["Color"]); notes.append("no tran map: transmission = albedo")
            add = nt.nodes.new("ShaderNodeAddShader"); add.location = (550, 150)
            nt.links.new(p.outputs[0], add.inputs[0]); nt.links.new(tl.outputs[0], add.inputs[1])
            tp = nt.nodes.new("ShaderNodeBsdfTransparent"); tp.location = (550, -100)
            mix = nt.nodes.new("ShaderNodeMixShader"); mix.location = (750, 0)
            nt.links.new(_img(nt, leaf, False, -500, -150).outputs["Color"], mix.inputs["Fac"])
            nt.links.new(tp.outputs[0], mix.inputs[1]); nt.links.new(add.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], out.inputs[0])
        else:
            p.inputs["IOR"].default_value = 1.52
            nt.links.new(p.outputs[0], out.inputs[0])
        log[m.name] = {"base": base, "kind": "leaf" if leaf else "opaque", "notes": notes}
    return log


def open_loops(obj, material_index=None):
    """Open-edge loops (optionally of one material): z, span, closed, which side the faces are on - holes vs tube ends."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    sel = lambda f: material_index is None or f.material_index == material_index
    open_ = [e for e in bm.edges if len(e.link_faces) == 1 and sel(e.link_faces[0])]
    adj = {}
    for e in open_:
        for v in e.verts:
            adj.setdefault(v, []).append(e)
    left, loops = set(open_), []
    while left:
        e0 = left.pop(); grp = [e0]; stack = [e0]
        while stack:
            e = stack.pop()
            for v in e.verts:
                for n in adj[v]:
                    if n in left:
                        left.remove(n); grp.append(n); stack.append(n)
        vs = {v for e in grp for v in e.verts}
        c = sum((obj.matrix_world @ v.co for v in vs), Vector()) / len(vs)
        span = max((a.co - b.co).length for a in vs for b in vs) if len(vs) < 300 else None
        fz = [e.link_faces[0].calc_center_median().z - sum(v.co.z for v in e.verts) / 2 for e in grp]
        loops.append({"edges": len(grp), "z": round(c.z, 3), "span": round(span, 4) if span else None,
                      "closed": all(len([n for n in adj[v] if n in grp]) == 2 for v in vs),
                      "faces_side": "below" if all(z < 0 for z in fz) else "above" if all(z > 0 for z in fz) else "mixed"})
    bm.free()
    return sorted(loops, key=lambda l: l["z"])


def slot_maps(objs, maps_dir, exts=(".jpg", ".png", ".tif")):
    """Bitmap per slot prefix (leaf1, leaf2, seed ...) per object, read BEFORE tidy(): in a VRay2Sided sub the BACK slot often carries the bitmap name and the front none, and tidy() drops the unused back slots. The map is the longest tail of '<max name>_<bitmap stem>' that exists in maps_dir (a Blender '.001' suffix is ignored)."""
    out = {}
    for o in objs:
        d = out.setdefault(o.name, {})
        for s in o.material_slots:
            if not s.material:
                continue
            stem = re.sub(r"\.\d+$", "", s.material.name)
            if not re.search(r"_(?:diffuse|albedo)$", stem):
                continue
            parts = stem.split("_")
            for k in range(1, len(parts)):
                hit = next((os.path.join(maps_dir, "_".join(parts[k:]) + e) for e in exts
                            if os.path.exists(os.path.join(maps_dir, "_".join(parts[k:]) + e))), None)
                if hit:
                    d.setdefault(parts[0].rstrip("FB"), hit)
                    break
    return out


def origin_to_root(obj):
    """Move the mesh so its root (bbox centre in plan, lowest z) sits at the object origin - for scattering clumps on terrain."""
    vs = [v.co for v in obj.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    root = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    obj.data.transform(Matrix.Translation(-root))
    obj.location = (0, 0, 0)
    return {"height_m": hi.z - lo.z, "width_m": max(hi.x - lo.x, hi.y - lo.y)}
