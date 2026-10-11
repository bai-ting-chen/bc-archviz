# Learning from YouTube

Tools: yt-dlp (+ Deno, FFmpeg) via winget, in `%LOCALAPPDATA%\Microsoft\WinGet\Links\`. Config
`%APPDATA%\yt-dlp\config.txt` (`--js-runtimes`, `--ffmpeg-location`) needs forward slashes, quoted.

    python scripts/yt_learn.py search "<query>" --n 8
    python scripts/yt_learn.py <id> <study>/_wip/video [--frames --max-height 1080 --every 8]

Output `<dir>/<id>/`: `info.json`, `transcript.txt` (`[mm:ss]`), `frames/` (only with `--frames`;
the video is deleted). Prefer captions-only (YouTube terms discourage downloads). Outputs go in
the study's `_wip/` (RULES 10d); delete frames once the notes are written. Run with the MCP venv python (prints UTF-8).

Reading: chapters + transcript first; frames only for exact node values; verify against the manual
and a control render before anything enters the skill; summarise in our own words with credit
(title, channel, id); prefer the native, physically based variant (RULES 1–2).

FFmpeg 9: `-fps_mode vfr` (no `-vsync`); timestamps from the `showinfo` log; add a periodic frame
(`gte(t-prev_selected_t,8)`) to scene detection.
