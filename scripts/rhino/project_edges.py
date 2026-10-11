# Run inside Rhino through Rook rhino_execute:
#     CAM = {"eye": (0, 0, 0.5), "yaw_deg": 0, "f_mm": 24, "sensor_mm": 36,
#            "w_px": 1000, "h_px": 1053, "horizon_px": 624, "out": r"...\_wip\edges.json"}
#     import os; exec(open(os.path.expanduser(r"~\.claude\skills\blender-archviz\scripts\rhino\project_edges.py")).read())
# Projects every brep edge of the open document through a LEVEL pinhole camera with lens shift
# (horizon row given in pixels from the top) and writes [layer, [[x, y] | null, ...]] polylines in
# pixels. Draw them over the reference with scripts/edge_overlay.py. Units: model mm -> m.
# Why: Rook viewport captures ignore the requested size, so an asymmetric-frustum named view
# captures shifted -- this check does not depend on Rhino's viewport at all.
import json
import math
import Rhino
import scriptcontext as sc

c = CAM  # noqa: F821  (set by the caller)
ex, ey, ez = c["eye"]
yaw = math.radians(c.get("yaw_deg", 0.0))           # 0 = looking along +Y
f = c["w_px"] * c["f_mm"] / c["sensor_mm"]
cx, hor = c["w_px"] / 2.0, c["horizon_px"]
lines = []
for o in sc.doc.Objects:
    b = Rhino.DocObjects.ObjRef(o.Id).Brep()
    if b is None:
        continue
    lay = sc.doc.Layers[o.Attributes.LayerIndex].Name
    for e in b.Edges:
        pts = []
        for t in e.DivideByCount(40, True) or []:
            p = e.PointAt(t)
            x, y, z = p.X / 1000.0 - ex, p.Y / 1000.0 - ey, p.Z / 1000.0 - ez
            xr = x * math.cos(yaw) + y * math.sin(yaw)         # camera right
            yr = -x * math.sin(yaw) + y * math.cos(yaw)        # depth
            pts.append(None if yr < 0.2 else (cx + f * xr / yr, hor - f * z / yr))
        lines.append([lay, pts])
with open(c["out"], "w") as f:
    json.dump(lines, f)
print("edges", len(lines))
