"""Stone ramp; canonical implementation behind stone."""

def _ramp(g, loc, frame, stops, label=None, interp="LINEAR"):
    r = g.node("ShaderNodeValToRGB", loc, frame, label)
    cr = r.color_ramp
    cr.interpolation = interp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    for pos, col in stops[1:]:
        e = cr.elements.new(pos)
        e.color = (*col, 1)
    return r
