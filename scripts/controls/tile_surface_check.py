"""Control: TileSurface builds, every feature toggle changes the render at its tier threshold and restores it,
a 2 x 1 m face map keeps its aspect, resizing tiles keeps the per-tile patches, no unlinked
required sockets. Run: blender -b --factory-startup --python <this>"""
import os, sys, math, shutil, tempfile, struct, zlib, json, warnings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blender"))
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
import _scene
import materials.tile_mapping as tile_mapping
import materials.tile_surface as tile_surface

def scene(mat_kwargs):
    """Create a repeatable wall and light rig for feature comparisons."""
    sc = _scene.black_scene(samples=64, res=256)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=0.6, rotation=(math.pi/2, 0, 0))   # a wall facing -Y
    w = bpy.context.object
    tile_mapping.planar_uv(w)
    mat = tile_surface.tile_material("T", **mat_kwargs); w.data.materials.append(mat)
    sun = bpy.data.objects.new("L", bpy.data.lights.new("L", "AREA"))        # light from above
    sun.data.energy, sun.data.size = 200, 0.5
    sun.location, sun.rotation_euler = (0, -0.4, 0.8), (math.radians(30), 0, 0)
    sc.collection.objects.link(sun)
    cam = _scene.ortho_camera(0, 0.3); cam.location = (0, -2, 0); cam.rotation_euler = (math.pi/2, 0, 0)
    sc.cycles.seed = 1
    return sc, mat

def rel_change(a, b):
    """Return per-pixel relative luminance changes, with a dark-pixel floor."""
    weights = np.array((0.2126, 0.7152, 0.0722))
    lum_a = np.sum(a[..., :3] * weights, axis=-1)
    lum_b = np.sum(b[..., :3] * weights, axis=-1)
    return np.abs(lum_a - lum_b) / np.maximum(lum_b, 1e-3)


def write_stripes(path):
    """Write a linear-designed RGB test map as a correctly encoded sRGB PNG."""
    width, height = 1024, 512
    u, v = np.meshgrid((np.arange(width) + .5) / width, (np.arange(height) + .5) / height)
    linear = np.stack((.2 + .2 * (np.sin(math.tau * 20 * u) > 0),
                       .2 + .2 * (np.sin(math.tau * 10 * v) > 0), np.full_like(u, .3)), axis=-1)
    encoded = np.where(linear <= .0031308, linear * 12.92, 1.055 * linear ** (1/2.4) - .055)
    data = np.round(encoded * 255).astype(np.uint8)
    def chunk(kind, payload):
        """Encode one PNG chunk with its length and checksum."""
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))
    scanlines = b''.join(b'\x00' + row.tobytes() for row in data)
    with open(path, 'wb') as file:
        file.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                   + chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b''))


def emission_probe(mat, node_name, output='Vector'):
    """Render a named actual material signal as linear emission without lighting."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    original = next(link.from_socket for link in out.inputs['Surface'].links)
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(nt.nodes[node_name].outputs[output], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    try:
        return _scene.render_linear()
    finally:
        nt.links.new(original, out.inputs['Surface'])
        nt.nodes.remove(em)


def stripe_cycles(line):
    """Count complete stripe cycles across a probe, allowing partial endpoint stripes."""
    high = line > (np.min(line) + np.max(line)) / 2
    return np.count_nonzero(high[1:] != high[:-1]) / 2


def check_face_contrast(mat, reference, fails):
    """Prove scan contrast endpoints and half-strength variation in linear emission."""
    base_std = np.std(reference[..., :3], axis=(0, 1))
    active = base_std > np.mean(reference[..., :3], axis=(0, 1)) * .01
    tile_surface.set_param(mat, 'face_contrast', 0.)
    flat = emission_probe(mat, 'TileFaceAlbedo')[..., :3]
    flat_ratio = np.std(flat, axis=(0, 1)) / np.maximum(np.mean(flat, axis=(0, 1)), 1e-6)
    if np.any(flat_ratio >= .01):
        fails.append(f'face_contrast=0: std/mean must be <1%, got {flat_ratio}')
    tile_surface.set_param(mat, 'face_contrast', .5)
    half = emission_probe(mat, 'TileFaceAlbedo')[..., :3]
    half_ratio = np.std(half, axis=(0, 1))[active] / np.maximum(base_std[active], 1e-8)
    if not np.any(active) or np.any(np.abs(half_ratio / .5 - 1) > .1):
        fails.append(f'face_contrast=0.5: std must halve within 10%, got {half_ratio}')
    print('TILE_SURFACE_FACE_CONTRAST flat_std/mean', flat_ratio, 'half_std/base', half_ratio)
    tile_surface.set_param(mat, 'face_contrast', 1.)


def check_face_maps(folder, fails):
    """Prove true map scale, aspect, phase stability and normalized linear face albedo."""
    write_stripes(os.path.join(folder, 'stripe_diff.png'))
    with open(os.path.join(folder, 'meta.json'), 'w', encoding='utf-8') as file:
        json.dump({'dimensions_mm': [2000, 1000]}, file)
    sc = _scene.black_scene(samples=1, res=512)
    sc.cycles.filter_width = .01
    bpy.ops.mesh.primitive_plane_add(size=8)
    ob = bpy.context.object
    tile_mapping.planar_uv(ob)
    target = (.3, .35, .4)  # Low contrast avoids clipping; cap behavior is tested separately.
    kwargs = dict(face=folder, tile_w=2., tile_h=1., joint=0., corner_radius=0.,
                  body_albedo=target, off=tile_surface.FEATURES)
    mat = tile_surface.tile_material('FaceProbe', **kwargs)
    ob.data.materials.append(mat)
    _scene.ortho_camera(1., .6, xy=(.5, .5))  # Entire 0.6 m patch lies inside cell (0,0).
    face = emission_probe(mat, 'TileFaceAlbedo')
    for axis, line in (('U', face[256, :, 0]), ('V', face[:, 256, 1])):
        cycles = stripe_cycles(line)
        frequency = cycles / .6
        print(f'TILE_SURFACE_STRIPES {axis} cycles={cycles:.1f} per_m={frequency:.4f}')
        if abs(frequency - 10.) > 1.:
            fails.append(f'map {axis}: expected 10 stripes/metre, got {frequency:.4f}')
    mean = np.mean(face[..., :3], axis=(0, 1))
    print('TILE_SURFACE_FACE_MEAN', *mean)
    if np.any(np.abs(mean / np.asarray(target) - 1) > .02):
        fails.append(f'linear emission face mean {mean} differs from body_albedo by >2%')
    check_face_contrast(mat, face, fails)
    phase_before = emission_probe(mat, 'TileMapUV')
    tile_surface.set_param(mat, 'tile_w', 3.)
    phase_after = emission_probe(mat, 'TileMapUV')
    if np.max(np.abs(phase_before[..., :2] - phase_after[..., :2])) > 1e-5:
        fails.append('resize changed same-cell map-space patch phase')
    after_face = emission_probe(mat, 'TileFaceAlbedo')
    if np.max(np.abs(after_face[..., :3] - face[..., :3])) > 1e-4:
        fails.append('resize changed same-cell sampled face patch')
    # Rebuilding must retain the material datablock and avoid group/image accumulation.
    old_pointer = mat.as_pointer()
    image_ids = {n.image.as_pointer() for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE'}
    counts = (len(bpy.data.materials), len(bpy.data.node_groups), len(bpy.data.images))
    rebuilt = tile_surface.tile_material('FaceProbe', **kwargs)
    if rebuilt.as_pointer() != old_pointer or counts != (len(bpy.data.materials), len(bpy.data.node_groups), len(bpy.data.images)):
        fails.append('repeated build accumulated material, group or image datablocks')
    groups = [g for g in bpy.data.node_groups if g.get('tile_surface_owner') == rebuilt['tile_surface_id']]
    if len(groups) != 1:
        fails.append('repeated build did not leave exactly one owned TileFinish group')
    if image_ids != {n.image.as_pointer() for n in rebuilt.node_tree.nodes if n.type == 'TEX_IMAGE'}:
        fails.append('repeated build did not reuse face images')
    # Exercise every keyword, including structural options and both new real-unit inputs.
    settings = tile_surface._settings(rebuilt)
    for key, value in settings.items():
        tile_surface.set_param(rebuilt, key, value)
    if abs(rebuilt.node_tree.nodes['TileFinish'].inputs['Speck Size'].default_value - .001) > 1e-8:
        fails.append('speck_size did not reach TileFinish')
    disp = next(n for n in rebuilt.node_tree.nodes if n.type == 'DISPLACEMENT')
    if disp.space != 'WORLD':
        fails.append('displacement must use WORLD space')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        tile_surface.set_param(rebuilt, 'body_albedo', (.8, .8, .8))
    capped = emission_probe(rebuilt, 'TileFaceAlbedo')
    if not any('exceeds 0.9' in str(w.message) for w in caught):
        fails.append('high normalized map did not warn about albedo clipping')
    if np.max(capped[..., :3]) > .90001:
        fails.append('normalized face albedo exceeds 0.9 cap')
    return rebuilt

fails = []
sc, mat = scene({})
base = _scene.render_linear()
again = _scene.render_linear()
floor = rel_change(again, base)                            # noise floor, same seed
floor95, floor99 = np.percentile(floor, (95, 99))
print(f"TILE_SURFACE_NOISE p95={floor95:.8f} p99={floor99:.8f}")
print("TILE_SURFACE_FEATURE | p95 off | p99 restore | fraction >0.02 | floor fraction >0.02 | p99.9 off")
for f in (*tile_surface.FEATURES, "lippage"):
    case_base, case_floor = base, floor
    if f == "damage":
        # Sparse default damage may miss this patch; this row proves the toggle at full coverage.
        current = tile_surface._settings(mat)
        saved_damage = {key: current[key] for key in ('damage', 'chip_share', 'crack_share')}
        for key in saved_damage:
            tile_surface.set_param(mat, key, 1.)
        case_base = _scene.render_linear()
        case_floor = rel_change(_scene.render_linear(), case_base)
    if f == "specks":
        # A 1 mm dot is subpixel at 256 px over 0.3 m; use 512 px (~0.6 mm/px).
        # Re-measure baseline and same-seed noise at this resolution before toggling.
        sc.render.resolution_x = sc.render.resolution_y = 512
        case_base = _scene.render_linear()
        case_floor = rel_change(_scene.render_linear(), case_base)
    case_floor95, case_floor99 = np.percentile(case_floor, (95, 99))
    if f == "lippage":
        # Isolate height offsets while retaining the existing tilt and its shared switch.
        saved_lippage = mat.node_tree.nodes['TileFinish'].inputs['Lippage'].default_value
        tile_surface.set_param(mat, 'lippage', 0.)
        off = _scene.render_linear()
        tile_surface.set_param(mat, 'lippage', saved_lippage)
        back = _scene.render_linear()
    else:
        tile_surface.toggle(mat, f, False); off = _scene.render_linear()
        tile_surface.toggle(mat, f, True); back = _scene.render_linear()
    changed = rel_change(off, case_base)
    d, tail = np.percentile(changed, (95, 99.9))
    fraction = float(np.mean(changed > 0.02))
    floor_fraction = float(np.mean(case_floor > 0.02))
    restored = float(np.percentile(rel_change(back, case_base), 99))
    print(f"{f} | {d:.8f} | {restored:.8f} | {fraction:.8f} | {floor_fraction:.8f} | {tail:.8f}")
    if f in ("specks", "damage"):
        # Sparse features (dots ~0.3 % of the face; chips/cracks hug a few arrises even at full
        # coverage): p95 cannot measure their presence, so count changed pixels instead.
        if fraction <= 0.0005 or fraction <= 3 * floor_fraction:
            fails.append(f"{f}: changed fraction {fraction:.8f} must exceed 0.0005 and 3x floor ({floor_fraction:.8f})")
    else:
        # Profile, variation and dust carry the look; tilt, wave and lippage are subtle.
        # Macro is a 3 m field on this 0.3 m patch; its full-scene proof is separate.
        threshold = 0.02 if f in ("profile", "variation", "dust") else 0.002
        if d <= threshold or d <= 3 * case_floor95:
            fails.append(f"{f}: p95 off {d:.6f} must exceed {threshold:.3f} and 3x floor ({case_floor95:.6f})")
    if restored > 3 * case_floor99 + 1e-4:
        fails.append(f"{f}: p99 restore {restored:.6f} exceeds {3 * case_floor99 + 1e-4:.6f}")
    if f == "damage":
        for key, value in saved_damage.items():
            tile_surface.set_param(mat, key, value)
    if f == "specks":
        sc.render.resolution_x = sc.render.resolution_y = 256
# Emission probes use the actual face albedo and coordinate graph, with every feature off.
tmp = tempfile.mkdtemp(prefix="archviz_tile_")
try:
    mat = check_face_maps(tmp, fails)
except Exception:                       # Blender exits 0 after an uncaught script error: fail explicitly
    import traceback
    traceback.print_exc()
    print("TILE_SURFACE_CHECK\n  FAIL\n  exception in check_face_maps")
    sys.exit(1)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
# no required socket left unlinked on the output
out = next(n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL")
if not out.inputs["Surface"].is_linked: fails.append("material output not linked")
if out.inputs["Displacement"].is_linked: fails.append("displacement must stay unconnected (bump first)")
print("TILE_SURFACE_CHECK", "FAIL" if fails else "PASS", *fails, sep="\n  ")
sys.exit(1 if fails else 0)
