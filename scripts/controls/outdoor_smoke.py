# Smoke test of the outdoor helpers on a scene they were not written for:
#   ARCHVIZ_PROJECT=<folder with library/polyhaven: concrete_wall_006, grass_ground, forest_ground_05,
#   hdris/kloofendal_misty_morning> blender -b --factory-startup --python scripts/controls/outdoor_smoke.py -- <out.png>
# A box hut with one opening on a landform hill, a meadow of procedural blades (no vendor assets),
# wet grass + near dew, weathered concrete with chips, runoff leaks and cracks, distorted glass,
# Mie fog. Asserts the GN fields and instances exist; renders a small frame to look at.
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender"))
import archviz  # noqa: E402
import atmosphere  # noqa: E402
import lookdev  # noqa: E402
import scatter  # noqa: E402
import study_materials  # noqa: E402
import terrain  # noqa: E402
import vegetation  # noqa: E402
import wear  # noqa: E402

out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_homefile(use_empty=True)
archviz.set_project(os.environ["ARCHVIZ_PROJECT"])
sc = bpy.context.scene
archviz.render_setup(400, 500, 64, look="AgX - Base Contrast")
C, HALF = (0.0, 0.0), (2.5, 2.0)

# hut: a closed box with a recessed opening (window) in the -Y face
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, vec=(4.0, 3.2, 2.8), verts=bm.verts)
bmesh.ops.translate(bm, vec=(0, 0, 1.4), verts=bm.verts)
front = next(f for f in bm.faces if f.normal.y < -0.9)
r = bmesh.ops.inset_individual(bm, faces=[front], thickness=0.9, depth=0.0)
bmesh.ops.translate(bm, vec=(0, 0.15, 0), verts=list(front.verts))      # recess 15 cm
hut = bpy.data.objects.new("HUT", bpy.data.meshes.new("HUT")); bm.to_mesh(hut.data); bm.free()
sc.collection.objects.link(hut)
wear.dice(hut, 0.2)
archviz.box_uv(hut, 2.0)
wear.add_leak_field(hut)                                   # first, on the clean shell
wear.add_edge_wear(hut, wear.edge_wear_group("SMOKE WEAR", band=0.08, level=3), Seed=(1.0, 2.0, 3.0))
assert hut.modifiers[0].name == "LEAK FIELD", [m.name for m in hut.modifiers]
conc = wear.weathered_concrete("SMOKE_CONCRETE", stain=False, tex_id="concrete_wall_006")
study_materials.retone(conc, (0.28, 0.28, 0.28), 0.25, tex_id="concrete_wall_006")
wear.add_runoff(conc)
wv = [v.co for v in hut.data.vertices if abs(v.co.y + 1.45) < 0.01]    # recessed window face
xs, zs = [v.x for v in wv], [v.z for v in wv]
wear.add_cracks(conc, [("y", -1.6, min(xs), max(xs), min(zs), max(zs), False, (45, 225))])
hut.data.materials.append(conc)
pane = bpy.data.objects.new("PANE", bpy.data.meshes.new("PANE"))
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, vec=(max(xs) - min(xs), 0.02, max(zs) - min(zs)), verts=bm.verts)
bmesh.ops.translate(bm, vec=(0, -1.48, (min(zs) + max(zs)) / 2), verts=bm.verts)
bm.to_mesh(pane.data); bm.free(); sc.collection.objects.link(pane)
pane.data.materials.append(lookdev.glass_distortion(archviz.dielectric("SMOKE_GLASS"), pane))

# hill + ground
topo = terrain.landform_group("SMOKE_LAND", centre=C, pad_half=HALF, size=120, verts=241, fall=4, run=25)
ground = terrain.ground_material("grass_ground", "forest_ground_05", "SMOKE_GROUND", wet_gamma=1.4)
ter = terrain.add_terrain(topo, ground)

# camera down the slope
cam = bpy.data.objects.new("CAM", bpy.data.cameras.new("CAM")); sc.collection.objects.link(cam)
a = math.radians(-120); x, y = 16 * math.cos(a), 16 * math.sin(a)
cam.location = (x, y, terrain.height(x, y, C, HALF, fall=4, run=25) + 1.5)
cam.rotation_euler = (Vector((0, 0, 1.6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
archviz.physical_camera(cam, 100, 8.0, 8.0 ** 2 / 2 ** 11.0, 40.0, focus_distance=16)
archviz.straighten_verticals(cam)

# meadow of procedural blades: wet + dew
blades = bpy.data.collections.new("SMOKE_BLADES"); sc.collection.children.link(blades)
mat = vegetation.blade_material("SMOKE_BLADE", colour=(0.10, 0.16, 0.04), wet=vegetation.WET, dew=vegetation.DEW_GRASS)
for i in range(4):
    bm = bmesh.new()
    for k in range(9):
        ang = k / 9 * 6.283 + i
        lean = 0.02 + 0.01 * ((k * 7 + i) % 3)
        v0 = bm.verts.new((0.0, 0.0, 0.0)); v1 = bm.verts.new((0.004, 0.0, 0.0))
        v2 = bm.verts.new((lean * math.cos(ang), lean * math.sin(ang), 0.10 + 0.02 * i))
        bm.faces.new((v0, v1, v2))
    o = bpy.data.objects.new("BLADE_%d" % i, bpy.data.meshes.new("BLADE_%d" % i)); bm.to_mesh(o.data); bm.free()
    o.data.materials.append(mat); blades.objects.link(o)
bpy.context.view_layer.layer_collection.children[blades.name].exclude = True
grp = scatter.meadow_layer_group(scatter.load_scatter_on_surface(), "SMOKE_MEADOW")
tx, ty = scatter.frustum_tangents(cam, (400, 500))
scatter.meadow_layer("SMOKE_GRASS", grp, ter, blades, cam, Density=400.0, Tan_X=tx, Tan_Y=ty, Max_Distance=40.0)

# fog + sky
atmosphere.fog_volume(centre=C, visibility_m=150, box=(200, 200, -20, 80), top=(20, 60),
                      clear_boxes=[(-2.0, 2.0, -1.6, 1.6, 2.8)])
atmosphere.volume_render_settings()
archviz.world_hdri_lux("kloofendal_misty_morning", 12000)

dg = bpy.context.evaluated_depsgraph_get()
e = hut.evaluated_get(dg).data
n_inst = sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.name == "SMOKE_GRASS")
checks = {"leak_d": "leak_d" in e.attributes, "chip": "chip" in e.attributes, "pad_d": "pad_d" in ter.evaluated_get(dg).data.attributes,
          "grass_instances_viewport": n_inst}
print("SMOKE CHECKS", checks)
assert all(checks.values()), checks
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("SMOKE DONE", out)
