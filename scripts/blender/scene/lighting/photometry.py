"""Photometric conversions shared by lights, the physical camera and the HDRI world.

Blender radiance is treated as photometric through one constant, so a lamp in lumens, an HDRI in
lux and a camera in EV100 all agree.
"""
import math

LM_PER_W = 683.0  # luminous efficacy used to read Cycles radiance as photometric units


def ev100(iso, fstop, shutter_s):
    """EV100 of a camera triple: log2(N^2/t) - log2(ISO/100)."""
    return math.log2(fstop ** 2 / shutter_s) - math.log2(iso / 100.0)
