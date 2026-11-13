"""No-render checks for lab startup, source-only bakes, fixed extents and rectangular scan fitting."""
import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
import bpy
import numpy as np
import OpenImageIO as oiio

sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'blender'),str(Path(__file__).parent)]
import surface_wear_lab as lab
import surface_wear_compare as compare
from surface_wear_match import remap,fit_levels,statistics,prefilter_mask
from effects.wear.wear import WearLayer,MaskSource,apply_surface_wear
from effects.wear.image_masks import MASK_LEVELS_LABEL,MASK_GAMMA_LABEL
from materials.shared.node_graph import NodeGraph,active_socket
from core import assets


class GraphReady(Exception):
    """Stop the real lab immediately before its first render."""


def check_startup(project,out):
    """Invoke the real CLI outside the project with no environment fallback and intercept rendering."""
    assert not (Path.cwd()/'library').exists()
    def first_render(*args):
        assert assets.project_root()==str(project)
        assert any(m.name=='mask-controls' for m in bpy.data.materials)
        raise GraphReady
    argv=['surface_wear_lab.py','--','--project',str(project),'--out',str(out)]
    with patch.object(assets,'_PROJECT',None),patch.dict(os.environ,{'ARCHVIZ_PROJECT':''}), \
         patch.object(sys,'argv',argv),patch.object(lab,'render',side_effect=first_render):
        try:
            lab.main()
        except GraphReady:
            return
    raise AssertionError('Lab did not reach the render boundary')


def check_bake(out):
    """Inspect the actual upward bake graph: its source product has unit extent, not a wall gate."""
    def source_graph(*args):
        material=bpy.data.materials['placeholder-chipping']
        aov=next(n for n in material.node_tree.nodes if n.type=='OUTPUT_AOV' and n.aov_name=='var_surface-chipping')
        switch=aov.inputs['Value'].links[0].from_node
        product=active_socket(switch.inputs,'B').links[0].from_node
        assert product.operation=='MULTIPLY'
        assert not product.inputs[1].is_linked and product.inputs[1].default_value==1
        assert product.inputs[0].is_linked
        assert switch.inputs[0].links[0].from_socket.default_value==1
        raise GraphReady
    with patch.object(lab,'render',side_effect=source_graph):
        try:
            lab._bake(out,'chipping')
        except GraphReady:
            return
    raise AssertionError('Bake did not reach the render boundary')


def defaults(material):
    def value(socket):
        result=socket.default_value
        return tuple(result) if hasattr(result,'__len__') and not isinstance(result,str) else result
    return {(node.name,index):value(socket) for node in material.node_tree.nodes
            if node.label not in (MASK_LEVELS_LABEL,MASK_GAMMA_LABEL) and not node.label.endswith(' amount')
            for index,socket in enumerate(node.inputs) if hasattr(socket,'default_value')}


def check_calibration(path):
    """Exercise every raw-mask graph and preserve all location/socket defaults during fitting."""
    for kind in lab.LAYERS:
        material=bpy.data.materials.new('calibration-'+kind)
        graph=NodeGraph(material)
        coat=graph.node('ShaderNodeBsdfPrincipled',(5000,0))
        under=graph.node('ShaderNodeBsdfPrincipled',(5000,-1000))
        apply_surface_wear(graph,coat,{kind:WearLayer(source='mask',mask=MaskSource(str(path)))},under.outputs[0])
        compare._calibration_fields(material,kind)
        before=defaults(material)
        compare._set_levels(material,kind,dict(black=.1,white=.8,gamma=1.4,amount=.6))
        assert defaults(material)==before,kind
        assert any(n.type=='MAP_RANGE' and n.label!=MASK_LEVELS_LABEL for n in graph.tree.nodes)
        assert all(abs(n.inputs['From Min'].default_value-.1)<1e-6 for n in graph.tree.nodes if n.label==MASK_LEVELS_LABEL)
        switch=next(n for n in graph.tree.nodes if n.label=='surface-'+kind)
        product=active_socket(switch.inputs,'B').links[0].from_node
        for name,index in (('scan',0),('extent',1)):
            aov=next(n for n in graph.tree.nodes if n.type=='OUTPUT_AOV' and n.aov_name.endswith('-calibration-'+name))
            assert aov.inputs['Value'].links[0].from_socket==product.inputs[index].links[0].from_socket
    rng=np.random.default_rng(81)
    scan=np.clip(rng.uniform(0,1,(800,1))+rng.normal(0,.08,(800,16)),0,1)
    extent=np.broadcast_to(np.where(np.arange(800)[:,None]%4==0,0,rng.uniform(.1,1,(800,1))),scan.shape)
    known=(.2,.6,1.7,.65)
    expected=(np.clip((scan-.2)/.6,0,1)**1.7*extent*.65).mean(-1)
    assert np.array_equal(remap(scan,known,extent),expected)
    target=statistics(expected)
    fit=fit_levels(scan,target,extent=extent)
    assert abs(fit['predicted']['mean']/target['mean']-1)<.03,fit
    assert abs(fit['predicted']['sd']/target['sd']-1)<.03,fit
    assert abs(fit['predicted']['coverage']-target['coverage'])<.01,fit
    return fit


def check_rectangle(out,path):
    """Check scan labels and equal physical-frequency attenuation along unequal texture axes."""
    manifest=out/'rectangular-manifest.json'
    manifest.write_text(json.dumps({'grunge':[{'id':'rectangle','map':'Mask'}],
                                    'worn-through':[{'id':'rectangle','map':'Mask'}]}))
    with patch('effects.wear.image_masks.asset_mask',return_value=MaskSource(str(path),size_m=(2.,3.))):
        candidates=compare._assets(manifest,None)
        assert 'chipping' in candidates and 'worn-through' not in candidates
        candidate=candidates['grunge'][0]
    assert candidate['scan']=='2x3 m' and candidate['size_m']==(2.,3.)
    y,x=np.mgrid[:48,:64]
    pixels=.5+.2*np.sin(2*np.pi*4*x/64)+.2*np.sin(2*np.pi*6*y/48)
    filtered,info=prefilter_mask(out,candidate,pixels,.16,.5)
    assert np.allclose(info['sigma_texels_xy'],[2.56,1.28])
    actual=oiio.ImageBuf(str(filtered)).get_pixels(oiio.FLOAT)[...,0]
    attenuation=np.exp(-2*np.pi**2*(.08*2)**2)
    assert np.max(abs(actual-(.5+(pixels-.5)*attenuation)))<1e-6
    return info


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.out.mkdir(parents=True,exist_ok=True)
    with patch.object(bpy.ops.render,'render',side_effect=AssertionError('Rendering forbidden')):
        check_startup(args.project.resolve(),args.out)
        check_bake(args.out)
        fit=check_calibration(args.out/'mask-levels.exr')
        filtering=check_rectangle(args.out,args.out/'mask-levels.exr')
    (args.out/'control-check.json').write_text(json.dumps(dict(lab_project_initialized=True,
        bake_extent_one=True,location_controls_unchanged=True,fit=fit,rectangular_filter=filtering,
        renders=0),indent=2))
    print('SURFACE_WEAR_CONTROLS_PASS (no renders)',flush=True)


if __name__=='__main__':
    main()
