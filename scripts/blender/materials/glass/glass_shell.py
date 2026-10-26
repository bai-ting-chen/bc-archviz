"""Glass shell; canonical implementation behind glass."""

def glass_shell(objs, thickness=0.003):
    """Solid Rhino spheres are lens balls: Solidify inward to a thin shell, shade smooth."""
    for o in objs:
        if not o.modifiers.get("Shell"):
            mod = o.modifiers.new("Shell", "SOLIDIFY")
            mod.thickness, mod.offset = thickness, -1.0
        for p in o.data.polygons:
            p.use_smooth = True
