"""Dust config; canonical implementation behind luxcore."""

DUST_DIST = 0.20                    # m, AO reach = width of the band; 0.12 read as a pencil line

DUST_BAND = (0.55, 0.97)            # AO in the joint .. AO where the dust has faded out

DUST_POWER = 1.2                    # falloff shape: higher = tighter to the corner

DUST_TINT = (0.62, 0.58, 0.52)      # albedo multiplier at full dust (grey-brown)

DUST_HEIGHT = (0.6, 2.6, 1.0, 0.45) # world z from, z to, strength at from, at to: floor > ceiling

DUST_PX = 4096
