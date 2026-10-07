# Render settings (Cycles 5.2)

`archviz.render_setup(w, h, samples, look)`: GPU, adaptive 0.01, denoise, AgX, bounces 12.
Times (3060 Ti): 1000² 256 spp night interior ≈ 14 s; 1600² 1024 spp ≈ 145 s; first OptiX run in a
fresh Blender compiles kernels (~80 s).

## Sampling and denoising
- Adaptive threshold 0.01 for stills (0.005 for finals); min samples auto.
- **Final-render denoising runs on CPU by default** — set `cycles.denoising_use_gpu = True`.
- Denoiser: manual rates **OIDN** highest quality (GPU on RTX); prefilter ACCURATE, quality HIGH,
  passes RGB_ALBEDO_NORMAL. OptiX for previews. *(OIDN vs OptiX crop A/B not yet run.)*
- Noise floor: at 256 spp + denoise a seed change alone gave diff 0.83 — finals need ≥ 1024 spp.
- Light tree on (default); `light_sampling_threshold` is ignored while it is on.

## Biased settings — use knowingly
Bounce caps (energy beyond is lost), `sample_clamp_indirect` (keep direct at 0), Filter Glossy,
caustics off, Fast GI, `volume_biased`, shadow-transparent glass. Unbiased: Russian roulette
(`min_light_bounces`), adaptive sampling, blue-noise pattern, denoising (post).

## Memory (8 GB)
`texture_limit_render`, `texture_resolution_render` (5.2); 5.2 Texture Cache
(`render.use_texture_cache`; auto-generate writes `.tx` into `blender_tx/` beside each image — set
Preferences `texture_cache_directory` first to keep `library/` clean); `tile_size` 2048 (small tiles
are slow on GPU); instances (Alt+D); `use_persistent_data` for re-render loops.

## Colour management
Per-file working space (Rec.709 default / Rec.2020 / ACEScg) — pick at project start. Views: AgX
(our default, "Medium High Contrast" look), ACES 2.0, Khronos PBR Neutral. `film_exposure` acts on
render data, `view_settings.exposure` on the view; we set exposure via `physical_camera`.
