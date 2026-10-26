"""Water geometry built as field maps on analytic carriers (references/materials/water/water-*.md).

Pure numpy modules (no bpy): noise, curtain, film, fragments, foot, ripple, wet.
Blender modules: mesh (geometry objects), motion (velocity motion blur), shading (materials, ripple bump),
build (one entry point).
All lengths in metres, speeds in m/s. A lip is any straight horizontal edge in the scene (curtain.Lip).
"""
