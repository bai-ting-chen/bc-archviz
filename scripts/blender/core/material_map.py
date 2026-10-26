"""Material map: assign a material to each mesh by the nearest collection that names one.

Material assignment calls the canonical builder (materials.shared.pbr) lazily to preserve asset-state ownership.
"""


def _ancestors(coll, parents):
    while coll:
        yield coll
        coll = parents.get(coll)


def apply_material_map(root, mapping):
    """mapping: {collection_name: material spec}. Each mesh gets the material of the nearest
    collection (its layer, a parent layer, or its block definition) that has an entry."""
    from materials.shared.pbr import material_from_spec
    mats = {k: material_from_spec(dict(v) if isinstance(v, dict) else v) for k, v in mapping.items()}
    parents = {}
    for c in [root, *root.children_recursive]:
        for ch in c.children:
            parents[ch] = c
    report = {}
    for ob in root.all_objects:
        if ob.type != "MESH":
            continue
        for coll in ob.users_collection:
            hit = next((mats[c.name] for c in _ancestors(coll, parents) if c.name in mats), None)
            if hit:
                ob.data.materials.clear()
                ob.data.materials.append(hit)
                report.setdefault(hit.name, []).append(ob.name)
                break
        else:
            report.setdefault("<unmapped>", []).append(ob.name)
    return report
