"""Archviz helpers that run inside Blender (via the Blender MCP or the Python console).

Rhino supplies geometry only. Everything visual -- materials, lighting, cameras, render
settings -- is built here, from the local Poly Haven library.

    import os, sys; sys.path.insert(0, os.path.expanduser(r"~\\.claude\\skills\\bc-archviz\\scripts\\blender"))
    import core.archviz as archviz

This module is the one import point: each job lives in its own module, re-exported here so
callers keep working (RULES GOV_04, one module per job):
    assets       project folder, library(), read_meta / write_meta
    photometry   LM_PER_W, ev100
    render       use_gpu, render_setup, render_to, framing_render
    lighting     world_hdri, world_hdri_lux, hdri_analyse, sun_from_direction
    camera       use_camera, physical_camera, straighten_verticals
    uv           directional_uv, box_uv, height_span_uv
    rhino_import import_rhino
    material_map apply_material_map
"""
from core.assets import library, project_root, read_meta, set_project, write_meta  # noqa: F401
from scene.lighting.camera import physical_camera, straighten_verticals, use_camera  # noqa: F401
from scene.lighting.lighting import hdri_analyse, sun_from_direction, world_hdri, world_hdri_lux  # noqa: F401
from core.material_map import apply_material_map  # noqa: F401
from scene.lighting.photometry import LM_PER_W, ev100  # noqa: F401
from renderer.render import framing_render, render_setup, render_to, use_gpu  # noqa: F401
from scene.io.rhino_import import import_rhino  # noqa: F401
from core.uv import box_uv, directional_uv, height_span_uv  # noqa: F401
