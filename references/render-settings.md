# Render settings (Cycles 5.2)

`archviz.render_setup(w, h, samples, look)`: GPU, adaptive threshold, denoise, AgX, bounces 12.

Render times are a property of the machine, not of the craft — measure once on the box you are
on (first OptiX run in a fresh Blender also pays a one-off kernel compile) and plan iterations
around that, rather than carrying someone else's numbers.

## Sampling and denoising
- Adaptive threshold ~0.01 for working stills, tighter for finals; min samples auto.
- **Final-render denoising runs on CPU by default** — set `cycles.denoising_use_gpu = True`.
- Denoiser: the manual rates **OIDN** highest quality (GPU on RTX); prefilter ACCURATE, quality
  HIGH, passes RGB_ALBEDO_NORMAL. OptiX for previews. *(OIDN vs OptiX crop A/B not yet run.)*
- **Know your noise floor before trusting any comparison.** Render the same frame twice with
  only the seed changed; that difference is the floor. At moderate sample counts with denoising
  it is high enough to swamp a real effect — hence finals at a thousand-plus samples, and
  controls that must beat the floor by a clear multiple (RULES 9).
- Light tree on (default); `light_sampling_threshold` is ignored while it is on.
- **Fireflies vs real highlights:** per region compare the raw *mean / median* (≈ 1 clean, ≫ 1 =
  energy in rare samples) and look again in an independent render: real caustic hot spots span
  several pixels and land on the same pixels; fireflies are lone random pixels. Remove fireflies
  *before* the denoiser (clamping; luxcore.md › Fireflies) — OIDN smears them into blotches.

## Biased settings — use knowingly
Bounce caps (energy beyond is lost), `sample_clamp_indirect` (keep direct at 0), Filter Glossy,
caustics off, Fast GI, `volume_biased`, shadow-transparent glass. Unbiased: Russian roulette
(`min_light_bounces`), adaptive sampling, blue-noise pattern, denoising (post).

## Memory
Check VRAM before committing to a heavy scene; adaptive subdivision across large diced surfaces
is the usual way to exhaust it. Tools: `texture_limit_render`, `texture_resolution_render` (5.2);
5.2 Texture Cache (`render.use_texture_cache`; auto-generate writes `.tx` beside each image — set
Preferences `texture_cache_directory` first to keep `library/` clean); a large `tile_size`
(small tiles are slow on GPU); instances (Alt+D); `use_persistent_data` for re-render loops.

## Colour management
Per-file working space (Rec.709 default / Rec.2020 / ACEScg) — pick it at project start, because
changing it later re-reads every material. Views: AgX (our default), ACES 2.0, Khronos PBR
Neutral. Pick the AgX look from the reference's contrast, not from habit. `film_exposure` acts on
render data, `view_settings.exposure` on the view; we set exposure via `physical_camera`.
