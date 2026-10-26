"""Thin wall; implementation for water.shading."""



def thin_wall_copy(material, name):
    """Copy of a water material with Principled Thin Wall on (an open shell with solid water glows white)."""
    copy = material.copy()
    copy.name = name
    for node in copy.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Thin Wall'].default_value = True
    return copy
