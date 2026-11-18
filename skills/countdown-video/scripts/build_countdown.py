"""Turn items.json into a renderable countdown page + timeline, SFX cues and YouTube chapters.

Usage: python3 build_countdown.py items.json _work/
Writes _work/build.html, _work/timeline.json, _work/cues.json, _work/chapters.txt
Image paths in items.json are relative to items.json (or absolute). Missing images get a
title card placeholder, and the script lists them so you can add them before rendering.
"""
import json, os, sys, pathlib
from playwright.sync_api import sync_playwright

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
here = pathlib.Path(__file__).resolve().parent
base = pathlib.Path(src).resolve().parent
data = json.load(open(src, encoding="utf-8"))
missing = []
for it in data["items"]:
    img = it.get("image")
    if img:
        p = (base / img).resolve() if not img.startswith(("http", "file:", "data:")) else None
        if p is not None:
            if p.exists(): it["image"] = p.as_uri()
            else: missing.append(img); it.pop("image")
    clip = it.get("clip")
    if clip and clip.get("file"):
        cp = (base / clip["file"]).resolve()
        if cp.exists(): clip["file"] = str(cp)
        else: missing.append(clip["file"]); it.pop("clip")
if data.get("intro_image"):
    ip = (base / data["intro_image"]).resolve()
    if ip.exists(): data["intro_image"] = ip.as_uri()
    else: missing.append(data["intro_image"]); data.pop("intro_image")
tpl = (here.parent / "templates" / "countdown_template.html").read_text(encoding="utf-8")
html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
bp = os.path.join(out, "build.html"); open(bp, "w", encoding="utf-8").write(html)

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1920, "height": 1080})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(pathlib.Path(bp).resolve().as_uri()); pg.wait_for_load_state("networkidle")
    broken = pg.evaluate("Promise.all([...document.querySelectorAll('image')].map(i=>new Promise(r=>{const im=new Image();im.onload=()=>r(null);im.onerror=()=>r(i.getAttribute('href'));im.src=i.getAttribute('href')})))")
    tl = pg.evaluate("window.TIMELINE"); dur = pg.evaluate("window.DURATION"); b.close()

json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), indent=1)
# SFX cues: whoosh into every rank card, a hit when the number lands, pops as stats/ratings reveal
cues = []
for s in tl:
    if s["kind"] == "rank":
        cues += [{"t": s["start"] - 0.15, "sfx": "whoosh"}, {"t": s["start"] + 0.45, "sfx": "hit"}]
    if s["kind"] == "item":
        it = next(i for i in data["items"] if i.get("title") == s["title"])
        n = len(it.get("stats", []))
        cues += [{"t": s["start"] + 0.9 + 0.4 + j * 0.7, "sfx": "pop"} for j in range(n)]
        r0 = s["start"] + (1.3 + n * 0.7 + 1.0 if n else 1.2) + 0.5
        cues += [{"t": r0 + j * 0.35, "sfx": "tick"} for j in range(len(it.get("ratings", {})))]
    if s["kind"] == "clip":
        cues.append({"t": s["start"] - 0.2, "sfx": "whoosh"})
    if s["kind"] == "intro":
        cues.append({"t": 0.15, "sfx": "hit"})
json.dump(cues, open(os.path.join(out, "cues.json"), "w"), indent=1)

def mmss(t): t = int(t); return f"{t//60}:{t%60:02d}"
# YouTube needs the first chapter at 0:00 and every chapter >= 10 s, so the short intro joins the first rank
ranks = [s for s in tl if s["kind"] == "rank"]
ch = [f"{'0:00' if i == 0 else mmss(s['start'])} {s['label']} {s['title']}" if s['label'] != str(s.get('year')) else f"{'0:00' if i == 0 else mmss(s['start'])} {s['title']} ({s['year']})" for i, s in enumerate(ranks)]
ch.append(f"{mmss([s for s in tl if s['kind']=='outro'][0]['start'])} Outro")
open(os.path.join(out, "chapters.txt"), "w", encoding="utf-8").write("\n".join(ch) + "\n")

print(f"duration {dur:.1f} s, {len(data['items'])} items, {sum(1 for x in tl if x['kind']=='clip')} clips, mode {data.get('mode','countdown')} | JS errors: {errs or 'none'}")
if missing: print("MISSING files (skipped / placeholder used):", ", ".join(missing))
bad = [x for x in broken if x]
if bad: print("UNREADABLE images:", ", ".join(bad))
