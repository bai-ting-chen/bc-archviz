"""Shared line/dust defaults and the LuxCore mask bake resolution."""
from effects.edge_dirt import (AO_REACH, CORNER_MASK_CAP, DUST_AMOUNT, DUST_GAIN, DUST_SATURATION,
                               DUST_WIDTH, GRIME_TINT, LINE_AMOUNT, LINE_GAIN, LINE_WIDTH,
                               RGB_LUMINANCE)  # noqa: F401

DUST_PX = 4096  # square UV mask resolution; R=line, G=dust, B=0
