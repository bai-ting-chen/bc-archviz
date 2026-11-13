"""Fit mask levels to screen-space coverage, mean and SD without changing spatial scale."""
import numpy as np


def statistics(field):
    """Measure a rendered factor; coverage counts pixels above 0.01."""
    return dict(mean=float(field.mean()), sd=float(field.std()), coverage=float(np.mean(field > .01)))


def remap(samples, parameters, extent=1.):
    """Apply levels/gamma to the scan, then fixed location extent and amount before pixel averaging."""
    black, width, gamma, amount = parameters
    return (np.clip((samples - black) / width, 0, 1) ** gamma * extent * amount).mean(axis=-1)


def fit_levels(samples, target, hard=False, extent=None):
    """Fit three AOV statistics with levels, gamma and amount; hard favours narrow levels."""
    # Fixed subsets keep the numerical fit reproducible and inexpensive.
    pixels = samples.reshape(-1, samples.shape[-1])
    stride = max(1, len(pixels) // 4000)
    pixels = pixels[::stride].astype(np.float64)
    location = 1. if extent is None else extent.reshape(-1, samples.shape[-1])[::stride].astype(np.float64)
    desired = np.array([target[k] for k in ('mean', 'sd', 'coverage')])
    tolerance = np.array([max(.0003, desired[0] * .02), max(.001, desired[1] * .02), .01])

    def decode(x):
        return np.array([x[0], np.exp(x[1]), np.exp(x[2]), np.exp(x[3])])

    def objective(x):
        black, width, gamma, amount = decode(x)
        if not (-.25 <= black < 1 and .0001 <= width <= 2 and .05 <= gamma <= 30 and .001 <= amount <= 1):
            return 1e12
        field = remap(pixels, (black, width, gamma, amount), location)
        measured = np.array([field.mean(), field.std(), np.mean(field > .01)])
        penalty = max(0, width - .08) ** 2 * 100 if hard else 0
        return float(np.sum(((measured - desired) / tolerance) ** 2) + penalty)

    active = pixels if extent is None else pixels[location > 0]
    eligible = 1. if extent is None else float(np.mean(np.any(location > 0, axis=-1)))
    threshold = float(np.quantile(active, 1 - min(1., target['coverage']/eligible)))
    starts = []
    for gamma in (.4, 1, 3):
        width = max(.01, float(np.quantile(active, .995)) - threshold)
        starts.append(np.array([threshold, np.log(width), np.log(gamma), np.log(.95)]))
    best = None
    for start in starts:
        point, error = _simplex(objective, start, (.02, .5, .5, .2))
        if best is None or error < best[1]:
            best = point, error
    black, width, gamma, amount = decode(best[0])
    return dict(black=float(black), white=float(black + width), gamma=float(gamma), amount=float(amount),
                predicted=statistics(remap(pixels, (black, width, gamma, amount), location)), objective=best[1])


def _simplex(function, start, steps, iterations=280):
    points = [start.copy()]
    for i, step in enumerate(steps):
        point = start.copy()
        point[i] += step
        points.append(point)
    scores = [function(p) for p in points]
    for _ in range(iterations):
        order = np.argsort(scores)
        points = [points[i] for i in order]
        scores = [scores[i] for i in order]
        centre = np.mean(points[:-1], axis=0)
        reflection = centre + (centre - points[-1])
        reflected = function(reflection)
        if reflected < scores[0]:
            expansion = centre + 2 * (reflection - centre)
            expanded = function(expansion)
            points[-1], scores[-1] = (expansion, expanded) if expanded < reflected else (reflection, reflected)
        elif reflected < scores[-2]:
            points[-1], scores[-1] = reflection, reflected
        else:
            contraction = centre + .5 * (points[-1] - centre)
            contracted = function(contraction)
            if contracted < scores[-1]:
                points[-1], scores[-1] = contraction, contracted
            else:
                for i in range(1, len(points)):
                    points[i] = points[0] + .5 * (points[i] - points[0])
                    scores[i] = function(points[i])
    index = int(np.argmin(scores))
    return points[index], scores[index]


def prefilter_mask(out, candidate, pixels, metres_per_pixel, sigma_pixels=.5):
    """Average unresolved scan detail before nonlinear levels; retain the 4K grid and scan size."""
    import OpenImageIO as oiio
    from effects.wear.masks import mask_dimensions_m
    # The footprint is in final-view pixels, independent of the asset's listed size.
    sigma_m = sigma_pixels * metres_per_pixel
    width_m, height_m = mask_dimensions_m(candidate['size_m'])
    sigma_x = sigma_m * pixels.shape[1] / width_m
    sigma_y = sigma_m * pixels.shape[0] / height_m
    frequencies_x = np.fft.rfftfreq(pixels.shape[1])[None, :]
    frequencies_y = np.fft.fftfreq(pixels.shape[0])[:, None]
    transfer = np.exp(-2 * np.pi ** 2 * (sigma_x**2 * frequencies_x**2 + sigma_y**2 * frequencies_y**2))
    filtered = np.fft.irfft2(np.fft.rfft2(pixels) * transfer, s=pixels.shape).astype(np.float32)
    path = out / (candidate['id'] + '-prefilter.exr')
    writer = oiio.ImageOutput.create(str(path))
    writer.open(str(path), oiio.ImageSpec(pixels.shape[1], pixels.shape[0], 1, oiio.FLOAT))
    writer.write_image(filtered[..., None])
    writer.close()
    return path, dict(sigma_m=sigma_m, sigma_pixels=sigma_pixels, sigma_texels_xy=[sigma_x, sigma_y],
                      resolution_px=list(pixels.shape), wrap='periodic')

