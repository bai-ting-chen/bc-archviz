"""Headless look-dev / control render of a saved .blend, with overrides. Never saves the .blend.

blender -b scene.blend --python render_variant.py -- out.png [key=value ...]
  res=800x800  samples=256  disp=off  caustics=off  wear=off  stain=off  noise_seed=N
  chips=off  breaks=off  woodwear=off  dirt=off  mnee=off  denoise=off  adaptive=T  sun_angle=DEG
  mask_view=1|<node label>
  camera=<object name>  material_view=<material name> [coll=<collection>]  (one material on every mesh)
  key_area=SIZE,DIST[,LUX] [key_target=x,y,z]   water_test=empty_glass|water_only (glassware scenes)
"""
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archviz  # noqa: E402

KNOWN = {"res", "samples", "noise_seed", "camera", "disp", "caustics", "wear", "stain", "chips", "breaks",
         "woodwear", "dirt", "mask_view", "material_view", "coll", "key_area", "key_target", "mnee",
         "adaptive", "denoise", "water_test", "sun_angle"}
argv = sys.argv[sys.argv.index("--") + 1:]
out, opts = argv[0], dict(a.split("=", 1) for a in argv[1:])
unknown = set(opts) - KNOWN
if unknown:   # a typo must not render an unchanged "control"
    sys.exit("render_variant: unknown option(s) %s; known: %s" % (sorted(unknown), sorted(KNOWN)))
sc = bpy.context.scene
archviz.use_gpu()

if "res" in opts:
    sc.render.resolution_x, sc.render.resolution_y = map(int, opts["res"].split("x"))
if "samples" in opts:
    sc.cycles.samples = int(opts["samples"])
if "noise_seed" in opts:
    sc.cycles.seed = int(opts["noise_seed"])
if "camera" in opts:
    sc.camera = bpy.data.objects[opts["camera"]]
if opts.get("disp") == "off":  # negative control: no geometry displacement, bump only
    for m in bpy.data.materials:
        if m.displacement_method in ("DISPLACEMENT", "BOTH"):
            m.displacement_method = "BUMP"
    for ob in bpy.data.objects:
        for md in ob.modifiers:
            if md.type == "SUBSURF":
                md.show_render = False
if "key_area" in opts:  # key_area=SIZE,DIST[,LUX]: swap the sun for a square area light, same direction
    import math
    from mathutils import Vector
    size, dist, *lux = [float(x) for x in opts["key_area"].split(",")]
    lux = lux[0] if lux else 6000.0
    sun = next(o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN")
    d = (sun.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()   # towards the light
    target = Vector([float(v) for v in opts.get("key_target", "0,0,0").split(",")])
    lamp = bpy.data.lights.new("Key_area", "AREA")
    lamp.shape, lamp.size = "SQUARE", size
    lamp.energy = lux * math.pi * dist ** 2 / 683.0          # archviz.LM_PER_W
    lamp.cycles.is_caustics_light = sun.data.cycles.is_caustics_light
    ob = bpy.data.objects.new("Key_area", lamp)
    sc.collection.objects.link(ob)
    ob.location = target + d * dist
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    ob.visible_camera = False
    bpy.data.objects.remove(sun)
if opts.get("mnee") == "off":  # keep path-traced caustics, drop the MNEE shortcut
    for ob in bpy.data.objects:
        ob.cycles.is_caustics_caster = False
        ob.cycles.is_caustics_receiver = False
    for l in bpy.data.lights:
        l.cycles.is_caustics_light = False
if "adaptive" in opts:
    sc.cycles.adaptive_threshold = float(opts["adaptive"])
if opts.get("denoise") == "off":
    sc.cycles.use_denoising = False
if opts.get("water_test") == "empty_glass":  # glass alone: interface becomes glass->air
    bpy.data.objects["WATER_SURFACE"].hide_render = True
    bpy.data.materials["GLASS_TO_WATER"].node_tree.nodes[0].inputs["IOR"].default_value = 1.52
if opts.get("water_test") == "water_only":  # water column alone: interface becomes water->air
    bpy.data.objects["GLASS_TUMBLER"].hide_render = True
    bpy.data.materials["GLASS_TO_WATER"].node_tree.nodes[0].inputs["IOR"].default_value = 1.333
if "sun_angle" in opts:
    for l in bpy.data.lights:
        if l.type == "SUN":
            l.angle = __import__("math").radians(float(opts["sun_angle"]))
if opts.get("caustics") == "off":
    for ob in bpy.data.objects:
        ob.cycles.is_caustics_caster = False
        ob.cycles.is_caustics_receiver = False
    for l in bpy.data.lights:
        l.cycles.is_caustics_light = False
    sc.cycles.caustics_refractive = sc.cycles.caustics_reflective = False
for key, label in (("wear", "Wear Layered (BRDFLayered)"),):
    if opts.get(key) == "off":
        for m in bpy.data.materials:
            n = m.node_tree and next((n for n in m.node_tree.nodes if n.label == label), None)
            if n:
                n.inputs["Fac"].default_value = 0.0
                for l in list(n.inputs["Fac"].links):
                    m.node_tree.links.remove(l)

if "material_view" in opts:  # assign one material to every concrete mesh (mask comparisons)
    mv = bpy.data.materials[opts["material_view"]]
    for ob in bpy.data.collections[opts.get("coll", "concrete")].all_objects:
        if ob.type == "MESH":
            if ob.data.materials:
                ob.data.materials[0] = mv
            else:
                ob.data.materials.append(mv)
    sc.view_settings.exposure = 0
    sc.view_settings.view_transform = "Standard"
def _zero_gn_input(input_name):
    """Zero a Geometry Nodes modifier input on every object whose group has it (wear.set_input)."""
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wear import set_input
    for ob in bpy.data.objects:
        for md in ob.modifiers:
            if md.type == "NODES" and md.node_group and any(
                    getattr(i, "in_out", "") == "INPUT" and i.name == input_name
                    for i in md.node_group.interface.items_tree):
                set_input(md, input_name, 0.0)


if opts.get("chips") == "off":  # negative control: no chip/dent geometry (and so no chip shading)
    _zero_gn_input("Chip Depth")
if opts.get("breaks") == "off":  # negative control: no torn-skin geometry on the wood top
    _zero_gn_input("Break Depth")
if opts.get("woodwear") == "off":  # negative control: no worn-edge shading on the wood
    for m in bpy.data.materials:
        nt = m.node_tree
        n = nt and next((n for n in nt.nodes if n.label == "worn edges over varnish"), None)
        if n:
            for l in list(n.inputs["Fac"].links):
                nt.links.remove(l)
            n.inputs["Fac"].default_value = 0.0
if opts.get("stain") == "off":  # negative control: no leak stain in the wear mask
    for m in bpy.data.materials:
        nt = m.node_tree
        n = nt and next((n for n in nt.nodes if n.label == "stain (vertical faces)"), None)
        if n:
            for l in list(n.outputs[0].links):
                to = l.to_socket
                nt.links.remove(l)
                to.default_value = 0.0
if opts.get("dirt") == "off":  # negative control: no dirty-edge grime
    for m in bpy.data.materials:
        nt = m.node_tree
        n = nt and next((n for n in nt.nodes if n.label == "edge band"), None)
        if n:
            n.inputs["To Min"].default_value = 0.0

if opts.get("mask_view"):  # diagnostic: show the wear mask (or any labelled node's output) as emission
    for m in bpy.data.materials:
        nt = m.node_tree
        mix = nt and next((n for n in nt.nodes if n.label == "Wear Layered (BRDFLayered)"), None)
        if not mix:
            continue
        src = mix.inputs["Fac"].links[0].from_socket if mix.inputs["Fac"].links else None
        if opts["mask_view"] != "1":
            node = next(n for n in nt.nodes if n.label == opts["mask_view"])
            src = node.outputs[0]
        em = nt.nodes.new("ShaderNodeEmission")
        out_n = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        nt.links.new(src, em.inputs["Color"])
        nt.links.new(em.outputs["Emission"], out_n.inputs["Surface"])
    sc.view_settings.exposure = 0
    sc.view_settings.view_transform = "Standard"

prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.refresh_devices()
print("DEVICE scene=%s backend=%s used=%s" % (sc.cycles.device, prefs.compute_device_type,
      [d.name for d in prefs.devices if d.use]))
sc.render.filepath = out
sc.render.image_settings.file_format = "PNG"
t = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER_TIME %.1f s -> %s" % (time.time() - t, out))
