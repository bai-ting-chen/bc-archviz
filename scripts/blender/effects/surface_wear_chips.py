"""Resolve bare-substrate signals verified against each flaked-paint scan's BaseColor."""
from dataclasses import replace
from effects.surface_wear_masks import asset_mask

# Pale exposed substrate is rougher in the first scan; green substrate is smoother in the second.
WORN_SCAN_LEVELS={'tmulfghdy':('Roughness',.80,.85,False),
                  'ub1meemn':('Roughness',.65,.72,True)}


def flaked_paint_masks(asset_ids=tuple(WORN_SCAN_LEVELS),project=None):
    """Resolve per-scan Roughness polarity: white is exposed substrate, black is intact paint."""
    result=[]
    for asset_id in asset_ids:
        map_name,black,white,invert=WORN_SCAN_LEVELS[asset_id]
        mask=asset_mask(asset_id,map_name,project)
        result.append(replace(mask,black=black,white=white,invert=invert) if mask is not None else None)
    return result


