"""Voice-over per beat with Sarvam Bulbul v3; writes one WAV per beat and prints its length.

Usage: python app/video/voice.py <scene> [--speaker rahul] [--only 3,5]
Lines are spelled for speech (Vaani, sixty-two, G S T) so the voice says them right; the screen keeps the normal spelling.
Skips a beat whose WAV already exists unless it is named in --only (credits are low).
"""
import argparse
import base64
import io
import json
import os
import wave

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SR = 24000

LINES = {
    "scene12": [
        "IndiaMART knows a lot about each seller. Business, categories, past calls.",
        "Every call has one objective: a meeting with an IndiaMART executive.",
        "But today, Vaani speaks to every seller the same way, for the whole call.",
        "When a seller is in a rush, Vaani does not change.",
        "In these calls, meetings fall by half.",
        "We close this gap with a persona for each seller.",
        "For each seller, we read sixty-two data points.",
        "Business. Catalogue. Buy leads. Competitors. Past calls.",
        "Each one gives Vaani a reason to meet.",
        "Before the model sees anything, personal data is removed.",
        "Names become tokens. Phone, G S T and PAN stay inside IndiaMART.",
    ],
}


def env_key(name):
    for line in open(os.path.join(REPO, ".env"), encoding="utf-8"):
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit(f"{name} missing in .env")


def tts(text, speaker, key, pace=1.0):
    r = requests.post("https://api.sarvam.ai/text-to-speech", timeout=60, headers={"api-subscription-key": key},
                      json={"text": text, "target_language_code": "en-IN", "model": "bulbul:v3", "speaker": speaker,
                            "speech_sample_rate": SR, "pace": pace})
    if r.status_code != 200:
        raise SystemExit(f"TTS {r.status_code}: {r.text[:300]}")
    return base64.b64decode(r.json()["audios"][0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--speaker", default="shubh")
    ap.add_argument("--pace", type=float, default=0.85)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {int(i) for i in a.only.split(",") if i}
    out = os.path.join(HERE, "build", a.scene, "audio")
    os.makedirs(out, exist_ok=True)
    key = env_key("SARVAM_STT_API_KEY")
    lengths = {}
    for n, line in enumerate(LINES[a.scene], 1):
        path = os.path.join(out, f"beat{n:02d}.wav")
        if not os.path.exists(path) or n in only:
            open(path, "wb").write(tts(line, a.speaker, key, a.pace))
        with wave.open(path) as w:
            lengths[n] = round(w.getnframes() / w.getframerate(), 2)
        print(n, lengths[n], line)
    json.dump(lengths, open(os.path.join(out, "lengths.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
