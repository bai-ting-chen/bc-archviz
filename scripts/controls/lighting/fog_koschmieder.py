
import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
# Rerun after a Blender upgrade: blender -b --factory-startup --python scripts/controls/lighting/fog_koschmieder.py
# Control: the fog density from atmosphere.fog_volume is an extinction coefficient in 1/m
# (Koschmieder sigma = 3.912 / V). A small emitter seen through d metres of uniform fog in a black
# world: with the volume switched to pure absorption the transmitted fraction must be exp(-sigma d).
# With the real Mie scatter the centre pixel reads higher (forward-scattered glow around the
# source) - reported, not asserted.
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "blender"))
from _scene import black_scene, render_linear  # noqa: E402

import scene.lighting.atmosphere as atmosphere  # noqa: E402

V, D = 150.0, 30.0          # visibility m, distance camera -> emitter m


def scene(fog, absorb=False):
    sc = black_scene(256, 64)
    sc.cycles.volume_bounces = 8
    em = bpy.data.materials.new("em"); em.use_nodes = True
    nt = em.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Strength"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, D, 0), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(em)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    cam.data.lens = 2000; cam.location = (0, 0, 0); cam.rotation_euler = (math.radians(90), 0, 0)
    sc.camera = cam
    if fog:
        ob = atmosphere.fog_volume(centre=(0, D / 2), visibility_m=V, box=(20.0, D - 1.0, -10.0, 10.0),
                                   top=(1e3, 2e3), valley=(0.0, -1.0, 0.0), patch=(0.01, 0.0))
        ob.location.y = (D - 1.0) / 2 + 0.25            # box from y 0.25 to D - 0.75
        if absorb:
            nt = ob.data.materials[0].node_tree
            vs = next(n for n in nt.nodes if n.type == "SCATTER_VOLUME" or n.bl_idname == "ShaderNodeVolumeScatter")
            ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
            ab.inputs["Color"].default_value = (0, 0, 0, 1)
            nt.links.new(vs.inputs["Density"].links[0].from_socket, ab.inputs["Density"])
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            nt.links.new(ab.outputs[0], out.inputs["Volume"])
    img = render_linear()
    h, w = img.shape[:2]
    return float(img[h // 2 - 4:h // 2 + 4, w // 2 - 4:w // 2 + 4, 1].mean())


clear = scene(False)
absorb = scene(True, absorb=True)
mie = scene(True)
path = D - 1.0                                  # metres of fog along the ray
expect = math.exp(-atmosphere.sigma_from_visibility(V) * path)
print("FOG CONTROL  sigma %.4f /m  path %.1f m  expected T %.4f" % (atmosphere.sigma_from_visibility(V), path, expect))
print("FOG CONTROL  absorption-only T %.4f (ratio to expected %.3f)" % (absorb / clear, absorb / clear / expect))
print("FOG CONTROL  Mie scatter centre %.4f (forward glow adds to the direct beam)" % (mie / clear))
