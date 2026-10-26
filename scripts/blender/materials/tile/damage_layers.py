"""Damage layers; canonical implementation behind tile_damage."""

def _layers(a, i, e, depth, deep, p):
    """Apply hard coating strata and include clay relief in the physical removal field."""
    m = a.m
    shell = m('GREATER_THAN', e, 0)
    lip = m('MULTIPLY', shell, m('LESS_THAN', e, i['Glaze Lip Width']))
    ring = m('LESS_THAN', e, m('ADD', i['Glaze Lip Width'], i['Engobe Ring']))
    layers = m('ADD', i['Glaze Thickness'], i['Engobe Thickness'])
    reaches_body = m('GREATER_THAN', depth, m('SUBTRACT', layers, 1e-8))
    body = m('MULTIPLY', m('MULTIPLY', shell, m('SUBTRACT', 1, ring)), reaches_body)
    grain_uv = a.v('ADD', p, a.xyz(*a.hash_vector(i['Cell'])))
    relief = m('MULTIPLY', .00015, a.amplitude(grain_uv, 1/.00045))
    # Relief belongs only to exposed body. Its amplitude fades at the actual
    # depth threshold, so it cannot manufacture clay in a shallow shell.
    relief = m('MULTIPLY',relief,m('MINIMUM',1,m('DIVIDE',m('MAXIMUM',m('SUBTRACT',depth,layers),0),.00015)))
    removed = m('MULTIPLY',shell,m('MAXIMUM',i['Glaze Thickness'],
                m('SUBTRACT',depth,m('MULTIPLY',body,relief))))
    # Depth thresholds and the inward rings both apply; nothing forces Body.
    body = m('MULTIPLY',body,m('GREATER_THAN',removed,m('SUBTRACT',layers,1e-8)))
    engobe = m('MULTIPLY',shell,m('SUBTRACT',1,m('ADD',lip,body)))
    return removed, lip, engobe, body
