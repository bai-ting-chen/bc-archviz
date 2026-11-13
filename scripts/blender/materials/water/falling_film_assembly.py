"""One entry point: a free-falling water film with its foot, pool ripples, wet-wall proxy and motion blur
(references/materials/water/water-free-falling-film.md and the files it links).

    from materials.water import falling_film_assembly, ballistic_sheet
    lip = ballistic_sheet.LaunchLip(origin_m=(x, y, z_lip), along_axis=(1, 0, 0), outward_axis=(0, -1, 0), length_m=6.0, drop_m=3.0)
    objects, stats = falling_film_assembly.falling_film(lip, pool_height_m, film_mat, foam_mat, pool_mat, exr_path, wet_proxy)

Every scene input comes from the arguments (lip, pool height, materials, file paths, proxy object).
"""
from dataclasses import dataclass, field
from pathlib import Path

import bpy
import numpy as np

from materials.water import ballistic_sheet, mesh_builders, motion_blur, surface_shading
from materials.water import falling_film as _film, film_fragments as _fragments, pool_impacts as _foot, pool_ripples as _ripple, wet_wall_proxy as _wet


@dataclass
class FallingFilmSetup:
    """Grid, flow and every layer's parameters (all with starting-value defaults)."""
    film_cell_m: float = .0025                     # m film grid
    along_lip_range_m: tuple = None                   # (s0, s1) m: build part of the lip (lab strips); None = whole lip
    flow: ballistic_sheet.SheetFlow = field(default_factory=ballistic_sheet.SheetFlow)
    film: _film.FilmParams = field(default_factory=_film.FilmParams)
    fragments: _fragments.FragmentParams = field(default_factory=_fragments.FragmentParams)
    impacts: _foot.ImpactParams = field(default_factory=_foot.ImpactParams)
    pool_ripples: _ripple.RippleParams = field(default_factory=_ripple.RippleParams)
    wet_wall: _wet.WetParams = field(default_factory=_wet.WetParams)
    motion_shutter_frames: float = .02             # frames; 0 = no motion blur


def _film_objects(lip, st, film_mat, collection, name):
    """Film sheet, strings and drops; returns objects, the film fields, all drops and stats."""
    s0, s1 = st.along_lip_range_m or (0., lip.length_m)
    s = np.arange(s0, s1 + 1e-9, st.film_cell_m)
    d = np.arange(0., lip.drop_m + 1e-9, st.film_cell_m)
    ff = _film.film_surfaces(lip, st.flow, st.film, s, d)
    strings, gap_drops = _fragments.gap_fill(ff, lip, st.fragments, s, d)
    drops = np.r_[_fragments.edge_drops(ff, lip, st.fragments, s, d), gap_drops]
    objs = {
        'film': mesh_builders.film_sheet(f'{name} | film', ff.front, ff.back, ff.keep, film_mat, collection),
        'strings': mesh_builders.tubes(f'{name} | strings', strings, film_mat, collection),
        'drops': mesh_builders.spheroids(f'{name} | drops', drops, film_mat, collection),
    }
    foot_rows = max(1, len(d) // 40)
    stats = dict(torn=float(1 - ff.keep.mean()), torn_foot=float(1 - ff.keep[-foot_rows:].mean()),
                 folded=ff.folded_fraction, strings=len(strings), drops=len(drops))
    return objs, ff, drops, stats


def _add_motion_blur(objs, ff, lip, st):
    lip_z = lip.origin_m[2]
    motion_blur.set_velocity(objs['film'], motion_blur.film_velocity(ff.front, ff.back, lip_z, st.flow.launch_speed_m_s))
    for key in ('strings', 'drops'):
        motion_blur.falling_velocity(objs[key], lip_z, st.flow.launch_speed_m_s)
    motion_blur.enable_motion_blur(bpy.context.scene, st.motion_shutter_frames)


def _foot_objects(lip, st, ff, drops, pool_height_m, film_mat, foam_mat, collection, name):
    """Impacts from the film's bottom row and the drops, then crowns, bubbles, foam and splash."""
    bottom_mid = (ff.front[-1] + ff.back[-1]) / 2
    bottom_thick = np.linalg.norm(ff.front[-1] - ff.back[-1], axis=-1)
    pts, strength = _foot.impacts(lip, bottom_mid, ff.keep[-1], bottom_thick, drops, pool_height_m, st.impacts)
    thin = surface_shading.thin_wall_copy(film_mat, f'{name} | thin-wall water')
    objs = {
        'crowns': mesh_builders.from_arrays(f'{name} | crowns', *_foot.crowns(pts, strength, st.impacts), thin, collection),
        'bubbles': mesh_builders.from_arrays(f'{name} | bubbles', *_foot.bubbles(lip, pts, strength, pool_height_m, st.impacts),
                                    thin, collection),
        'foam': mesh_builders.from_arrays(f'{name} | foam', *_foot.foam(lip, pts, strength, pool_height_m, st.impacts),
                                 foam_mat or film_mat, collection, smooth=False),
        'splash': mesh_builders.spheroids(f'{name} | splash', _foot.splash(lip, pts, strength, pool_height_m, st.impacts),
                                 film_mat, collection),
    }
    return objs, pts, strength


def _pool_ripples(lip, st, pts, strength, pool_mat, exr_path):
    """Ripple height field -> EXR -> bump on the pool material; returns stats."""
    s_axis, o_axis, H = _ripple.height_field(lip, pts, strength, st.pool_ripples)
    image = surface_shading.save_height_exr(H, Path(exr_path))
    surface_shading.install_bump(pool_mat, image, lip, (s_axis[0], s_axis[-1]), (o_axis[0], o_axis[-1]))
    return dict(ripple_mm=surface_shading.height_range_mm(image), ripple_slope_rad=_ripple.slope_stats(H, st.pool_ripples.cell_m))


def _replace_wet_proxy(lip, st, pool_height_m, proxy, name):
    """Replace the proxy's mesh in place (every reference to the object stays valid); vertices in its local space."""
    verts, faces = _wet.build_proxy(lip, pool_height_m, st.wet_wall)
    to_local = np.array(proxy.matrix_world.inverted())
    verts = verts @ to_local[:3, :3].T + to_local[:3, 3]
    old = proxy.data
    new = bpy.data.meshes.new(f'{name} | wet proxy')
    new.from_pydata(verts.tolist(), [], faces.tolist())
    new.update()
    proxy.data = new
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return dict(wet_proxy_faces=len(new.polygons))


def falling_film(lip, pool_height_m, film_mat, foam_mat=None, pool_mat=None, exr_path=None, wet_proxy=None,
                 setup=None, collection=None, name='Water'):
    """Build film, strings, drops, foot, pool bump and wet proxy for one lip; returns (objects dict, stats dict).

    pool_height_m: receiving surface height. pool_mat + exr_path: bump the pool's material in place (both or neither).
    wet_proxy: an existing object whose mesh is replaced in place, or None to skip.
    """
    st = setup or FallingFilmSetup()
    objs, ff, drops, stats = _film_objects(lip, st, film_mat, collection, name)
    if st.motion_shutter_frames:
        _add_motion_blur(objs, ff, lip, st)
    foot_objs, pts, strength = _foot_objects(lip, st, ff, drops, pool_height_m, film_mat, foam_mat, collection, name)
    objs.update(foot_objs)
    stats['impacts'] = len(pts)
    if pool_mat is not None and exr_path is not None and len(pts):
        stats.update(_pool_ripples(lip, st, pts, strength, pool_mat, exr_path))
    if wet_proxy is not None:
        stats.update(_replace_wet_proxy(lip, st, pool_height_m, wet_proxy, name))
    return objs, stats
