# Physical Ranges

## Physical ranges and conventions
These transfer to any scene and any renderer — they are measurements of the world, not settings.

- Non-metal albedo ~ 0.03-0.85 linear: charcoal 0.02, asphalt 0.04, brick 0.26, concrete 0.51,
  paper 0.79, marble 0.83. Keep <= 0.8 to limit bounce noise.
- Real IOR: stone/concrete 1.5, water 1.333, glass 1.52. `Specular IOR Level` 0.5 = neutral.
  Specular Tint white on dielectrics; on metals it is the F82 edge tint.
- Polished steel base ~ (0.67, 0.64, 0.60) with edge tint ~0.8 — a property of the metal, not of
  a scene. For other metals, measured n,k go into Metallic BSDF *Physical Conductor*.
- Colour maps sRGB, data maps Non-Color. ARM: R = AO (leave unused — it double-darkens),
  G rough, B metal.
- Image maps on real-metre UVs (`box_uv`, Poly Haven `dimensions_mm`). Tangent-space normal maps
  need a UV map; shader-box-projected maps get Bump from height instead (`materials.pbr.pbr_material`).
- Bump: Distance = the real height of the relief in metres, Strength 1. Relief chain:
  Normal Map -> Bump -> (Bevel node). The Bevel node costs ~20 % and is invalid on MNEE
  casters/receivers → use the Bevel *modifier* there.


- Rough mineral surfaces (plaster, concrete, brick, fabric): Principled **Diffuse Roughness**
  (Oren-Nayar, 4.3+) — to try.


## MAT_01 procedure

Wire every map that applies; real-world UVs; physically plausible albedo/IOR ([README.md](README.md)) —
   wrong scale or albedo reads as "CG" faster than any lighting error.
