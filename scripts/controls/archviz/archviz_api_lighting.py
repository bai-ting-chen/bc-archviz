"""Archviz lighting API checks."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import math
import os
import bpy
import bmesh
from mathutils import Vector
import core.archviz as archviz
from archviz_api_rig import HDRI, rounded, cube, uv_table

def check_ev():
    """EV100 of two camera triples and the lumens-per-watt constant."""
    return {"ev_sunny16": rounded(archviz.ev100(100, 16, 1 / 100)),
            "ev_iso800": rounded(archviz.ev100(800, 2.8, 1 / 60)),
            "lm_per_w": rounded(archviz.LM_PER_W)}

def check_hdri_analyse():
    """Lux at strength 1 and the sun direction of one HDRI, rotated."""
    return rounded(archviz.hdri_analyse(HDRI, rotation_deg=37.5))

def world_summary(world):
    """Mapping rotation, background strength and the env image name of the HDRI world."""
    nt = world.node_tree
    mapping = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeMapping")
    bg = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBackground")
    env = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexEnvironment")
    return {"rot_z": rounded(mapping.inputs["Rotation"].default_value[2]),
            "strength": rounded(bg.inputs["Strength"].default_value),
            "image": env.image.name if env.image else None,
            "links": len(nt.links), "nodes": sorted(n.bl_idname for n in nt.nodes),
            "camera_visible": world.cycles_visibility.camera}

def check_world():
    """HDRI world scaled to a target lux, with its node summary."""
    info = archviz.world_hdri_lux(HDRI, 9000.0, rotation_deg=37.5, visible=False)
    world = bpy.context.scene.world
    return {"info": rounded(info), "world": world_summary(world)}

def check_world_plain():
    """HDRI world at a given strength and rotation, with its node summary."""
    world = archviz.world_hdri(HDRI, strength=2.5, rotation_deg=-20.0)
    return world_summary(world)

def check_sun():
    """Sun lamp energy, angle and rotation from a direction."""
    ob = archviz.sun_from_direction([0.3, -0.4, 0.86], 25000.0, angle_deg=0.53)
    return {"energy": rounded(ob.data.energy), "angle": rounded(ob.data.angle),
            "rot": rounded(tuple(ob.rotation_euler))}
