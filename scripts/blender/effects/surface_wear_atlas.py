"""Pack chosen decal colour and opacity maps without changing their physical aspect ratios."""
from dataclasses import dataclass
import math
from pathlib import Path


@dataclass
class StampAtlas:
    """RGBA atlas with physical sizes, metre cell spacing and 0–1 occupied-cell probability."""
    path: str
    sizes_m: tuple
    columns: int
    rows: int
    cell_m: float = 3.2
    density: float = .8
    scale_min: float = .7
    scale_max: float = 1.1
    centre_jitter: float = .2
    tilt_deg: float = 7.
    profile: str = 'tone'
    opacity_white: float = 1.
    rim_m: float = .015
    anchor: str = 'centre'
    cutout_indices: tuple = ()


def _texture_cutout(alpha):
    """Extract an irregular, zero-bordered piece from a continuous opacity texture."""
    import numpy as np
    height,width=alpha.shape
    # Coarse source averages choose the outline; no second procedural noise implementation.
    coarse=np.array([[block.mean() for block in np.array_split(rows,6,axis=1)]
                     for rows in np.array_split(alpha,6,axis=0)])
    x=np.linspace(0,5,width)
    y=np.linspace(0,5,height)
    horizontal=np.array([np.interp(x,np.arange(6),row) for row in coarse])
    field=np.array([np.interp(y,np.arange(6),column) for column in horizontal.T]).T
    black,white=np.quantile(coarse,(.4,.85))
    shape=np.clip((field-black)/max(white-black,1e-6),0,1)
    u=np.linspace(0,1,width)[None,:]
    v=np.linspace(0,1,height)[:,None]
    border=np.minimum(np.minimum(u,1-u),np.minimum(v,1-v))
    return shape*np.clip(border/.13,0,1)**2


def _deposit_tile(tile,soft_opacity,size_m,scatter,cutout):
    """Pack linear source tone, a broad dark rim and normalized opacity as independent data."""
    import numpy as np
    opacity=tile[...,3]
    footprint=_texture_cutout(opacity) if cutout else 1
    white=scatter.get('opacity_white',1.)
    alpha=(np.clip(opacity/white,0,1)**.65)*footprint
    support=(np.clip(soft_opacity/white,0,1)**.65)*footprint
    tile_px=alpha.shape[0]
    radius_x=max(1,round(scatter.get('rim_m',.015)/size_m[0]*tile_px))
    radius_y=max(1,round(scatter.get('rim_m',.015)/size_m[1]*tile_px))
    padded=np.pad(support,((radius_y,radius_y),(radius_x,radius_x)),mode='constant')
    eroded=support.copy()
    for dy in (-radius_y,0,radius_y):
        for dx in (-radius_x,0,radius_x):
            eroded=np.minimum(eroded,padded[radius_y+dy:radius_y+dy+tile_px,radius_x+dx:radius_x+dx+tile_px])
    rgb=tile[...,:3]
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    tile[...,0]=linear @ np.array((.2126,.7152,.0722))
    tile[...,1]=np.clip((support-eroded)*2.5,0,1)
    tile[...,2]=0
    tile[...,3]=alpha


def build_stamp_atlas(project, asset_ids, path, tile_px=768, **scatter):
    """Pack 4K colour/opacity into a derived tone, deposit-data or chip-opacity atlas."""
    import numpy as np
    import OpenImageIO as oiio
    from effects.surface_wear_masks import asset_maps, scan_size_m
    columns = math.ceil(math.sqrt(len(asset_ids)))
    rows = math.ceil(len(asset_ids)/columns)
    pixels = np.zeros((rows*tile_px, columns*tile_px, 4), dtype=np.float32)
    sizes = []
    for index, asset_id in enumerate(asset_ids):
        asset = asset_maps(asset_id, ('BaseColor', 'Opacity'), project)
        if asset is None:
            raise FileNotFoundError('Missing chosen decal maps: ' + asset_id)
        maps, metadata = asset
        sizes.append(scan_size_m(metadata))
        resized = {}
        for name, source in maps.items():
            buf = oiio.ImageBuf(str(source))
            resized[name] = oiio.ImageBufAlgo.resize(buf, roi=oiio.ROI(0,tile_px,0,tile_px)).get_pixels()
        row, column = divmod(index, columns)
        tile = pixels[row*tile_px:(row+1)*tile_px, column*tile_px:(column+1)*tile_px]
        tile[..., :3] = resized['BaseColor'][..., :3]
        tile[..., 3] = resized['Opacity'][..., 0]
        if scatter.get('profile')=='deposit':
            source=oiio.ImageBuf(str(maps['Opacity']))
            low=oiio.ImageBufAlgo.resize(source,roi=oiio.ROI(0,96,0,96))
            soft=oiio.ImageBufAlgo.resize(low,roi=oiio.ROI(0,tile_px,0,tile_px)).get_pixels()[...,0]
            _deposit_tile(tile,soft,sizes[-1],scatter,index in scatter.get('cutout_indices',()))
    writer = oiio.ImageOutput.create(str(path))
    spec = oiio.ImageSpec(columns*tile_px, rows*tile_px, 4, oiio.UINT8)
    spec.alpha_channel = 3
    spec.attribute('oiio:UnassociatedAlpha',1)
    writer.open(str(path), spec)
    writer.write_image(pixels)
    writer.close()
    return StampAtlas(str(Path(path)), tuple(sizes), columns, rows, **scatter)
