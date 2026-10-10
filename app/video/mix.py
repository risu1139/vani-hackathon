"""Trim silence from each beat's voice line, set beat lengths, and build the scene's voice track.

Usage: python app/video/mix.py <scene> [--gap 0.35]
Writes build/<scene>/audio/durs.json (beat lengths for render.mjs --durs) and build/<scene>/audio/voice.wav.
"""
import argparse, json, os, subprocess, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("scene"); ap.add_argument("--gap", type=float, default=0.35); a = ap.parse_args()
aud = os.path.join(HERE, "build", a.scene, "audio")
ff = lambda *x: subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *x], check=True)
durs, parts = [], []
n = 1
while os.path.exists(os.path.join(aud, f"beat{n:02d}.wav")):
    src, trim = os.path.join(aud, f"beat{n:02d}.wav"), os.path.join(aud, f"trim{n:02d}.wav")
    # cut silence at both ends (reverse trick for the tail)
    ff("-i", src, "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse", trim)
    with wave.open(trim) as w:
        d = round(w.getnframes() / w.getframerate() + a.gap, 2)
    durs.append(d); parts.append((trim, d)); n += 1
inputs = sum((["-i", p] for p, _ in parts), [])
pads = "".join(f"[{i}]apad,atrim=0:{d}[p{i}];" for i, (_, d) in enumerate(parts))
ff(*inputs, "-filter_complex", pads + "".join(f"[p{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[o]", "-map", "[o]", os.path.join(aud, "voice.wav"))
json.dump(durs, open(os.path.join(aud, "durs.json"), "w"))
print(durs, "total", round(sum(durs), 2))
