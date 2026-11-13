"""Water geometry built as field maps on analytic carriers (references/materials/water/water-*.md).

Pure numpy modules (no bpy): seeded_noise, ballistic_sheet, falling_film, film_fragments, pool_impacts, pool_ripples, wet_wall_proxy.
Blender modules: mesh_builders (geometry objects), motion_blur (velocity motion blur), surface_shading (materials, ripple bump),
falling_film_assembly (one entry point).
All lengths in metres, speeds in m/s. A lip is any straight horizontal edge in the scene (ballistic_sheet.LaunchLip).
"""
