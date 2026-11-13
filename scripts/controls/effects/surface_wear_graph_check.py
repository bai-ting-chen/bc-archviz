"""Headless graph checks for layer defaults, orientation routing, fallback and scratch source composition."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'blender'))
from core.assets import set_project
from materials.shared.nodes import G, sock
from effects.surface_wear import WearLayer, wear_factor, apply_surface_wear
from effects.surface_wear_defaults import DEFAULT_SOURCES
from effects import surface_wear_defaults,surface_wear_hybrid
from effects.surface_wear_masks import asset_mask, scan_size_m


def _graph(kind, settings=None):
    mat = bpy.data.materials.new('check-' + kind)
    g = G(mat)
    factor, _ = wear_factor(g, kind, settings or WearLayer())
    return g, factor


def _image_ids(socket):
    nodes = [link.from_node for link in socket.links]
    visited = set()
    result = set()
    while nodes:
        node = nodes.pop()
        if node in visited:
            continue
        visited.add(node)
        if node.type == 'TEX_IMAGE':
            result.add(Path(node.image.filepath).parent.name)
        nodes.extend(link.from_node for value in node.inputs for link in value.links)
    return result


def main():
    """Validate graph structure without rendering any of the already-decided layers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    set_project(args.project)
    assert DEFAULT_SOURCES == dict.fromkeys(('grunge', 'dried-marks', 'worn-through', 'scratches'), 'hybrid')
    from effects.surface_wear_tiling import stochastic_mask
    assert surface_wear_hybrid.stochastic_mask is stochastic_mask
    assert 'stamps' not in DEFAULT_SOURCES.values()
    for text, expected in (('70 x 70 cm',(.7,.7)),('700 x 1000 mm',(.7,1.)),
                           ('2 x 3 m',(2.,3.)),('70 cm x 1 m',(.7,1.)),('0.7 m',(.7,.7))):
        assert all(abs(a-b)<1e-12 for a,b in zip(scan_size_m({'scan':text}),expected)),text
    surface_wear_defaults._missing_reported.clear()
    missing_scratch=io.StringIO()
    with patch.object(surface_wear_hybrid,'asset_mask',return_value=None), contextlib.redirect_stdout(missing_scratch):
        for _ in range(2):
            g,_=_graph('scratches')
            assert not any(n.type=='TEX_IMAGE' for n in g.nt.nodes)
            assert sum(n.bl_idname=='ShaderNodeVectorRotate' for n in g.nt.nodes)==4
    scratch_log=missing_scratch.getvalue().splitlines()
    assert len(scratch_log)==1 and 'vdekdjrc' in scratch_log[0] and 'Fab search:' in scratch_log[0]
    with patch.object(surface_wear_hybrid,'asset_mask',side_effect=AssertionError('Disabled asset lookup')), \
         patch.object(surface_wear_defaults,'asset_mask',side_effect=AssertionError('Disabled asset lookup')), \
         patch('effects.surface_wear_chips.asset_mask',side_effect=AssertionError('Disabled asset lookup')), \
         patch('effects.surface_wear_stamps.stamps_field',side_effect=AssertionError('Disabled stamp lookup')):
        for kind in DEFAULT_SOURCES:
            for source in (None,'procedural','mask','hybrid','stamps'):
                g,factor=_graph(kind,WearLayer(enabled=False,source=source))
                assert not any(n.type=='TEX_IMAGE' for n in g.nt.nodes)
                assert factor.node.inputs[0].links[0].from_socket.default_value==0
    for kind, ids in (('grunge', {'uh4tfagc','uh4uabdc'}),
                      ('dried-marks', {'uh4tdhic','tjwtbgvc'}),
                      ('worn-through', {'ub1meemn','tmulfghdy'})):
        mat = bpy.data.materials.new('hybrid-parts-' + kind)
        graph = G(mat)
        parts = {}
        wear_factor(graph, kind, WearLayer(source='hybrid'), components=parts)
        assert not _image_ids(parts['region']), kind
        assert _image_ids(parts['interior']) == ids, kind
        product = parts['factor'].node
        assert product.operation == 'MULTIPLY'
        assert product.inputs[0].links[0].from_socket == parts['region']
        assert product.inputs[1].links[0].from_socket == parts['interior']
        assert not any(n.type == 'GROUP' for n in graph.nt.nodes), kind
        if kind == 'worn-through':
            assert parts['region'].node.operation == 'GREATER_THAN'
            assert parts['interior'].node.operation == 'GREATER_THAN'
            controls=[n for n in graph.nt.nodes if n.label=='surface-worn-through amount']
            assert len(controls)==1 and controls[0].outputs[0].default_value==1.
    material = bpy.data.materials.new('binary-coat-selection')
    graph = G(material)
    coat = graph.node('ShaderNodeBsdfPrincipled', (6000,0))
    under = graph.node('ShaderNodeBsdfPrincipled', (6000,-1000))
    surface = apply_surface_wear(graph, coat, {'worn-through':WearLayer(source='hybrid',amount=.5)},
                                 under_shader=under.outputs[0])
    assert surface.node.type=='MIX_SHADER'
    assert surface.node.inputs[1].links[0].from_socket==coat.outputs[0]
    assert surface.node.inputs[2].links[0].from_socket==under.outputs[0]
    assert sum(n.type=='BSDF_PRINCIPLED' for n in graph.nt.nodes)==2
    g, _ = _graph('grunge')
    assert [Path(n.image.filepath).parent.name for n in g.nt.nodes if n.type == 'TEX_IMAGE'] == ['uh4tfagc','uh4uabdc','uh4tfagc']
    g, _ = _graph('dried-marks', WearLayer(source='mask'))
    assert {Path(n.image.filepath).parent.name for n in g.nt.nodes if n.type == 'TEX_IMAGE'} == {'tjwtbgvc', 'uh4tdhic'}
    zone = next(n for n in g.nt.nodes if n.label == 'dried marks up-facing zone')
    assert zone.inputs['From Min'].default_value == .25 and zone.inputs['From Max'].default_value == .75
    mix = next(n for n in g.nt.nodes if n.type == 'MIX' and n.inputs[0].is_linked and n.inputs[0].links[0].from_node == zone)
    assert _image_ids(sock(mix.inputs, 'A')) == {'tjwtbgvc'}
    assert _image_ids(sock(mix.inputs, 'B')) == {'uh4tdhic'}
    for kind in ('grunge', 'dried-marks', 'worn-through'):
        g, _ = _graph(kind, WearLayer(source='procedural'))
        assert not any(n.type == 'TEX_IMAGE' for n in g.nt.nodes)
    g, _ = _graph('worn-through')
    assert {Path(n.image.filepath).parent.name for n in g.nt.nodes if n.type=='TEX_IMAGE'}=={'ub1meemn','tmulfghdy'}
    from effects.surface_wear_hybrid import _interior_masks, HybridSource
    from effects.surface_wear_chips import flaked_paint_masks
    assert all((m.black,m.white,m.gamma,m.invert)==(0.,1.,1.,False)
               for m in _interior_masks('grunge',HybridSource(),None))
    chips=flaked_paint_masks()
    assert [m.invert for m in chips]==[False,True]
    assert all('Roughness' in Path(m.path).stem for m in chips)
    with patch('effects.surface_wear_chips.asset_mask',return_value=None), contextlib.redirect_stdout(io.StringIO()):
        parts={}
        mat=bpy.data.materials.new('missing-chip-fallback')
        g=G(mat)
        factor,_=wear_factor(g,'worn-through',WearLayer(amount=.5),components=parts)
        assert parts=={} and not any(n.type=='TEX_IMAGE' for n in g.nt.nodes)
        assert factor.node.inputs[0].links[0].from_socket.default_value==.5
    g, _ = _graph('scratches', WearLayer(source='procedural'))
    assert sum(n.bl_idname == 'ShaderNodeVectorRotate' for n in g.nt.nodes) == 4
    g, _ = _graph('scratches', WearLayer(source='mask'))
    textures = [n for n in g.nt.nodes if n.type == 'TEX_IMAGE']
    assert len(textures) == 2 and textures[0].image == textures[1].image
    assert sum(n.bl_idname == 'ShaderNodeVectorRotate' for n in g.nt.nodes) == 1
    g, factor = _graph('grunge', WearLayer(enabled=False))
    assert factor.node.inputs[0].links[0].from_socket.default_value == 0
    assert asset_mask('missing-surface-wear', project=args.project) is None
    surface_wear_defaults._missing_reported.clear()
    output = io.StringIO()
    with patch.object(surface_wear_defaults, 'asset_mask', return_value=None), \
         patch.object(surface_wear_hybrid,'asset_mask',return_value=None), contextlib.redirect_stdout(output):
        for _ in range(2):
            for kind in ('grunge', 'dried-marks'):
                g, _ = _graph(kind)
                assert not any(n.type == 'TEX_IMAGE' for n in g.nt.nodes)
                assert any(n.type == 'TEX_NOISE' for n in g.nt.nodes)
    lines = output.getvalue().splitlines()
    assert len(lines) == 4 and all('Fab search:' in line for line in lines), lines
    assert all(sum(asset_id in line for line in lines) == 1 for asset_id in ('uh4tfagc','uh4uabdc','tjwtbgvc','uh4tdhic'))
    def missing_vertical(asset_id, map_name):
        return None if asset_id == 'tjwtbgvc' else asset_mask(asset_id, map_name)
    with patch.object(surface_wear_defaults, 'asset_mask', side_effect=missing_vertical):
        g, _ = _graph('dried-marks', WearLayer(source='mask'))
        assert {Path(n.image.filepath).parent.name for n in g.nt.nodes if n.type == 'TEX_IMAGE'} == {'uh4tdhic'}
        assert any(n.type == 'TEX_NOISE' for n in g.nt.nodes)
    g, _ = _graph('scratches', WearLayer(source='procedural'))
    shader = g.node('ShaderNodeBsdfPrincipled', (6000, 0))
    apply_surface_wear(g, shader, {'scratches': WearLayer(source='procedural')})
    assert shader.inputs['Normal'].is_linked and shader.inputs['Roughness'].is_linked
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'defaults-check.json').write_text(json.dumps(dict(defaults=DEFAULT_SOURCES,
        fallback_log=lines, partial_zone_fallback=True, orientation_gate=[.25, .75], 
        procedural_directions=4, mask_rotations=2, hybrid_region_bitmap_product=True,
        hybrid_uses_stamp_atlases=False, binary_chip_shader=True, scratch_fallback_log=scratch_log,
        disabled_layers_asset_free=True, scan_units_metres=True), indent=2))
    print('DEFAULTS_AND_SCRATCH_GRAPHS_PASS', flush=True)


if __name__ == '__main__':
    main()
