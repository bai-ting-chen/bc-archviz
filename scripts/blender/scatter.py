"""Geometry Nodes scatter for small instances: leaf litter, climbers, shrub foliage (run in Blender).

    group = scatter_group()
    leaf = leaf_proto("PROTO_DRY_LEAF", 0.07, 0.045, 0.012, material)
    scatter(objs, leaf, density=0.35, z_max=0.5, seed=3, patch=0.42)

Points are distributed on each target's faces where Z < `z_max` AND a 0.6/m noise > `patch`
(0 = everywhere), then instanced with random rotation and 0.6-1.3 x `scale`. The patch threshold
is sensitive near 0.5: on one wall 0.42 blanketed it, 0.48 gave patches, 0.53 left nothing.
Inputs are set through wear.set_input (Blender 5.2: mod["id"] = v raises).

Meadow / grass on terrain (materials.md > Grass and meadow):
    sos = load_scatter_on_surface()                   # Blender's own essentials group
    grp = meadow_layer_group(sos)
    tx, ty = frustum_tangents(cam, (w, h))
    meadow_layer("MEADOW_01", grp, terrain, grass_collection, cam, Density=220, Tan_X=tx, Tan_Y=ty)
One object per species; masks: species patches (noise), shared bare-soil noise (terrain.BARE_W),
clearance from the pad (`pad_d` from terrain.landform_group), camera frustum + distance. Grass
stays upright (Align Rotation off) and picks random variants of the collection.
"""
import math
import os

import bpy

from wear import set_input


def scatter_group(name="SCATTER"):
    """GN group: distribute points below a height and inside a noise patch, instance with random rotation/scale."""
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    it = ng.interface
    it.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm, typ in (("Instance", "NodeSocketObject"), ("Density", "NodeSocketFloat"), ("Scale", "NodeSocketFloat"),
                    ("Z Max", "NodeSocketFloat"), ("Seed", "NodeSocketInt"), ("Keep Source", "NodeSocketBool"),
                    ("Patchiness", "NodeSocketFloat")):
        it.new_socket(nm, in_out="INPUT", socket_type=typ)
    it.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ")
    L.new(pos.outputs[0], sep.inputs[0])
    below = N.new("FunctionNodeCompare"); below.data_type = "FLOAT"; below.operation = "LESS_THAN"
    L.new(sep.outputs["Z"], below.inputs["A"]); L.new(gi.outputs["Z Max"], below.inputs["B"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6
    patch = N.new("FunctionNodeCompare"); patch.data_type = "FLOAT"; patch.operation = "GREATER_THAN"
    L.new(nz.outputs[0], patch.inputs["A"]); L.new(gi.outputs["Patchiness"], patch.inputs["B"])
    both = N.new("FunctionNodeBooleanMath"); both.operation = "AND"
    L.new(below.outputs[0], both.inputs[0]); L.new(patch.outputs[0], both.inputs[1])
    dist = N.new("GeometryNodeDistributePointsOnFaces")
    L.new(gi.outputs["Geometry"], dist.inputs["Mesh"]); L.new(both.outputs[0], dist.inputs["Selection"])
    L.new(gi.outputs["Density"], dist.inputs["Density"]); L.new(gi.outputs["Seed"], dist.inputs["Seed"])
    oi = N.new("GeometryNodeObjectInfo"); oi.transform_space = "RELATIVE"
    L.new(gi.outputs["Instance"], oi.inputs["Object"])
    rot = N.new("FunctionNodeRandomValue"); rot.data_type = "FLOAT_VECTOR"
    rot.inputs["Max"].default_value = (6.2832, 6.2832, 6.2832)
    rs = N.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"
    rs.inputs["Min"].default_value = 0.6; rs.inputs["Max"].default_value = 1.3
    ms = N.new("ShaderNodeMath"); ms.operation = "MULTIPLY"
    L.new(rs.outputs["Value"], ms.inputs[0]); L.new(gi.outputs["Scale"], ms.inputs[1])
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(dist.outputs["Points"], inst.inputs["Points"]); L.new(oi.outputs["Geometry"], inst.inputs["Instance"])
    L.new(rot.outputs["Value"], inst.inputs["Rotation"]); L.new(ms.outputs[0], inst.inputs["Scale"])
    keep = N.new("GeometryNodeSwitch"); keep.input_type = "GEOMETRY"
    L.new(gi.outputs["Keep Source"], keep.inputs["Switch"]); L.new(gi.outputs["Geometry"], keep.inputs["True"])
    join = N.new("GeometryNodeJoinGeometry")
    L.new(keep.outputs[0], join.inputs[0]); L.new(inst.outputs[0], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    return ng


def leaf_proto(name, length, width, curl, material):
    """A small curled elliptical leaf (10-gon) in a hidden PROTOS collection; reused if present."""
    ob = bpy.data.objects.get(name)
    if ob:
        return ob
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=1.0)
    for v in bm.verts:
        x, y = v.co.x * length / 2, v.co.y * width / 2
        v.co = (x, y, curl * (x / length * 2) ** 2)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    sc = bpy.context.scene
    pc = bpy.data.collections.get("PROTOS") or bpy.data.collections.new("PROTOS")
    if pc.name not in sc.collection.children:
        sc.collection.children.link(pc)
    pc.objects.link(ob)
    pc.hide_render = True
    return ob


def scatter(objs, instance, density, scale=1.0, z_max=1e4, seed=0, keep_source=True, patch=0.0):
    """Add (or update) the SCATTER modifier on each object."""
    ng = scatter_group()
    for o in objs:
        mod = o.modifiers.get("SCATTER") or o.modifiers.new("SCATTER", "NODES")
        mod.node_group = ng
        for k, v in (("Instance", instance), ("Density", density), ("Scale", scale), ("Z Max", z_max),
                     ("Seed", seed), ("Keep Source", keep_source), ("Patchiness", patch)):
            set_input(mod, k, v)


# --- meadow --------------------------------------------------------------------------------

def load_scatter_on_surface():
    """Append Blender's essentials 'Scatter on Surface' node group (native, 5.x)."""
    ng = bpy.data.node_groups.get("Scatter on Surface")
    if ng:
        return ng
    path = os.path.join(os.path.dirname(bpy.app.binary_path), "%d.%d" % bpy.app.version[:2], "datafiles",
                        "assets", "nodes", "geometry_nodes_essentials.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.node_groups = ["Scatter on Surface"]
    return bpy.data.node_groups["Scatter on Surface"]


def meadow_layer_group(scatter_ng, name="MEADOW_LAYER", bare=(0.35, 0.62, 0.69)):
    """GN group: Scatter on Surface on a terrain object, masked by species patch noise, shared bare-soil noise, pad clearance and the camera frustum."""
    from study_materials import G
    from terrain import BARE_W
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.is_modifier = True
    it = ng.interface
    it.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    it.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for nm, typ, dv in (("Terrain", "NodeSocketObject", None), ("Collection", "NodeSocketCollection", None),
                        ("Camera", "NodeSocketObject", None), ("Density", "NodeSocketFloat", 1.0),
                        ("Seed", "NodeSocketInt", 0), ("Patch Scale", "NodeSocketFloat", 0.2),
                        ("Patch Low", "NodeSocketFloat", -1.0), ("Patch High", "NodeSocketFloat", -0.5),
                        ("Use Bare", "NodeSocketBool", True), ("Bare Scale", "NodeSocketFloat", bare[0]),
                        ("Bare Low", "NodeSocketFloat", bare[1]), ("Bare High", "NodeSocketFloat", bare[2]),
                        ("Pad Clear", "NodeSocketFloat", 0.08), ("Scale", "NodeSocketFloat", 1.0),
                        ("Scale Random", "NodeSocketFloat", 0.3), ("Sink", "NodeSocketFloat", 0.01),
                        ("Tan X", "NodeSocketFloat", 0.5), ("Tan Y", "NodeSocketFloat", 0.6),
                        ("Max Distance", "NodeSocketFloat", 150.0), ("Viewport Fraction", "NodeSocketFloat", 0.05)):
        s_ = it.new_socket(nm, in_out="INPUT", socket_type=typ)
        if dv is not None:
            s_.default_value = dv
    g = G(ng, clear=True)
    gi = g.n("NodeGroupInput", (-1600, 0))
    go = g.n("NodeGroupOutput", (1600, 0))
    I = gi.outputs
    oi = g.n("GeometryNodeObjectInfo", (-1300, 300), transform_space="RELATIVE")
    g.link(I["Terrain"], oi.inputs["Object"])
    pos = g.n("GeometryNodeInputPosition", (-1300, -100)).outputs[0]
    # species patches: noise low..high -> 0..1 (Patch Low < 0 = everywhere)
    pn = g.n("ShaderNodeTexNoise", (-1100, -100), noise_dimensions="4D")
    pn.inputs["Detail"].default_value = 3.0
    g.link(pos, pn.inputs["Vector"]); g.link(I["Patch Scale"], pn.inputs["Scale"])
    g.link(g.math("MULTIPLY", I["Seed"], 1.618, (-1300, -250)), pn.inputs["W"])
    pm = g.n("ShaderNodeMapRange", (-900, -100), interpolation_type="SMOOTHSTEP")
    g.link(pn.outputs[0], pm.inputs["Value"]); g.link(I["Patch Low"], pm.inputs["From Min"])
    g.link(I["Patch High"], pm.inputs["From Max"])
    # bare soil: shared noise (terrain.ground_material uses the same) thins the sward to nothing
    bn = g.n("ShaderNodeTexNoise", (-1100, -400), noise_dimensions="4D")
    bn.inputs["Detail"].default_value = 4.0
    bn.inputs["W"].default_value = BARE_W
    g.link(pos, bn.inputs["Vector"]); g.link(I["Bare Scale"], bn.inputs["Scale"])
    bm = g.n("ShaderNodeMapRange", (-900, -400), interpolation_type="SMOOTHSTEP")
    bm.inputs["To Min"].default_value, bm.inputs["To Max"].default_value = 1.0, 0.0
    g.link(bn.outputs[0], bm.inputs["Value"]); g.link(I["Bare Low"], bm.inputs["From Min"])
    g.link(I["Bare High"], bm.inputs["From Max"])
    bsw = g.n("GeometryNodeSwitch", (-700, -400), input_type="FLOAT")
    bsw.inputs["False"].default_value = 1.0
    g.link(I["Use Bare"], bsw.inputs["Switch"]); g.link(bm.outputs["Result"], bsw.inputs["True"])
    # pad clearance
    pad = g.named("pad_d", "FLOAT", (-1100, -700))
    pc = g.n("ShaderNodeMapRange", (-900, -700))
    g.link(pad, pc.inputs["Value"]); g.link(I["Pad Clear"], pc.inputs["From Min"])
    g.link(g.math("ADD", I["Pad Clear"], 0.3, (-1100, -850)), pc.inputs["From Max"])
    # camera frustum + distance: only what the camera can see is scattered
    ci = g.n("GeometryNodeObjectInfo", (-1300, -1000), transform_space="ORIGINAL")
    g.link(I["Camera"], ci.inputs["Object"])
    inv = g.n("FunctionNodeInvertMatrix", (-1100, -1000)); g.link(ci.outputs["Transform"], inv.inputs[0])
    tp = g.n("FunctionNodeTransformPoint", (-900, -1000))
    g.link(pos, tp.inputs["Vector"]); g.link(inv.outputs[0], tp.inputs["Transform"])
    cs = g.n("ShaderNodeSeparateXYZ", (-700, -1000)); g.link(tp.outputs[0], cs.inputs[0])
    depth = g.math("MAXIMUM", g.math("MULTIPLY", cs.outputs["Z"], -1.0, (-550, -1100)), 0.001, (-400, -1100))
    inx = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("DIVIDE", cs.outputs["X"], depth, (-250, -950)), 0.0, (-100, -950)),
                 I["Tan X"], (50, -950))
    iny = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("DIVIDE", cs.outputs["Y"], depth, (-250, -1050)), 0.0, (-100, -1050)),
                 I["Tan Y"], (50, -1050))
    ln = g.n("ShaderNodeVectorMath", (-550, -1250), operation="LENGTH"); g.link(tp.outputs[0], ln.inputs[0])
    near = g.math("LESS_THAN", ln.outputs["Value"], I["Max Distance"], (-400, -1250))
    front = g.math("GREATER_THAN", g.math("MULTIPLY", cs.outputs["Z"], -1.0, (-400, -1350)), 0.0, (-250, -1350))
    fr = g.math("MULTIPLY", g.math("MULTIPLY", inx, iny, (200, -1000)), g.math("MULTIPLY", near, front, (200, -1300)), (350, -1150))
    mask = g.math("MULTIPLY", g.math("MULTIPLY", pm.outputs["Result"], bsw.outputs[0], (400, -300)),
                  g.math("MULTIPLY", pc.outputs["Result"], fr, (400, -800)), (550, -500))
    sc = g.n("GeometryNodeGroup", (800, 0))
    sc.node_tree = scatter_ng
    S = sc.inputs
    g.link(oi.outputs["Geometry"], S["Mesh"]); g.link(I["Density"], S["Density"]); g.link(mask, S["Distribution Mask"])
    S["Keep Surface"].default_value = False
    g.link(I["Seed"], S["Seed"]); g.link(I["Seed"], S["Instance Seed"]); g.link(I["Seed"], S["Randomize Seed"])
    S["Input Type"].default_value = "Data-Block"
    S["Instance Type"].default_value = "Collection"
    g.link(I["Collection"], S["Collection"])
    S["Pick Instance"].default_value = True
    g.link(g.math("MULTIPLY", I["Sink"], -1.0, (600, -200)), S["Surface Offset"])
    S["Align Rotation"].default_value = False            # grass grows up, not along the slope normal
    sv = g.n("ShaderNodeCombineXYZ", (600, -350))
    for k in "XYZ":
        g.link(I["Scale"], sv.inputs[k])
    g.link(sv.outputs[0], S["Scale"])
    S["Randomize"].default_value = True
    S["Randomize Rotation"].default_value = (0.08, 0.08, 2 * math.pi)   # slight lean, any heading
    g.link(I["Scale Random"], [x for x in S if x.name == "Randomize Scale" and x.type == "VALUE"][0])
    g.link(I["Viewport Fraction"], S["Viewport Visibility"])
    g.link(sc.outputs[0], go.inputs[0])
    return ng


def frustum_tangents(cam, res, margin=1.15):
    """Half-tangents (x, y) of a camera's view incl. vertical lens shift, for the meadow frustum mask."""
    cd = cam.data
    tx = cd.sensor_width / 2 / cd.lens * margin
    ty = tx * res[1] / res[0] + abs(cd.shift_y) * cd.sensor_width / cd.lens + 0.1
    return tx, ty


def meadow_layer(name, group, terrain, collection, camera, target_collection=None, **inputs):
    """One meadow layer object (empty mesh + MEADOW_LAYER modifier); inputs by name, '_' for spaces."""
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    (target_collection or bpy.context.scene.collection).objects.link(ob)
    mod = ob.modifiers.new("MEADOW", "NODES")
    mod.node_group = group
    for k, v in dict(Terrain=terrain, Collection=collection, Camera=camera, **inputs).items():
        set_input(mod, k.replace("_", " "), v)
    return ob
