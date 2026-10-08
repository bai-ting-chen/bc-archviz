"""Turn a YouTube tutorial into material Claude can study: metadata, a clean timestamped
transcript, and (optionally) key frames at scene changes. Uses yt-dlp + ffmpeg (winget).

    python yt_learn.py <url-or-id> <out_dir> [--frames] [--max-height 1080] [--scene 0.12] [--every 8]
    python yt_learn.py search "<query>" [--n 5]

Output in <out_dir>/<video id>/: info.json (title, channel, chapters, description),
transcript.txt ("[mm:ss] text", de-duplicated auto-captions), frames/*.jpg (with --frames;
named by timestamp). The downloaded video is deleted after frame extraction.
Use: evidence, not authority -- verify against the manual and a control render; never copy
transcripts into the skill, summarise in our own words and credit the video.
"""
import glob
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINKS = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "WinGet", "Links")
YTDLP = os.path.join(LINKS, "yt-dlp.exe")
FFMPEG = os.path.join(LINKS, "ffmpeg.exe")


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def search(query, n=5):
    r = run([YTDLP, f"ytsearch{n}:{query}", "--skip-download", "--print",
             "%(id)s | %(duration_string)s | %(channel)s | %(upload_date)s | %(title)s"])
    print(r.stdout.strip())


def _ts(s):
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))


def clean_vtt(path):
    """Auto-captions repeat each line across cues and carry inline timing tags: keep each new line once."""
    out, seen_last = [], ""
    cue_t = None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        m = re.match(r"(\d+:\d+:\d+[.,]\d+) -->", line)
        if m:
            cue_t = _ts(m.group(1))
            continue
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:")) or line.isdigit():
            continue
        text = re.sub(r"<[^>]+>", "", line).strip()
        if text and text != seen_last:
            if not (out and text in out[-1][1]):
                out.append((cue_t or 0.0, text))
            seen_last = text
    return [f"[{int(t // 60):02d}:{int(t % 60):02d}] {s}" for t, s in out]


def learn(url, out_dir, frames=False, max_height=1080, scene=0.12, every=8):
    meta = json.loads(run([YTDLP, url, "--skip-download", "-J"]).stdout)
    vid = meta["id"]
    d = os.path.join(out_dir, vid)
    os.makedirs(d, exist_ok=True)
    info = {k: meta.get(k) for k in ("id", "title", "channel", "upload_date", "duration_string",
                                       "webpage_url", "description", "chapters", "tags")}
    json.dump(info, open(os.path.join(d, "info.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    run([YTDLP, url, "--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en.*,en",
         "--sub-format", "vtt", "-o", os.path.join(d, "subs.%(ext)s")])
    vtts = sorted(glob.glob(os.path.join(d, "subs*.vtt")), key=lambda p: ("orig" in p, p))
    lines = clean_vtt(vtts[0]) if vtts else ["(no captions available)"]
    open(os.path.join(d, "transcript.txt"), "w", encoding="utf-8").write("\n".join(lines))
    for v in vtts:
        os.remove(v)
    n_frames = 0
    if frames:
        video = os.path.join(d, "video.mp4")
        run([YTDLP, url, "-f", f"bv*[height<={max_height}][ext=mp4]/b[height<={max_height}]",
             "-o", video, "--no-playlist"])
        fd = os.path.join(d, "frames")
        os.makedirs(fd, exist_ok=True)
        # one frame per scene change (node graphs, panels); showinfo logs each kept frame's time,
        # frames are written in order, so the n-th logged pts_time belongs to frame n
        r = run([FFMPEG, "-hide_banner", "-loglevel", "info", "-i", video, "-vf",
                 # scene changes OR at least one frame every `every` seconds (screen recordings
                 # change subtly -- node graphs grow without a "cut")
                 f"select='gt(scene,{scene})+isnan(prev_selected_t)+gte(t-prev_selected_t,{every})',"
                 "showinfo,scale=1280:-2", "-fps_mode", "vfr",  # ffmpeg 9: no -vsync
                 os.path.join(fd, "f_%05d.jpg")])
        times = [float(t) for t in re.findall(r"pts_time:\s*([0-9.]+)", r.stderr)]
        for i, f in enumerate(sorted(glob.glob(os.path.join(fd, "f_*.jpg")))):
            t = times[i] if i < len(times) else 0.0
            os.replace(f, os.path.join(fd, f"t{int(t // 60):02d}m{int(t % 60):02d}s_{i:03d}.jpg"))
        n_frames = len(os.listdir(fd))
        if os.path.exists(video):
            os.remove(video)
    print(json.dumps({"dir": d, "title": info["title"], "channel": info["channel"],
                      "transcript_lines": len(lines), "chapters": len(info.get("chapters") or []),
                      "frames": n_frames}, ensure_ascii=False))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "search":
        search(a[1], int(a[a.index("--n") + 1]) if "--n" in a else 5)
    else:
        mh = int(a[a.index("--max-height") + 1]) if "--max-height" in a else 1080
        sc = float(a[a.index("--scene") + 1]) if "--scene" in a else 0.12
        ev = float(a[a.index("--every") + 1]) if "--every" in a else 8
        learn(a[0], a[1], frames="--frames" in a, max_height=mh, scene=sc, every=ev)
