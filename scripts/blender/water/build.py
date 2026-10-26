"""One entry point: a free-falling water film with its foot, pool ripples, wet-wall proxy and motion blur
(references/materials/water/water-free-falling-film.md, water-splash.md, water-foam.md, water-ripple.md, wet-surfaces.md).

    from water import build, curtain
    lip = curtain.Lip(origin=(x, y, z_lip), along=(1, 0, 0), out=(0, -1, 0), length=6.0, drop=3.0)
    out = build.falling_film(lip, pool_z=..., film_mat=..., foam_mat=..., pool_mat=..., exr_path=...)

Every scene input comes from the arguments (lip, pool height, materials, file paths): nothing is tied to one scene.
"""
from dataclasses import dataclass, field
from pathlib import Path

import bpy
import numpy as np

from . import curtain, mesh, pool
from . import film as _film, fragments as _frag, foot as _foot, ripple as _ripple, wet as _wet


@dataclass
class Setup:
    """Grid, flow and layer parameters (all with defaults)."""
    cell: float = .0025                     # m film grid
    s_range: tuple = None                   # (s0, s1) m to build a part of the lip (lab strips); None = whole lip
    flow: curtain.Flow = field(default_factory=curtain.Flow)
    film: _film.FilmParams = field(default_factory=_film.FilmParams)
    fragments: _frag.FragmentParams = field(default_factory=_frag.FragmentParams)
    foot: _foot.FootParams = field(default_factory=_foot.FootParams)
    ripple: _ripple.RippleParams = field(default_factory=_ripple.RippleParams)
    wet: _wet.WetParams = field(default_factory=_wet.WetParams)
    motion_shutter: float = .02             # frames; 0 = no motion blur (streak = U * shutter / fps)


def falling_film(lip, pool_z, film_mat, foam_mat=None, pool_mat=None, exr_path=None, wet_proxy=None,
                 setup=None, collection=None, name='Water'):
    """Build the film, strings, drops, foot, pool bump and wet proxy for one lip; returns objects and stats.

    pool_z: receiving surface height. pool_mat: the pool's material (bumped in place; needs exr_path).
    wet_proxy: an existing object whose mesh is replaced in place (keeps every reference to it), or None to skip.
    """
    st = setup or Setup()
    s0, s1 = st.s_range or (0., lip.length)
    s = np.arange(s0, s1 + 1e-9, st.cell); d = np.arange(0., lip.drop + 1e-9, st.cell)
    fs = _film.film_surfaces(lip, st.flow, st.film, s, d)
    objs = {}; stats = dict(torn=float(1 - fs['keep'].mean()), torn_foot=float(1 - fs['keep'][-max(1, len(d) // 40):].mean()),
                            folded=fs['folded'])
    objs['film'] = mesh.film_sheet(f'{name} | film', fs['front'], fs['back'], fs['keep'], film_mat, collection)
    strings, gap_drops = _frag.gap_fill(fs, lip, st.fragments, s, d)
    drops = np.r_[_frag.edge_drops(fs, lip, st.fragments, s, d), gap_drops]
    objs['strings'] = mesh.tubes(f'{name} | strings', strings, film_mat, collection)
    objs['drops'] = mesh.spheroids(f'{name} | drops', drops, film_mat, collection)
    stats.update(strings=len(strings), drops=len(drops))
    if st.motion_shutter:
        mesh.set_velocity(objs['film'], mesh.film_velocity(fs['front'], fs['back'], lip.origin[2], st.flow.v0))
        for k in ('strings', 'drops'): mesh.falling_velocity(objs[k], lip.origin[2], st.flow.v0)
        sc = bpy.context.scene; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = st.motion_shutter
    # foot: impacts from the film's own bottom row and the drops reaching the pool
    bottom = (fs['front'][-1] + fs['back'][-1]) / 2
    pts, strength = _foot.impacts(lip, bottom, fs['keep'][-1], np.linalg.norm(fs['front'][-1] - fs['back'][-1], axis=-1),
                                 drops, pool_z, st.foot)
    thin = mesh.thin_wall_copy(film_mat, f'{name} | thin-wall water')
    V, F = _foot.crowns(pts, strength, st.foot); objs['crowns'] = mesh.from_arrays(f'{name} | crowns', V, F, thin, collection)
    V, F = _foot.bubbles(lip, pts, strength, pool_z, st.foot); objs['bubbles'] = mesh.from_arrays(f'{name} | bubbles', V, F, thin, collection)
    V, F = _foot.foam(lip, pts, strength, pool_z, st.foot)
    objs['foam'] = mesh.from_arrays(f'{name} | foam', V, F, foam_mat or film_mat, collection, smooth=False)
    objs['splash'] = mesh.spheroids(f'{name} | splash', _foot.splash(lip, pts, strength, pool_z, st.foot), film_mat, collection)
    stats['impacts'] = len(pts)
    if pool_mat is not None and exr_path is not None and len(pts):
        o_ax, a_ax, H = _ripple.height_field(lip, pts, strength, st.ripple)
        img = pool.save_height_exr(H, Path(exr_path))
        pool.install_bump(pool_mat, img, lip, (o_ax[0], o_ax[-1]), (a_ax[0], a_ax[-1]))
        stats['ripple_mm'] = pool.readback_mm(img); stats['ripple_slope_rad'] = _ripple.slope_stats(H, st.ripple.step)
    if wet_proxy is not None:
        V, F = _wet.proxy(lip, pool_z, st.wet)
        M = np.array(wet_proxy.matrix_world.inverted())                  # world -> the proxy's local space
        V = V @ M[:3, :3].T + M[:3, 3]
        old = wet_proxy.data; new = bpy.data.meshes.new(f'{name} | wet proxy')
        new.from_pydata(V.tolist(), [], F.tolist()); new.update(); wet_proxy.data = new
        if old.users == 0: bpy.data.meshes.remove(old)
        stats['wet_proxy_faces'] = len(new.polygons)
    return objs, stats
