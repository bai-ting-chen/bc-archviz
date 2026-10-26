"""Layout reference; canonical implementation behind tile_layout."""

import numpy as np

from materials.tile.layout_config import _JITTER_SEEDS

def _white_noise(col, row, seed):
    """Mirror Cycles hash_float3_to_float (Jenkins lookup3, float32 input bits)."""
    # Algorithm (Apache-2.0):
    # https://github.com/blender/blender/blob/main/intern/cycles/util/hash.h
    x, y = np.broadcast_arrays(np.asarray(col, dtype=np.float32),
                               np.asarray(row, dtype=np.float32))
    keys = ((x + np.float32(seed[0])).view(np.uint32),
            (y + np.float32(seed[1])).view(np.uint32),
            np.full(x.shape, seed[2], dtype=np.float32).view(np.uint32))
    mask = np.uint64(0xffffffff)
    a, b, c = [(key.astype(np.uint64) + np.uint64(0xdeadbeef + 12 + 13)) & mask
               for key in keys]

    def rot(value, bits):
        return ((value << np.uint64(bits)) | (value >> np.uint64(32 - bits))) & mask

    # uint64 plus explicit masking gives uint32 wrap without overflow warnings.
    def sub(value, other):
        return (value + np.uint64(0x100000000) - other) & mask

    c = sub(c ^ b, rot(b, 14))
    a = sub(a ^ c, rot(c, 11))
    b = sub(b ^ a, rot(a, 25))
    c = sub(c ^ b, rot(b, 16))
    a = sub(a ^ c, rot(c, 4))
    b = sub(b ^ a, rot(a, 14))
    c = sub(c ^ b, rot(b, 24))
    return (c.astype(np.float32) * np.float32(1.0 / 4294967296.0)).astype(float)

def _jitter_transform(col, row, tile_w, tile_h, joint, jitter_offset, jitter_rotation):
    """Return per-cell X/Y shifts and angle conservatively contained inside the cell."""
    diagonal_half = np.hypot(tile_w, tile_h) / 2
    clearance = max(joint / 2 - 1e-5, 0.0)
    random = [(_white_noise(col, row, seed) - 0.5) * 2 for seed in _JITTER_SEEDS]
    angle = random[2] * min(abs(jitter_rotation), clearance / diagonal_half)
    # Rotation displaces any point by at most |a| * half-diagonal.
    # Thus each axis shift <= joint/2 - |a| * half-diagonal - 1e-5.
    limit = np.minimum(abs(jitter_offset), np.maximum(clearance - np.abs(angle) * diagonal_half, 0))
    return random[0] * limit, random[1] * limit, angle

def reference(u, v, tile_w, tile_h, joint, row_offset=0.0, rotation=0.0,
              origin=(0.0, 0.0), corner_radius=0.0, jitter_offset=0.0,
              jitter_rotation=0.0):
    """Return layout truth in metres; row_offset accepts any real value and wraps."""
    u, v = np.broadcast_arrays(np.asarray(u, dtype=float), np.asarray(v, dtype=float))
    x, y = u - origin[0], v - origin[1]
    c, s = np.cos(rotation), np.sin(rotation)
    qx, qy = c * x + s * y, -s * x + c * y
    pw, ph = tile_w + joint, tile_h + joint
    row = np.floor(qy / ph)
    offset = row * row_offset
    xp = qx - (offset - np.floor(offset)) * pw
    col = np.floor(xp / pw)
    tx, ty = xp - col * pw - joint / 2, qy - row * ph - joint / 2
    ox, oy, angle = _jitter_transform(col, row, tile_w, tile_h, joint,
                                       jitter_offset, jitter_rotation)
    cx, cy = tx - tile_w / 2 - ox, ty - tile_h / 2 - oy
    ca, sa = np.cos(angle), np.sin(angle)
    tx, ty = ca * cx + sa * cy + tile_w / 2, -sa * cx + ca * cy + tile_h / 2
    rc = np.clip(corner_radius, 0, min(tile_w, tile_h) / 2)
    dx = np.abs(tx - tile_w / 2) - (tile_w / 2 - rc)
    dy = np.abs(ty - tile_h / 2) - (tile_h / 2 - rc)
    edge = -(np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))
             + np.minimum(np.maximum(dx, dy), 0) - rc)
    return dict(tile_uv_x=np.clip(tx / tile_w, 0, 1),
                tile_uv_y=np.clip(ty / tile_h, 0, 1), edge=edge,
                joint=(edge < -1e-7).astype(float), col=col, row=row)
