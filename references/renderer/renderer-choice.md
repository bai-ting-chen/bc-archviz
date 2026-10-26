# Choosing a renderer and method (RULES REN_01–REN_03)

## REN_01 procedure

**Native first.** Blender's own features (Cycles, shader nodes, Geometry Nodes, modifiers, Sky
   Texture) before self-written external tools — native work stays editable in the .blend and
   survives Blender updates; external tools are a last resort, and say so when used.


## REN_02 procedure

**Unbiased first.** Order: (a) Cycles path tracing; (b) native physically based approximations
   (for example, MNEE or GN wavefront caustics; see [caustics.md](../effects/caustics.md)) only when (a) cannot converge — state why and the bias;
   (c) external tools only when nothing native works — tell the user. Fakes (light-path tricks,
   projected patterns) only as a declared fallback. The point of the studies is renders that
   hold up as physics, so a bias must always be named, never hidden.

## REN_03 procedure

**Renderer: Cycles by default, LuxCore for detailed caustics**. When
   caustics or heavy refraction carry the shot — sun through patterned glass or glass block,
   glass-on-water, multi-interface glass — render in LuxCore (BlendLuxCore, path tracing with
   light tracing: GPU camera paths + CPU light paths). It is the one standing exception to
   native-first: Cycles path tracing, path guiding and MNEE all fail on specular–diffuse–specular
   paths from a sun-sized source, while LuxCore light tracing is unbiased and energy-correct there ([caustics comparison](../effects/caustics.md#applying-ren_02-to-caustics#applying-ren_02-to-caustics)). Say it is
   an external engine when you switch.

Setup and settings: [luxcore.md](luxcore.md).
