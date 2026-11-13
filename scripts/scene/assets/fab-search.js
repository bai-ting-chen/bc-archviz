// Search Quixel assets on Fab and return candidate rows with their Megascans id.
// Fab sits behind Cloudflare, so this runs inside a fab.com tab of the built-in browser pane
// (javascript_tool), where the site's own JSON API answers. No sign-in is needed.
// Usage: send this file's text followed by one call, e.g.
//   await fabSearch({query: "concrete", type: "material", category: "building-human-made--concrete", max_results: 48})
// Options:
//   seller    "Quixel Megascans" (default) or "Quixel Megaplants"
//   type      material | 3d-model | decal | brush (Fab listing type); omit for all
//   category  Fab category slug, e.g. "nature-plants--plants"; omit for all
//   query     keywords
//   max_results  rows to return (Fab pages hold 24; pages are followed until max_results)
//   details   true (default): fetch scan size, maps, Megascans id, download file and size_mb per row (3 requests each)

const FAB_PAGE_SIZE = 24;        // fixed by Fab: larger counts are ignored
const FAB_PAUSE_MS = 250;   // between requests, to stay gentle on the API
const FAB_ID_FORMATS = ["texture-set", "fbx", "image", "gltf", "usd"];  // where download names carry the id

const fabSleep = ms => new Promise(r => setTimeout(r, ms));

async function fabJson(path) {
  await fabSleep(FAB_PAUSE_MS);
  const r = await fetch(path);
  if (!r.ok) return null;
  return r.json();
}

function fabSlug(title) {
  return title.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

// Download names are "<title slug>_<id>_<res or variant>.zip"; Megaplants have no id.
function fabIdFromName(name, title) {
  const prefix = fabSlug(title) + "_";
  const stem = name.toLowerCase();
  if (stem.startsWith(prefix)) {
    const token = stem.slice(prefix.length).split(/[_.]/)[0];
    if (/^[a-z0-9]{5,10}$/.test(token)) return token;
  }
  const m = stem.match(/_([a-z0-9]{5,10})_(?:\d+k|raw|high|mid|low|exr|gltf|ue)\b/);
  return m ? m[1] : null;
}

// Scan area, texel density, maps and species are written in the listing description.
function fabFacts(html) {
  const text = (html || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
  const pick = re => (text.match(re) || [])[1]?.trim() || null;
  return {
    scan: pick(/Scan Area:\s*([0-9.,]+\s*x\s*[0-9.,]+\s*c?m)/i),
    texel: pick(/Texel density:\s*([0-9]+\s*px\/m)/i),
    maps: pick(/Maps:\s*([A-Za-z ]+?)(?= Create | Plant | Quixel |$)/),
    species: pick(/Plant species:\s*([A-Z][a-z]+ [a-z]+)/),
  };
}

// Download files ({name, size} in bytes) of the first format that has any, largest resolution first.
async function fabDownloadFiles(uid, formats) {
  for (const code of FAB_ID_FORMATS.filter(c => formats.includes(c))) {
    const d = await fabJson(`/i/listings/${uid}/asset-formats/${code}`);
    if (d && d.files && d.files.length) return d.files;
  }
  return [];
}

async function fabSearch({seller = "Quixel Megascans", type, category, query, max_results = 24, details = true} = {}) {
  const base = new URLSearchParams({seller, count: String(FAB_PAGE_SIZE)});
  if (type) base.set("listing_types", type);
  if (category) base.set("categories", category);
  if (query) base.set("q", query);
  const hits = [];
  let cursor = null;
  do {
    const p = new URLSearchParams(base);
    if (cursor) p.set("cursor", cursor);
    const page = await fabJson("/i/listings/search?" + p);
    if (!page) break;
    hits.push(...page.results);
    cursor = page.cursors && page.cursors.next;
  } while (cursor && hits.length < max_results);

  const rows = [];
  for (const h of hits.slice(0, max_results)) {
    const formats = h.assetFormats.map(f => f.assetFormatType.code);
    const images = (h.thumbnails[0] && h.thumbnails[0].images) || [];
    const thumb = images.find(i => i.width === 640) || images[images.length - 1];
    const row = {
      title: h.title,
      type: h.listingType,
      category: h.category && h.category.path,
      tags: h.tags.map(t => t.slug).join(","),
      formats: formats.join(","),
      link: `https://www.fab.com/listings/${h.uid}`,
      thumb: thumb ? thumb.url : null,
    };
    if (details) {
      const d = await fabJson(`/i/listings/${h.uid}`);
      Object.assign(row, fabFacts(d && d.description));
      const files = await fabDownloadFiles(h.uid, formats);
      row.id = files.map(f => fabIdFromName(f.name, h.title)).find(Boolean) || null;
      row.file = files[0] ? files[0].name : null;
      row.size_mb = files[0] ? Math.round(files[0].size / 1e6) : null;
    }
    rows.push(row);
  }
  return rows;
}
