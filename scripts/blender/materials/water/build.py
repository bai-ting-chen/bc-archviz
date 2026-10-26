"""One entry point: a free-falling water film with its foot, pool ripples, wet-wall proxy and motion blur
(references/materials/water/water-free-falling-film.md and the files it links).

    from materials.water import build, curtain
    lip = curtain.Lip(origin=(x, y, z_lip), along=(1, 0, 0), out=(0, -1, 0), length=6.0, drop=3.0)
    objects, stats = build.falling_film(lip, pool_z, film_mat, foam_mat, pool_mat, exr_path, wet_proxy)

Every scene input comes from the arguments (lip, pool height, materials, file paths, proxy object).
"""
from dataclasses import dataclass, field
from pathlib import Path

import bpy
import numpy as np

from materials.water import curtain, mesh, motion, shading
from materials.water import film as _film, fragments as _fragments, foot as _foot, ripple as _ripple, wet as _wet


@dataclass
class Setup:
    """Grid, flow and every layer's parameters (all with starting-value defaults)."""
    cell: float = .0025                     # m film grid
    s_range: tuple = None                   # (s0, s1) m: build part of the lip (lab strips); None = whole lip
    flow: curtain.Flow = field(default_factory=curtain.Flow)
    film: _film.FilmParams = field(default_factory=_film.FilmParams)
    fragments: _fragments.FragmentParams = field(default_factory=_fragments.FragmentParams)
    foot: _foot.FootParams = field(default_factory=_foot.FootParams)
    ripple: _ripple.RippleParams = field(default_factory=_ripple.RippleParams)
    wet: _wet.WetParams = field(default_factory=_wet.WetParams)
    motion_shutter: float = .02             # frames; 0 = no motion blur


def _film_objects(lip, st, film_mat, collection, name):
    """Film sheet, strings and drops; returns objects, the film fields, all drops and stats."""
    s0, s1 = st.s_range or (0., lip.length)
    s = np.arange(s0, s1 + 1e-9, st.cell)
    d = np.arange(0., lip.drop + 1e-9, st.cell)
    ff = _film.film_surfaces(lip, st.flow, st.film, s, d)
    strings, gap_drops = _fragments.gap_fill(ff, lip, st.fragments, s, d)
    drops = np.r_[_fragments.edge_drops(ff, lip, st.fragments, s, d), gap_drops]
    objs = {
        'film': mesh.film_sheet(f'{name} | film', ff.front, ff.back, ff.keep, film_mat, collection),
        'strings': mesh.tubes(f'{name} | strings', strings, film_mat, collection),
        'drops': mesh.spheroids(f'{name} | drops', drops, film_mat, collection),
    }
    foot_rows = max(1, len(d) // 40)
    stats = dict(torn=float(1 - ff.keep.mean()), torn_foot=float(1 - ff.keep[-foot_rows:].mean()),
                 folded=ff.folded, strings=len(strings), drops=len(drops))
    return objs, ff, drops, stats


def _add_motion_blur(objs, ff, lip, st):
    lip_z = lip.origin[2]
    motion.set_velocity(objs['film'], motion.film_velocity(ff.front, ff.back, lip_z, st.flow.v0))
    for key in ('strings', 'drops'):
        motion.falling_velocity(objs[key], lip_z, st.flow.v0)
    motion.enable(bpy.context.scene, st.motion_shutter)


def _foot_objects(lip, st, ff, drops, pool_z, film_mat, foam_mat, collection, name):
    """Impacts from the film's bottom row and the drops, then crowns, bubbles, foam and splash."""
    bottom_mid = (ff.front[-1] + ff.back[-1]) / 2
    bottom_thick = np.linalg.norm(ff.front[-1] - ff.back[-1], axis=-1)
    pts, strength = _foot.impacts(lip, bottom_mid, ff.keep[-1], bottom_thick, drops, pool_z, st.foot)
    thin = shading.thin_wall_copy(film_mat, f'{name} | thin-wall water')
    objs = {
        'crowns': mesh.from_arrays(f'{name} | crowns', *_foot.crowns(pts, strength, st.foot), thin, collection),
        'bubbles': mesh.from_arrays(f'{name} | bubbles', *_foot.bubbles(lip, pts, strength, pool_z, st.foot),
                                    thin, collection),
        'foam': mesh.from_arrays(f'{name} | foam', *_foot.foam(lip, pts, strength, pool_z, st.foot),
                                 foam_mat or film_mat, collection, smooth=False),
        'splash': mesh.spheroids(f'{name} | splash', _foot.splash(lip, pts, strength, pool_z, st.foot),
                                 film_mat, collection),
    }
    return objs, pts, strength


def _pool_ripples(lip, st, pts, strength, pool_mat, exr_path):
    """Ripple height field -> EXR -> bump on the pool material; returns stats."""
    s_axis, o_axis, H = _ripple.height_field(lip, pts, strength, st.ripple)
    image = shading.save_height_exr(H, Path(exr_path))
    shading.install_bump(pool_mat, image, lip, (s_axis[0], s_axis[-1]), (o_axis[0], o_axis[-1]))
    return dict(ripple_mm=shading.readback_mm(image), ripple_slope_rad=_ripple.slope_stats(H, st.ripple.step))


def _replace_wet_proxy(lip, st, pool_z, proxy, name):
    """Replace the proxy's mesh in place (every reference to the object stays valid); vertices in its local space."""
    verts, faces = _wet.proxy(lip, pool_z, st.wet)
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


def falling_film(lip, pool_z, film_mat, foam_mat=None, pool_mat=None, exr_path=None, wet_proxy=None,
                 setup=None, collection=None, name='Water'):
    """Build film, strings, drops, foot, pool bump and wet proxy for one lip; returns (objects dict, stats dict).

    pool_z: receiving surface height. pool_mat + exr_path: bump the pool's material in place (both or neither).
    wet_proxy: an existing object whose mesh is replaced in place, or None to skip.
    """
    st = setup or Setup()
    objs, ff, drops, stats = _film_objects(lip, st, film_mat, collection, name)
    if st.motion_shutter:
        _add_motion_blur(objs, ff, lip, st)
    foot_objs, pts, strength = _foot_objects(lip, st, ff, drops, pool_z, film_mat, foam_mat, collection, name)
    objs.update(foot_objs)
    stats['impacts'] = len(pts)
    if pool_mat is not None and exr_path is not None and len(pts):
        stats.update(_pool_ripples(lip, st, pts, strength, pool_mat, exr_path))
    if wet_proxy is not None:
        stats.update(_replace_wet_proxy(lip, st, pool_z, wet_proxy, name))
    return objs, stats
