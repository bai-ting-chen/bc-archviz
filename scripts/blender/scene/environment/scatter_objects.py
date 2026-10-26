"""Scatter objects; implementation for scatter."""
from effects.edge_wear import set_input
from scene.environment.scatter_graph import scatter_group


def scatter(objs, instance, density, scale=1.0, z_max=1e4, seed=0, keep_source=True, patch=0.0):
    """Add (or update) the SCATTER modifier on each object."""
    ng = scatter_group()
    for o in objs:
        mod = o.modifiers.get("SCATTER") or o.modifiers.new("SCATTER", "NODES")
        mod.node_group = ng
        for k, v in (("Instance", instance), ("Density", density), ("Scale", scale), ("Z Max", z_max),
                     ("Seed", seed), ("Keep Source", keep_source), ("Patchiness", patch)):
            set_input(mod, k, v)
