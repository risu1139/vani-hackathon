"""Voice override spike: does a per-call text_to_speech_config (speaker_id UUID, pace, pitch) and
initial_language_name change what the Sarvam agent sounds like?

Each case opens a CALL session, records only the agent's greeting (~12 s), then hangs up. Same opening text
for the voice/pace/pitch cases so speech duration is comparable. Measures: voiced duration, median F0
(male ~85-155 Hz, female ~165-255 Hz), and a Sarvam STT transcript. WAVs saved to outputs/voice_override/.
"""
import asyncio
import base64
import io
import json
import os
import time
import wave

import numpy as np
import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

from call_spike import ROOT, SR, Line

OPEN = "Namaste! Main IndiaMART se bol raha hoon. Kya aapke paas do minute hain?"
ANAND_M = "01a0e8fc-8a76-72d3-ae24-89b4688928eb"  # Anand - Documentary Voice, male, TTS v4, Hindi
AARTI_F = "01a0cf16-90ae-7470-941d-2c1f17b37528"  # Aarti - Support Agent, female, TTS v4, Hindi
CASES = [
    ("default", {"initial_bot_message": OPEN}),
    ("anand_m_p1.0", {"initial_bot_message": OPEN, "text_to_speech_config": {"speaker_id": ANAND_M, "speech_settings": {"pace": 1.0}}}),
    ("aarti_f_p0.85", {"initial_bot_message": OPEN, "text_to_speech_config": {"speaker_id": AARTI_F, "speech_settings": {"pace": 0.85}}}),
    ("aarti_f_p1.25", {"initial_bot_message": OPEN, "text_to_speech_config": {"speaker_id": AARTI_F, "speech_settings": {"pace": 1.25}}}),
    ("aarti_f_pitch+0.2", {"initial_bot_message": OPEN, "text_to_speech_config": {"speaker_id": AARTI_F, "speech_settings": {"pace": 1.0, "pitch": 0.2}}}),
    ("aarti_f_pitch-0.2", {"initial_bot_message": OPEN, "text_to_speech_config": {"speaker_id": AARTI_F, "speech_settings": {"pace": 1.0, "pitch": -0.2}}}),
    ("lang_english_no_opening", {"initial_language_name": "English"}),
]
OUT = ROOT / "outputs" / "voice_override"


async def record(name, extra, secs=12):
    buf = bytearray()

    async def on_audio(m):
        buf.extend(base64.b64decode(m.audio_base64 or ""))

    async def on_tr(m):
        pass

    cfg = InteractionConfig(org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"],
                            app_id=os.environ["SARVAM_AGENT_APP_ID"], version=1, interaction_type=InteractionType.CALL,
                            user_identifier_type=UserIdentifierType.CUSTOM, user_identifier=f"voice-{name}-{int(time.time())}",
                            sample_rate=SR, agent_variables={"seller_mode": "neutral", "persona_directive": "Continue normally."},
                            **extra)
    a = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg,
                          audio_callback=on_audio, transcript_callback=on_tr)
    await a.start()
    await a.wait_for_connect()
    line = Line(a)
    t = asyncio.create_task(line.run())
    await asyncio.sleep(secs)
    await a.stop()
    t.cancel()
    return bytes(buf)


def f0_median(x):
    """Median F0 over voiced 40 ms frames via autocorrelation (60-400 Hz)."""
    f, hop = int(0.04 * SR), int(0.01 * SR)
    vals = []
    for i in range(0, len(x) - f, hop):
        fr = x[i:i + f] - x[i:i + f].mean()
        if np.sqrt((fr ** 2).mean()) < 1500:
            continue
        ac = np.correlate(fr, fr, "full")[f - 1:]
        lo, hi = SR // 400, SR // 60
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.4 * ac[0]:
            vals.append(SR / k)
    return (round(float(np.median(vals)), 1), len(vals)) if vals else (None, 0)


def voiced_seconds(x):
    f = int(0.02 * SR)
    fr = x[: len(x) // f * f].reshape(-1, f)
    rms = np.sqrt((fr.astype(np.float64) ** 2).mean(axis=1))
    on = np.where(rms > 700)[0]
    return round((on[-1] - on[0] + 1) * 0.02, 2) if len(on) else 0.0, round(float((rms > 700).mean() * len(rms) * 0.02), 2)


def stt(wav_bytes):
    r = requests.post("https://api.sarvam.ai/speech-to-text", headers={"api-subscription-key": os.environ["SARVAM_API_KEY"]},
                      files={"file": ("g.wav", wav_bytes, "audio/wav")}, data={"model": "saarika:v2.5", "language_code": "unknown"},
                      timeout=60)
    j = r.json()
    return j.get("transcript", r.text[:200]), j.get("language_code")


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, extra in CASES:
        try:
            pcm = await record(name, extra)
        except Exception as e:  # e.g. rejected override
            rows.append({"case": name, "error": repr(e)[:300]})
            print(name, "ERROR", repr(e)[:300])
            continue
        x = np.frombuffer(pcm, dtype=np.int16).astype(np.float64)
        w = io.BytesIO()
        with wave.open(w, "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm)
        (OUT / f"{name}.wav").write_bytes(w.getvalue())
        span, active = voiced_seconds(x)
        f0, nf = f0_median(x)
        text, lang = stt(w.getvalue())
        row = {"case": name, "speech_span_s": span, "active_speech_s": active, "f0_median_hz": f0, "voiced_frames": nf,
               "stt_lang": lang, "transcript": text}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
        await asyncio.sleep(2)
    (OUT / "results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
