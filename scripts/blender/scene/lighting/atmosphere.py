"""Volumetric fog / mist (run in Blender). lighting-camera.md > Fog and mist.

    import scene.lighting.atmosphere as atmosphere
    atmosphere.fog_volume(centre=(25, 25), visibility_m=150, clear_boxes=[house_bbox])
    atmosphere.volume_render_settings()

Radiation fog and mist are water droplets of ~5-20 um: Mie scattering, strongly forward-peaked,
no absorption (white). Blender 5.2's Volume Scatter has a native Mie phase function with a droplet
diameter input (Cycles). Density = extinction coefficient from the visibility (Koschmieder):
sigma = 3.912 / V (V = meteorological visibility, contrast threshold 2 %). Fog is thickest low
down and in hollows and thins to clear air at its top; patchy, never a uniform wall (RULES MAT_05).
Indoor air has no fog: clear boxes around buildings (a dark room behind glass filled with fog
is also a noise source).
"""
import bmesh
import bpy

from materials.shared.nodes import G


def sigma_from_visibility(visibility_m):
    """Koschmieder: extinction coefficient (1/m) for a meteorological visibility (m)."""
    return 3.912 / visibility_m


def fog_volume(centre=(0.0, 0.0), visibility_m=150.0, diameter_um=15.0, box=(500.0, 500.0, -25.0, 130.0),
               top=(25.0, 85.0), valley=(0.0, -8.0, 0.5), patch=(0.012, 0.6), clear_boxes=(),
               name="FOG_VOLUME", collection=None):
    """Box of heterogeneous Mie fog: sigma(V) x height fade (full below top[0], clear at top[1]) x valley boost x patch noise; zero in clear_boxes [(xmin,xmax,ymin,ymax,zmax)]."""
    sx, sy, z0, z1 = box
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = (centre[0], centre[1], (z0 + z1) / 2)
    ob.scale = (sx, sy, z1 - z0)
    (collection or bpy.context.scene.collection).objects.link(ob)
    mat = bpy.data.materials.new(name + "_MIE")
    g = G(mat)
    out = g.n("ShaderNodeOutputMaterial", (1500, 0))
    vs = g.n("ShaderNodeVolumeScatter", (1250, 0), phase="MIE")
    vs.inputs["Diameter"].default_value = diameter_um
    vs.inputs["Color"].default_value = (1, 1, 1, 1)
    g.link(vs.outputs[0], out.inputs["Volume"])
    geo = g.n("ShaderNodeNewGeometry", (-900, 0))
    sep = g.n("ShaderNodeSeparateXYZ", (-700, 0)); g.link(geo.outputs["Position"], sep.inputs[0])
    height = g.range(sep.outputs["Z"], top[0], top[1], (-500, 100), 1.0, 0.0, smooth=True, label="fog top")
    hollow = g.range(sep.outputs["Z"], valley[0], valley[1], (-500, -100), 1.0, 1.0 + valley[2], smooth=True, label="hollows")
    nz = g.noise(geo.outputs["Position"], patch[0], (-500, -300), detail=3.0, rough=0.5)
    pt = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", nz, 0.5, (-300, -300)), 2 * patch[1], (-150, -300)), 1.0, (0, -300))
    dens = g.math("MULTIPLY", g.math("MULTIPLY", height, hollow, (-150, 0)), g.math("MAXIMUM", pt, 0.2, (150, -300)), (300, 0))
    dens = g.math("MULTIPLY", dens, sigma_from_visibility(visibility_m), (450, 0))
    y = -600
    for x0, x1, y0, y1, zt in clear_boxes:
        inx = g.math("MULTIPLY", g.math("GREATER_THAN", sep.outputs["X"], x0, (300, y)), g.math("LESS_THAN", sep.outputs["X"], x1, (300, y - 100)), (450, y))
        iny = g.math("MULTIPLY", g.math("GREATER_THAN", sep.outputs["Y"], y0, (300, y - 200)), g.math("LESS_THAN", sep.outputs["Y"], y1, (300, y - 300)), (450, y - 200))
        inside = g.math("MULTIPLY", g.math("MULTIPLY", inx, iny, (600, y - 100)), g.math("LESS_THAN", sep.outputs["Z"], zt, (450, y - 400)), (750, y - 200))
        dens = g.math("MULTIPLY", dens, g.math("SUBTRACT", 1.0, inside, (900, y - 200)), (1050, y))
        y -= 600
    g.link(dens, vs.inputs["Density"])
    ob.data.materials.append(mat)
    return ob


def volume_render_settings(bounces=8, max_bounces=16):
    """Forward-peaked Mie fog needs multiple scattering: volume bounces 8 (default 0 = murky/dark)."""
    c = bpy.context.scene.cycles
    c.volume_bounces = bounces
    c.max_bounces = max(c.max_bounces, max_bounces)
