"""Materials and images for the water geometry (references/materials/water/water-ripple.md §3, water-splash.md §2).

- thin_wall_copy: water for open shells (crowns, bubbles): glints and rims, straight transmission.
- save_height_exr / install_bump / readback_mm: a ripple height field as a bump on the pool's own material.
  The height goes to a float EXR in millimetres and is loaded from that file (a generated image is lost on reload);
  world positions map to the field through the lip's axes, so any wall orientation works.
"""
import bpy
import numpy as np


def thin_wall_copy(material, name):
    """Copy of a water material with Principled Thin Wall on (an open shell with solid water glows white)."""
    copy = material.copy()
    copy.name = name
    for node in copy.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Thin Wall'].default_value = True
    return copy


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


def install_bump(material, image, lip, s_range, o_range):
    """Bump the material's Principled Normal with image (mm) mapped over lip-local s_range x o_range (metres).

    Image rows run along s, columns along o (as save_height_exr writes them). Only up-facing faces are bumped.
    """
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    geometry = nodes.new('ShaderNodeNewGeometry')

    def lip_coordinate(axis, lo, hi):
        """0..1 along one lip axis: ((P - origin) . axis - lo) / (hi - lo)."""
        rel = nodes.new('ShaderNodeVectorMath')
        rel.operation = 'SUBTRACT'
        links.new(geometry.outputs['Position'], rel.inputs[0])
        rel.inputs[1].default_value = tuple(lip.origin)
        dot = nodes.new('ShaderNodeVectorMath')
        dot.operation = 'DOT_PRODUCT'
        links.new(rel.outputs[0], dot.inputs[0])
        dot.inputs[1].default_value = tuple(axis)
        remap = nodes.new('ShaderNodeMapRange')
        remap.clamp = False
        links.new(dot.outputs['Value'], remap.inputs['Value'])
        remap.inputs['From Min'].default_value = lo
        remap.inputs['From Max'].default_value = hi
        return remap.outputs['Result']

    uv = nodes.new('ShaderNodeCombineXYZ')
    links.new(lip_coordinate(lip.out, *o_range), uv.inputs['X'])      # image columns = o
    links.new(lip_coordinate(lip.along, *s_range), uv.inputs['Y'])    # image rows = s
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.extension = 'CLIP'
    tex.interpolation = 'Cubic'
    links.new(uv.outputs[0], tex.inputs['Vector'])
    normal_z = nodes.new('ShaderNodeSeparateXYZ')
    links.new(geometry.outputs['True Normal'], normal_z.inputs[0])
    is_top = nodes.new('ShaderNodeMath')
    is_top.operation = 'GREATER_THAN'
    links.new(normal_z.outputs['Z'], is_top.inputs[0])
    is_top.inputs[1].default_value = .5
    height = nodes.new('ShaderNodeMath')
    height.operation = 'MULTIPLY'
    links.new(tex.outputs['Color'], height.inputs[0])
    links.new(is_top.outputs[0], height.inputs[1])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = .001                      # image values are millimetres
    links.new(height.outputs[0], bump.inputs['Height'])
    if bsdf.inputs['Normal'].is_linked:                               # keep an existing normal/bump chain
        links.new(bsdf.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return bump


def readback_mm(image):
    """Min/max (mm) of a loaded height image: proof the field survived saving and loading."""
    pixels = np.empty(image.size[0] * image.size[1] * 4, np.float32)
    image.pixels.foreach_get(pixels)
    return float(pixels[0::4].min()), float(pixels[0::4].max())
