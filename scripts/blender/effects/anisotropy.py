"""Directional microfacet roughness shared by reflective and transmissive materials."""


def anisotropy(bsdf, amount=0.0, rotation=0.0, tangent=(1.0, 0.0, 0.0)):
    """Set directional roughness; rotation is in turns, tangent a world vector or UV-map name."""
    # BSDF socket names differ between Glass and Principled.
    amount_input = bsdf.inputs.get('Anisotropic') or bsdf.inputs.get('Anisotropy')
    rotation_input = bsdf.inputs.get('Anisotropic Rotation') or bsdf.inputs.get('Rotation')
    amount_input.default_value = amount
    rotation_input.default_value = rotation
    tangent_input = bsdf.inputs['Tangent']
    tree = bsdf.id_data
    for link in list(tangent_input.links):
        source = link.from_node
        tree.links.remove(link)
        # A repeated call replaces the tangent node this helper made before.
        if source.type in {'TANGENT', 'COMBXYZ'} and not any(o.links for o in source.outputs):
            tree.nodes.remove(source)
    if isinstance(tangent, str):
        node = tree.nodes.new('ShaderNodeTangent')
        node.direction_type = 'UV_MAP'
        node.uv_map = tangent
    else:
        # Cycles uses a fallback tangent for an unlinked input, even with a vector default.
        node = tree.nodes.new('ShaderNodeCombineXYZ')
        for socket, value in zip(node.inputs, tangent):
            socket.default_value = value
    node.location = (bsdf.location.x - 220, bsdf.location.y - 240)
    tree.links.new(node.outputs[0], tangent_input)
