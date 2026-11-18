---
name: countdown-video
description: Make Top-N countdown or year-by-year "evolution" videos (movies, box office, ratings or any ranked list) as animated cards with rank/year reveals, optional trailer clips, music, SFX and YouTube chapters, rendered to MP4.
license: MIT
compatibility: Needs code execution with Python 3.10+, ffmpeg and headless Chromium (Playwright).
---

# Countdown Video

Turn a ranked list into a finished list video in the style of movie/list channels. Two modes:

- `"mode": "countdown"` (default): No.N → No.1, an orange "No.X" slam before every entry.
- `"mode": "timeline"`: an "evolution" video (e.g. *LAIKA Animation Evolution 2005–2022*), oldest → newest, a big year card before every entry.

In both modes an entry can carry a **trailer clip** that plays full screen right after its card, with a lower-third title and the trailer's own sound (music ducks underneath). On list channels, card + ~25–30 s of trailer per film is the format that holds viewers longest.

The video has an intro, then for every entry a "No.X" rank slam followed by an animated card (image, title, year, genre, money stats with bars, ratings, a fun fact), a progress tracker, and an end screen with slots for YouTube end-screen elements. Everything is data-driven: research goes into `items.json`, the engine renders it.

Talk to the user in their preferred language; keep code and `items.json` in English unless they want on-screen text in another language.

## Files (relative to this skill folder)

| File | Purpose |
|---|---|
| `templates/countdown_template.html` | The engine: intro, rank cards, item cards, tracker, outro. Theme + timing are overridable from `items.json`. |
| `scripts/build_countdown.py` | `items.json` → `_work/build.html`, `timeline.json`, `cues.json` (SFX), `chapters.txt`; flags missing/unreadable images. |
| `scripts/render.py` | Deterministic frame-range renderer (Playwright → x264). |
| `scripts/compose_clips.py` | Lays each entry's trailer clip in full frame (letterboxed) with a lower-third "TRAILER · Title (Year)", and extracts the clip audio. Run automatically by `make_countdown.sh`. |
| `scripts/countdown_audio.py` | Original upbeat music loop (or `--music your_track.mp3`), whoosh/hit/pop/tick SFX on cues, trailer audio with music ducked to `--clip-music` (default 0.12), optional rank voice. |
| `scripts/make_countdown.sh` | Whole pipeline: build → parallel render → audio → MP4 + QA sheet + chapters. |

Setup: `pip install playwright soundfile scipy pillow --break-system-packages` and `playwright install chromium` if missing; ffmpeg on PATH. Optional voice: Kokoro TTS (see the PPT Animation Skill's `voiceover.py`).

## Workflow

1. **Brief.** Topic, mode (countdown or timeline), how many entries (N), ranking metric (e.g. worldwide box office), which fields to show, whether to include trailer clips (and how long, default 25 s), video length (≈ 5 s intro + N × (~11 s + clip) + 12 s outro), music (user's track or generated). Ask once if the user is present; otherwise pick sensible defaults and say so.
2. **Research the ranking.** Use web search and open the source pages; never fill numbers from memory. Preferred sources: Box Office Mojo / The Numbers (budget, worldwide gross), IMDb, Rotten Tomatoes, Metacritic (ratings), Wikipedia for years and genres. Record the URL(s) in each item's `sources`. If two sources disagree, use one source consistently for the ranking metric and note it. If a value can't be found, leave the field out (the card adapts) — never invent it.
3. **Write `items.json`** (schema below), ranks 1..N where 1 is the top entry. The video counts down N → 1 (`"order": "up"` reverses).
4. **Images and clips.** Use images and trailer files the user supplies (`posters/<slug>.jpg`, 2:3 portrait; `clips/<slug>.mp4`). Do not download posters, trailers, stills or photos of people from the web yourself; ask the user to drop them in the folder. Without an image the card shows a clean title placeholder, and a missing clip is skipped, so a draft can be rendered first. For each clip, pick `start` (skip studio logos and black frames) and `duration`. Trailers can draw Content ID claims on YouTube; that is the channel owner's call, so mention it once.
5. **Build + preview.** `python3 scripts/build_countdown.py items.json _work/` then screenshot a few moments (intro ~3 s, a rank card, a full item card at its end, the outro) and LOOK: nothing overlapping, long titles fit, numbers readable at 360p.
6. **Render.** `bash scripts/make_countdown.sh items.json out.mp4 [chunks] [-- --music track.mp3 --music-vol 0.5 --voice vo_dir]`.
7. **QA.** Open `out_sheet.png`; spot-check numbers against `items.json`; confirm the duration and that every rank appears once.
8. **Deliver.** The MP4, the chapters (`out_chapters.txt`, paste into the YouTube description), the sources list, and a suggested title / description / tags. Remind the user to add the end-screen elements over the outro slots in YouTube Studio.

## `items.json` schema

```json
{
  "title": "Top 5 Highest-Grossing Stop-Motion Movies",
  "subtitle": "Ranked by worldwide box office",
  "channel": "Channel Name",
  "currency": "$",
  "order": "down",
  "mode": "countdown",
  "intro_image": "logo.png",
  "outro_title": "Which one is your favourite?",
  "outro_subtitle": "Tell us in the comments!",
  "timing": {"intro": 5, "rank": 1.8, "item": 9, "outro": 12},
  "theme": {"bgA": "#8BE36A", "bgB": "#F7E25A", "border": "#F0385C", "money": "#9B59D0", "ratings": "#5BD3F5"},
  "items": [
    {
      "rank": 1, "title": "Chicken Run", "year": 2000, "subtitle": "Family/Comedy",
      "image": "posters/chicken-run.jpg",
      "stats": [{"label": "Budget", "value": 45000000}, {"label": "Box Office", "value": 225100000}],
      "multiple": "5x its budget",
      "ratings": {"imdb": 7.1, "rt": 96, "rt_audience": 60, "metacritic": 88},
      "fact": "One short, sourced sentence.",
      "teaser": "optional line under the No.X slam",
      "clip": {"file": "clips/chicken-run-trailer.mp4", "start": "0:12", "duration": 25},
      "label": "optional text for the slam card instead of No.X / the year",
      "seconds": 9,
      "sources": ["https://www.boxofficemojo.com/title/tt0120630/"]
    }
  ]
}
```

- `stats[].value` as a number → animated count-up + comparison bar (bars share one scale per card); as a string → shown as-is (e.g. `"N/A"`, `"8,848 m"`). Any labels work, so the same engine fits non-movie countdowns (tallest buildings, richest people, fastest cars).
- `ratings` keys are optional: `imdb` (0–10, star), `rt` / `rt_audience` / `metacritic` (0–100, ring). Missing keys disappear; a card with no ratings centres its other boxes.
- `clip.start` accepts seconds or `m:ss`; the clip is letterboxed to 16:9 and plays after the card. Chapters and the end-screen timing account for clip length automatically.
- `intro_image` (e.g. a studio logo the user provides) replaces the TOP N / EVOLUTION badge on the intro.
- In timeline mode entries are sorted by `year`; the rank badge on the card is hidden and chapters read "Title (Year)".
- `multiple` is a short highlight pill under the money box; compute it from the sourced numbers (round to one decimal).
- Ratings are shown as text labels only — no brand logos.
- Any rating, number or fact shown on screen must come from a source in `sources`.

## Style notes

- Default theme matches classic list channels: alternating green/yellow crayon-textured cards, red border, orange "No.X" slam with rays, purple money box, blue ratings box. Override any colour in `theme`.
- Readability at 360p: keep titles short (subtitle carries the genre), keep facts ≤ 2 lines, don't add more than 4 stats.
- Retention: ~11 s per entry; put the strongest entries last; the rank slam + whoosh/hit SFX resets attention every entry; keep the intro ≤ 5 s.
- YouTube chapters need ≥ 10 s each, so the intro is folded into the first rank's chapter automatically.
