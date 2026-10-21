# Wood

- **Coated** `coated_wood()`: the coat trap — satin varnish is a *low* coat weight with *tight*
  coat roughness, not a strong rough coat. Spread the base roughness toward matte; don't lower
  IOR to compensate. Coat › Normal can stay smooth over bumped wood (to try).
- Cladding: pick the plank map by its real size and run `archviz.directional_uv(obj, tex_size_m, axis)` so the
  grain follows the boards. A map whose grain runs along V needs `along="V"`.
- Battens and veneers want matte — a coat mirrors lenses as halos.
- **Dark veneer floor seen at a low camera angle** reads light grey under a satin coat: Fresnel
  reflects the bright sky at grazing angles. A matte coat keeps it dark.
