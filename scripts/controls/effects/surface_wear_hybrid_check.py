"""Render hybrid period and underside controls without any dependency on decal atlases."""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np

SCRIPTS=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(SCRIPTS/'blender'),str(SCRIPTS/'controls'),str(Path(__file__).parent)]
from core.assets import set_project
from materials.shared.node_graph import NodeGraph
from effects.wear.wear import WearLayer,WearExtent,HybridSource,MaskSource,wear_factor
from effects.wear.masks import asset_mask
from variation_lab import black_scene,ortho_camera,plane,emission,render,channel


def _fixture(settings,down=False):
    black_scene(samples=128,res=700 if not down else 64)
    material=bpy.data.materials.new('hybrid-source-check')
    g=NodeGraph(material)
    factor,_=wear_factor(g,'dried-marks' if down else 'grunge',settings)
    emission(g,factor)
    if down:
        bpy.ops.mesh.primitive_cube_add(size=7,location=(0,0,3.5))
        bpy.context.object.data.materials.append(material)
        camera=ortho_camera(-5,7)
        camera.rotation_euler=(math.pi,0,0)
    else:
        ob=plane(material,7)
        for loop in ob.data.loops:
            point=ob.data.vertices[loop.vertex_index].co
            ob.data.uv_layers.active.data[loop.index].uv=(point.x/.7,point.y/.7)
        ortho_camera(5,7)
    return material


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.out.mkdir(parents=True,exist_ok=True)
    set_project(str(args.project))
    hybrid=HybridSource()
    result=dict(period_correlation={},underside_max={})
    for source in ('mask','hybrid','hybrid-uv'):
        uv_mask=MaskSource(asset_mask('uh4tfagc').path,size_m=.7,mapping='uv',uv_map='UVMap') if source=='hybrid-uv' else None
        _fixture(WearLayer(source='hybrid' if uv_mask else source,mask=uv_mask,
                          extent=WearExtent(enabled=False),hybrid=hybrid))
        value=channel(render(args.out,'period-'+source),'var_surface-grunge')
        result['period_correlation'][source]={}
        for axis in (0,1):
            first=value[:-70,:] if axis==0 else value[:,:-70]
            second=value[70:,:] if axis==0 else value[:,70:]
            result['period_correlation'][source][str(axis)]=float(np.corrcoef(first.ravel(),second.ravel())[0,1])
    for source in ('procedural','mask','hybrid'):
        _fixture(WearLayer(source=source,extent=WearExtent(enabled=False),hybrid=hybrid),down=True)
        value=channel(render(args.out,'underside-'+source),'var_surface-dried-marks')
        result['underside_max'][source]=float(abs(value).max())
        assert result['underside_max'][source]==0
    (args.out/'hybrid-check.json').write_text(json.dumps(result,indent=2))
    raw=result['period_correlation']['mask']
    new=result['period_correlation']['hybrid']
    assert min(raw.values())>.9,raw
    assert max(abs(value) for value in new.values())<.7,new
    assert max(abs(value) for value in result['period_correlation']['hybrid-uv'].values())<.7
    print('HYBRID_PATTERN_AND_UNDERSIDE_PASS',json.dumps(result),flush=True)


if __name__=='__main__':
    main()
