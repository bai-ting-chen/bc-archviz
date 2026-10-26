"""Deterministic water fields and mesh readback for the module-boundary regression control."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import hashlib

import bpy
import numpy as np

from graph_dump import dump_material


def array(value):
    """Fingerprint every numeric value, retaining shape and type."""
    a = np.asarray(value)
    assert np.isfinite(a).all()
    return dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest())


def object_mesh(ob):
    """Read mesh coordinates, topology, smoothing and velocity back from Blender."""
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    loops = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get('vertex_index', loops)
    sizes = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get('loop_total', sizes)
    smooth = np.empty(len(me.polygons), bool)
    me.polygons.foreach_get('use_smooth', smooth)
    result = dict(vertices=array(co), loops=array(loops), sizes=array(sizes), smooth=array(smooth))
    if 'velocity' in me.attributes:
        vel = np.empty(len(me.vertices) * 3, np.float32)
        me.attributes['velocity'].data.foreach_get('vector', vel)
        result['velocity'] = array(vel)
    return result


def check(out):
    """Exercise water layers, assembly, image roundtrip and empty geometry paths."""
    from materials.water import build, curtain, film, foot, fragments, mesh, motion, ripple, shading, wet
    lip = curtain.Lip((1., 2., 2.35), (.866, .5, 0), (.5, -.866, 0), 1.2, 2.4)
    flow = curtain.Flow()
    s, d = np.linspace(0, lip.length, 121), np.linspace(0, lip.drop, 241)
    ff = film.film_surfaces(lip, flow, film.FilmParams(), s, d)
    result = {k: array(v) for k, v in vars(ff).items()}
    strings, drops = fragments.gap_fill(ff, lip, fragments.FragmentParams(), s, d)
    edge = fragments.edge_drops(ff, lip, fragments.FragmentParams(), s, d)
    result['strings'] = [array(v) for v in strings]
    result['drops'], result['edge'] = array(drops), array(edge)
    pts, strength = foot.impacts(lip, (ff.front[-1] + ff.back[-1]) / 2, ff.keep[-1],
                                np.linalg.norm(ff.front[-1] - ff.back[-1], axis=-1), drops, -.05, foot.FootParams())
    result['impacts'], result['strength'] = array(pts), array(strength)
    for key, geometry in dict(crowns=foot.crowns(pts, strength, foot.FootParams()),
                              foam=foot.foam(lip, pts, strength, -.05, foot.FootParams()),
                              bubbles=foot.bubbles(lip, pts, strength, -.05, foot.FootParams())).items():
        result[key] = [array(geometry[0]), geometry[1]]
    result['splash'] = array(foot.splash(lip, pts, strength, -.05, foot.FootParams()))
    for key, geometry in dict(sheet=mesh.film_sheet('numeric sheet', ff.front, ff.back, ff.keep),
                              tubes=mesh.tubes('numeric tubes', strings[:3]),
                              drops=mesh.spheroids('numeric drops', drops[:4]),
                              empty_tubes=mesh.tubes('empty tubes', []),
                              empty_drops=mesh.spheroids('empty drops', [])).items():
        result[key] = object_mesh(geometry)
    for key, values in dict(crowns=foot.crowns(np.zeros((0, 3)), np.zeros(0), foot.FootParams()),
                            foam=foot.foam(lip, np.zeros((0, 3)), np.zeros(0), -.05, foot.FootParams()),
                            bubbles=foot.bubbles(lip, np.zeros((0, 3)), np.zeros(0), -.05, foot.FootParams())).items():
        result['empty_' + key] = [array(values[0]), values[1]]
    rp = ripple.RippleParams(step=.03)
    sa, oa, H = ripple.height_field(lip, pts, strength, rp)
    result['ripple'] = [array(sa), array(oa), array(H), ripple.slope_stats(H, rp.step)]
    result['wet'] = [array(v) for v in wet.proxy(lip, -.05, wet.WetParams())]
    mat = bpy.data.materials.new('numeric water')
    mat.use_nodes = True
    pool = mat.copy()
    pool.name = 'numeric pool'
    proxy = bpy.data.objects.new('numeric wet proxy', bpy.data.meshes.new('numeric wet proxy'))
    bpy.context.scene.collection.objects.link(proxy)
    objs, stats = build.falling_film(lip, -.05, mat, pool_mat=pool, exr_path=out / 'numeric_ripple.exr',
                                    wet_proxy=proxy, setup=build.Setup(cell=.02), name='numeric build')
    result['build'] = dict(stats=stats, objects={k: object_mesh(v) for k, v in objs.items()},
                           pool=dump_material(pool), proxy=object_mesh(proxy))
    result['thin_wall'] = dump_material(shading.thin_wall_copy(mat, 'numeric thin wall'))
    return result
