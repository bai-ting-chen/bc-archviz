"""Blade config; canonical implementation behind vegetation."""

BLADE = dict(rough=0.45, ior=1.45, trans_gain=0.8)        # waxy cuticle; T a little under R

WET = dict(gamma=1.7, coat=0.9, coat_rough=0.08, range=(0.75, 1.0), patch_scale=0.15)

DEW_GRASS = dict(cell=0.003, r=(0.2, 0.45), cover=0.5, reflect=0.85, rough=0.04, up=0.2, fade=(6.0, 14.0))

DEW_BROAD = dict(DEW_GRASS, cell=0.005)                   # clover-type leaves: 2-4.5 mm beads
