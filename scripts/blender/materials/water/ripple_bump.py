"""Ripple bump; implementation for water.shading."""



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
