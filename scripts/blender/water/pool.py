"""Install a ripple height field as a bump on the pool's own material (references/materials/water-ripple.md §3).

The height is written to a float EXR (millimetres) and loaded from that file, so it survives a reload; world
positions map to the field through the lip's axes, so any wall orientation works. Only up-facing faces are bumped.
"""
import bpy
import numpy as np


def save_height_exr(H, path, name='water ripple height (mm)'):
    """Write H (metres, [a, o]) as a float EXR in millimetres and return the loaded image datablock."""
    na, no = H.shape
    img = bpy.data.images.new(name + ' tmp', no, na, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'          # before writing pixels (api-traps)
    px = np.zeros((na, no, 4), np.float32); px[..., :3] = (H * 1000)[..., None]; px[..., 3] = 1
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = str(path); img.file_format = 'OPEN_EXR'
    sc = bpy.context.scene; s = sc.render.image_settings
    keep = (s.media_type, s.file_format, s.color_depth, s.exr_codec)
    s.media_type = 'IMAGE'                               # OPEN_EXR is not valid under MULTI_LAYER_IMAGE
    s.file_format = 'OPEN_EXR'; s.color_depth = '32'; s.exr_codec = 'ZIP'
    try:
        img.save_render(str(path), scene=sc)
    finally:
        s.media_type = keep[0]; s.file_format, s.color_depth, s.exr_codec = keep[1:]
    bpy.data.images.remove(img)
    out = bpy.data.images.load(str(path), check_existing=False); out.name = name
    out.colorspace_settings.name = 'Non-Color'
    return out


def install_bump(material, image, lip, o_range, a_range):
    """Bump the material's Principled Normal with image (mm) mapped over lip-local o_range x a_range (metres)."""
    nt = material.node_tree; N = nt.nodes; L = nt.links
    bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    geo = N.new('ShaderNodeNewGeometry')

    def coord(axis, lo, hi):
        sub = N.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'
        L.new(geo.outputs['Position'], sub.inputs[0]); sub.inputs[1].default_value = tuple(lip.origin)
        dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
        L.new(sub.outputs[0], dot.inputs[0]); dot.inputs[1].default_value = tuple(axis)
        mr = N.new('ShaderNodeMapRange'); mr.clamp = False
        L.new(dot.outputs['Value'], mr.inputs['Value']); mr.inputs['From Min'].default_value = lo; mr.inputs['From Max'].default_value = hi
        return mr.outputs['Result']

    comb = N.new('ShaderNodeCombineXYZ')
    L.new(coord(lip.out, *o_range), comb.inputs['X']); L.new(coord(lip.along, *a_range), comb.inputs['Y'])
    tex = N.new('ShaderNodeTexImage'); tex.image = image; tex.extension = 'CLIP'; tex.interpolation = 'Cubic'
    L.new(comb.outputs[0], tex.inputs['Vector'])
    up = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['True Normal'], up.inputs[0])
    gt = N.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; L.new(up.outputs['Z'], gt.inputs[0]); gt.inputs[1].default_value = .5
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; L.new(tex.outputs['Color'], mul.inputs[0]); L.new(gt.outputs[0], mul.inputs[1])
    bump = N.new('ShaderNodeBump'); bump.inputs['Distance'].default_value = .001      # image in mm
    L.new(mul.outputs[0], bump.inputs['Height'])
    if bsdf.inputs['Normal'].is_linked:
        L.new(bsdf.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
    L.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return bump


def readback_mm(image):
    """Min/max (mm) of a loaded height image: proof the field survived saving and loading."""
    a = np.empty(image.size[0] * image.size[1] * 4, np.float32); image.pixels.foreach_get(a)
    return float(a[0::4].min()), float(a[0::4].max())
