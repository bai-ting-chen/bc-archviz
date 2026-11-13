"""Fingerprint every surface source, amount/switch path and shader effect without rendering."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/blender'))
sys.path.insert(0,str(ROOT/'scripts/controls/regression'))
import bpy
from regress_graph import graph
from core.assets import set_project
from materials.shared.node_graph import NodeGraph
from effects.wear.wear import WearLayer, apply_surface_wear, LAYERS
from effects.wear.masks import asset_mask
from effects.wear.atlas import StampAtlas
from effects.wear.stamps import StampSource
from effects.wear.wear_locations import WearExtent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--baseline',type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
set_project(args.project)
out=args.out
mask=asset_mask('uh4tfagc')
atlas=StampAtlas(mask.path,((.5,1.),),1,1,cell_m=3.2)
stamps=StampSource(vertical_stamps=atlas,wall_stamps=atlas,floor_stamps=atlas,worn_stamps=atlas)
result={}
for kind in LAYERS:
    sources=[None,'procedural','mask','hybrid']+(['stamps'] if kind in ('dried-marks','chipping') else [])
    for source in sources:
        for amount,enabled in ((.5,True),(0.,True),(.73,False)):
            settings=WearLayer(source=source,amount=amount,enabled=enabled,stamps=stamps,
                               extent=WearExtent(drip_top_m=2.4))
            name=f'{kind}:{source}:{amount}:{enabled}'
            material=bpy.data.materials.new(name)
            g=NodeGraph(material)
            shader=g.node('ShaderNodeBsdfPrincipled',(5000,0))
            under=g.node('ShaderNodeBsdfPrincipled',(5000,-600),Roughness=.8)
            surface=apply_surface_wear(g,shader,{kind:settings},under_shader=under.outputs[0])
            output=g.node('ShaderNodeOutputMaterial',(6000,0))
            g.link(surface,output.inputs['Surface'])
            result[name]=graph(g.tree)
# Whole stack catches composition and ordering changes as well as individual sources.
for source in ('procedural','mask','hybrid'):
    material=bpy.data.materials.new('stack-'+source)
    g=NodeGraph(material)
    shader=g.node('ShaderNodeBsdfPrincipled',(5000,0))
    under=g.node('ShaderNodeBsdfPrincipled',(5000,-600))
    apply_surface_wear(g,shader,{k:WearLayer(source=source) for k in LAYERS},under_shader=under.outputs[0])
    result['stack:'+source]=graph(g.tree)
out.write_text(json.dumps(result,sort_keys=True))
print('SURFACE_GRAPH_CASES',len(result),flush=True)

if args.baseline:
    old=json.loads(args.baseline.read_text().replace('worn-through','chipping').replace('Worn-through','Chipping'))
    # Relabelling changes sort order; sort again after the explicit alias rewrite.
    for graphs in (old,result):
        for value in graphs.values():
            value['nodes'].sort()
            value['links'].sort()
    differences=[key for key in old.keys()|result.keys() if old.get(key)!=result.get(key)]
    assert not differences,differences
    print('WEAR_GRAPH_EQUIVALENCE_PASS',len(result),flush=True)
