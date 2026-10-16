"""Control: TileLayout node group = numpy reference (stack, running, rotated), ids distinct per
tile, no aliasing banding on a far plane. Run: blender -b --factory-startup --python <this>"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blender"))
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
import _scene, tile_layout

RES, SIZE = 400, 1.0                       # 400 px over 1 m: 2.5 mm per px
CASES = {
    "jitter": dict(tile_w=0.0375, tile_h=0.25, joint=0.004,
                   jitter_offset=0.0004, jitter_rotation=0.0044),
    "stack":   dict(tile_w=0.10, tile_h=0.05, joint=0.01),
    "rounded": dict(tile_w=0.10, tile_h=0.05, joint=0.01, corner_radius=0.012),
    "running": dict(tile_w=0.10, tile_h=0.05, joint=0.01, row_offset=0.5),
    "rotated": dict(tile_w=0.145, tile_h=0.045, joint=0.008, rotation=0.5236, origin=(0.013, -0.02)),
}
OUTS = ("Edge", "Joint", "Tile UV", "Tile ID")

def plane_with(output, params):
    sc = _scene.black_scene(samples=1, res=RES)
    sc.cycles.filter_width = 0.01
    bpy.ops.mesh.primitive_plane_add(size=SIZE)
    ob = bpy.context.object
    m = bpy.data.materials.new("probe"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grp = tile_layout.add_layout(nt, tc.outputs["Object"], **params)
    em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    src = grp.outputs[output]
    if output == "Edge":                      # map metres to a visible, positive range
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"
        mul.inputs[1].default_value, mul.inputs[2].default_value = 10.0, 0.5
        nt.links.new(src, mul.inputs[0]); src = mul.outputs[0]
    nt.links.new(src, em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
    ob.data.materials.append(m)
    _scene.ortho_camera(1.0, SIZE)
    return _scene.render_linear()

def pixel_coords():
    c = (np.arange(RES) + 0.5) / RES * SIZE - SIZE / 2
    return np.meshgrid(c, c)                  # row 0 = bottom, matches render_linear

def stable(mask):                             # pixels whose 3x3 neighbourhood shares the value
    m = mask.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            m &= np.roll(np.roll(mask, dy, 0), dx, 1)
    return m

fails = []
for name, p in CASES.items():
    u, v = pixel_coords()
    ref = tile_layout.reference(u, v, **p)
    cell = ref["col"] * 100003 + ref["row"]
    same = np.ones_like(cell, bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            same &= np.roll(np.roll(cell, dy, 0), dx, 1) == cell
    ok = same & stable(ref["joint"] == 0) | (same & stable(ref["joint"] == 1))
    img = plane_with("Edge", p)[..., 0]
    err = np.abs(img - (ref["edge"] * 10 + 0.5))[ok]
    if np.median(err) > 2e-3: fails.append(f"{name}: Edge median err {np.median(err):.4f}")
    img = plane_with("Joint", p)[..., 0]
    if np.mean(np.abs(img - ref["joint"])[ok]) > 0.01: fails.append(f"{name}: Joint mismatch")
    img = plane_with("Tile UV", p)
    face = ok & (ref["joint"] == 0)
    if np.median(np.abs(img[..., 0] - ref["tile_uv_x"])[face]) > 0.01: fails.append(f"{name}: UV x")
    if np.median(np.abs(img[..., 1] - ref["tile_uv_y"])[face]) > 0.01: fails.append(f"{name}: UV y")
    ids = plane_with("Tile ID", p)[..., 0]
    per = {}
    for c, val in zip(cell[face].ravel(), ids[face].ravel()):
        per.setdefault(c, []).append(val)
    spread = max(np.ptp(vs) for vs in per.values())
    uniq = len({round(float(np.median(vs)), 4) for vs in per.values()}) / len(per)
    if spread > 1e-4: fails.append(f"{name}: Tile ID not constant within a tile ({spread:.5f})")
    if uniq < 0.97: fails.append(f"{name}: Tile IDs not distinct ({uniq:.3f})")

def check_jitter_gaps():
    """Measure face crossings for 200 tiles on each axis and reject overlap."""
    params = CASES["jitter"]
    w, h, joint = params["tile_w"], params["tile_h"], params["joint"]
    cells = np.arange(-100, 100)
    ox, oy, angle = tile_layout._jitter_transform(
        cells, cells[::-1], w, h, joint,
        params["jitter_offset"], params["jitter_rotation"])
    # Bound every corner, not only centreline gaps: containment rules out overlap
    # at the ends of a rotated tile as well as across staggered rows.
    for x in (-w / 2, w / 2):
        for y in (-h / 2, h / 2):
            xx = np.cos(angle) * x - np.sin(angle) * y + ox
            yy = np.sin(angle) * x + np.cos(angle) * y + oy
            assert np.all(np.abs(xx) <= (w + joint) / 2), "jitter: X corner outside cell"
            assert np.all(np.abs(yy) <= (h + joint) / 2), "jitter: Y corner outside cell"
    for vertical in (False, True):
        pitch = (h if vertical else w) + joint
        cells = np.arange(-100, 100)
        base = cells * pitch
        centre = base + pitch / 2

        def edge(coordinate):
            x, y = (w / 2 + joint / 2, coordinate) if vertical else (coordinate, h / 2 + joint / 2)
            return tile_layout.reference(x, y, **params)["edge"]

        # Bisect entry/exit crossings of the real, rotated tile at its cell centreline.
        bounds = []
        for entering in (True, False):
            lo = base.copy() if entering else centre.copy()
            hi = centre.copy() if entering else base + pitch - 1e-10
            assert np.all(edge(centre) > 0), "jitter: missing centre face"
            assert np.all(edge(lo if entering else hi) < 0), "jitter: face crosses cell boundary"
            for _ in range(45):
                mid = (lo + hi) / 2
                inside = edge(mid) >= 0
                move_low = ~inside if entering else inside
                lo = np.where(move_low, mid, lo)
                hi = np.where(move_low, hi, mid)
            bounds.append((lo + hi) / 2)
        gaps = bounds[0][1:] - bounds[1][:-1]
        assert np.std(gaps) > 0, "jitter: joint widths do not vary"
        assert np.all(gaps >= 0), "jitter: negative joint width (overlap)"
        print(f"JITTER_GAPS {'Y' if vertical else 'X'}: 200 tiles, "
              f"min={gaps.min():.9f} m, std={gaps.std():.9f} m")


try:
    check_jitter_gaps()
except AssertionError as exc:
    fails.append(str(exc))

# Emission probe proves the new output forwards width/height in metres (Z = 0).
size_probe = plane_with("Tile Size", dict(tile_w=0.123, tile_h=0.067, joint=0.004))
assert np.allclose(size_probe[..., :3], (0.123, 0.067, 0), atol=1e-6), "Tile Size pass-through mismatch"

# Zero-width joints must not produce rounding speckles.
zero = plane_with("Joint", dict(tile_w=0.10, tile_h=0.05, joint=0))[..., 0]
if np.mean(zero == 0) <= 0.999:
    fails.append("zero joint: nonzero mask on >= 0.1% of pixels")


def check_rebuild(change_interface=False):
    """Check values and both link directions through an old-version group rebuild."""
    material = bpy.data.materials.new("rebuild_probe")
    material.use_nodes = True
    nt = material.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    group = tile_layout.add_layout(nt, tc.outputs["Object"], joint=0.004)
    sink = nt.nodes.new("ShaderNodeMath")
    nt.links.new(group.outputs["Edge"], sink.inputs[0])
    old = group.node_tree
    # Removing the newly added socket simulates the previous interface version.
    if change_interface:
        item = next(item for item in old.interface.items_tree
                    if item.item_type == "SOCKET" and item.in_out == "INPUT"
                    and item.name == "Corner Radius")
        old.interface.remove(item)
    old["tile_layout_version"] = 0
    rebuilt = tile_layout.layout_group()
    assert group.node_tree == rebuilt, "instance not retargeted"
    assert abs(group.inputs["Joint"].default_value - 0.004) < 1e-8, "Joint value lost"
    assert any(link.from_node == tc and link.from_socket.name == "Object"
               and link.to_node == group and link.to_socket.name == "Vector"
               for link in nt.links), "Vector link lost"
    assert any(link.from_node == group and link.from_socket.name == "Edge"
               and link.to_node == sink and link.to_socket == sink.inputs[0]
               for link in nt.links), "Edge link lost"
    if not change_interface:
        assert rebuilt == old, "matching interface was replaced"


for changed in (False, True):
    try:
        check_rebuild(changed)
    except AssertionError as exc:
        fails.append(f"rebuild (interface changed={changed}): {exc}")

# far plane: 8 m over 200 px = 40 mm/px, so 3 mm joints are sub-pixel; with pixel filtering
# the column means must be smooth (< 3 % spread), not banded by aliasing
SIZE, RES = 8.0, 200
far = plane_with("Joint", dict(tile_w=0.045, tile_h=0.145, joint=0.003))[..., 0]
cols = far.mean(axis=0)
if np.std(cols) / max(np.mean(cols), 1e-6) > 0.03: fails.append("far plane: joint banding (aliasing)")

print("TILE_LAYOUT_CHECK", "FAIL" if fails else "PASS", *fails, sep="\n  ")
sys.exit(1 if fails else 0)
