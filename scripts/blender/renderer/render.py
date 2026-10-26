"""Render engine, quality settings and output: the Cycles set-up every render starts from.

Look-up of the GPU device, the Cycles quality block (render-settings.md), the fast colour pass used
while solving a camera, and the single-frame render to a PNG.
"""
import bpy


def use_gpu(force=False):
    """Cycles on the GPU. --factory-startup leaves no compute device, so scene "GPU" would
    silently render on the CPU: pick OptiX then (always, with force=True)."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    if force or prefs.compute_device_type == "NONE":
        prefs.compute_device_type = "OPTIX"
        prefs.refresh_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
    bpy.context.scene.cycles.device = "GPU"


def framing_render(root, path):
    """Fast Workbench render, one colour per layer collection -- compare with the reference
    (`scripts/research/refmatch.py pair --overlay`) while solving the camera. Restores the engine after."""
    import random
    sc = bpy.context.scene
    engine = sc.render.engine
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light, sc.display.shading.color_type = "STUDIO", "OBJECT"
    for o in root.all_objects:
        random.seed(sum(map(ord, o.users_collection[0].name)))
        o.color = (random.random(), random.random(), random.random(), 1)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.render.engine = engine
    return path


def render_setup(width=1920, height=1080, samples=256, look="AgX - Medium High Contrast", exposure=0.0):
    """Cycles on the GPU, adaptive sampling, OptiX denoise, AgX look, 12 bounces (render-settings.md)."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    use_gpu()
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    sc.cycles.max_bounces = 12
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = look
    except TypeError:
        pass
    sc.view_settings.exposure = exposure
    sc.unit_settings.system = "METRIC"


def render_to(path):
    """Render the active camera and write a PNG to `path`."""
    sc = bpy.context.scene
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return path
