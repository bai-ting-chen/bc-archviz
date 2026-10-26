# Metal

`materials.metal.metal.polished_steel()`: Metallic BSDF F82, low roughness, shade smooth. Brushed:
Anisotropic + Tangent.

## Brushed anodised metal around water (sized for the final view, RULES MAT_03)
- Metallic BSDF F82 (edge tint brighter, warmer than base), anisotropy ~0.75 with the tangent from
  a directional UV along the part's length, brush streaks in roughness (noise stretched ~400:1);
  bevel 1–2 mm with hardened normals.
- Water marks as coffee rings (rim stronger), tide lines of dried puddles on tops, drip/tea streaks
  on verticals, AO dust in joints, ±6 % per-part tone. Spots under ~3 px vanish: at ~3 mm/px they
  need 8–25 mm.
