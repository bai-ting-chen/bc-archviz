"""Layout config; canonical implementation behind tile_layout."""

_VERSION = 4

_INPUTS = {
    "tile_w": "Tile W", "tile_h": "Tile H", "joint": "Joint", "corner_radius": "Corner Radius",
    "jitter_offset": "Jitter Offset", "jitter_rotation": "Jitter Rotation",
    "row_offset": "Row Offset", "rotation": "Rotation", "origin": "Origin",
}

_JITTER_SEEDS = ((0.5, 0.5, 11.5), (0.5, 0.5, 23.5), (0.5, 0.5, 37.5))
