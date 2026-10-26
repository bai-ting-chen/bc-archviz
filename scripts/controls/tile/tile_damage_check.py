"""Packed, bounded headless acceptance probes; --only SECTION, --full for slow evidence.

Runner only: each section lives in its own module (RULES GOV_04):
    tile_damage_rig          scene set-up, packed EXR probe, aligned tile grids (shared)
    tile_damage_geometry     pixel-mask helpers (shared)
    tile_damage_crack        crack network
    tile_damage_pieces       piece planes
    tile_damage_chips        chips, flakes, spalls and the glaze step
    tile_damage_layout       square tiles, rotation/jitter, fraction rate
    tile_damage_switches     damage on/off in the render
    tile_damage_upgrade      v6 -> v7 damage group upgrade
    tile_damage_displacement true displacement of the damage
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'blender'))
sys.path.insert(0, str(HERE))
import materials.tile.tile_damage as tile_damage  # noqa: E402
from tile_damage_chips import check_chips, check_flakes, check_spalls
from tile_damage_crack import check_crack
from tile_damage_displacement import check_chip_displacement, check_damage_displacement, check_displacement
from tile_damage_layout import check_rate, check_rotated, check_square
from tile_damage_pieces import check_pieces
from tile_damage_switches import check_onoff
from tile_damage_upgrade import check_upgrade

SECTIONS=dict(rate=check_rate,crack=check_crack,pieces=check_pieces,chips=check_chips,
              flakes=check_flakes,spalls=check_spalls,square=check_square,rotated=check_rotated,
              onoff=check_onoff,displacement=check_displacement,damage_displacement=check_damage_displacement,
              chip_displacement=check_chip_displacement,
              upgrade=check_upgrade)
# Chip look is still in development (not approved): these sections report WIP warnings, never a failure.
WIP=('chips','flakes','chip_displacement','rotated')   # rotated = chip containment under rotation/jitter


def main(args):
    """Run each selected section once, retaining failures and timings in one report."""
    args.output.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter(); metrics={}; failures=[]; wip=[]
    group=tile_damage.damage_group()
    metrics['nodes']=len(group.nodes)
    metrics['white_noise_nodes']=sum(n.bl_idname=='ShaderNodeTexWhiteNoise' for n in group.nodes)
    metrics['voronoi_nodes']=sum(n.bl_idname=='ShaderNodeTexVoronoi' for n in group.nodes)
    if metrics['nodes']>800 or metrics['white_noise_nodes']>40 or metrics['voronoi_nodes']>8:
        failures.append('node budget: '+str({k:metrics[k] for k in ('nodes','white_noise_nodes','voronoi_nodes')}))
    for name in ([args.only] if args.only else SECTIONS):
        folder=args.output/name; folder.mkdir(exist_ok=True)
        tick=time.perf_counter()
        try:
            result=SECTIONS[name](folder,args.full) if name.endswith('displacement') else SECTIONS[name](folder)
            metrics.update(result or {})
            print('TILE_DAMAGE_SECTION_PASS',name,flush=True)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            (wip if name in WIP else failures).append(f'{name}: {exc}')
            if name in WIP: print('TILE_DAMAGE_SECTION_WIP',name,flush=True)
        metrics[name+'_seconds']=round(time.perf_counter()-tick,3)
    metrics['wall_seconds']=round(time.perf_counter()-start,3)
    metrics['failures']=failures
    metrics['wip_warnings']=wip
    (args.output/('metrics_'+(args.only or 'all')+'.json')).write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print('TILE_DAMAGE_'+('FAIL' if failures else 'PASS'),json.dumps(metrics),flush=True)
    return bool(failures)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--only',choices=SECTIONS)
    parser.add_argument('--full',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    sys.exit(main(args))
