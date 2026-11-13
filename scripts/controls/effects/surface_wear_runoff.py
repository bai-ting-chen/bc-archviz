"""Concrete lab adapter for the existing edge-wear run-off builder."""


def runoff_fixture(project, samples, kind, settings):
    """Adapt only the lab's concrete material to the existing run-off builder contract."""
    import bpy
    import surface_wear_lab as lab
    from effects.wear.wear import WearLayer, image_mask
    from effects.wear.water_marks import add_runoff
    from effects.wear.leak_field import add_leak_field
    from effects.wear.dirt import GRIME_TINT
    from materials.shared.node_graph import NodeGraph, layer_frame, layer_switch
    sc, materials, regions = lab._fixture(project, samples, 'grunge', WearLayer(enabled=False))
    material = materials[-1]
    g = NodeGraph(material.node_tree)
    shaders = [n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
    shaders[1].inputs['Base Color'].default_value = (*GRIME_TINT, 1)
    shaders[1].inputs['Roughness'].default_value = .93
    mix = g.node('ShaderNodeMixShader', (6000, 0), label='Wear Layered (BRDFLayered)')
    g.link(shaders[0].outputs[0], mix.inputs[1])
    g.link(shaders[1].outputs[0], mix.inputs[2])
    output = next(n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
    g.link(mix.outputs[0], output.inputs['Surface'])
    if settings.source == 'procedural':
        add_leak_field(bpy.data.objects['concrete-wall'])
        # Isolate the existing leak term; its separate grunge and soil-splash terms stay off.
        add_runoff(material, grunge=(.6, 9, .56, .62, 0), splash=(.08, .35, 0), ground_z=-.825)
        factor = next(n for n in material.node_tree.nodes if n.label == 'Run-off strength').outputs[0]
        amount = g.node('ShaderNodeValue', (5700, -600), label='surface-run-off amount')
        amount.outputs[0].default_value = settings.amount if settings.enabled else 0
        g.link(amount.outputs[0], factor.node.inputs[1])
        aov = g.node('ShaderNodeOutputAOV', (6200, -600))
        aov.aov_name = 'var_surface-run-off'
        g.link(factor, aov.inputs['Value'])
    else:
        frame = layer_frame(g, 'surface-wear: run-off')
        raw = image_mask(g, settings.mask, lab._surface_vector(g, 1.9), frame)
        factor = layer_switch(g, 'surface-run-off', raw, settings.amount, 0, frame)
    g.link(factor, mix.inputs[0])
    return sc, [material], {'concrete-wall': regions['concrete-wall']}

