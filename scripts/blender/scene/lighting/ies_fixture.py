"""Ies fixture; implementation for interior."""
import math
import os
import bpy
from core.archviz import LM_PER_W
from scene.lighting.light_objects import _light_obj, _warm
from scene.lighting.ies_profile import ies_read


IES_POWER = 177.83 / LM_PER_W


def ies_light(name, path, loc, rot=(0.0, 0.0, 0.0), lumens=None, kelvin=3000, radius=0.02,
              kind="POINT", coll=None):
    """A light with the manufacturer's measured distribution. Unscaled (`lumens=None`) it emits
    exactly the file's candela; `lumens` rescales it to another lumen package or a dimmed level.
    The file is embedded (Internal mode) so the .blend stays self-contained. Aim with `rot`: the
    profile's nadir is the light's -Z, C0 its -Y, a linear fixture's length its -X. `radius` sets the
    shadow/highlight softness of the emitting lens; place `loc` at least radius + 2 mm from any
    surface -- the part of the sphere inside a ceiling or housing is shadowed (0.57x measured)."""
    info = ies_read(path)
    ob, ld = _light_obj(name, kind, loc, rot, coll=coll)
    ld.shadow_soft_size = radius
    if kind == "SPOT":
        ld.spot_size, ld.spot_blend = math.pi, 0.0        # cone off: the profile shapes the beam
    ld.energy = IES_POWER * (lumens / info["lumens"] if lumens else 1.0)
    _warm(ld, kelvin)
    ld.use_nodes = True
    nt = ld.node_tree
    em = next(n for n in nt.nodes if n.type == "EMISSION")
    ies = next((n for n in nt.nodes if n.type == "TEX_IES"), None) or nt.nodes.new("ShaderNodeTexIES")
    txt_name = "IES_" + os.path.basename(path)
    txt = bpy.data.texts.get(txt_name) or bpy.data.texts.new(txt_name)
    with open(path, errors="replace") as f:
        txt.from_string(f.read())
    ies.mode, ies.ies = "INTERNAL", txt
    ies.location = (em.location.x - 250, em.location.y)
    nt.links.new(ies.outputs["Fac"], em.inputs["Strength"])
    ob["ies_file"], ob["ies_lumens"] = os.path.basename(path), round(lumens or info["lumens"], 1)
    return ob
