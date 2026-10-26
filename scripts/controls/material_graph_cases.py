"""Shared deterministic fixtures for the material-family refactor controls.

Tiny generated maps keep controls independent of study assets. No study files are edited.
Each topic wrapper accepts one output JSON path after Blender's -- separator.
"""
import importlib
import ast
import json
import math
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender"))
from graph_dump import dump_material, dump_tree, value, write


def mesh_state(obj):
    """Record geometry, UVs, normals, attributes and modifier settings."""
    return {
        "vertices": [value(v.co) for v in obj.data.vertices],
        "faces": [list(p.vertices) for p in obj.data.polygons],
        "smooth": [p.use_smooth for p in obj.data.polygons],
        "sharp": [e.use_edge_sharp for e in obj.data.edges],
        "uv": {layer.name: [value(d.uv) for d in layer.data] for layer in obj.data.uv_layers},
        "properties": {k: value(obj[k]) for k in obj.keys()},
        "modifiers": [{"name": m.name, "type": m.type,
                       "thickness": getattr(m, "thickness", None),
                       "offset": getattr(m, "offset", None)} for m in obj.modifiers],
    }


def cube():
    """Create a small real mesh for geometry and mapping controls."""
    bpy.ops.mesh.primitive_cube_add(size=0.4)
    return bpy.context.object


def group_state(group):
    """Record graph and ordered interface, including defaults and bounds."""
    return {"tree": dump_tree(group), "interface": [
        {key: value(getattr(s, key, None)) for key in
         ("name", "in_out", "socket_type", "default_value", "min_value", "max_value", "subtype")}
        for s in group.interface.items_tree if s.item_type == "SOCKET"]}


def import_smoke(topic):
    """Import material owners and direct callers; check control imports without running renders."""
    scripts = Path(__file__).resolve().parents[1]
    for path in sorted((scripts / "blender" / "materials").glob("*.py")):
        importlib.import_module("materials." + path.stem)
    callers = []
    for path in sorted(scripts.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        relevant = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "materials." + topic for alias in node.names):
                    relevant.append(node)
            elif isinstance(node, ast.ImportFrom):
                name = node.module or ""
                facade_import = name == "materials." + topic or (node.level == 1 and name == topic)
                package_import = (name == "materials" or (node.level == 1 and not name)) and any(
                    alias.name == topic for alias in node.names)
                if facade_import or package_import:
                    relevant.append(node)
        if not relevant:
            continue
        if scripts / "blender" in path.parents:
            module = ".".join(path.relative_to(scripts / "blender").with_suffix("").parts)
            importlib.import_module(module)
        else:
            # Controls have top-level scene/render operations: import only their declarations.
            for node in relevant:
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), {})
        callers.append(str(path.relative_to(scripts)))
    print("IMPORT_SMOKE", topic, callers)


def run(topic):
    """Build every path relevant to one material facade and write its baseline."""
    out = Path(sys.argv[sys.argv.index("--") + 1])
    with tempfile.TemporaryDirectory(prefix="material-control-") as directory:
        folder = Path(directory)
        image = bpy.data.images.new("fixture", 4, 4)
        image.pixels[:] = [c for i in range(16) for c in (0.2 + i / 50, 0.4, 0.6, 1.0)]
        image.filepath_raw = str(folder / "map.png")
        image.file_format = "PNG"
        image.save()
        maps = {k: k + ".png" for k in ("diff", "arm", "rough", "nor_gl", "disp")}
        for filename in maps.values():
            (folder / filename).write_bytes((folder / "map.png").read_bytes())
        meta = {"maps": maps,
                "dimensions_mm": [1000, 750], "source": "generated control fixture"}
        (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        import core.archviz as archviz
        # Route only this process's asset requests to disposable, measured fixtures.
        archviz.library = lambda *parts: str(folder / "map.png") if Path(parts[-1]).suffix else str(folder)
        m = importlib.import_module("materials." + topic)
        result = {}

        def fresh():
            bpy.ops.wm.read_homefile(use_empty=True)

        def material(label, builder):
            fresh()
            result[label] = dump_material(builder())

        if topic == "tile_damage":
            fresh()
            group = m.damage_group()
            result["default"] = group_state(group)
            result["reuse"] = m.damage_group() == group
            group["tile_damage_revision"] = -1
            result["upgrade"] = group_state(m.damage_group())
            material("damage_bsdfs", lambda: importlib.import_module("materials.tile.tile_surface").tile_material("damage", displacement="damage"))
        elif topic == "tile_layout":
            fresh()
            group = m.layout_group()
            result["default"] = group_state(group)
            result["reuse"] = m.layout_group() == group
            group["tile_layout_version"] = -1
            result["upgrade"] = group_state(m.layout_group())
            mat = bpy.data.materials.new("layout")
            mat.use_nodes = True
            vector = mat.node_tree.nodes.new("ShaderNodeTexCoord").outputs["Generated"]
            m.add_layout(mat.node_tree, vector, row_offset=-0.5, origin=(0.1, 0.2))
            result["instance"] = dump_material(mat)
            for label, kwargs in (("plain", {}), ("jitter", dict(jitter_offset=.004, jitter_rotation=.1,
                                      row_offset=-.5, rotation=.2, corner_radius=.003))):
                truth = m.reference(np.linspace(-.3, .3, 13), np.linspace(-.2, .2, 13), .1, .12, .005, **kwargs)
                result[label] = {k: value(v) for k, v in truth.items()}
        elif topic == "tile_mapping":
            fresh()
            obj = cube()
            obj.rotation_euler = (.1, .2, .3)
            obj.location = (1, 2, 3)
            m.planar_uv(obj, origin=(.2, .3), facing=(0, -1, 0))
            result["planar"] = mesh_state(obj)
            fresh()
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1, depth=1)
            obj = bpy.context.object
            m.cylinder_uv(obj, (0, 0), 1, seam_angle=.3)
            result["cylinder"] = mesh_state(obj)
            m.annulus_uv(obj, (0, 0), 1, like=obj, name="Annulus")
            result["annulus"] = mesh_state(obj)
            mat = bpy.data.materials.new("mapping")
            mat.use_nodes = True
            m.layout_vector(mat.node_tree, obj=obj)
            result["vector"] = dump_material(mat)
        elif topic == "concrete":
            for label, kwargs in (("default", {}), ("off", dict(stain=False, bevel_chips=False, edge_dark=False))):
                material(label, lambda kwargs=kwargs: m.concrete_study(**kwargs))
            fresh()
            mat = m.concrete_study(stain=False)
            result["retone_gain"] = m.retone(mat, (.4, .45, .5), "fixture")
            result["retone"] = dump_material(mat)
            for cylinder in (None, (1, 2, 3)):
                material("boards_" + str(cylinder), lambda cylinder=cylinder: m.vertical_boards(
                    importlib.import_module("materials.shared.pbr").albedo_material("fixture", "boards", (.4, .4, .4)), cylinder=cylinder))
        elif topic == "wood_wear":
            fresh()
            obj = cube()
            # Test the authored grain mapping; bevel interpolation of Blender's default
            # cube UVs lands on a rounding tie and varies with BMesh iteration order.
            obj.data.uv_layers.remove(obj.data.uv_layers.active)
            m.round_arrises(obj)
            m.grain_uv(obj, 1.0)
            result["geometry"] = mesh_state(obj)
            result["wear_group"] = group_state(m.wood_wear_group(level=1))
            material("shader", m.weathered_wood)
        elif topic == "pbr":
            for label, builder in (
                ("pbr", lambda: m.pbr_material("fixture")),
                ("tint", lambda: m.pbr_material("fixture", tint=(.8, .9, 1))),
                ("dielectric", lambda: m.dielectric("dielectric")),
                ("glass", m.glass_material),
                ("simple", lambda: m.simple_material("simple", (.2, .3, .4))),
                ("spec", lambda: m.material_from_spec({"type": "simple", "name": "spec", "color": (.2, .3, .4)})),
                ("spec_ph", lambda: m.material_from_spec("ph:fixture")),
                ("spec_glass", lambda: m.material_from_spec("glass")),
                ("backdrop", m.white_backdrop),
                ("albedo", lambda: m.albedo_material("fixture", "albedo", (.4, .5, .6)))):
                material(label, builder)
            fresh()
            mat = m.glass_material()
            result["glass_edit"] = dump_material(m.glass_material(tint=(1, .9, .8)))
            result["levels"] = m.solve_levels(str(folder / "map.png"), (.4, .5, .6))
            result["mean"] = m.map_mean("fixture")
            result["cached_mean"] = m.map_mean("fixture")
        elif topic == "stone":
            material("granite", m.polished_granite)
            material("tiles", m.stone_tiles)
            for axis in ("X", "Y"):
                material("pavers_" + axis, lambda axis=axis: m.long_pavers("fixture", "pavers", (.3, .4, .5), long_axis=axis))
        elif topic == "luxcore":
            import addon_utils
            fresh()
            # LuxCore image nodes require their in-memory preference entry. Register
            # after the factory reset, which would otherwise discard that entry.
            addon_utils.enable("bl_ext.user_default.blendluxcore", default_set=True)
            assert hasattr(bpy.types.Material, "luxcore"), "LuxCore registration failed"
            obj = cube()
            obj.data.uv_layers.new(name="BoxUV")
            m.dust_uv(obj)
            result["uv"] = mesh_state(obj)
            result["dust"] = dump_material(m._dust_bake_material())
            # Cached branch exercises bake routing without a stochastic GPU bake.
            cache = folder / "cache"
            cache.mkdir()
            (cache / (obj.name + ".png")).write_bytes(b"cached")
            result["cached_bake"] = sorted(m.bake_dust([obj], str(cache)))
            for dust in (None, str(folder / "map.png")):
                mat = m.lux_textured("native" + str(dust is not None), str(folder), obj.data, dust_png=dust)
                result["native_" + str(dust is not None)] = group_state(mat.luxcore.node_tree)
            result["glass"] = dump_material(m.glass_instance_tint())
        elif topic == "glass":
            material("clear", m.clear_glass)
            fresh()
            obj = cube()
            m.glass_shell([obj])
            m.glass_shell([obj])
            result["shell"] = mesh_state(obj)
            result["distortion"] = dump_material(m.glass_distortion(m.clear_glass(), obj))
        elif topic == "ground":
            material("displaced", m.displaced_ground)
            material("dry", lambda: m.ground_material("fixture", "fixture"))
            material("wet", lambda: m.ground_material("fixture", "fixture", wet_gamma=1.4))
        elif topic == "vegetation":
            material("dry", lambda: m.blade_material("dry"))
            material("wet", lambda: m.blade_material("wet", wet=m.WET))
            for label, dew in (("grass", m.DEW_GRASS), ("broad", m.DEW_BROAD)):
                material(label, lambda label=label, dew=dew: m.blade_material(label, tex=str(folder / "map.png"), wet=m.WET, dew=dew))
        elif topic == "water":
            material("pool", m.pool_water)
            fresh()
            obj = cube()
            m.smooth_flat(obj)
            result["smooth"] = mesh_state(obj)
            result["count"] = m.water_surface(obj, .1)
            result["surface"] = mesh_state(obj)
        elif topic == "tile_nodes":
            fresh()
            result["layout"] = group_state(importlib.import_module("materials.tile.tile_layout").layout_group())
            result["damage"] = group_state(importlib.import_module("materials.tile.tile_damage").damage_group())
            material("tile", lambda: importlib.import_module("materials.tile.tile_surface").tile_material("tile"))
            fresh()
            old = bpy.data.node_groups.new("Old", "ShaderNodeTree")
            new = bpy.data.node_groups.new("New", "ShaderNodeTree")
            for group, inputs in ((old, ("Value", "Bias")), (new, ("Bias", "Extra", "Value"))):
                for name in inputs:
                    group.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketFloat")
                group.interface.new_socket("Result", in_out="OUTPUT", socket_type="NodeSocketFloat")
            mat = bpy.data.materials.new("Users")
            mat.use_nodes = True
            world = bpy.data.worlds.new("UsersWorld")
            world.use_nodes = True
            light = bpy.data.lights.new("UsersLight", "POINT")
            light.use_nodes = True
            nested = bpy.data.node_groups.new("NestedUsers", "ShaderNodeTree")
            trees = [mat.node_tree, world.node_tree, light.node_tree, nested]
            for tree in trees:
                tree.nodes.clear()
                source = tree.nodes.new("ShaderNodeValue")
                source.outputs[0].default_value = .37
                first = tree.nodes.new("ShaderNodeGroup")
                second = tree.nodes.new("ShaderNodeGroup")
                first.node_tree = second.node_tree = old
                first.inputs["Bias"].default_value = .23
                second.inputs["Bias"].default_value = .73
                sink = tree.nodes.new("ShaderNodeMath")
                tree.links.new(source.outputs[0], first.inputs["Value"])
                tree.links.new(first.outputs["Result"], second.inputs["Value"])
                tree.links.new(second.outputs["Result"], sink.inputs[0])
            retarget = m._replace_group_users
            if "--reference" in sys.argv:
                # Reproduce the saved pre-split implementation without modifying the checkout.
                import types
                reference = types.ModuleType("retarget_reference")
                path = Path(sys.argv[sys.argv.index("--reference") + 1])
                exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), reference.__dict__)
                retarget = reference._replace_group_users
            retarget(old, new)
            for tree in trees:
                users = [n for n in tree.nodes if n.bl_idname == "ShaderNodeGroup"]
                assert all(n.node_tree == new for n in users)
                assert [round(n.inputs["Bias"].default_value, 2) for n in users] == [.23, .73]
                assert len(tree.links) == 3
            result["linked_retarget"] = [dump_tree(tree) for tree in trees]
        else:
            raise ValueError(topic)
        import_smoke(topic)
        write(out, result)
        print("MATERIAL_GRAPH_CHECK", topic, "cases", len(result))

