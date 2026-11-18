"""Music bed + sound effects (+ optional rank voice) for a countdown video.

Usage: python3 countdown_audio.py _work/ mix.wav [--music track.mp3] [--music-vol 0.5]
                                  [--voice vo_dir] [--bpm 112]
Without --music it synthesizes an original upbeat loop (copyright-free).
--voice: a folder with NN.wav per countdown rank, from voiceover lines like "Number 5. Corpse Bride."
"""
import argparse, json, os, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, lfilter, resample_poly

ap = argparse.ArgumentParser()
ap.add_argument("work"); ap.add_argument("out")
ap.add_argument("--music"); ap.add_argument("--music-vol", type=float, default=0.5)
ap.add_argument("--voice"); ap.add_argument("--bpm", type=float, default=112)
ap.add_argument("--clip-music", type=float, default=0.12, help="music level while a trailer clip plays")
a = ap.parse_args()
SR = 48000
tl = json.load(open(os.path.join(a.work, "timeline.json"))); cues = json.load(open(os.path.join(a.work, "cues.json")))
D = tl[-1]["start"] + tl[-1]["dur"]; N = int(D * SR) + SR
t_all = np.arange(N) / SR
rng = np.random.default_rng(3)

def add(arr, st, sig):
    st = int(st)
    if st >= len(arr) or st + len(sig) <= 0: return
    if st < 0: sig = sig[-st:]; st = 0
    e = min(len(arr), st + len(sig)); arr[st:e] += sig[:e - st]
def env(n, a_=0.005, r=0.2):
    x = np.arange(n) / SR; return np.minimum(1, x / a_) * np.exp(-x / r)
f = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---------- music ----------
if a.music:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.music, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    m = np.frombuffer(raw, np.float32).astype(float)
    m = np.tile(m, int(np.ceil(N / len(m))))[:N]
else:
    m = np.zeros(N); beat = 60 / a.bpm
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    nbeats = int(D / beat) + 2
    kick_n = int(.25 * SR); xk = np.arange(kick_n) / SR
    kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-xk * 30)) * xk) * np.exp(-xk * 9)
    hat = lfilter(*butter(2, 7000 / (SR / 2), "high"), rng.standard_normal(int(.05 * SR))) * env(int(.05 * SR), .001, .015)
    for b in range(nbeats):
        st = b * beat * SR; bar = b // 4; ch = prog[bar % 4]
        add(m, st, kick * .9)
        add(m, st + beat / 2 * SR, hat * .25)
        if b % 2 == 1: add(m, st, lfilter(*butter(2, [1500 / (SR / 2), 6000 / (SR / 2)], "band"), rng.standard_normal(int(.12 * SR))) * env(int(.12 * SR), .002, .05) * .5)  # clap
        n_b = int(beat * SR); xb = np.arange(n_b) / SR
        add(m, st, np.sign(np.sin(2 * np.pi * f(ch[0] - 24) * xb)) * env(n_b, .005, .18) * .16)  # bass
        for i8 in range(2):  # arpeggio 8ths
            note = ch[(b * 2 + i8) % 3] + 12; n8 = int(beat / 2 * SR); x8 = np.arange(n8) / SR
            add(m, st + i8 * n8, (np.sin(2 * np.pi * f(note) * x8) + .3 * np.sin(4 * np.pi * f(note) * x8)) * env(n8, .003, .12) * .12)
        if b % 4 == 0:  # pad
            n4 = int(4 * beat * SR); x4 = np.arange(n4) / SR
            add(m, st, sum(np.sin(2 * np.pi * f(n) * x4) for n in ch) * np.minimum(1, x4 / .3) * np.minimum(1, (4 * beat - x4) / .3) * .05)
m = m / (np.max(np.abs(m)) or 1)
m = m * np.minimum(1, t_all / 1.5) * np.minimum(1, np.maximum(0, (D - t_all) / 3)) * a.music_vol

# ---------- SFX ----------
fx = np.zeros(N)
def whoosh():
    n = int(.6 * SR); x = np.linspace(0, 1, n); s = rng.standard_normal(n)
    return lfilter(*butter(2, [400 / (SR / 2), 4000 / (SR / 2)], "band"), s) * np.sin(np.pi * x) ** 2 * .35
def hit():
    n = int(.6 * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * (40 + 120 * np.exp(-x * 25)) * x) * np.exp(-x * 6) + lfilter(*butter(2, 3000 / (SR / 2)), rng.standard_normal(n)) * np.exp(-x * 30) * .4) * .8
def pop():
    n = int(.12 * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * (500 + 900 * x / .12) * x) * np.exp(-x * 40) * .35
def tick():
    n = int(.15 * SR); x = np.arange(n) / SR; return (np.sin(2 * np.pi * 1760 * x) + .5 * np.sin(2 * np.pi * 2640 * x)) * np.exp(-x * 30) * .18
SFX = {"whoosh": whoosh, "hit": hit, "pop": pop, "tick": tick}
for c in cues: add(fx, c["t"] * SR, SFX[c["sfx"]]())

# ---------- optional voice ----------
vo = np.zeros(N)
if a.voice:
    ranks = [s for s in tl if s["kind"] == "rank"]
    for i, s in enumerate(ranks):
        p = os.path.join(a.voice, f"{i:02d}.wav")
        if not os.path.exists(p): continue
        w, sr = sf.read(p); w = w.mean(1) if w.ndim > 1 else w
        if sr != SR: w = resample_poly(w, SR, sr)
        add(vo, (s["start"] + 0.35) * SR, w * .9)
    # duck music under the voice
    envv = np.convolve(np.abs(vo), np.ones(4800) / 4800, mode="same"); m = m * (1 - .6 * np.clip(envv * 8, 0, 1))

# ---------- trailer clips: their own audio, music ducked underneath ----------
ca = np.zeros(N); duck = np.ones(N)
for k, s in enumerate([s for s in tl if s["kind"] == "clip"]):
    a0, a1 = int(s["start"] * SR), int((s["start"] + s["dur"]) * SR)
    ramp = int(.5 * SR)
    duck[a0:a1] = a.clip_music
    duck[max(0, a0 - ramp):a0] = np.linspace(1, a.clip_music, a0 - max(0, a0 - ramp))
    duck[a1:a1 + ramp] = np.linspace(a.clip_music, 1, len(duck[a1:a1 + ramp]))
    p = os.path.join(a.work, f"clipaudio_{k}.wav")
    if os.path.exists(p):
        w, sr = sf.read(p); w = w.mean(1) if w.ndim > 1 else w
        w = w / (np.max(np.abs(w)) or 1) * .9
        fade = np.minimum(1, np.minimum(np.arange(len(w)), len(w) - np.arange(len(w))) / (.3 * SR))
        add(ca, a0, w * fade)
m = m * duck
mix = (m + fx + vo + ca)[: int(D * SR)]; mix = mix / max(1, np.max(np.abs(mix)) / .95)
sf.write(a.out, np.stack([mix, mix], 1), SR); print("audio", round(D, 1), "s ->", a.out)
