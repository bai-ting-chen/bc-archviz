"""Displacement material helpers; canonical implementations."""


def enable_true_displacement(obj, pixel_size=1.0):
    """Adaptive (camera-dicing) subdivision, the view-dependent
    edge_length in pixels."""
    mod = next((m for m in obj.modifiers if m.type == "SUBSURF"), None) or \
        obj.modifiers.new("Adaptive Subdivision", "SUBSURF")
    mod.subdivision_type = "SIMPLE"
    mod.use_adaptive_subdivision = True
    mod.adaptive_space = "PIXEL"
    mod.adaptive_pixel_size = pixel_size
    return mod
