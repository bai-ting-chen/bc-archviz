"""Damage contract; canonical implementation behind tile_damage."""

_VERSION = 7

_REVISION = 1

PIECE_BINS = 65536

PARAMS = dict(damage='Fraction',crack_share='Crack Share',chip_share='Chip Share',
              step_height='Step Height',piece_tilt='Piece Tilt',crack_width='Crack Width',
              crack_depth='Crack Depth',chip_size='Chip Size',chip_depth='Chip Depth',
              spall_size='Spall Size',spall_density='Spall Density',glaze_thickness='Glaze Thickness',
              engobe_thickness='Engobe Thickness',glaze_lip_width='Glaze Lip Width',engobe_ring='Engobe Ring',
              force_kind='Force Kind',shell_exponent='Shell Exponent',crack_dirt='Crack Dirt',
              dirt_width='Dirt Width',warp='Warp',warp_scale='Warp Scale',crack_cell='Crack Cell',
              crack_density='Crack Density',chip_density='Chip Density')

DEFAULTS=(.05,.45,.35,.00015,.0035,.00018,.0008,.004,.0008,.001,.25,.0003,.0002,
          .0002,.0003,0,.6,.85,.004,.004,.02,.03,.35,.5)

_LAYOUT_INPUTS=('Tile ID','Cell','Tile UV','Edge','Tile Size')

_OUTPUTS=('Chip Depth Out','Piece Height','Piece','Crack','Crack Depth Out','Glaze Lip','Engobe',
          'Body','Damaged','Kind','Dirt','Chip','Picked','Crack Distance','Chip Cell','Chip Site Edge')
