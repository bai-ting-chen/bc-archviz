# Run inside Rhino through Rook rhino_execute:
#     CAM = {"eye": (0, 0, 0.5), "yaw_deg": 0, "f_mm": 24, "sensor_mm": 36,
#            "w_px": 1000, "h_px": 1053, "horizon_px": 624, "out": r"...\_wip\edges.json"}
#     import os; exec(open(os.path.expanduser(r"~\.claude\skills\bc-archviz\scripts\rhino\project_edges.py")).read())
# Projects the edges of every visible object of the open document through a LEVEL pinhole camera
# with lens shift (horizon row given in pixels from the top) and writes [layer, [[x, y] | null, ...]]
# polylines in pixels. Draw them over the reference with scripts/research/edge_overlay.py. Eye in metres;
# model units are read from the document. Breps, extrusions, surfaces and SubDs give their edges,
# meshes their naked and creased (> 30 deg) edges; block instances are walked with their transforms
# (import_rhino brings blocks in as instances, so they must be in the check too).
# Why: Rook viewport captures ignore the requested size, so an asymmetric-frustum named view
# captures shifted -- this check does not depend on Rhino's viewport at all.
import json
import math

import Rhino
import scriptcontext as sc

c = CAM  # noqa: F821  (set by the caller)
ex, ey, ez = c["eye"]
yaw = math.radians(c.get("yaw_deg", 0.0))           # 0 = looking along +Y
foc = c["w_px"] * c["f_mm"] / c["sensor_mm"]
cx, hor = c["w_px"] / 2.0, c["horizon_px"]
k = Rhino.RhinoMath.UnitScale(sc.doc.ModelUnitSystem, Rhino.UnitSystem.Meters)
CREASE = math.radians(30.0)


def project(p):
    x, y, z = p.X * k - ex, p.Y * k - ey, p.Z * k - ez
    xr = x * math.cos(yaw) + y * math.sin(yaw)          # camera right
    yr = -x * math.sin(yaw) + y * math.cos(yaw)         # depth
    return None if yr < 0.2 else (cx + foc * xr / yr, hor - foc * z / yr)


def curves_of(geom):
    """Edge curves of one piece of geometry, already in world space."""
    if isinstance(geom, Rhino.Geometry.Mesh):
        m = geom.DuplicateMesh()
        m.Normals.ComputeNormals(); m.FaceNormals.ComputeFaceNormals()
        te = m.TopologyEdges
        out = []
        for i in range(te.Count):
            faces = te.GetConnectedFaces(i)
            if len(faces) == 1 or (len(faces) == 2 and Rhino.Geometry.Vector3d.VectorAngle(
                    Rhino.Geometry.Vector3d(m.FaceNormals[faces[0]]),
                    Rhino.Geometry.Vector3d(m.FaceNormals[faces[1]])) > CREASE):
                out.append(te.EdgeLine(i).ToNurbsCurve())
        return out
    if isinstance(geom, Rhino.Geometry.SubD):
        geom = geom.ToBrep(Rhino.Geometry.SubDToBrepOptions.Default)
    b = Rhino.Geometry.Brep.TryConvertBrep(geom) if not isinstance(geom, Rhino.Geometry.Brep) else geom
    return [e.DuplicateCurve() for e in b.Edges] if b is not None else []


def walk(obj, xform, layer, lines, skipped):
    if isinstance(obj, Rhino.DocObjects.InstanceObject):
        idef = obj.InstanceDefinition
        x = xform * obj.InstanceXform
        for sub in idef.GetObjects():
            walk(sub, x, layer, lines, skipped)
        return
    g = obj.Geometry.Duplicate()
    if not xform.IsIdentity:
        g.Transform(xform)
    crvs = curves_of(g)
    if not crvs and not isinstance(g, (Rhino.Geometry.Curve, Rhino.Geometry.Point, Rhino.Geometry.TextEntity)):
        skipped.append(str(g.ObjectType))
    for crv in crvs:
        pts = [project(crv.PointAt(t)) for t in (crv.DivideByCount(40, True) or [])]
        lines.append([layer, pts])


lines, skipped = [], []
settings = Rhino.DocObjects.ObjectEnumeratorSettings()
settings.HiddenObjects, settings.LockedObjects = False, True
for o in sc.doc.Objects.GetObjectList(settings):
    if not sc.doc.Layers[o.Attributes.LayerIndex].IsVisible:
        continue
    walk(o, Rhino.Geometry.Transform.Identity, sc.doc.Layers[o.Attributes.LayerIndex].Name, lines, skipped)
with open(c["out"], "w") as fh:
    json.dump(lines, fh)
print("edges", len(lines), "units->m", k, "skipped", skipped)
