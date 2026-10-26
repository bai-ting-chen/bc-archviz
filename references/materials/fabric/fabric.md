# Fabric

## 1. Overview
Sheer curtain cloth: light, high-albedo fabric that lets light through, so a lit room behind it
glows through the curtain. The lit room behind and what it shows are covered in lighting-camera.md
(› Glass and what it shows, plain-text neighbour).

## 2. Layers and node-editor diagram
This file is a single layer: one sheer-curtain material, with no stack and no generic layers of its
own. It is a Mix of Diffuse and Translucent at about 0.5, at high albedo (§4.1).

## 3. Code
- `scripts/blender/materials/fabric/fabric.py`: `sheer(name, color, translucency)`, called as
  `materials.fabric.fabric.sheer()`.
- Control: the `sheer` case in `scripts/controls/regression/regress_cases.py`.

## 4. Instructions and parameters, per layer

### 4.1 Sheer curtain (Mix of Diffuse and Translucent)
- Mix(Diffuse, Translucent, ~0.5) at high albedo, so a lit room behind glows through the curtain.
- The glow depends on the lit room behind (see lighting-camera.md in §1), not on the curtain alone.

| Parameter | Value |
|---|---|
| Mix factor (Diffuse to Translucent) | ~0.5 |
| Albedo | high |

### Generic layers, fabric settings
| Layer | Reference | Fabric note |
|---|---|---|
| Lit room behind the curtain | lighting-camera.md › Glass and what it shows (plain text) | the source of the glow (§4.1) |

## 5. Troubleshooting
No symptoms are recorded for this file. Generic problems are in
troubleshooting.md.
