"""Transcribe + translate long recordings with Sarvam's real-time endpoints, in 25-second pieces.

Uses SARVAM_STT_API_KEY only (the main key is reserved for file-upload jobs, with the user's OK).
Writes data/roleplay_recordings/transcripts/<name>.txt with the Hindi transcript and the English translation per piece.

Usage: python app/spike/transcribe_chunks.py "<audio file>" ["<audio file>" ...]
"""
import os
import subprocess
import sys
import tempfile

import requests

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "data", "roleplay_recordings", "transcripts")
KEY = next(l.split("=", 1)[1].strip().strip('"\'') for l in open(os.path.join(REPO, ".env"), encoding="utf-8")
           if l.startswith("SARVAM_STT_API_KEY="))
PIECE = 25


def call(url, data, wav):
    with open(wav, "rb") as fh:
        r = requests.post(url, headers={"api-subscription-key": KEY}, data=data,
                          files={"file": ("a.wav", fh, "audio/wav")}, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"{url.rsplit('/', 1)[1]} HTTP {r.status_code}: {r.text[:200]}")
    return r.json().get("transcript", "")


def run(path):
    name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", "-f", "segment",
                    "-segment_time", str(PIECE), os.path.join(tmp, "p%03d.wav")], check=True)
    pieces = sorted(os.listdir(tmp))
    hi, en = [], []
    for p in pieces:
        w = os.path.join(tmp, p)
        hi.append(call("https://api.sarvam.ai/speech-to-text", {"model": "saarika:v2.5", "language_code": "unknown"}, w))
        en.append(call("https://api.sarvam.ai/speech-to-text-translate", {"model": "saaras:v2.5"}, w))
    with open(os.path.join(OUT, f"{name}.txt"), "w", encoding="utf-8") as f:
        f.write(f"# {name} ({len(pieces)} pieces of {PIECE}s)\n\n## English\n\n" + "\n".join(en) +
                "\n\n## Original\n\n" + "\n".join(hi) + "\n")
    print(f"{name}: {len(pieces)} pieces done")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        try:
            run(a)
        except Exception as e:
            print(f"FAILED {a}: {e}")
            sys.exit(1)
