"""Dust shader; canonical implementation behind luxcore."""

import bpy

from renderer.luxcore.dust_config import DUST_BAND, DUST_DIST, DUST_HEIGHT, DUST_POWER

def _dust_bake_material():
    m = bpy.data.materials.get("DustBake") or bpy.data.materials.new("DustBake"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    def rng(lo, hi, to_lo, to_hi):
        r = N("ShaderNodeMapRange"); r.clamp = True
        r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = lo, hi
        r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = to_lo, to_hi
        return r
    def mul(a, b):
        m_ = N("ShaderNodeMath"); m_.operation = "MULTIPLY"; L(a, m_.inputs[0]); L(b, m_.inputs[1]); return m_.outputs[0]
    ao = N("ShaderNodeAmbientOcclusion"); ao.inside = False; ao.only_local = False; ao.samples = 16
    ao.inputs["Distance"].default_value = DUST_DIST
    band = rng(DUST_BAND[0], DUST_BAND[1], 1.0, 0.0); L(ao.outputs["AO"], band.inputs["Value"])
    shape = N("ShaderNodeMath"); shape.operation = "POWER"; shape.inputs[1].default_value = DUST_POWER
    L(band.outputs["Result"], shape.inputs[0])
    geo = N("ShaderNodeNewGeometry")
    big = N("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 5.0; big.inputs["Detail"].default_value = 6
    fine = N("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 90.0; fine.inputs["Detail"].default_value = 4
    L(geo.outputs["Position"], big.inputs["Vector"]); L(geo.outputs["Position"], fine.inputs["Vector"])
    bigr = rng(0.35, 0.65, 0.45, 1.0); L(big.outputs["Fac"], bigr.inputs["Value"])      # patchy extent
    finer = rng(0.3, 0.7, 0.7, 1.0); L(fine.outputs["Fac"], finer.inputs["Value"])      # speckle
    sep = N("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sep.inputs["Vector"])
    hgt = rng(*DUST_HEIGHT); L(sep.outputs["Z"], hgt.inputs["Value"])
    v = mul(mul(mul(shape.outputs[0], bigr.outputs["Result"]), finer.outputs["Result"]), hgt.outputs["Result"])
    em = N("ShaderNodeEmission"); out = N("ShaderNodeOutputMaterial")
    L(v, em.inputs["Color"]); L(em.outputs[0], out.inputs["Surface"])
    tgt = N("ShaderNodeTexImage"); tgt.name = "target"; nt.nodes.active = tgt
    return m
