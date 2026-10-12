# Render settings (Cycles 5.2)

`archviz.render_setup(width, height, samples, look, exposure=0.0)`: GPU, adaptive threshold,
OptiX denoise, AgX, bounces 12. It **sets view exposure** - call it before `physical_camera`.

Render times are a property of the machine, not of the craft — measure once on the box you are
on (first OptiX run in a fresh Blender also pays a one-off kernel compile) and plan iterations
around that, rather than carrying someone else's numbers.

## Sampling and denoising
- Adaptive threshold ~0.01 for working stills, tighter for finals; min samples auto.
- **Final-render denoising runs on CPU by default** — `cycles.denoising_use_gpu = True`
  (`finals.setup_unlimited` sets it).
- Denoiser: the manual rates **OIDN** highest quality (GPU on RTX); prefilter ACCURATE, quality
  HIGH, passes RGB_ALBEDO_NORMAL - finals use it (`finals.setup_unlimited`, and the rebuild from
  passes). OptiX (`render_setup`) for previews and look-dev. *(OIDN vs OptiX crop A/B not yet run.)*
- **Know your noise floor before trusting any comparison.** Render the same frame twice with
  only the seed changed; that difference is the floor. At moderate sample counts with denoising
  it is high enough to swamp a real effect — hence finals at a thousand-plus samples, and the
  control criterion of RULES 9.
- Light tree on (default); `light_sampling_threshold` is ignored while it is on.
- **Fireflies vs real highlights:** per region compare the raw *mean / median* (≈ 1 clean, ≫ 1 =
  energy in rare samples) and look again in an independent render: real caustic hot spots span
  several pixels and land on the same pixels; fireflies are lone random pixels. Remove fireflies
  *before* the denoiser (clamping; luxcore.md › Fireflies) — OIDN smears them into blotches.

## Finals with no sample limit (`finals.py`, RULES 10b)
- Estimate before launch from a full-frame test at the final settings: s/sample measured, raw
  noise in a smooth region at two sample counts; noise ~ 1/sqrt(N). Tell the user the time at
  which more samples stop showing (raw ~1-2 % on a smooth sky with OIDN, ~0.4 % = one 8-bit
  step without) - Blender's own countdown is to the 1e6 cap and means nothing.
- **Auto-tiling:** frames larger than the 2048 px tile render tile by tile; with no limit only
  the first tile ever renders. Auto-tile off **and** tile size > frame (a large frame can still
  show tiles with auto-tile off; read the UI header). The untiled frame and its passes must fit
  VRAM: watch `nvidia-smi` during the full-frame test.
- **Stopping skips the denoiser:** a stop from the viewer fired render_complete but saved
  Combined == Noisy Image; Esc fires render_cancel and skips the compositor. Save every pass
  (multilayer EXR with the denoising passes) and rebuild: `finals.py -- denoise` (OIDN from
  Noisy Image + Albedo + Normal) then `-- png` (the scene's view settings). Means match the raw.
- A fine speckle seen only in a downscaled 8-bit crop can be scaling; check 1:1 and with
  `render.dither_intensity = 0` before chasing it in the scene.

## Biased settings — use knowingly
Bounce caps (energy beyond is lost), `sample_clamp_indirect` (keep direct at 0), Filter Glossy,
caustics off, Fast GI, `volume_biased`, shadow-transparent glass. Unbiased: Russian roulette
(`min_light_bounces`), adaptive sampling, blue-noise pattern, denoising (post).

## Memory
VRAM first (RULES 13). Tools: `texture_limit_render`, `texture_resolution_render` (5.2);
5.2 Texture Cache (`render.use_texture_cache`; auto-generate writes `.tx` beside each image — set
Preferences `texture_cache_directory` first to keep `library/` clean); a large `tile_size`
(small tiles are slow on GPU); instances (Alt+D); `use_persistent_data` for re-render loops.

## Colour management
Per-file working space (Rec.709 default / Rec.2020 / ACEScg) — pick it at project start, because
changing it later re-reads every material. Views: AgX (our default), ACES 2.0, Khronos PBR
Neutral. Pick the AgX look from the reference's contrast, not from habit. `film_exposure` acts on
render data, `view_settings.exposure` on the view; we set exposure via `physical_camera`.
