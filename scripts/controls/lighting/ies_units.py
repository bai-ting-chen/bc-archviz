
import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
# Rerun after a Blender upgrade: blender -b --factory-startup --python scripts/controls/lighting/ies_units.py
# Control: how Cycles 5.2 scales an IES Texture on a light, and which way the profile points.
# Synthetic LM-63 files with a known candela value; illuminance on a white Lambert plane read
# from the linear render (pixel = albedo * E / pi), as in light_units.py.
# Prediction from intern/cycles/util/ies.cpp: candela * 4*pi/177.83 (D65 efficacy), times the
# light's power/(4*pi) for a point light -> E = P * S * I / (177.83 d^2) Blender W/m2.
# The skill's convention is 683 lm/W, i.e. E = I / (683 d^2): needs P*S = 177.83/683 = 0.2604.
import math
import os
import shutil
import sys
import tempfile

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _scene import black_scene, ortho_camera, render_linear, white_lambert  # noqa: E402

D = 2.0          # light height above the plane, m
I0 = 1000.0      # candela in the test files
TMP = tempfile.mkdtemp(prefix="ies_units_")


def ies_file(name, v_angles, h_angles, cd):
    """cd[h][v] in candela, LM-63-2002, photometric type C."""
    lines = ["IESNA:LM-63-2002", "[TEST] control", "TILT=NONE",
             f"1 -1 1 {len(v_angles)} {len(h_angles)} 1 2 0 0 0", "1 1 0",
             " ".join(f"{a:g}" for a in v_angles), " ".join(f"{a:g}" for a in h_angles)]
    lines += [" ".join(f"{c:g}" for c in row) for row in cd]
    p = os.path.join(TMP, name)
    with open(p, "w") as f:
        f.write("\n".join(lines) + "\n")
    return p


V = [0, 30, 60, 90, 120, 150, 180]
ISO = ies_file("iso.ies", V, [0], [[I0] * len(V)])                               # uniform sphere
DOWN = ies_file("down.ies", V, [0], [[I0, I0, I0, I0, 0, 0, 0]])                   # lower hemisphere
# C0 half only (h 0..90 lit, 90..360 dark): shows where the C0 plane points in light space
H = [0, 45, 90, 135, 180, 225, 270, 315, 360]
C0 = ies_file("c0.ies", V, H, [[I0 if h in (0, 45, 315, 360) else 0.0] * len(V) for h in H])
C90 = ies_file("c90.ies", V, H, [[I0 if h in (45, 90, 135) else 0.0] * len(V) for h in H])


def base(cam_z=0.5, ortho=0.1, plane=0.2):
    sc = black_scene(256, 64)
    bpy.ops.mesh.primitive_plane_add(size=plane)
    bpy.context.object.data.materials.append(white_lambert())
    ortho_camera(cam_z, ortho)
    return sc


def ies_light(sc, kind, path, power=1.0, strength=1.0, rot=(0, 0, 0), **kw):
    ld = bpy.data.lights.new("L", kind); ld.energy = power
    for k, v in kw.items():
        setattr(ld, k, v)
    ld.use_nodes = True
    nt = ld.node_tree
    ies = nt.nodes.new("ShaderNodeTexIES"); ies.mode = "EXTERNAL"; ies.filepath = path
    ies.inputs["Strength"].default_value = strength
    nt.links.new(ies.outputs["Fac"], nt.nodes["Emission"].inputs["Strength"])
    lo = bpy.data.objects.new("L", ld); sc.collection.objects.link(lo)
    lo.location = (0, 0, D); lo.rotation_euler = rot
    return lo


def render(sc):
    return render_linear()[:, :, 0] * math.pi        # E in Blender W/m2 (albedo 1)


try:
    E683 = I0 / (683 * D * D)
    E178 = I0 / (177.83 * D * D)
    print(f"\nE if 683 lm/W   I/(683 d2)    = {E683:.5f}")
    print(f"E if 177.83 lm/W I/(177.83 d2) = {E178:.5f}   (P=1 W, Strength=1)")
    rows = []
    for name, kind, path, kw in [("POINT iso P=1", "POINT", ISO, {"shadow_soft_size": 0.0}),
                                 ("POINT down P=1", "POINT", DOWN, {"shadow_soft_size": 0.0}),
                                 ("POINT iso P=0.2604", "POINT", ISO, {"shadow_soft_size": 0.0, "power": 177.83 / 683}),
                                 ("POINT iso P=1 S=0.2604", "POINT", ISO, {"shadow_soft_size": 0.0, "strength": 177.83 / 683}),
                                 ("POINT iso r=0.05", "POINT", ISO, {"shadow_soft_size": 0.05}),
                                 ("SPOT 180 iso P=1", "SPOT", ISO, {"shadow_soft_size": 0.0, "spot_size": math.pi, "spot_blend": 0.0}),
                                 ("AREA 0.05 disk iso P=1", "AREA", ISO, {"shape": "DISK", "size": 0.05})]:
        sc = base()
        p = kw.pop("power", 1.0); s = kw.pop("strength", 1.0)
        ies_light(sc, kind, path, power=p, strength=s, **kw)
        e = render(sc).mean()
        rows.append((name, e))
        print(f"{name:26s} E = {e:.5f}  x683-pred = {e / E683:.3f}")

    # Orientation: top-down view of a 6 m floor, light pointing down (no rotation).
    for nm, path in (("C0", C0), ("C90", C90)):
        sc = base(cam_z=1.0, ortho=6.0, plane=6.0)
        ies_light(sc, "POINT", path, shadow_soft_size=0.0)
        e = render(sc)                                   # rows run -Y -> +Y (image origin bottom-left)
        h, w = e.shape
        q = {"+X": e[:, w // 2 + 4:].mean(), "-X": e[:, :w // 2 - 4].mean(),
             "+Y": e[h // 2 + 4:, :].mean(), "-Y": e[:h // 2 - 4, :].mean()}
        print(f"{nm}-lit profile, light unrotated, floor mean by side:", {k: round(float(v), 5) for k, v in q.items()})
    sc = base(cam_z=1.0, ortho=6.0, plane=6.0)
    ies_light(sc, "POINT", DOWN, shadow_soft_size=0.0, rot=(math.pi, 0, 0))
    print("down profile, light flipped 180 about X: floor mean =", round(render(sc).mean(), 6))
finally:
    shutil.rmtree(TMP, ignore_errors=True)
