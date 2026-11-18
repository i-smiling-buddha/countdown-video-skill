"""Lay user-supplied trailer clips into the rendered video (full frame, letterboxed) with a
lower-third title, and extract each clip's audio for the mix.

Usage: python3 compose_clips.py _work/   (reads _work/timeline.json + _work/video.mp4,
writes _work/video_clips.mp4 and _work/clipaudio_K.wav)
Clip paths in items.json are resolved by build_countdown.py. `start` accepts 75, "1:15" or "0:01:15".
"""
import json, os, subprocess, sys, pathlib
from playwright.sync_api import sync_playwright

work = sys.argv[1]
tl = json.load(open(os.path.join(work, "timeline.json")))
clips = [s for s in tl if s["kind"] == "clip"]
if not clips: print("no clips"); sys.exit(0)

def secs(v):
    if isinstance(v, (int, float)): return float(v)
    p = [float(x) for x in str(v).split(":")]; t = 0
    for x in p: t = t * 60 + x
    return t

# lower-third title cards, rendered with a transparent background
lt = []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1920, "height": 1080})
    for k, s in enumerate(clips):
        title = (s.get("title") or "").replace("&", "&amp;").replace("<", "&lt;")
        year = f" ({s['year']})" if s.get("year") else ""
        html = f"""<html><body style="margin:0;background:transparent"><svg width="1920" height="1080">
<g transform="translate(70 930)"><rect x="0" y="-70" width="{max(520, 30*len(title+year)+80)}" height="110" rx="20" fill="#0E1C2D" fill-opacity=".82"/>
<rect x="0" y="-70" width="12" height="110" rx="6" fill="#F0385C"/>
<text x="40" y="-22" font-family="Poppins,sans-serif" font-weight="700" font-size="26" fill="#FFE34D">TRAILER</text>
<text x="40" y="22" font-family="Poppins,sans-serif" font-weight="700" font-size="44" fill="#fff">{title}{year}</text></g></svg></body></html>"""
        pg.set_content(html); out = os.path.join(work, f"lowerthird_{k}.png")
        pg.screenshot(path=out, omit_background=True); lt.append(out)
    b.close()

D = tl[-1]["start"] + tl[-1]["dur"]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(work, "video.mp4")]
for s in clips:
    cmd += ["-ss", str(secs(s["clip"].get("start", 0))), "-t", str(s["dur"]), "-i", s["clip"]["file"]]
for f in lt:
    cmd += ["-loop", "1", "-t", f"{D:.2f}", "-i", f]
fc, last, n = [], "[0:v]", len(clips)
for k, s in enumerate(clips):
    a, b = s["start"], s["start"] + s["dur"]
    fc.append(f"[{k+1}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30,setpts=PTS-STARTPTS+{a}/TB[c{k}]")
    fc.append(f"{last}[c{k}]overlay=0:0:enable='between(t,{a},{b-0.01})':eof_action=pass[v{k}]")
    fc.append(f"[{n+1+k}:v]format=rgba,fade=t=in:st={a+0.6}:d=0.4:alpha=1,fade=t=out:st={a+5.6}:d=0.4:alpha=1[l{k}]")
    fc.append(f"[v{k}][l{k}]overlay=0:0:enable='between(t,{a+0.5},{a+6.1})'[w{k}]")
    last = f"[w{k}]"
cmd += ["-filter_complex", ";".join(fc), "-map", last, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-t", f"{D:.3f}", os.path.join(work, "video_clips.mp4")]
subprocess.run(cmd, check=True)
for k, s in enumerate(clips):
    out = os.path.join(work, f"clipaudio_{k}.wav")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(secs(s["clip"].get("start", 0))), "-t", str(s["dur"]), "-i", s["clip"]["file"], "-vn", "-ac", "1", "-ar", "48000", out])
    if r.returncode != 0 and os.path.exists(out): os.remove(out)
print(f"{len(clips)} clips laid in -> video_clips.mp4")
