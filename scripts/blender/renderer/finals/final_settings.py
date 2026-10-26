"""Final settings; implementation for finals."""
import bpy


def setup_unlimited(res, samples=1_000_000, denoiser="OPENIMAGEDENOISE"):
    """Final settings: full res, untiled (tile > frame), no adaptive/time limit, denoiser + its passes stored, multilayer EXR."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.use_border = False
    c = sc.cycles
    c.device = "GPU"
    c.samples = samples
    c.use_adaptive_sampling = False
    c.time_limit = 0.0
    c.use_denoising = True
    c.denoiser = denoiser
    c.denoising_use_gpu = True                             # final denoising defaults to CPU
    c.use_auto_tile = False
    c.tile_size = max(4096, *res)                          # > frame: one tile even if Cycles tiles anyway
    sc.view_layers[0].cycles.denoising_store_passes = True
    f = sc.render.image_settings
    f.media_type = "MULTI_LAYER_IMAGE"; f.file_format = "OPEN_EXR_MULTILAYER"
    f.color_depth = "32"; f.exr_codec = "ZIP"
    return sc
