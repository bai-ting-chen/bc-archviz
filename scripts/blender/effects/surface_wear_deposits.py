"""Irregular deposit bodies and uneven rims without radial or circular primitives."""


def deposit_profile(g, body, rim, tone, frame=None):
    """Keep a faint deposit body inside a stronger dark rim, with scan/noise tone variation."""
    variation=g.range(tone,0,1,(-600,-18000),tmin=.32,tmax=.18,frame=frame)
    interior=g.math('MULTIPLY',body,variation,(-300,-18000),frame)
    return g.math('MAXIMUM',interior,rim,(0,-18000),frame)


def deposit_distance(g,vector,scale_m,frame=None):
    """Return a continuous warped blob distance and tone, before body/rim plateaus are applied."""
    scale=g.node('ShaderNodeVectorMath',(-3000,-18000),frame)
    scale.operation='SCALE'
    scale.inputs['Scale'].default_value=1/scale_m
    g.link(vector,scale.inputs[0])
    warp=g.node('ShaderNodeTexNoise',(-2800,-18000),frame,Scale=1.8,Detail=3.)
    g.link(scale.outputs[0],warp.inputs['Vector'])
    offset=g.node('ShaderNodeVectorMath',(-2500,-18000),frame)
    offset.operation='SUBTRACT'
    g.link(warp.outputs['Color'],offset.inputs[0])
    offset.inputs[1].default_value=(.5,.5,.5)
    stretch=g.node('ShaderNodeVectorMath',(-2300,-18000),frame)
    stretch.operation='SCALE'
    stretch.inputs['Scale'].default_value=1.6  # domain distortion relative to blob spacing
    g.link(offset.outputs[0],stretch.inputs[0])
    warped=g.node('ShaderNodeVectorMath',(-2000,-18000),frame)
    warped.operation='ADD'
    g.link(scale.outputs[0],warped.inputs[0])
    g.link(stretch.outputs[0],warped.inputs[1])
    field=g.noise(warped.outputs[0],1.,(-1800,-18000),frame,detail=3,rough=.65)
    slow=g.noise(scale.outputs[0],.35,(-1800,-18600),frame,detail=2)
    threshold=g.range(slow,0,1,(-1500,-18600),tmin=.49,tmax=.64,frame=frame)
    distance=g.math('SUBTRACT',field,threshold,(-1200,-18000),frame)
    return distance,slow,warped.outputs[0]


def irregular_deposits(g,vector,scale_m,frame=None):
    """Warp a multiscale noise domain into varied, sometimes merged blobs with broken rims."""
    distance,slow,warped=deposit_distance(g,vector,scale_m,frame)
    body=g.range(distance,-.008,.025,(-900,-18000),frame=frame,smooth=True)
    absolute=g.math('ABSOLUTE',distance,0,(-1200,-18400),frame)
    rim=g.range(absolute,.006,.025,(-900,-18400),tmin=1,tmax=0,frame=frame,smooth=True)
    broken=g.noise(warped,4.,(-1200,-19000),frame,detail=2)
    broken=g.range(broken,.25,.75,(-900,-19000),tmin=.25,tmax=1,frame=frame)
    rim=g.math('MULTIPLY',rim,broken,(-600,-18400),frame)
    return deposit_profile(g,body,rim,slow,frame)
