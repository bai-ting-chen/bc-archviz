"""Independent wear layers sharing procedural and grayscale-image factor inputs."""
from dataclasses import dataclass, field
from materials.shared.node_graph import layer_frame, layer_switch
from effects.wear.procedural_patterns import procedural_field
from effects.wear.image_masks import MaskSource, image_mask, mask_field, surface_coordinates
from effects.wear.default_sources import default_field, DEFAULT_SOURCES
from effects.wear.wear_locations import WearExtent, location_extent
from effects.wear.hybrid_sources import HybridSource, hybrid_field
from effects.wear.scratches import scratch_hybrid
from effects.wear.dirt import grunge
from effects.wear.decal_stamps import StampSource, stamps_field

from effects.wear.layer_names import LAYERS, canonical_layer


@dataclass
class WearLayer:
    """One layer's switch, metre sizes and 0–1 strength; binary chips use strength for coverage."""
    enabled: bool = True
    amount: float = 1.0
    source: str | None = None
    mask: MaskSource | None = None
    scale_m: float = .25
    scratch_width_m: float = .003
    extent: WearExtent = field(default_factory=WearExtent)
    hybrid: HybridSource = field(default_factory=HybridSource)
    stamps: StampSource = field(default_factory=StampSource)


def wear_factor(graph, kind, settings, vector=None, components=None):
    """Return a switched wear factor; binary hybrid chips vary coverage instead of transparency."""
    kind = canonical_layer(kind)
    if kind not in LAYERS or settings.source not in (None, 'procedural', 'mask', 'hybrid', 'stamps'):
        raise ValueError('Unknown layer or source')
    if not 0 <= settings.amount <= 1 or settings.scale_m <= 0 or settings.scratch_width_m <= 0:
        raise ValueError('Amount must be 0–1 and shape sizes must be positive')
    frame = layer_frame(graph, 'surface-wear: ' + kind)
    if vector is None:
        vector = surface_coordinates(graph, frame)
    source = settings.source if settings.source is not None else DEFAULT_SOURCES[kind]
    if not settings.enabled:
        source = 'procedural'  # Disabled layers must not require any local asset.
    extent = location_extent(graph, kind, settings.extent, frame)
    binary_amount = None
    fallback = False
    if source == 'hybrid' and kind == 'chipping':
        control = graph.node('ShaderNodeValue', (200, -27400), frame, label='surface-chipping amount')
        control.outputs[0].default_value = settings.amount if settings.enabled else 0
        binary_amount = control.outputs[0]
    if source == 'hybrid' and kind != 'scratches':
        parts = hybrid_field(graph, kind, settings, vector, extent, frame, amount=binary_amount)
        raw = parts['factor']
        fallback = parts.get('fallback', False)
        if components is not None and not fallback:
            components.update(parts)
        for name in ('region', 'interior', 'rim', 'scan', 'driver'):
            if name not in parts:
                continue
            aov = graph.node('ShaderNodeOutputAOV', (400, -27000), frame)
            aov.aov_name = 'var_surface-' + kind + '-' + name
            graph.link_or_set(aov.inputs['Value'], parts[name])
        extent = 1  # already included before the procedural region threshold
    elif source == 'hybrid':
        raw = scratch_hybrid(graph, settings, vector, frame)
    elif source == 'stamps':
        raw = stamps_field(graph, kind, settings, vector, extent, frame)
    elif source == 'mask':
        if settings.mask is None:
            raw = default_field(graph, kind, settings, vector, frame)
        else:
            raw = mask_field(graph, settings.mask, vector, frame, crossed=kind == 'scratches')
    else:
        raw = procedural_field(graph, kind, vector, settings.scale_m, settings.scratch_width_m, frame)
    raw = graph.math('MULTIPLY', raw, extent, (0, -25000), frame)
    if binary_amount is None:
        switch = settings.amount if settings.enabled else 0
    elif fallback:
        switch = binary_amount
    else:
        switch = graph.math('GREATER_THAN', binary_amount, 0, (0, -27400), frame)
    factor = layer_switch(graph, 'surface-' + kind, raw, switch, 0, frame)
    return factor, frame


def apply_surface_wear(graph, shader, layers, under_shader=None, vector=None):
    """Compose requested layers on a Principled shader; return the resulting Surface socket."""
    surface = shader.outputs[0]
    for kind, settings in layers.items():
        kind = canonical_layer(kind)
        parts = {}
        factor, frame = wear_factor(graph, kind, settings, vector, components=parts)
        color_gain = {'grunge': -.48, 'scratches': 0, 'dried-marks': -.65, 'chipping': 0}[kind]
        rough_gain = {'grunge': .35, 'scratches': -.8, 'dried-marks': .45, 'chipping': 0}[kind]
        if kind == 'chipping':
            if under_shader is None:
                raise ValueError('Chipping requires an under-material shader socket')
            if parts:
                mix = graph.node('ShaderNodeMixShader', (3200, 0), frame)
                graph.link(factor, mix.inputs[0])
                graph.link(surface, mix.inputs[1])
                graph.link(under_shader, mix.inputs[2])
                surface = mix.outputs[0]
                continue  # Binary coat/bare selection adds no dirt shader or wet-looking tint.
            # Keep the legacy transition border for the continuous reference sources.
            amount = factor.node.inputs[0].links[0].from_socket
            shape = graph.math('DIVIDE', factor, amount, (1700, -600), frame)
            border = graph.math('SUBTRACT', 1, shape, (2000, -600), frame)
            border = graph.math('MULTIPLY', border, shape, (2300, -600), frame)
            border = graph.math('MULTIPLY', border, 2.6, (2600, -600), frame)  # max 65% dirt at the transition
            border = graph.math('MULTIPLY', border, amount, (2900, -600), frame)
            mix = graph.node('ShaderNodeMixShader', (3200, 0), frame)
            graph.link(factor, mix.inputs[0])
            graph.link(surface, mix.inputs[1])
            graph.link(under_shader, mix.inputs[2])
            dirt = graph.node('ShaderNodeBsdfPrincipled', (3200, -1000), frame, Roughness=.8)
            dirt.inputs['Base Color'].default_value = (.025, .021, .018, 1)
            edged = graph.node('ShaderNodeMixShader', (3500, 0), frame)
            graph.link(border, edged.inputs[0])
            graph.link(mix.outputs[0], edged.inputs[1])
            graph.link(dirt.outputs[0], edged.inputs[2])
            surface = edged.outputs[0]
        else:
            if color_gain:
                _multiply_input(graph, shader.inputs['Base Color'], factor, color_gain, frame, 0)
            if kind == 'dried-marks' and parts:
                rim = graph.math('MULTIPLY', factor, parts['rim'], (2600, -2400), frame)
                _multiply_input(graph, shader.inputs['Base Color'], rim, -.25, frame, -2400)
            _multiply_input(graph, shader.inputs['Roughness'], factor, rough_gain, frame, -800)
            if kind == 'scratches':
                bump = graph.node('ShaderNodeBump', (3200, -1600), frame, Strength=.4, Distance=.00015)
                bump.invert = True
                graph.link(factor, bump.inputs['Height'])
                if shader.inputs['Normal'].is_linked:
                    graph.link(shader.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
                graph.link(bump.outputs[0], shader.inputs['Normal'])
    return surface


def _multiply_input(graph, socket, factor, gain, frame, y):
    if socket.is_linked:
        original = socket.links[0].from_socket
    elif socket.type == 'RGBA':
        original = tuple(socket.default_value)
    else:
        original = socket.default_value
    delta = graph.math('MULTIPLY', factor, gain, (2600, y - 200), frame)
    multiplier = graph.math('ADD', delta, 1, (2800, y - 200), frame)
    if socket.type == 'RGBA':
        node = graph.node('ShaderNodeMixRGB', (3000, y), frame)
        node.blend_type = 'MULTIPLY'
        node.inputs[0].default_value = 1
        graph.link_or_set(node.inputs[1], original)
        graph.link(multiplier, node.inputs[2])
        result = node.outputs[0]
    else:
        result = graph.math('MULTIPLY', original, multiplier, (3000, y), frame)
    graph.link(result, socket)
