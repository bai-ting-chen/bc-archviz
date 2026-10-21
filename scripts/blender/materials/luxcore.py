"""LuxCore material helpers: corner dust, anti-tiling, per-instance variation (luxcore.md,
references/materials/edge-wear.md > Concave corners, references/materials/variation.md).

bake_dust(objs, cache_dir)    Cycles bake of a concave-corner dust mask per object into its own
                              UV layout "DustUV" (LuxCore has no AO texture). Cached PNGs.
lux_textured(name, folder, me, dust_png)
                              native LuxCore Disney from a map folder (meta.json "maps": diff,
                              rough; "dimensions_mm"), Image > Randomized Tiling on, albedo x
                              mix(1, DUST_TINT, dust). The Cycles-tree converter cannot set
                              Randomized Tiling, hence a native tree.
glass_instance_tint()         clear glass whose colour varies per instance (Object Info Random
                              converts to LuxCore objectidnormalized; every instance gets its own ID).
Run in Blender (headless or UI). Operators get an explicit context: a --python startup script in
the UI has no active object in its context, unlike background mode."""
import os, json
import bpy

import archviz

DUST_DIST = 0.20                    # m, AO reach = width of the band; 0.12 read as a pencil line
DUST_BAND = (0.55, 0.97)            # AO in the joint .. AO where the dust has faded out
DUST_POWER = 1.2                    # falloff shape: higher = tighter to the corner
DUST_TINT = (0.62, 0.58, 0.52)      # albedo multiplier at full dust (grey-brown)
DUST_HEIGHT = (0.6, 2.6, 1.0, 0.45) # world z from, z to, strength at from, at to: floor > ceiling
DUST_PX = 4096

def _ctx(ob, edit=False):
    win = bpy.context.window_manager.windows[0] if bpy.context.window_manager.windows else None
    ov = dict(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob])
    if win: ov.update(window=win, screen=win.screen)
    if edit: ov["edit_object"] = ob
    return bpy.context.temp_override(**ov)

def dust_uv(ob, name="DustUV"):
    """Non-overlapping layout for a baked map, beside the tiling UVs. Smart Project is
    deterministic, so a cached map still matches: always call it, even when not re-baking
    (a missing layer makes a LuxCore mapping uvindex -1, which crashes pyluxcore)."""
    me = ob.data
    if me.uv_layers.find(name) >= 0: return
    keep = me.uv_layers.active.name if me.uv_layers.active else None
    me.uv_layers.new(name=name); me.uv_layers.active = me.uv_layers[name]
    for o in bpy.context.view_layer.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    with _ctx(ob): bpy.ops.object.mode_set(mode="EDIT")
    with _ctx(ob, edit=True):
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    if keep: me.uv_layers.active = me.uv_layers[keep]

def _dust_bake_material():
    m = bpy.data.materials.get("DustBake") or bpy.data.materials.new("DustBake"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    def rng(lo, hi, to_lo, to_hi):
        r = N("ShaderNodeMapRange"); r.clamp = True
        r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = lo, hi
        r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = to_lo, to_hi
        return r
    def mul(a, b):
        m_ = N("ShaderNodeMath"); m_.operation = "MULTIPLY"; L(a, m_.inputs[0]); L(b, m_.inputs[1]); return m_.outputs[0]
    ao = N("ShaderNodeAmbientOcclusion"); ao.inside = False; ao.only_local = False; ao.samples = 16
    ao.inputs["Distance"].default_value = DUST_DIST
    band = rng(DUST_BAND[0], DUST_BAND[1], 1.0, 0.0); L(ao.outputs["AO"], band.inputs["Value"])
    shape = N("ShaderNodeMath"); shape.operation = "POWER"; shape.inputs[1].default_value = DUST_POWER
    L(band.outputs["Result"], shape.inputs[0])
    geo = N("ShaderNodeNewGeometry")
    big = N("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 5.0; big.inputs["Detail"].default_value = 6
    fine = N("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 90.0; fine.inputs["Detail"].default_value = 4
    L(geo.outputs["Position"], big.inputs["Vector"]); L(geo.outputs["Position"], fine.inputs["Vector"])
    bigr = rng(0.35, 0.65, 0.45, 1.0); L(big.outputs["Fac"], bigr.inputs["Value"])      # patchy extent
    finer = rng(0.3, 0.7, 0.7, 1.0); L(fine.outputs["Fac"], finer.inputs["Value"])      # speckle
    sep = N("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sep.inputs["Vector"])
    hgt = rng(*DUST_HEIGHT); L(sep.outputs["Z"], hgt.inputs["Value"])
    v = mul(mul(mul(shape.outputs[0], bigr.outputs["Result"]), finer.outputs["Result"]), hgt.outputs["Result"])
    em = N("ShaderNodeEmission"); out = N("ShaderNodeOutputMaterial")
    L(v, em.inputs["Color"]); L(em.outputs[0], out.inputs["Surface"])
    tgt = N("ShaderNodeTexImage"); tgt.name = "target"; nt.nodes.active = tgt
    return m

def bake_dust(objs, cache_dir, rebake=False, samples=64):
    """One dust mask per object into cache_dir/<object>.png (EMIT bake, GPU). Returns {name: path}."""
    os.makedirs(cache_dir, exist_ok=True)
    paths = {o.name: os.path.join(cache_dir, o.name + ".png") for o in objs}
    for o in objs: dust_uv(o)
    todo = [o for o in objs if rebake or not os.path.exists(paths[o.name])]
    if not todo: return paths
    sc = bpy.context.scene; eng = sc.render.engine
    sc.render.engine = "CYCLES"; sc.cycles.samples = samples; sc.cycles.use_denoising = False
    archviz.use_gpu(force=True)
    bm = _dust_bake_material(); tgt = bm.node_tree.nodes["target"]
    try:
        _bake_each(todo, bm, tgt, paths)
    finally:                                  # every object bakes under Cycles; engine back once
        sc.render.engine = eng
    return paths


def _bake_each(todo, bm, tgt, paths):
    for o in todo:
        img = bpy.data.images.new("dust_" + o.name, DUST_PX, DUST_PX, float_buffer=False, is_data=True)
        tgt.image = img
        saved = [s.material for s in o.material_slots]
        added = not o.material_slots          # an object without slots would bake nothing
        if added: o.data.materials.append(bm)
        for s in o.material_slots: s.material = bm
        me = o.data; keep = me.uv_layers.active.name; me.uv_layers.active = me.uv_layers["DustUV"]
        try:
            for x in bpy.context.view_layer.objects: x.select_set(False)
            bpy.context.view_layer.objects.active = o; o.select_set(True)
            with _ctx(o): bpy.ops.object.bake(type="EMIT", margin=8, use_clear=True)
            img.filepath_raw = paths[o.name]; img.file_format = "PNG"; img.save()
        finally:                              # a failed bake must not leave the scene on DustBake
            me.uv_layers.active = me.uv_layers[keep]
            if added: o.data.materials.clear()
            for s, mat in zip(o.material_slots, saved): s.material = mat

def lux_textured(name, folder, me, dust_png=None, uv_tex="BoxUV", uv_dust="DustUV", randomized=True, specular=0.5):
    """Native LuxCore Disney from a generated/scanned map folder; `me` = the mesh it goes on
    (its UV layer indices are baked into the tree, so one material per mesh layout)."""
    meta = archviz.read_meta(folder)
    i_tex = me.uv_layers.find(uv_tex); i_dust = me.uv_layers.find(uv_dust)
    if i_tex < 0 or (dust_png and i_dust < 0):
        raise RuntimeError("%s lacks UV layer %s / %s" % (me.name, uv_tex, uv_dust))
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    tree = bpy.data.node_groups.new(name + "_lux", "luxcore_material_nodes")
    m.luxcore.node_tree = tree; m.luxcore.use_cycles_nodes = False
    N, L = tree.nodes.new, tree.links.new
    out = N("LuxCoreNodeMatOutput"); dis = N("LuxCoreNodeMatDisney")
    dis.inputs["Specular"].default_value = specular
    def image(path, gamma, idx, rnd):
        mp = N("LuxCoreNodeTexMapping2D"); mp.mapping_type = "uvmapping2d"; mp.uvindex = idx
        t = N("LuxCoreNodeTexImagemap"); t.image = bpy.data.images.load(path, check_existing=True)
        t.gamma = gamma; t.wrap = "repeat"; t.randomized_tiling = rnd
        L(mp.outputs["2D Mapping"], t.inputs["2D Mapping"]); return t
    diff = image(os.path.join(folder, meta["maps"]["diff"]), 2.2, i_tex, randomized)
    rough = image(os.path.join(folder, meta["maps"]["rough"]), 1.0, i_tex, randomized)
    split = N("LuxCoreNodeTexSplitFloat3"); L(rough.outputs["Color"], split.inputs["Color"])
    L(split.outputs["R"], dis.inputs["Roughness"])
    col = diff.outputs["Color"]
    if dust_png:
        dust = image(dust_png, 1.0, i_dust, False); dust.wrap = "clamp"
        mix = N("LuxCoreNodeTexColorMix"); mix.mode = "mix"
        mix.inputs["Color 1"].default_value = (1, 1, 1); mix.inputs["Color 2"].default_value = DUST_TINT
        L(dust.outputs["Color"], mix.inputs["Fac"])
        mul = N("LuxCoreNodeTexColorMix"); mul.mode = "scale"
        L(col, mul.inputs["Color 1"]); L(mix.outputs["Color"], mul.inputs["Color 2"]); col = mul.outputs["Color"]
    L(col, dis.inputs["Base Color"]); L(dis.outputs["Material"], out.inputs["Material"])
    m["texture_size_m"] = meta["dimensions_mm"][0] / 1000.0
    return m

def glass_instance_tint(name="Glass_rand", tint=(0.985, 0.996, 0.99), ior=1.52):
    """Clear glass; Object Info Random mixes white -> `tint` per instance (per face crossed, so a
    hollow block's 4 faces give ~tint^4)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    info = N("ShaderNodeObjectInfo"); mix = N("ShaderNodeMixRGB"); mix.blend_type = "MIX"
    mix.inputs["Color1"].default_value = (1, 1, 1, 1); mix.inputs["Color2"].default_value = (*tint, 1)
    g = N("ShaderNodeBsdfGlass"); g.inputs["IOR"].default_value = ior; g.inputs["Roughness"].default_value = 0
    o = N("ShaderNodeOutputMaterial")
    L(info.outputs["Random"], mix.inputs["Fac"]); L(mix.outputs["Color"], g.inputs["Color"]); L(g.outputs[0], o.inputs["Surface"])
    m.luxcore.use_cycles_nodes = True
    return m
