"""Transcribe a call recording with Sarvam speech-to-text (voice use of the Sarvam API).

Splits the audio into <= 25 s chunks (realtime STT limit is 30 s) with the ffmpeg bundled in
imageio_ffmpeg, calls Sarvam STT per chunk, and writes data/call_flows/<name>.json + .md.
Key from env SARVAM_API_KEY only; never written to disk.

Run: SARVAM_API_KEY=... python app/context/transcribe_call.py "<file.mp3>" [--chunk 25] [--model saarika:v2.5]
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "call_flows"))


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def duration(ff, path):
    out = subprocess.run([ff, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else None


def stt(key, wav, model, lang):
    with open(wav, "rb") as f:
        r = requests.post("https://api.sarvam.ai/speech-to-text", headers={"api-subscription-key": key}, timeout=90,
                          files={"file": (os.path.basename(wav), f, "audio/wav")},
                          data={"model": model, "language_code": lang})
    if r.status_code != 200:
        return {"error": f"{r.status_code}: {r.text[:160]}"}
    return r.json()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("audio")
    a.add_argument("--chunk", type=int, default=25)
    a.add_argument("--model", default="saarika:v2.5")
    a.add_argument("--lang", default="unknown")
    p = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    key = os.environ.get("SARVAM_API_KEY") or sys.exit("set SARVAM_API_KEY")
    ff = ffmpeg()
    total = duration(ff, p.audio)
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.splitext(os.path.basename(p.audio))[0])
    os.makedirs(ROOT, exist_ok=True)
    segs, t0 = [], time.time()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", p.audio, "-ac", "1", "-ar", "16000", "-f", "segment",
                        "-segment_time", str(p.chunk), "-c:a", "pcm_s16le", os.path.join(tmp, "c%04d.wav")], check=True)
        for i, wav in enumerate(sorted(glob.glob(os.path.join(tmp, "c*.wav")))):
            j = stt(key, wav, p.model, p.lang)
            segs.append({"start_sec": i * p.chunk, "text": j.get("transcript", ""), "language": j.get("language_code"),
                         "error": j.get("error")})
            print(f"chunk {i} @ {i * p.chunk}s: {(j.get('language_code') or j.get('error'))}", file=sys.stderr)
    res = {"file": os.path.basename(p.audio), "seconds": total, "chunks": len(segs), "model": p.model,
           "stt_wall_sec": round(time.time() - t0, 1), "segments": segs}
    json.dump(res, open(os.path.join(ROOT, f"{name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, f"{name}.md"), "w", encoding="utf-8") as f:
        f.write(f"# Transcript: {res['file']} ({round(total or 0)} s, {len(segs)} chunks, {p.model})\n\n")
        for s in segs:
            f.write(f"- `{s['start_sec']:>4}s` [{s['language']}] {s['text'] or ('(error: ' + str(s['error']) + ')')}\n")
    print(os.path.join(ROOT, f"{name}.md"))


if __name__ == "__main__":
    main()
