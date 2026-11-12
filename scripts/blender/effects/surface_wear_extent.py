"""Location and patch extents shared by every surface-wear source."""
from dataclasses import dataclass


@dataclass
class WearExtent:
    """World-metre wear location; edge_distance is a clean-mesh distance socket when available."""
    enabled: bool = True
    floor_z_m: float = 0.
    foot_height_m: float = .7
    soffit_edge_m: float = .18
    patch_scale_m: float = 2.3
    edge_distance: object = None
    foot_full_m: float = .02
    patch_black: float = .46
    patch_white: float = .66
    drip_top_m: float | None = None
    drip_length_m: float = 1.


def face_z(g, frame=None):
    """Return world shading-normal Z, independent of the projected mask coordinates."""
    geometry = g.node('ShaderNodeNewGeometry', (-6000, -9000), frame)
    xyz = g.node('ShaderNodeSeparateXYZ', (-5800, -9000), frame)
    g.link(geometry.outputs['Normal'], xyz.inputs[0])
    return xyz.outputs['Z']


def patch_extent(g, vector, scale_m, frame=None, black=.46, white=.66):
    """Return a slow patch field with real zero regions, rather than uniform modulation."""
    noise = g.noise(vector, 1/scale_m, (-5600, -10000), frame, detail=2, rough=.55)
    return g.range(noise, black, white, (-5300, -10000), frame=frame, smooth=True)


def location_extent(g, kind, settings, frame=None):
    """Gate feet, floor patches and supplied soffit-edge distances; dried marks exclude undersides."""
    nz = face_z(g, frame)
    eligible = g.math('GREATER_THAN', nz, -.001, (-5500, -9200), frame) if kind == 'dried-marks' else 1
    if not settings.enabled:
        return eligible
    geo = g.node('ShaderNodeNewGeometry', (-6000, -10500), frame)
    pos = g.node('ShaderNodeSeparateXYZ', (-5800, -10500), frame)
    g.link(geo.outputs['Position'], pos.inputs[0])
    height = g.math('SUBTRACT', pos.outputs['Z'], settings.floor_z_m, (-5500, -10500), frame)
    foot = g.range(height, settings.foot_full_m, settings.foot_height_m, (-5200, -10500), tmin=1, tmax=0,
                   frame=frame, smooth=True)
    absz = g.math('ABSOLUTE', nz, 0, (-5500, -10800), frame)
    vertical = g.range(absz, .1, .55, (-5200, -10800), tmin=1, tmax=0, frame=frame)
    up = g.range(nz, .35, .85, (-5200, -11100), frame=frame)
    wall_foot = g.math('MULTIPLY', foot, vertical, (-4900, -10500), frame)
    drips = 0
    if settings.drip_top_m is not None:
        drips = g.range(pos.outputs['Z'], settings.drip_top_m-settings.drip_length_m,
                        settings.drip_top_m, (-4900,-11700), frame=frame, smooth=True)
        below = g.math('LESS_THAN',pos.outputs['Z'],settings.drip_top_m,(-5200,-11700),frame)
        drips = g.math('MULTIPLY',drips,below,(-4600,-11700),frame)
        drips = g.math('MULTIPLY',drips,vertical,(-4300,-11700),frame)
    if kind == 'worn-through':
        location = wall_foot
    elif kind == 'grunge':
        edge = 0
        if settings.edge_distance is not None:
            band = g.range(settings.edge_distance, .015, settings.soffit_edge_m,
                           (-5200, -11400), tmin=1, tmax=0, frame=frame, smooth=True)
            down = g.math('LESS_THAN', nz, -.5, (-5500, -11400), frame)
            edge = g.math('MULTIPLY', band, down, (-4900, -11400), frame)
        floor = g.math('MULTIPLY', up, .16, (-4900, -11100), frame)  # faint floor dirt
        location = g.math('MAXIMUM', wall_foot, floor, (-4600, -10500), frame)
        location = g.math('MAXIMUM', location, edge, (-4300, -10500), frame)
        location = g.math('MAXIMUM', location, drips, (-4000,-11700), frame)
    elif kind == 'dried-marks':
        wall = g.math('MAXIMUM', foot, .12, (-4900, -10800), frame)  # occasional wall marks above feet
        wall = g.math('MULTIPLY', wall, vertical, (-4600, -10800), frame)
        floor = g.math('MULTIPLY', up, .45, (-4900, -11100), frame)
        location = g.math('MAXIMUM', wall, floor, (-4300, -10800), frame)
        location = g.math('MAXIMUM',location,drips,(-4000,-11700),frame)
    else:
        location = g.math('MAXIMUM', wall_foot, .15, (-4300, -10800), frame)
    patch = patch_extent(g, geo.outputs['Position'], settings.patch_scale_m, frame,
                         settings.patch_black, settings.patch_white)
    extent = g.math('MULTIPLY', location, patch, (-4000, -10500), frame)
    return g.math('MULTIPLY', extent, eligible, (-3700, -10500), frame)
