"""Compatibility facade for glass; each job has one owner."""
import bpy
from materials.shared.nodes import G, sock
from materials.shared.pbr import dielectric, _principled
from materials.glass.clear_glass import clear_glass
from materials.glass.glass_shell import glass_shell
from materials.glass.glass_distortion import glass_distortion
