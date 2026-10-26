"""Wood uv; canonical implementation behind wood_wear."""

def grain_uv(obj, size, name="BoxUV", axis=None, along="U"):
    """Kept for existing scripts: archviz.directional_uv, which serves every directional texture
    (not only wood)."""
    import core.archviz as archviz
    return archviz.directional_uv(obj, size, name=name, axis=axis, along=along)
