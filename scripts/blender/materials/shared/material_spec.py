"""Material spec; canonical implementation behind pbr."""

from materials.shared.dielectric import glass_material

from materials.shared.pbr_build import pbr_material

from materials.shared.simple import simple_material

def material_from_spec(spec):
    """spec: "ph:<tex_id>" | "glass" | {"type": "ph"|"glass"|"simple", ...kwargs}."""
    if isinstance(spec, str):
        if spec.startswith("ph:"):
            return pbr_material(spec[3:])
        if spec == "glass":
            return glass_material()
        raise ValueError(spec)
    spec = dict(spec)
    kind = spec.pop("type")
    return {"ph": lambda **k: pbr_material(**k), "glass": glass_material, "simple": simple_material}[kind](**spec)
