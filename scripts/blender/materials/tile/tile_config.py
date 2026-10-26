"""Tile material parameters: feature names, the parameter groups that map to node sockets, and the
validation rules for each metre or probability value. Pure data and checks, no node building.
"""
import math

FEATURES = ("profile", "variation", "tilt", "wave", "dust", "specks", "macro", "damage")

# Layout sockets on the TileLayout group, keyed by tile_material keyword.
LAYOUT = dict(tile_w="Tile W", tile_h="Tile H", joint="Joint", corner_radius="Corner Radius", row_offset="Row Offset",
              rotation="Rotation", origin="Origin", jitter_offset="Jitter Offset",
              jitter_rotation_deg="Jitter Rotation")
OPTIONAL_LAYOUT = ("jitter_offset", "jitter_rotation_deg")

# Damage keywords that existed before the v7 damage model; a stored material still carrying them is
# accepted and they are dropped on rebuild.
REMOVED_DAMAGE = ('chip_reach', 'flake_margin', 'crack_wander', 'crack_branch_share',
                  'spall_share', 'spall_reach', 'kink_size', 'kink_amp', 'branch_share')

# Finish sockets on the TileFinish group, keyed by tile_material keyword.
FINISH = dict(body_albedo="Body Albedo", coat_ior="Coat IOR", coat_rough="Coat Rough",
              edge_radius="Edge Radius", recess="Recess", grout_albedo="Grout Albedo",
              grout_rough="Grout Rough", dust="Dust", dust_width="Dust Width",
              tint_var="Tint Var", rough_var="Rough Var", tilt_deg="Tilt Deg", lippage="Lippage",
              wave_amp="Wave Amp", specks="Specks", speck_size="Speck Size", macro="Macro", map_size="Map Size",
              face_contrast="Face Contrast", face_saturation="Face Saturation")


def validate_damage(key, value):
    """Reject negative/nonfinite metre parameters and invalid probabilities."""
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{key} must be finite and nonnegative')
    if key in ('damage', 'chip_share', 'crack_share', 'spall_density', 'crack_dirt', 'crack_density', 'chip_density') and value > 1:
        raise ValueError(f'{key} must lie in [0, 1]')
    if key in ('warp_scale','crack_cell') and value <= 0:
        raise ValueError(f'{key} must be positive')
    if key == 'force_kind' and value not in (0, 1, 2, 3):
        raise ValueError('force_kind must be 0, 1, 2 or 3')
    if key == 'shell_exponent' and not .2 <= value <= 2:
        raise ValueError('shell_exponent must lie in [0.2, 2]')
