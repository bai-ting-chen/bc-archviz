"""Tile asset thumbnails into one labelled contact sheet.

Rows come from fab-search.js (Quixel on Fab) or maxtree_search.py --out (Maxtree).
Usage (MCP venv python, it has Pillow):
    python asset_sheet.py <rows.json> <sheet.png> [--columns 4]
Thumbnails are cached next to the sheet in thumbs/. Each tile is labelled with the asset id
(or the download file for Megaplants), the title and the real size.
"""
import argparse
import json
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageOps

THUMB_HOSTS = ("https://media.fab.com/", "https://maxtree.org/wp-content/uploads/")  # the only hosts fetched from
TILE_WIDTH_PX, TILE_HEIGHT_PX = 320, 180              # px, 16:9; other shapes are fitted inside
LABEL_HEIGHT_PX = 34                           # px, two text lines under each tile
REQUEST_HEADERS = {"User-Agent": "ArchvizBlenderPipeline/0.1"}


def tile_key(row, index):
    """Name a row by its asset id, else its download file, else its position."""
    return row.get("id") or os.path.splitext(row.get("file") or "")[0] or f"row{index:03d}"


def cache_name(url):
    """Cache a thumbnail under its own image file name (unique per image on both hosts)."""
    return url.rstrip("/").rsplit("/", 1)[-1] if url else ""


def fetch_thumbnail(url, dst):
    """Download one thumbnail into the cache unless it is already there."""
    if os.path.exists(dst):
        return
    if not url or not url.startswith(THUMB_HOSTS):
        raise ValueError(f"not a known thumbnail host: {url}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=REQUEST_HEADERS)) as r:
        data = r.read()
    with open(dst, "wb") as f:
        f.write(data)


def draw_tile(sheet, draw, font, row, key, path, x, y):
    """Paste one thumbnail at (x, y) with its two label lines below."""
    try:
        img = ImageOps.contain(Image.open(path).convert("RGB"), (TILE_WIDTH_PX, TILE_HEIGHT_PX))
        sheet.paste(img, (x + (TILE_WIDTH_PX - img.width) // 2, y + (TILE_HEIGHT_PX - img.height) // 2))
    except (OSError, ValueError):
        draw.text((x + 8, y + 8), "no thumbnail", fill="white", font=font)
    scan = row.get("scan") or row.get("size") or row.get("species") or ""
    draw.text((x + 4, y + TILE_HEIGHT_PX + 2), key, fill="yellow", font=font)
    draw.text((x + 4, y + TILE_HEIGHT_PX + 17), f"{row['title'][:34]}  {scan}", fill="white", font=font)


def build_sheet(rows, out, cols):
    """Fetch every row's thumbnail and write the tiled sheet to out."""
    if not rows:
        print("no rows: the search found nothing, no sheet written")
        return
    thumbs = os.path.join(os.path.dirname(os.path.abspath(out)), "thumbs")
    lines = -(-len(rows) // cols)  # ceiling division
    sheet = Image.new("RGB", (cols * TILE_WIDTH_PX, lines * (TILE_HEIGHT_PX + LABEL_HEIGHT_PX)), "black")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, row in enumerate(rows):
        key = tile_key(row, i)
        path = os.path.join(thumbs, cache_name(row.get("thumb")) or key + ".jpg")
        try:
            fetch_thumbnail(row.get("thumb"), path)
        except Exception as ex:
            print(f"thumbnail failed for {key}: {ex}")
        draw_tile(sheet, draw, font, row, key, path, (i % cols) * TILE_WIDTH_PX, (i // cols) * (TILE_HEIGHT_PX + LABEL_HEIGHT_PX))
    sheet.save(out)
    print(f"{len(rows)} tiles -> {out}")


def main():
    """Command line: rows JSON in, contact sheet PNG out."""
    p =argparse.ArgumentParser()
    p.add_argument("rows")
    p.add_argument("out")
    p.add_argument("--columns", type=int, default=4, dest='cols')
    a = p.parse_args()
    with open(a.rows, encoding="utf-8") as f:
        build_sheet(json.load(f), a.out, a.cols)


if __name__ == "__main__":
    main()
