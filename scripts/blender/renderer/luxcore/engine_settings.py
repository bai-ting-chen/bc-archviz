"""LuxCore engine settings: PATH + light tracing, GPU camera paths with CPU light paths (luxcore.md).

The settings every LuxCore render starts from, applied in code so none is forgotten. Defaults
BlendLuxCore gets wrong for this pipeline:
- halt-by-samples is on (32 samples): a time budget alone would stop at "100 %" within seconds;
- light tracing is off: no caustic;
- clamping is off: caustic-bounce fireflies, which OIDN smears into blotches.
"""
import bpy

ADDON_MODULE = "bl_ext.user_default.blendluxcore"

MAX_PATH_BOUNCES = 32       # bounces per path
MAX_DIFFUSE_BOUNCES = 4      # BlendLuxCore's default, kept
MAX_GLOSSY_BOUNCES = 16      # glossy floors and metal reflecting each other
MAX_SPECULAR_BOUNCES = 32    # glass and water chains need many specular bounces
CAMERA_RADIANCE_CLAMP = 2000.0         # camera-path radiance clamp; light-traced caustics are never clamped


def set_halt(seconds, scene=None):
    """Halt after `seconds` of rendering, or never (None: a final). Halt by samples and by noise always off."""
    h = (scene or bpy.context.scene).luxcore.halt
    h.use_samples = False                                  # default on at 32 samples
    h.use_light_samples = False
    h.use_noise_thresh = False
    h.enable = seconds is not None
    h.use_time = seconds is not None
    if seconds is not None:
        h.time = max(1, round(seconds))                    # s; LuxCore takes whole seconds
    return h


def engine_setup(halt_s=None, backend="CUDA", clamp=CAMERA_RADIANCE_CLAMP, camera=None, scene=None):
    """LuxCore PATH + light tracing on GPU camera paths and CPU light paths; halt after `halt_s` seconds or never (None)."""
    sc = scene or bpy.context.scene
    sc.render.engine = "LUXCORE"
    cfg = sc.luxcore.config
    cfg.engine = "PATH"
    cfg.device = "OCL"                                     # always GPU + CPU, never CPU only (RULES REN_03)
    bpy.context.preferences.addons[ADDON_MODULE].preferences.gpu_backend = backend
    sc.luxcore.devices.use_native_cpu = True               # light tracing runs only on CPU threads, GPU engine too
    p = cfg.path
    p.hybridbackforward_enable = True                      # "Add Light Tracing": light paths splat on the film
    p.hybridbackforward_lightpartition_opencl = 100        # GPU mode: CPU threads trace only light paths
    p.depth_total = MAX_PATH_BOUNCES
    p.depth_diffuse = MAX_DIFFUSE_BOUNCES
    p.depth_glossy = MAX_GLOSSY_BOUNCES
    p.depth_specular = MAX_SPECULAR_BOUNCES
    p.use_clamping = clamp is not None
    if clamp is not None:
        p.clamping = clamp
    set_halt(halt_s, sc)
    cam = camera or sc.camera
    if cam is not None:                                    # linear, no auto: for measurement and AgX later
        tm = cam.data.luxcore.imagepipeline.tonemapper
        tm.type = "TONEMAP_LINEAR"
        tm.use_autolinear = False
        tm.linear_scale = 1.0
    return {"device": cfg.device, "halt_s": halt_s, "clamp": clamp, "tonemapper": cam.name if cam else None}
