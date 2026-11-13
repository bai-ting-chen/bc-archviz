"""Search the Maxtree plant catalog and write candidate rows for asset_sheet.py.

Maxtree's shop answers its public WooCommerce Store API over plain HTTP. Its search matches
Latin names only, so the whole catalog (about 2,400 products, 25 requests) is fetched into
<dir>/catalog.json and searched locally, common names included.

Usage:
    python maxtree_search.py <study>/_wip/maxtree fetch
    python maxtree_search.py <study>/_wip/maxtree search <words> [--category Conifers]
        [--min-height-cm 300] [--max-height-cm 800] [--top 24] [--out rows.json]
Words match the model name, Latin and common names, the species a volume holds, variant names
and categories (all words must match).
Heights are in cm, per variant; a model matches when any variant lies in the range.
"""
import argparse
import html
import json
import os
import re
import time
import urllib.request

CATALOG_API_URL = "https://maxtree.org/wp-json/wc/store/v1/products"
REQUEST_HEADERS = {"User-Agent": "ArchvizBlenderPipeline/0.1"}
PAGE_SIZE = 100          # the Store API's largest page
PAUSE_S = 0.5       # between pages, to stay gentle on the shop
STALE_DAYS = 7      # refetch the catalog when it is older than this
CATALOG_SCHEMA_VERSION = 3          # bump when model_row changes, so old caches are refetched

VARIANT_PATTERN = re.compile(r"(MT_\w+):\s*\(\s*Polygons:\s*(\d+)\s*\),\s*\(\s*Height:\s*(\d+)\s*cm\s*\)")
COMMON_NAME_PATTERN = re.compile(r"referred to as ([^.]+)\.")
SPECIES_PATTERN = re.compile(r"([A-Z][a-z]+(?: [a-z×.-]+)+)\s*\[([^\]]+)\]")  # "Latin name[Common, names]"
VOLUME_PATTERN = re.compile(r"FROM\s+(Plant Models Vol \d+|[A-Z][\w ]+ Vol \d+)")


def plain(text):
    """HTML to one line of plain text."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def model_row(p):
    """One catalog row from a Store API product."""
    short, desc = plain(p["short_description"]), plain(p["description"])
    variants = [{"name": n, "polygons": int(poly), "height_cm": int(h)} for n, poly, h in VARIANT_PATTERN.findall(desc)]
    heights = [v["height_cm"] for v in variants]
    common = COMMON_NAME_PATTERN.search(short)
    volume = VOLUME_PATTERN.search(short)
    image = p["images"][0] if p["images"] else {}
    latin = re.sub(r"^V\d+_|_\d+$", "", p["name"]).replace("_", " ")
    species = SPECIES_PATTERN.findall(desc)  # every species in the model or volume
    common = common.group(1).strip() if common else ", ".join(c for _, c in species)
    return {
        "id": p["name"],
        "title": common.split(",")[0] or latin,  # the sheet's second label line
        "latin": latin,
        "common": common,
        "species": [f"{latin_name} [{names}]" for latin_name, names in species],
        "categories": [html.unescape(c["name"]) for c in p["categories"]],
        "volume": volume.group(1) if volume else "",
        "pack": not volume and " Vol " in f" {p['name']} ",  # a whole volume, not one model
        "size": f"{min(heights) / 100:g}-{max(heights) / 100:g} m tall" if heights else "",
        "variants": variants,
        "blender": "Blender" in desc,
        "formats": [t["name"] for a in p["attributes"] if a["name"] == "Format" for t in a["terms"]],
        "price_usd": int(p["prices"]["price"]) / 10 ** p["prices"]["currency_minor_unit"],
        "link": p["permalink"],
        "thumb": image.get("thumbnail") or image.get("src"),
    }


def fetch_catalog(folder):
    """Fetch every product page into <folder>/catalog.json and return the rows."""
    rows, page = [], 1
    while True:
        url = f"{CATALOG_API_URL}?per_page={PAGE_SIZE}&page={page}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=REQUEST_HEADERS)) as r:
            products = json.load(r)
        if not products:
            break
        rows.extend(model_row(p) for p in products)
        page += 1
        time.sleep(PAUSE_S)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump({"schema": CATALOG_SCHEMA_VERSION, "rows": rows}, f, ensure_ascii=False)
    print(f"{len(rows)} products -> {folder}")
    return rows


def load_catalog(folder):
    """The cached catalog, refetched when missing, older than STALE_DAYS or of another SCHEMA."""
    path = os.path.join(folder, "catalog.json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < STALE_DAYS * 86400:
        with open(path, encoding="utf-8") as f:
            cache = json.load(f)
        if isinstance(cache, dict) and cache.get("schema") == CATALOG_SCHEMA_VERSION:
            return cache["rows"]
    return fetch_catalog(folder)


def matches(row, words, category, lo, hi):
    """Whether a row has every word, the category and a variant in the height range (cm)."""
    names = [row["id"], row["latin"], row["common"], *row["species"], *row["categories"]]
    text = " ".join(names + [v["name"] for v in row["variants"]]).lower()
    if not all(w.lower() in text for w in words):
        return False
    if category and category.lower() not in (c.lower() for c in row["categories"]):
        return False
    return any(lo <= v["height_cm"] <= hi for v in row["variants"])


def search(folder, words, category, lo, hi, top, out):
    """Print matching models (single models before volume packs) and optionally save them."""
    hits = [r for r in load_catalog(folder) if matches(r, words, category, lo, hi)]
    hits.sort(key=lambda r: (r["pack"], r["id"]))
    for r in hits[:top]:
        blend = "" if r["blender"] else "  (no .blend)"
        print(f"{r['id']:40s} {r['common'][:30]:30s} {r['size']:18s} {r['volume']}{blend}")
    print(f"{len(hits)} match(es), {min(top, len(hits))} shown")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(hits[:top], f, ensure_ascii=False, indent=1)


def main():
    """Command line: fetch the catalog, or search it."""
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("cmd", choices=["fetch", "search"])
    p.add_argument("words", nargs="*")
    p.add_argument("--category")
    p.add_argument("--min-height-cm", type=int, default=0, dest='min_height')
    p.add_argument("--max-height-cm", type=int, default=10 ** 6, dest='max_height')
    p.add_argument("--top", type=int, default=24)
    p.add_argument("--out")
    a = p.parse_args()
    if a.cmd == "fetch":
        fetch_catalog(a.folder)
    else:
        search(a.folder, a.words, a.category, a.min_height, a.max_height, a.top, a.out)


if __name__ == "__main__":
    main()
