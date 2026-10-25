"""Weathering lab: whole-wall weathering multiplier in native shader nodes on a flat test wall (metres).

Design a look layer here (renders take seconds), then install the exact node graph in the scene
(references/materials/edge-wear.md > Runoff; references/review/validation.md > Flat-wall lab).
Factors, all multiplicative around 1 (RULES MAT_07):
  1 run-off streaks from the top: two widths, clustered, meandering, own length per streak
  2 dirt band under the top     3 damp base with an uneven edge
  4 large soft patches          5 medium blotches
  6 leaks under horizontal joints: short drips, a pattern per joint
Defaults are a tuned, balanced set; override any of them as key=value.

Usage: blender -b --factory-startup --python weathering_lab.py -- <out_dir> <tag> [key=value ...]
Writes <out_dir>/lab_<tag>.png (8 x 4 m wall, joints drawn for scale, Standard view).
"""
import bpy, sys
from pathlib import Path
argv = sys.argv[sys.argv.index('--') + 1:]; O = Path(argv[0]); TAG = argv[1]
P = dict(board_h=.28, j_amp=.24, j_w=18.0, j_len_min=.10, j_len_span=.55, j_density=.55, j_thr=.46,
         wiggle=.06, cluster_scale=.45, cluster_thr=.28, topband_amp=.156, len_min=1.2, len_span=3.0,
         fade_pow=1.0, streak_amp=.37, streak_w=7.0, streak_len=.45, streak_thr=.44, base_amp=.286,
         base_h=.55, patch_amp=.195, patch_scale=.35, blot_amp=.065, blot_scale=2.5, show_joints=1.0)
for kv in argv[2:]:
    k, v = kv.split('='); P[k] = float(v)
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
W, H = 8.0, 4.0
bpy.ops.mesh.primitive_plane_add(size=1); wall = bpy.context.object
wall.scale = (W, H, 1); wall.rotation_euler = (1.5708, 0, 0); wall.location = (W / 2, 0, H / 2)
m = bpy.data.materials.new('lab'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
for n in list(N): N.remove(n)
out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); L.new(em.outputs[0], out.inputs[0])
geo = N.new('ShaderNodeNewGeometry'); pos = geo.outputs['Position']   # world metres: x along wall, z up
sep = N.new('ShaderNodeSeparateXYZ'); L.new(pos, sep.inputs[0])
def math(op, a, b=0.0, clamp=False):
    n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if hasattr(v, 'node'): L.new(v, n.inputs[i])
        else: n.inputs[i].default_value = v
    return n.outputs[0]
def comb(x, y, z):
    n = N.new('ShaderNodeCombineXYZ')
    for i, v in enumerate((x, y, z)):
        if hasattr(v, 'node'): L.new(v, n.inputs[i])
        else: n.inputs[i].default_value = v
    return n.outputs[0]
def noise(vec, scale, detail=2.0, rough=.5, dim='3D'):
    n = N.new('ShaderNodeTexNoise'); n.noise_dimensions = dim; L.new(vec, n.inputs['Vector'])
    n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough; n.inputs['Distortion'].default_value = 0.0
    return n.outputs['Fac']
def ramp(v, a, b, smooth=True):
    n = N.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP' if smooth else 'LINEAR'
    L.new(v, n.inputs['Value']); n.inputs['From Min'].default_value = a; n.inputs['From Max'].default_value = b
    return n.outputs['Result']
x, z = sep.outputs['X'], sep.outputs['Z']
top = H
# 1. run-off streaks: narrow along x, long along z; start at the top, each streak with its own length.
xw = math('ADD', x, math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, .7), math('MULTIPLY', z, 2.2), 5.0), 1.0, detail=2.0), .5), P['wiggle']))  # meandering edges
fine = ramp(noise(comb(math('MULTIPLY', xw, P['streak_w']), math('MULTIPLY', z, P['streak_len']), 0.0), 1.0, detail=3.0, rough=.55), P['streak_thr'], P['streak_thr'] + .18)
wide = ramp(noise(comb(math('MULTIPLY', xw, P['streak_w'] * .4), math('MULTIPLY', z, P['streak_len'] * .7), 2.0), 1.0, detail=2.0, rough=.5), P['streak_thr'] + .02, P['streak_thr'] + .22)
cluster = ramp(noise(comb(math('MULTIPLY', x, P['cluster_scale']), 0, 4.4), 1.0, detail=1.0), P['cluster_thr'], P['cluster_thr'] + .2)
streak = math('MULTIPLY', math('MAXIMUM', fine, math('MULTIPLY', wide, .75)), cluster)
length = math('ADD', P['len_min'], math('MULTIPLY', ramp(noise(comb(math('MULTIPLY', x, 1.6), 0, 7.3), 1.0, detail=1.0), .3, .7, False), P['len_span']))
depth = math('SUBTRACT', top, z)
fade = math('SUBTRACT', 1.0, math('DIVIDE', depth, length), True)   # 1 at top -> 0 at its length
fade = math('POWER', fade, P['fade_pow'])
S = math('MULTIPLY', streak, fade)
# 2. base zone: dark at the foot, irregular top edge.
edge = math('ADD', P['base_h'], math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, .9), 3.1, 0), 1.0, detail=3.0), .5), .7))
B = ramp(math('SUBTRACT', edge, z), -.15, .25)
# 3. large soft patches (1-3 m), signed.
C = math('SUBTRACT', ramp(noise(comb(x, 0, math('MULTIPLY', z, 1.3)), P['patch_scale'], detail=2.0, rough=.5), .3, .7, False), .5)
# 4. medium blotches, signed.
D = math('SUBTRACT', ramp(noise(comb(x, 11.0, z), P['blot_scale'], detail=4.0, rough=.6), .3, .7, False), .5)
T = ramp(math('SUBTRACT', top, z), .35, 0.0)  # dirt under the coping
M = math('MULTIPLY', math('SUBTRACT', 1.0, math('MULTIPLY', T, P['topband_amp'])), math('SUBTRACT', 1.0, math('MULTIPLY', S, P['streak_amp'])))
M = math('MULTIPLY', M, math('SUBTRACT', 1.0, math('MULTIPLY', B, P['base_amp'])))
M = math('MULTIPLY', M, math('ADD', 1.0, math('MULTIPLY', C, 2 * P['patch_amp'])))
M = math('MULTIPLY', M, math('ADD', 1.0, math('MULTIPLY', D, 2 * P['blot_amp'])))
# 6. small leaks from board joints: water held on each joint ledge drips below it.
dj = math('MODULO', math('SUBTRACT', top, z), P['board_h'])                 # metres below the joint above
row = math('FLOOR', math('DIVIDE', math('SUBTRACT', top, z), P['board_h']))  # joint index -> its own pattern
jx = math('ADD', x, math('MULTIPLY', math('SUBTRACT', noise(comb(math('MULTIPLY', x, 1.5), math('MULTIPLY', z, 4.0), 9.0), 1.0, detail=2.0), .5), .015))
jstreak = ramp(noise(comb(math('MULTIPLY', jx, P['j_w']), math('MULTIPLY', dj, 2.0), math('MULTIPLY', row, 3.7)), 1.0, detail=2.0, rough=.5), P['j_thr'], P['j_thr'] + .16)
jpresent = ramp(noise(comb(math('MULTIPLY', x, 2.2), math('MULTIPLY', row, 5.1), 1.7), 1.0, detail=1.0), 1.0 - P['j_density'], 1.0 - P['j_density'] + .15)
jlen = math('ADD', P['j_len_min'], math('MULTIPLY', ramp(noise(comb(math('MULTIPLY', x, 9.0), math('MULTIPLY', row, 2.3), 4.2), 1.0, detail=1.0), .3, .7, False), P['j_len_span']))
jfade = math('POWER', math('SUBTRACT', 1.0, math('DIVIDE', dj, jlen), True), 1.4)
J = math('MULTIPLY', math('MULTIPLY', jstreak, jpresent), jfade)
M = math('MULTIPLY', M, math('SUBTRACT', 1.0, math('MULTIPLY', J, P['j_amp'])))
# board joints for scale only: dark line every 0.28 m.
j = math('MULTIPLY', math('LESS_THAN', math('PINGPONG', math('SUBTRACT', top, z), P['board_h'] / 2), .006), P['show_joints'])
col = math('MULTIPLY', math('MULTIPLY', M, .62), math('SUBTRACT', 1.0, math('MULTIPLY', j, .35)))
L.new(col, em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
wall.data.materials.append(m)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = W; cam.location = (W / 2, -10, H / 2); cam.rotation_euler = (1.5708, 0, 0)
sc.render.resolution_x, sc.render.resolution_y = 1200, 600
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'
sc.view_settings.view_transform = 'Standard'; sc.world = None
sc.render.filepath = str(O / f'lab_{TAG}.png'); bpy.ops.render.render(write_still=True)
print('LAB_DONE', TAG, P)
