"""Pixel-mask helpers for the tile damage probes: neighbourhoods, boundaries, connected bands,
blurs and local line directions. Pure numpy, no Blender.
"""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import numpy as np


def dilate(mask, radius=1):
    """Chebyshev neighbourhood without wrapping across the image boundary."""
    pad = np.pad(mask, radius)
    return np.logical_or.reduce([pad[radius+dy:radius+dy+mask.shape[0], radius+dx:radius+dx+mask.shape[1]]
                                 for dy in range(-radius,radius+1) for dx in range(-radius,radius+1)])


def boundary(mask):
    """Return the inner four-neighbour boundary."""
    p = np.pad(mask, 1)
    return mask & ~(p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:])


def components(mask):
    """Count connected eight-neighbour pixel bands."""
    remaining = set(zip(*np.nonzero(mask))); sizes = []
    while remaining:
        stack = [remaining.pop()]; size = 0
        while stack:
            y, x = stack.pop(); size += 1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    q = (y+dy,x+dx)
                    if q in remaining: remaining.remove(q); stack.append(q)
        sizes.append(size)
    return sizes


def box_blur(field,radius):
    """Mean over a (2r+1)^2 window via cumulative sums, edges padded by reflection."""
    p=np.pad(field,radius+1,mode='reflect'); c=p.cumsum(0).cumsum(1); k=2*radius+1
    return (c[k:,k:]-c[:-k,k:]-c[k:,:-k]+c[:-k,:-k])[:field.shape[0],:field.shape[1]]/k/k


def local_directions(mask,radius=4):
    """Line direction (deg, 0-180) at each mask pixel from the structure tensor of its neighbourhood."""
    f=box_blur(mask.astype(float),1)
    gy,gx=np.gradient(f)
    jxx,jxy,jyy=(box_blur(v,radius) for v in (gx*gx,gx*gy,gy*gy))
    gradient=.5*np.degrees(np.arctan2(2*jxy,jxx-jyy))
    return (gradient+90)%180
