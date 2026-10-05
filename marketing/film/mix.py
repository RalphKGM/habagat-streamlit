"""Original soundtrack (synthesised here, so no licensing questions) + voice-over mix -> audio/mix.wav.

Music follows timeline.json: wind-noise intro, a lift into the logo, a soft marimba pulse under the
product scenes, and a resolve on the end card. It ducks under every voice line.
"""
import json, os, subprocess
import numpy as np

SR = 48000
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
TL = json.load(open("timeline.json"))
S = {s["id"]: s for s in TL["scenes"]}
N = int((TL["duration"] + 0.6) * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(4)


def decode(path):
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def hz(n):  # MIDI note -> Hz
    return 440 * 2 ** ((n - 69) / 12)


def env(x, a, b, fade_in=0.5, fade_out=0.5):
    """1 between a and b with linear fades, 0 outside."""
    return np.clip(np.minimum((x - a) / fade_in + 1, (b - x) / fade_out + 1), 0, 1)


def lowpass(x, cutoff):
    """Gentle zero-phase low-pass (first-order magnitude response) via FFT."""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / cutoff) ** 2), len(x))


music = np.zeros(N)

# --- chord pad: D major colour, 3 s per chord (80 bpm bars) ---
CHORDS = [[50, 57, 61, 64, 66], [47, 54, 57, 62, 66], [43, 50, 54, 57, 62], [45, 52, 57, 61, 64]]  # Dmaj9 Bm7 Gmaj9 A
BAR = 3.0
pad = np.zeros(N)
start_pad = 0.2
nb = int((TL["duration"] - start_pad) // BAR) + 2
for b in range(nb):
    t0 = start_pad + b * BAR
    ch = CHORDS[b % 4] if t0 < S["end"]["from"] - 0.5 else CHORDS[0]
    seg = env(t, t0, t0 + BAR, 1.2, 1.4)
    for n in ch:
        f = hz(n)
        for det in (-0.12, 0.12):
            ph = 2 * np.pi * f * (1 + det / 100) * t
            pad += seg * (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)) / len(ch)
pad *= 0.10 * (0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t))
pad *= env(t, start_pad, TL["duration"] + 0.3, 3.0, 2.2)
music += pad

# --- monsoon wind: filtered noise swell under the intro ---
noise = rng.standard_normal(N)
wind = lowpass(noise, 500) - lowpass(noise, 120)
wind *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.18 * t + 1)) * env(t, 0.0, S["map"]["from"] + 0.4, 1.2, 1.0)
wind += 0.4 * (lowpass(noise, 300) - lowpass(noise, 90)) * env(t, S["end"]["from"], TL["duration"], 1.5, 2)
music += 0.22 * wind / (np.abs(wind).max() + 1e-9)

# --- riser into the logo, then a low hit ---
br = S["map"]["from"]
rise = env(t, br - 1.2, br, 1.2, 0.02) * (lowpass(noise, 3000) - lowpass(noise, 600))
music += 0.18 * rise / (np.abs(rise).max() + 1e-9) * np.clip((t - (br - 1.2)) / 1.2, 0, 1) ** 2
hit = (t >= br) * np.exp(-np.maximum(t - br, 0) * 2.2) * np.sin(2 * np.pi * hz(38) * (t - br))
music += 0.35 * hit

# --- marimba pulse: 8th-note arpeggio from the logo to the end card ---
def pluck(t0, f, amp):
    i0 = int(t0 * SR); L = int(1.2 * SR)
    if i0 >= N: return
    L = min(L, N - i0); x = np.arange(L) / SR
    w = (np.sin(2 * np.pi * f * x) + 0.35 * np.sin(2 * np.pi * 4 * f * x) * np.exp(-x * 18)) * np.exp(-x * 5.5)
    w *= np.clip(x / 0.004, 0, 1)
    music[i0:i0 + L] += amp * w

e8 = BAR / 8
p0, p1 = br + 0.0, S["end"]["from"] + 0.2
k = 0; tt = p0
while tt < p1:
    b = int((tt - start_pad) // BAR); ch = CHORDS[b % 4]
    pat = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[4] + 12, ch[3] + 12, ch[2] + 12, ch[3] + 12]
    build = min(1, (tt - p0) / 3) * (1.15 if S["stat"]["from"] <= tt < S["stat"]["to"] else 1)
    acc = 1.0 if k % 2 == 0 else 0.7
    pluck(tt, hz(pat[k % 8]), 0.075 * build * acc)
    k += 1; tt = p0 + k * e8
# sub bass on chord roots
for b in range(nb):
    t0 = start_pad + b * BAR
    if br <= t0 < S["end"]["from"]:
        seg = env(t, t0, t0 + BAR, 0.05, 0.6)
        music += 0.09 * seg * np.sin(2 * np.pi * hz(CHORDS[b % 4][0] - 12) * t)
# final resolve chime
for n, d in ((74, 0), (78, 0.12), (81, 0.24), (86, 0.36)):
    pluck(S["end"]["voAt"] + 1.6 + d, hz(n), 0.06)

# --- voice-over and ducking ---
voice = np.zeros(N); duck = np.ones(N)
for s in TL["scenes"]:
    v = decode(f"audio/vo_{s['vo']}.mp3"); i = int(s["voAt"] * SR)
    v = v[: N - i]; voice[i:i + len(v)] += v
    duck = np.minimum(duck, 1 - 0.55 * env(t, s["voAt"], s["voAt"] + s["voDur"], 0.25, 0.5))
music *= duck
music /= np.abs(music).max() + 1e-9
voice /= np.abs(voice).max() + 1e-9
mix = 0.9 * voice + 0.32 * music
fade = env(t, 0, TL["duration"], 0.05, 1.2)
mix *= fade
mix /= np.abs(mix).max() / 0.89
stereo = np.stack([mix, mix], 1)
# subtle width on music only
stereo[:, 0] += 0.04 * np.roll(music, 300) * fade; stereo[:, 1] -= 0.04 * np.roll(music, 300) * fade
os.makedirs("audio", exist_ok=True)
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-ar", str(SR), "audio/mix.wav"], input=stereo.astype(np.float64).tobytes(), check=True)
print("wrote audio/mix.wav", round(N / SR, 2), "s")
