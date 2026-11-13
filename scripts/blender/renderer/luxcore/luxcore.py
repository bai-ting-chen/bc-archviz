"""Compatibility facade for luxcore; each job has one owner."""
import os, json
import bpy
import core.archviz as archviz
from renderer.luxcore.dust_config import (CORNER_MASK_CAP, DUST_AMOUNT, DUST_GAIN, DUST_PX,
                                         DUST_SATURATION, DUST_WIDTH_M, GRIME_TINT, LINE_AMOUNT,
                                         LINE_GAIN, LINE_WIDTH_M)
from renderer.luxcore.dust_uv import _ctx, dust_uv
from renderer.luxcore.dust_shader import _dust_bake_material
from renderer.luxcore.dust_bake import bake_dust, _bake_each
from renderer.luxcore.textured_material import textured_material
from renderer.luxcore.glass_tint import glass_instance_tint
from renderer.luxcore.engine_settings import engine_setup, set_halt
