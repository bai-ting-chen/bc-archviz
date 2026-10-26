"""Height image; implementation for water.shading."""
import bpy
import numpy as np


def save_height_exr(H, path, name='water ripple height (mm)'):
    """Write H (metres, [s, o]) as a float EXR in millimetres and return the image loaded from that file."""
    n_s, n_o = H.shape
    img = bpy.data.images.new(name + ' tmp', n_o, n_s, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'          # before writing pixels, or the buffer is wiped (api-traps)
    pixels = np.zeros((n_s, n_o, 4), np.float32)
    pixels[..., :3] = (H * 1000)[..., None]
    pixels[..., 3] = 1
    img.pixels.foreach_set(pixels.ravel())
    settings = bpy.context.scene.render.image_settings
    saved = (settings.media_type, settings.file_format, settings.color_depth, settings.exr_codec)
    settings.media_type = 'IMAGE'                        # OPEN_EXR is not valid under MULTI_LAYER_IMAGE
    settings.file_format = 'OPEN_EXR'
    settings.color_depth = '32'
    settings.exr_codec = 'ZIP'
    try:
        img.save_render(str(path), scene=bpy.context.scene)
    finally:
        settings.media_type = saved[0]
        settings.file_format, settings.color_depth, settings.exr_codec = saved[1:]
    bpy.data.images.remove(img)
    loaded = bpy.data.images.load(str(path), check_existing=False)
    loaded.name = name
    loaded.colorspace_settings.name = 'Non-Color'
    return loaded


def readback_mm(image):
    """Min/max (mm) of a loaded height image: proof the field survived saving and loading."""
    pixels = np.empty(image.size[0] * image.size[1] * 4, np.float32)
    image.pixels.foreach_get(pixels)
    return float(pixels[0::4].min()), float(pixels[0::4].max())
