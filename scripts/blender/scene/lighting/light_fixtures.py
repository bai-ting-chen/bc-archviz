"""Light fixtures; implementation for interior."""
import math
from core.archviz import LM_PER_W
from scene.lighting.light_objects import _light_obj, _warm


def downlight(name, loc, lumens=800.0, beam_deg=24.0, kelvin=3000, radius=0.02, blend=0.3, coll=None):
    """Recessed spot pointing straight down. `lumens` = flux inside the beam."""
    ob, ld = _light_obj(name, "SPOT", loc, coll=coll)
    a = math.radians(beam_deg)
    omega = 2 * math.pi * (1 - math.cos(a / 2))
    ld.energy = lumens / LM_PER_W * 4 * math.pi / omega
    ld.spot_size, ld.spot_blend, ld.shadow_soft_size = a, blend, radius
    _warm(ld, kelvin)
    return ob


def led_strip(name, p0, p1, lm_per_m=1000.0, kelvin=2700, width=0.012, normal=(0, 0, -1),
              spread_deg=120.0, coll=None):
    """Linear LED (cove) as a thin rectangular area light from p0 to p1 facing `normal`."""
    from mathutils import Matrix, Vector
    p0, p1, n = Vector(p0), Vector(p1), Vector(normal).normalized()
    length = (p1 - p0).length
    x = (p1 - p0).normalized()
    n = (n - x * n.dot(x)).normalized()                       # aim orthogonal to the strip
    y = (-n).cross(x).normalized()
    m = Matrix((x, y, -n)).transposed()                       # local X along strip, emits along local -Z
    ob, ld = _light_obj(name, "AREA", (p0 + p1) / 2, m.to_euler(), coll=coll)
    ld.shape, ld.size, ld.size_y = "RECTANGLE", length, width
    ld.energy = lm_per_m * length / LM_PER_W
    ld.spread = math.radians(spread_deg)
    _warm(ld, kelvin)
    return ob


def panel_light(name, loc, rot, size=(0.2, 0.2), lumens=500.0, kelvin=3000, spread_deg=180.0, coll=None):
    """Rectangular area light emitting `lumens` (Lambert, `spread_deg` like a louvre)."""
    ob, ld = _light_obj(name, "AREA", loc, rot, coll=coll)
    ld.shape, ld.size, ld.size_y = "RECTANGLE", size[0], size[1]
    ld.energy = lumens / LM_PER_W
    ld.spread = math.radians(spread_deg)
    _warm(ld, kelvin)
    return ob
