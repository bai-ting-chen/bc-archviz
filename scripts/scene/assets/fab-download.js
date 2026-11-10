// Add the user's picked Quixel listings to their Fab library and return a direct download link per pick.
// Runs in a fab.com tab of the built-in browser where the user is signed in, after fab-search.js
// (reuses fabJson). The links are signed and expire within minutes: save the result as JSON and run
// fab_fetch.py on it at once.
// Usage: send fab-search.js, then this file's text, then
//   await fabDownloadLinks(picks)
// where picks are fabSearch rows (or {link, file}) with `file` set to the chosen download file.

const FAB_LICENSE = "professional";  // free for Quixel; studio work needs the professional licence

function fabCsrf() {
  return document.cookie.match(/fab_csrftoken=([^;]+)/)[1];
}

// Add a listing to the user's library under FAB_LICENSE; Fab answers 204, also when it is already there.
async function fabAddToLibrary(uid, listing) {
  const offer = listing.licenses.find(l => l.slug === FAB_LICENSE);
  if (!offer || offer.priceTier.price !== 0) throw new Error(`${uid}: no free ${FAB_LICENSE} licence`);
  const body = new FormData();
  body.append("offer_id", offer.offerId);
  const r = await fetch(`/i/listings/${uid}/add-to-library`, {method: "POST", headers: {"X-CsrfToken": fabCsrf()}, body});
  if (!r.ok) throw new Error(`${uid}: add to library failed (${r.status})`);
}

// Find the named file among the listing's formats and return its signed link and size in bytes.
async function fabFileLink(uid, listing, fileName) {
  for (const format of listing.assetFormats.map(f => f.assetFormatType.code)) {
    const d = await fabJson(`/i/listings/${uid}/asset-formats/${format}`);
    const file = d && d.files && d.files.find(f => f.name === fileName);
    if (!file) continue;
    const info = await fabJson(`/i/listings/${uid}/asset-formats/${format}/files/${file.uid}/download-info`);
    if (!info) throw new Error(`${fileName}: no download link (signed in?)`);
    return {url: info.downloadInfo[0].downloadUrl, size: file.size};
  }
  throw new Error(`${uid}: no file named ${fileName}`);
}

async function fabDownloadLinks(picks) {
  if ((await fetch("/i/users/me")).status !== 200) throw new Error("not signed in to Fab in this pane");
  const out = [];
  for (const pick of picks) {
    const uid = pick.link.split("/listings/")[1];
    const listing = await fabJson(`/i/listings/${uid}`);
    await fabAddToLibrary(uid, listing);
    out.push({...pick, license: `Fab Standard License (${FAB_LICENSE})`, ...await fabFileLink(uid, listing, pick.file)});
  }
  return out;
}
