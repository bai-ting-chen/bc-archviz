"""Tile Fab thumbnails from fab-search.js rows into one labelled contact sheet.

Usage (MCP venv python, it has Pillow):
    python fab_sheet.py <rows.json> <sheet.png> [--cols 4]
Thumbnails are cached next to the sheet in thumbs/. Each tile is labelled with the
Megascans id (or the download file for Megaplants), the title and the scan size.
"""
import argparse
import json
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

THUMB_HOST = "https://media.fab.com/"  # the only host thumbnails are fetched from
TILE_W, TILE_H = 320, 180              # px, Fab's 16:9 previews
LABEL_H = 34                           # px, two text lines under each tile
UA = {"User-Agent": "ArchvizBlenderPipeline/0.1"}


def tile_key(row, index):
    """Name a row by its Megascans id, else its download file, else its position."""
    return row.get("id") or os.path.splitext(row.get("file") or "")[0] or f"row{index:03d}"


def fetch_thumb(url, dst):
    """Download one thumbnail into the cache unless it is already there."""
    if os.path.exists(dst):
        return
    if not url or not url.startswith(THUMB_HOST):
        raise ValueError(f"not a Fab thumbnail: {url}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        data = r.read()
    with open(dst, "wb") as f:
        f.write(data)


def draw_tile(sheet, draw, font, row, key, path, x, y):
    """Paste one thumbnail at (x, y) with its two label lines below."""
    try:
        img = Image.open(path).convert("RGB").resize((TILE_W, TILE_H))
        sheet.paste(img, (x, y))
    except (OSError, ValueError):
        draw.text((x + 8, y + 8), "no thumbnail", fill="white", font=font)
    scan = row.get("scan") or row.get("species") or ""
    draw.text((x + 4, y + TILE_H + 2), key, fill="yellow", font=font)
    draw.text((x + 4, y + TILE_H + 17), f"{row['title'][:34]}  {scan}", fill="white", font=font)


def build_sheet(rows, out, cols):
    """Fetch every row's thumbnail and write the tiled sheet to out."""
    thumbs = os.path.join(os.path.dirname(os.path.abspath(out)), "thumbs")
    lines = -(-len(rows) // cols)  # ceiling division
    sheet = Image.new("RGB", (cols * TILE_W, lines * (TILE_H + LABEL_H)), "black")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, row in enumerate(rows):
        key = tile_key(row, i)
        path = os.path.join(thumbs, key + ".jpg")
        try:
            fetch_thumb(row.get("thumb"), path)
        except Exception as ex:
            print(f"thumbnail failed for {key}: {ex}")
        draw_tile(sheet, draw, font, row, key, path, (i % cols) * TILE_W, (i // cols) * (TILE_H + LABEL_H))
    sheet.save(out)
    print(f"{len(rows)} tiles -> {out}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("rows")
    p.add_argument("out")
    p.add_argument("--cols", type=int, default=4)
    a = p.parse_args()
    with open(a.rows, encoding="utf-8") as f:
        build_sheet(json.load(f), a.out, a.cols)


if __name__ == "__main__":
    main()
