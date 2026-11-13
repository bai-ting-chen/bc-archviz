"""Deterministic water fields and mesh readback for the module-boundary regression control."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
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
    from materials.water import falling_film_assembly, ballistic_sheet, falling_film, pool_impacts, film_fragments, mesh_builders, motion_blur, pool_ripples, surface_shading, wet_wall_proxy
    lip = ballistic_sheet.LaunchLip((1., 2., 2.35), (.866, .5, 0), (.5, -.866, 0), 1.2, 2.4)
    flow = ballistic_sheet.SheetFlow()
    s, d = np.linspace(0, lip.length_m, 121), np.linspace(0, lip.drop_m, 241)
    ff = falling_film.film_surfaces(lip, flow, falling_film.FilmParams(), s, d)
    result = {k: array(v) for k, v in vars(ff).items()}
    strings, drops = film_fragments.gap_fill(ff, lip, film_fragments.FragmentParams(), s, d)
    edge = film_fragments.edge_drops(ff, lip, film_fragments.FragmentParams(), s, d)
    result['strings'] = [array(v) for v in strings]
    result['drops'], result['edge'] = array(drops), array(edge)
    pts, strength = pool_impacts.impacts(lip, (ff.front[-1] + ff.back[-1]) / 2, ff.keep[-1],
                                np.linalg.norm(ff.front[-1] - ff.back[-1], axis=-1), drops, -.05, pool_impacts.ImpactParams())
    result['impacts'], result['strength'] = array(pts), array(strength)
    for key, geometry in dict(crowns=pool_impacts.crowns(pts, strength, pool_impacts.ImpactParams()),
                              foam=pool_impacts.foam(lip, pts, strength, -.05, pool_impacts.ImpactParams()),
                              bubbles=pool_impacts.bubbles(lip, pts, strength, -.05, pool_impacts.ImpactParams())).items():
        result[key] = [array(geometry[0]), geometry[1]]
    result['splash'] = array(pool_impacts.splash(lip, pts, strength, -.05, pool_impacts.ImpactParams()))
    for key, geometry in dict(sheet=mesh_builders.film_sheet('numeric sheet', ff.front, ff.back, ff.keep),
                              tubes=mesh_builders.tubes('numeric tubes', strings[:3]),
                              drops=mesh_builders.spheroids('numeric drops', drops[:4]),
                              empty_tubes=mesh_builders.tubes('empty tubes', []),
                              empty_drops=mesh_builders.spheroids('empty drops', [])).items():
        result[key] = object_mesh(geometry)
    for key, values in dict(crowns=pool_impacts.crowns(np.zeros((0, 3)), np.zeros(0), pool_impacts.ImpactParams()),
                            foam=pool_impacts.foam(lip, np.zeros((0, 3)), np.zeros(0), -.05, pool_impacts.ImpactParams()),
                            bubbles=pool_impacts.bubbles(lip, np.zeros((0, 3)), np.zeros(0), -.05, pool_impacts.ImpactParams())).items():
        result['empty_' + key] = [array(values[0]), values[1]]
    rp = pool_ripples.RippleParams(cell_m=.03)
    sa, oa, H = pool_ripples.height_field(lip, pts, strength, rp)
    result['ripple'] = [array(sa), array(oa), array(H), pool_ripples.slope_stats(H, rp.cell_m)]
    result['wet'] = [array(v) for v in wet_wall_proxy.build_proxy(lip, -.05, wet_wall_proxy.WetParams())]
    mat = bpy.data.materials.new('numeric water')
    mat.use_nodes = True
    pool = mat.copy()
    pool.name = 'numeric pool'
    proxy = bpy.data.objects.new('numeric wet proxy', bpy.data.meshes.new('numeric wet proxy'))
    bpy.context.scene.collection.objects.link(proxy)
    objs, stats = falling_film_assembly.falling_film(lip, -.05, mat, pool_mat=pool, exr_path=out / 'numeric_ripple.exr',
                                    wet_proxy=proxy, setup=falling_film_assembly.FallingFilmSetup(film_cell_m=.02), name='numeric build')
    result['build'] = dict(stats=stats, objects={k: object_mesh(v) for k, v in objs.items()},
                           pool=dump_material(pool), proxy=object_mesh(proxy))
    result['thin_wall'] = dump_material(surface_shading.thin_wall_copy(mat, 'numeric thin wall'))
    return result
